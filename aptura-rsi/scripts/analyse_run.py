"""Turn finished `stbench eval` runs into failure modes, skill interventions and a
measured verdict on the last intervention.

    uv run python analyse_run.py runs/h4-v1 --propose-skill submissions/curator/health
    uv run python analyse_run.py runs/h4-v2 --prev runs/h4-v1

Reads only what the harness already writes: `attempts.jsonl` (per-attempt score and
Harbor trial dir), each trial's `verifier/verdicts.json` rubric grades, and the
learner's own trajectory (`agent/trajectory.json`, `agent/response.txt`). The curator
is OpenAI (`OPENAI_API_KEY`), separate from the frozen learner in hackathon.toml.

With `--prev` the report leads with FIXED / REGRESSED / NEW / MARGINAL measured
rubric-item by rubric-item against the previous run, then updates the standing
beliefs about the learner instead of assuming the last intervention worked.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from dotenv import load_dotenv

EVIDENCE_CHARS = 400
RESPONSE_CHARS = 1800
PROMPT_CHARS = 900
DEFAULT_MODEL = "gpt-5"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

PHILOSOPHY = (
    "You are the curator in a sequential-experimental-design loop over a frozen learner "
    "model whose only lever is a read-only SKILL.md. Work by these rules:\n"
    "- Infer failure modes from what the learner actually did in its trajectory, not from "
    "the wording of rubric items; rubric text is evidence about the learner, not the label.\n"
    "- Prefer explanations and interventions that account for several failures through one "
    "common mechanism over per-symptom patches.\n"
    "- Name competing hypotheses explicitly and prefer the smallest intervention that would "
    "distinguish them.\n"
    "- When the evidence is insufficient, say which single observation would have the highest "
    "value of information.\n"
    "- Prioritise by expected improvement, generality across tasks, cost and risk of "
    "regression, and stay calibrated: say when you are guessing.\n"
    "Reply with JSON only."
)


@dataclass
class FailedItem:
    """One rubric item the learner lost points on."""
    id: str
    task_name: str
    kind: str  # "missed_positive" | "penalty_incurred"
    criterion: str
    explanation: str
    points: float
    impact: float  # fraction of the task's attainable score that this cost
    trial_dir: str


@dataclass
class Mode:
    name: str
    description: str
    mechanism: str = ""
    items: list[FailedItem] = field(default_factory=list)

    @property
    def tasks(self) -> list[str]:
        return sorted({i.task_name for i in self.items})

    @property
    def impact(self) -> float:
        return sum(i.impact for i in self.items)


# ------------------------------------------------------------------ loading

def load_attempts(run_dir: Path, arm: str | None) -> tuple[list[dict], str]:
    path = run_dir / "attempts.jsonl"
    if not path.exists():
        sys.exit(f"{path} not found: point me at an `stbench eval --out` directory")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    arms = sorted({r["arm"] for r in rows})
    if arm is None:
        arm = "skill" if "skill" in arms else arms[0]
    if arm not in arms:
        sys.exit(f"arm {arm!r} not in this run; available: {', '.join(arms)}")
    return [r for r in rows if r["arm"] == arm and r.get("trial_dir")], arm


def rubric_rows(attempts: list[dict]) -> dict[tuple[str, str], dict]:
    """(task, criterion) -> rubric record, for every graded rubric item."""
    out: dict[tuple[str, str], dict] = {}
    for row in attempts:
        verdicts = Path(row["trial_dir"]) / "verifier" / "verdicts.json"
        if not verdicts.exists():
            continue
        for r in json.loads(verdicts.read_text()).get("rubrics") or []:
            out[(row["task_name"], r["criterion"].strip())] = r
    return out


def failed_items(attempts: list[dict]) -> tuple[list[FailedItem], list[str]]:
    """Missed positive rubric items and incurred negative ones, across attempts."""
    items: list[FailedItem] = []
    skipped: list[str] = []
    for row in attempts:
        verdicts = Path(row["trial_dir"]) / "verifier" / "verdicts.json"
        if not verdicts.exists():
            skipped.append(f"{row['task_name']}: no verdicts.json (status {row.get('status')})")
            continue
        rubrics = json.loads(verdicts.read_text()).get("rubrics") or []
        attainable = sum(r["points"] for r in rubrics if r["points"] > 0) or 1.0
        for idx, r in enumerate(rubrics):
            met, points = bool(r.get("criteria_met")), float(r["points"])
            if points > 0 and not met:
                kind, lost = "missed_positive", points
            elif points < 0 and met:
                kind, lost = "penalty_incurred", -points
            else:
                continue
            items.append(FailedItem(
                id=f"{row['task_name'][:24]}#{idx}",
                task_name=row["task_name"],
                kind=kind,
                criterion=r["criterion"].strip(),
                explanation=" ".join((r.get("explanation") or "").split())[:EVIDENCE_CHARS],
                points=points,
                impact=lost / attainable,
                trial_dir=row["trial_dir"],
            ))
    return items, skipped


def trajectories(attempts: list[dict]) -> list[dict]:
    """What the learner was asked and what it actually produced, per task."""
    out = []
    for row in attempts:
        trial = Path(row["trial_dir"])
        prompt = ""
        traj = trial / "agent" / "trajectory.json"
        if traj.exists():
            steps = json.loads(traj.read_text()).get("steps") or []
            user = next((s for s in steps if s.get("source") == "user"), None)
            prompt = " ".join((user or {}).get("message", "").split())[:PROMPT_CHARS]
        response = trial / "agent" / "response.txt"
        out.append({
            "task": row["task_name"],
            "score": round(float(row.get("score") or 0.0), 3),
            "prompt": prompt,
            "learner_response": " ".join(response.read_text().split())[:RESPONSE_CHARS]
            if response.exists() else "",
        })
    return out


# ------------------------------------------------------- measured comparison

def compare(prev_attempts: list[dict], cur_attempts: list[dict]) -> dict:
    """Rubric-item-level diff of two runs over the same tasks (no LLM involved)."""
    prev, cur = rubric_rows(prev_attempts), rubric_rows(cur_attempts)
    shared = sorted(set(prev) & set(cur))
    fixed, regressed = [], []
    for key in shared:
        was, now = bool(prev[key].get("criteria_met")), bool(cur[key].get("criteria_met"))
        points = float(cur[key]["points"])
        if was == now:
            continue
        gained = (now and points > 0) or (not now and points < 0)
        rec = {"task": key[0], "criterion": key[1], "points": points,
               "grader_said": " ".join((cur[key].get("explanation") or "").split())[:EVIDENCE_CHARS]}
        (fixed if gained else regressed).append(rec)

    prev_score = {a["task_name"]: float(a.get("score") or 0.0) for a in prev_attempts}
    cur_score = {a["task_name"]: float(a.get("score") or 0.0) for a in cur_attempts}
    common = sorted(set(prev_score) & set(cur_score))
    per_task = [{"task": t, "before": round(prev_score[t], 3), "after": round(cur_score[t], 3),
                 "delta": round(cur_score[t] - prev_score[t], 3)} for t in common]
    mean_before = sum(prev_score[t] for t in common) / max(len(common), 1)
    mean_after = sum(cur_score[t] for t in common) / max(len(common), 1)
    return {"fixed": sorted(fixed, key=lambda r: -abs(r["points"])),
            "regressed": sorted(regressed, key=lambda r: -abs(r["points"])),
            "per_task": per_task, "n_shared_items": len(shared),
            "mean_before": round(mean_before, 4), "mean_after": round(mean_after, 4),
            "mean_delta": round(mean_after - mean_before, 4),
            "improved_tasks": sum(1 for r in per_task if r["delta"] > 0),
            "worsened_tasks": sum(1 for r in per_task if r["delta"] < 0)}


# ----------------------------------------------------------------- LLM glue

class LLM:
    """Curator model: OpenAI chat completions in JSON mode."""

    def __init__(self, model: str, knowledge: str = ""):
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            sys.exit("OPENAI_API_KEY is unset (put it in .env)")
        self.key, self.model = key, model
        self.knowledge = knowledge

    def json_call(self, system: str, user: str, max_tokens: int = 10000) -> dict:
        if self.knowledge:
            system = (f"{system}\n\nReason inside the framework of this knowledge corpus; it "
                      f"governs how you diagnose, intervene and update.\n\n{self.knowledge}")
        body = {"model": self.model,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}]}
        # gpt-5 family: fixed temperature, and completion tokens under a new name.
        if self.model.startswith("gpt-5"):
            body["max_completion_tokens"] = max_tokens
        else:
            body["temperature"] = 0
            body["max_tokens"] = max_tokens
        resp = httpx.post(OPENAI_URL, headers={"Authorization": f"Bearer {self.key}"},
                          json=body, timeout=900.0)
        if resp.status_code >= 400:
            sys.exit(f"OpenAI {resp.status_code}: {resp.text[:400]}")
        text = resp.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.split("```")[1].removeprefix("json").strip()
        return json.loads(text)


def group_into_modes(llm: LLM, items: list[FailedItem], traj: list[dict]) -> list[Mode]:
    payload = [{"id": i.id, "task": i.task_name, "kind": i.kind,
                "criterion": i.criterion, "grader_said": i.explanation} for i in items]
    out = llm.json_call(
        PHILOSOPHY,
        "Below are (a) the learner's own trajectories for each task and (b) the rubric items "
        "it lost points on. Read the trajectories first and describe what the learner's "
        "behaviour is actually like; use the rubric items as evidence for that behaviour "
        "rather than as categories. Group the lost items into 3-6 failure modes named after "
        "the learner's BEHAVIOUR AND ITS MECHANISM, not after rubric topics. Every id must "
        "appear in exactly one mode.\n\n"
        'Reply as {"modes": [{"name": "<= 6 words", "description": "one sentence on what the '
        'learner does", "mechanism": "one sentence on why it does it, inferred from the '
        'trajectory", "item_ids": ["..."]}]}\n\n'
        f"TRAJECTORIES\n{json.dumps(traj, indent=1)}\n\nLOST RUBRIC ITEMS\n"
        f"{json.dumps(payload, indent=1)}")
    by_id = {i.id: i for i in items}
    modes = []
    for m in out["modes"]:
        picked = [by_id[i] for i in m.get("item_ids", []) if i in by_id]
        if picked:
            modes.append(Mode(name=m["name"], description=m.get("description", ""),
                              mechanism=m.get("mechanism", ""), items=picked))
    for leftover in set(by_id) - {i.id for m in modes for i in m.items}:
        modes.append(Mode(name="Ungrouped", description="not assigned by the grouping call",
                          items=[by_id[leftover]]))
    return sorted(modes, key=lambda m: (m.impact, len(m.tasks)), reverse=True)


def mode_brief(mode: Mode, n_tasks: int) -> dict:
    return {"name": mode.name, "description": mode.description, "mechanism": mode.mechanism,
            "affected_tasks": f"{len(mode.tasks)}/{n_tasks}",
            "score_impact": round(mode.impact / max(n_tasks, 1), 3),
            "examples": [{"criterion": i.criterion, "grader_said": i.explanation}
                         for i in sorted(mode.items, key=lambda i: -i.impact)[:4]]}


def individual_fixes(llm: LLM, briefs: list[dict], skill_md: str) -> list[dict]:
    out = llm.json_call(
        PHILOSOPHY,
        "For each failure mode below: give the most plausible root cause, one rival "
        "hypothesis that would produce the same rubric losses, and the SMALLEST SKILL.md "
        "instruction that both plausibly fixes the failure and discriminates between the two "
        "hypotheses (a few lines of prose, no new tools or pipelines). Also say which single "
        "extra observation would most reduce your uncertainty, and score the intervention.\n\n"
        'Reply as {"fixes": [{"mode": "<name>", "root_cause": "1-2 sentences", '
        '"rival_hypothesis": "1 sentence", "intervention": "the instruction to add, quoted '
        'concretely", "discriminates": "what outcome supports which hypothesis", '
        '"highest_value_observation": "1 sentence", "expected_improvement": "high|medium|low", '
        '"generality": "high|medium|low", "cost": "low|medium|high", '
        '"regression_risk": "low|medium|high"}]}\n\n'
        f"CURRENT SKILL.md\n{skill_md[:4000]}\n\nFAILURE MODES\n{json.dumps(briefs, indent=1)}")
    return out["fixes"]


def shared_fix(llm: LLM, briefs: list[dict], fixes: list[dict], skill_md: str) -> dict:
    return llm.json_call(
        PHILOSOPHY,
        "Look at these failure modes and their individual fixes together. Is one common "
        "mechanism generating both? Give the single smallest intervention that would improve "
        "both if that mechanism is real, and say what result would falsify it. Be honest if "
        "the modes are unrelated.\n\n"
        'Reply as {"common_cause": "1-2 sentences", "intervention": "the instruction to add", '
        '"why_it_helps": "2-4 sentences covering both modes", '
        '"falsified_if": "the observation that would refute the common mechanism", '
        '"expected_improvement": "high|medium|low", "regression_risk": "low|medium|high", '
        '"confidence": "high|medium|low"}\n\n'
        f"CURRENT SKILL.md\n{skill_md[:4000]}\n\nmodes: {json.dumps(briefs, indent=1)}\n"
        f"individual fixes: {json.dumps(fixes, indent=1)}")


def write_skill_md(llm: LLM, skill_dir: Path, current: str, shared: dict, fixes: list[dict],
                   briefs: list[dict], diff: dict | None, beliefs: dict | None) -> Path:
    """Apply the shared intervention to SKILL.md (previous version kept as .bak)."""
    out = llm.json_call(
        PHILOSOPHY,
        "Rewrite the SKILL.md below so that it implements the shared intervention (and, only "
        "where it costs nothing extra, the individual fixes). Write general procedure, not "
        "content: state how to decide what to say, never rigid output templates, fixed section "
        "counts, length caps or task-specific wording, and do not encode answers to the quoted "
        "tasks. It is read by a frozen model at the start of every task in this domain, so "
        "prefer instructions that transfer to unseen tasks. Keep the YAML frontmatter with "
        "`name` and `description` fields. No external URLs.\n\n"
        'Reply as {"skill_md": "the complete new file contents", "changed": "1-2 sentences on '
        'what you changed and why", "predicted_effect": "what should improve and what should '
        'stay stable if the mechanism is right"}\n\n'
        f"CURRENT SKILL.md\n{current}\n\nshared intervention: {json.dumps(shared, indent=1)}\n"
        f"individual fixes: {json.dumps(fixes, indent=1)}\nmodes: {json.dumps(briefs, indent=1)}\n"
        f"last experiment's measured result: {json.dumps(diff, indent=1)}\n"
        f"belief update: {json.dumps(beliefs, indent=1)}")
    text = out["skill_md"].strip() + "\n"
    if not text.startswith("---"):
        sys.exit("curator returned a SKILL.md without frontmatter; not writing it")
    skill_dir.mkdir(parents=True, exist_ok=True)
    target = skill_dir / "SKILL.md"
    if target.exists():
        shutil.copyfile(target, skill_dir / "SKILL.md.bak")
    target.write_text(text)
    return target


def belief_update(llm: LLM, diff: dict, prev_modes: list[dict], briefs: list[dict],
                  intervention: str) -> dict:
    return llm.json_call(
        PHILOSOPHY,
        "An intervention was applied to SKILL.md and the same tasks were re-run. Below are the "
        "measured rubric-level changes. Update your beliefs about the learner: did the "
        "intervention work through the mechanism you assumed, through another one, or not at "
        "all? Distinguish signal from noise given the sample size, and say what to do next.\n\n"
        'Reply as {"verdict": "worked|partially worked|no effect|harmful", '
        '"mechanism_check": "2-3 sentences on whether the assumed mechanism is supported", '
        '"belief_update": "2-3 sentences on what you now believe about the learner", '
        '"keep_or_revert": "keep|refine|revert, with one clause of reason", '
        '"next_experiment": "the single next experiment and why it has the highest value of '
        'information", "confidence": "high|medium|low"}\n\n'
        f"intervention: {intervention}\n"
        f"previous top modes: {json.dumps(prev_modes, indent=1)}\n"
        f"measured change: {json.dumps(diff, indent=1)}\n"
        f"current top modes: {json.dumps(briefs, indent=1)}")


# -------------------------------------------------------------------- report

def wrap(text: str, indent: str, hang: str | None = None) -> str:
    return textwrap.fill(str(text), width=96, initial_indent=indent,
                         subsequent_indent=hang if hang is not None else indent)


def short(task: str) -> str:
    return re.sub(r"^healthbench-hard-", "", task)[:16]


def delta_section(diff: dict, beliefs: dict | None, prev_dir: Path) -> list[str]:
    out = [f"MARGINAL  ·  measured against {prev_dir}", ""]
    out.append(f"   mean score {diff['mean_before']:.4f} -> {diff['mean_after']:.4f} "
               f"({diff['mean_delta']:+.4f})   tasks better/worse: "
               f"{diff['improved_tasks']}/{diff['worsened_tasks']}")
    for t in diff["per_task"]:
        out.append(f"   {short(t['task'])}  {t['before']:.3f} -> {t['after']:.3f}  "
                   f"{t['delta']:+.3f}")
    out.append(f"   rubric items comparable across both runs: {diff['n_shared_items']}")
    out += ["", f"FIXED  ·  {len(diff['fixed'])} rubric items recovered", ""]
    for r in diff["fixed"][:8]:
        out.append(wrap(f"[{short(r['task'])}] (+{abs(r['points']):g}) {r['criterion']}",
                        "   · ", "     "))
    if len(diff["fixed"]) > 8:
        out.append(f"   ... {len(diff['fixed']) - 8} more")
    out += ["", (f"REGRESSED  ·  {len(diff['regressed'])} rubric items lost that were "
                 "previously earned"), ""]
    for r in diff["regressed"][:8]:
        out.append(wrap(f"[{short(r['task'])}] (-{abs(r['points']):g}) {r['criterion']}",
                        "   · ", "     "))
        if r["grader_said"]:
            out.append(wrap(f'grader: "{r["grader_said"][:200]}"', "       "))
    if len(diff["regressed"]) > 8:
        out.append(f"   ... {len(diff['regressed']) - 8} more")
    if beliefs:
        out += ["", "BELIEF UPDATE", "",
                (f"   verdict: {beliefs.get('verdict', '?')} "
                 f"(confidence {beliefs.get('confidence', '?')})"),
                wrap(f"mechanism: {beliefs.get('mechanism_check', '')}", "   "),
                wrap(f"now believe: {beliefs.get('belief_update', '')}", "   "),
                wrap(f"skill: {beliefs.get('keep_or_revert', '')}", "   "),
                wrap(f"next experiment: {beliefs.get('next_experiment', '')}", "   ")]
    return out + [""]


def report(run_dir: Path, arm: str, n_tasks: int, modes: list[Mode], fixes: list[dict],
           shared: dict, skipped: list[str], diff: dict | None, beliefs: dict | None,
           prev_dir: Path | None, skill_path: Path | None) -> str:
    out = [f"RUN {run_dir}  ·  arm {arm}  ·  {n_tasks} graded tasks", ""]
    if diff is not None and prev_dir is not None:
        out += delta_section(diff, beliefs, prev_dir)
    out += ["NEW — HIGHEST-PRIORITY FAILURE MODES" if diff else "TOP FAILURE MODES", ""]
    for n, m in enumerate(modes, 1):
        out.append(f"{n}. {m.name}")
        out.append(f"   affected: {len(m.tasks)}/{n_tasks} tasks · {len(m.items)} rubric items")
        out.append(f"   score impact: -{m.impact / max(n_tasks, 1):.3f} mean score "
                   f"(-{m.impact:.2f} points-share total)")
        if m.mechanism:
            out.append(wrap(f"mechanism: {m.mechanism}", "   "))
        out.append(f"   tasks: {', '.join(short(t) for t in m.tasks[:6])}"
                   + (" ..." if len(m.tasks) > 6 else ""))
        for i in sorted(m.items, key=lambda i: -i.impact)[:3]:
            out.append(wrap(f"[{i.id}] {i.kind} (-{i.impact:.3f}) {i.criterion}", "   · ", "     "))
            if i.explanation:
                out.append(wrap(f'grader: "{i.explanation[:220]}"', "       "))
        out.append(f"   evidence: {m.items[0].trial_dir}/verifier/verdicts.json")
        out.append("")
    out += ["INDIVIDUAL INTERVENTIONS", ""]
    for n, f in enumerate(fixes, 1):
        out.append(f"{n}. [{f.get('mode', '?')}] {f.get('intervention', '')}")
        out.append(wrap(f"root cause: {f.get('root_cause', '')}", "   "))
        out.append(wrap(f"rival hypothesis: {f.get('rival_hypothesis', '')}", "   "))
        out.append(wrap(f"discriminates: {f.get('discriminates', '')}", "   "))
        out.append(wrap(f"highest-value observation: {f.get('highest_value_observation', '')}",
                        "   "))
        out.append(f"   expected improvement {f.get('expected_improvement', '?')} · generality "
                   f"{f.get('generality', '?')} · cost {f.get('cost', '?')} · regression risk "
                   f"{f.get('regression_risk', '?')}")
        out.append("")
    out += ["SHARED / ROOT INTERVENTION", "", wrap(shared.get("intervention", ""), "   "), "",
            wrap(f"common cause: {shared.get('common_cause', '')}", "   "),
            wrap(f"why this may fix both: {shared.get('why_it_helps', '')}", "   "),
            wrap(f"falsified if: {shared.get('falsified_if', '')}", "   "),
            (f"   expected improvement {shared.get('expected_improvement', '?')} · regression "
             f"risk {shared.get('regression_risk', '?')} · confidence "
             f"{shared.get('confidence', '?')}")]
    out += ["", "TEST NEXT", ""]
    if beliefs and beliefs.get("next_experiment"):
        out.append(wrap(f"1. {beliefs['next_experiment']}", "", "   "))
        start = 2
    else:
        out.append("1. shared/root intervention — one skill edit, both failure modes move if the "
                   "common mechanism is real")
        start = 2
    for n, f in enumerate(fixes, start):
        out.append(f"{n}. individual fix for {f.get('mode', '?')} "
                   f"(expected {f.get('expected_improvement', '?')}, regression risk "
                   f"{f.get('regression_risk', '?')})")
    if skill_path:
        out += ["", f"skill written: {skill_path} (previous kept as {skill_path}.bak)"]
    out += ["", f"inspect trajectories: uv run harbor view {run_dir}/harbor-jobs"]
    if skipped:
        out += ["", "SKIPPED ATTEMPTS"] + [f"  - {s}" for s in skipped]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--arm", default=None, help="which arm to analyse (default: skill)")
    ap.add_argument("--prev", type=Path, default=None,
                    help="previous run over the same tasks: adds FIXED/REGRESSED/MARGINAL")
    ap.add_argument("--top", type=int, default=2, help="failure modes to propose fixes for")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="curator model (OpenAI id)")
    ap.add_argument("--skill", type=Path, default=None,
                    help="skill folder the run used (for context; default: --propose-skill dir)")
    ap.add_argument("--propose-skill", type=Path, default=None,
                    help="write the shared intervention into this skill folder's SKILL.md")
    ap.add_argument("--knowledge", type=Path, default=None,
                    help="markdown corpus the curator must reason inside (e.g. "
                         "docs/curator_knowledge_corpus.md)")
    ap.add_argument("--json-out", type=Path, default=None, help="also write the raw analysis JSON")
    args = ap.parse_args()

    load_dotenv()
    attempts, arm = load_attempts(args.run_dir, args.arm)
    items, skipped = failed_items(attempts)
    if not items:
        sys.exit("no failed rubric items found: nothing to analyse")
    n_tasks = len({a["task_name"] for a in attempts})
    print(f"{len(items)} failed rubric items across {n_tasks} tasks · curator {args.model}",
          file=sys.stderr)

    diff = prev_analysis = None
    if args.prev:
        prev_attempts, _ = load_attempts(args.prev, arm)
        diff = compare(prev_attempts, attempts)
        prev_json = args.prev / "failure_analysis.json"
        prev_analysis = json.loads(prev_json.read_text()) if prev_json.exists() else None
        print(f"vs {args.prev}: {len(diff['fixed'])} fixed, {len(diff['regressed'])} regressed, "
              f"mean {diff['mean_delta']:+.4f}", file=sys.stderr)

    skill_src = args.skill or args.propose_skill
    skill_md = (skill_src / "SKILL.md").read_text() if skill_src and (
        skill_src / "SKILL.md").exists() else "(none provided)"

    llm = LLM(args.model, args.knowledge.read_text() if args.knowledge else "")
    modes = group_into_modes(llm, items, trajectories(attempts))
    briefs = [mode_brief(m, n_tasks) for m in modes[:args.top]]
    fixes = individual_fixes(llm, briefs, skill_md)
    shared = shared_fix(llm, briefs, fixes, skill_md)

    beliefs = None
    if diff is not None:
        beliefs = belief_update(
            llm, diff, (prev_analysis or {}).get("modes", [])[:args.top],
            briefs, ((prev_analysis or {}).get("shared") or {}).get("intervention", "unknown"))

    skill_path = None
    if args.propose_skill:
        skill_path = write_skill_md(llm, args.propose_skill, skill_md, shared, fixes, briefs,
                                    diff, beliefs)

    text = report(args.run_dir, arm, n_tasks, modes, fixes, shared, skipped, diff, beliefs,
                  args.prev, skill_path)
    print(text)
    (args.run_dir / "failure_analysis.txt").write_text(text + "\n")
    out_json = args.json_out or (args.run_dir / "failure_analysis.json")
    out_json.write_text(json.dumps({
        "run_dir": str(args.run_dir), "arm": arm, "n_tasks": n_tasks,
        "modes": [{"name": m.name, "description": m.description, "mechanism": m.mechanism,
                   "tasks": m.tasks, "impact": m.impact,
                   "items": [i.__dict__ for i in m.items]} for m in modes],
        "fixes": fixes, "shared": shared, "diff": diff, "beliefs": beliefs,
        "knowledge": str(args.knowledge) if args.knowledge else None,
        "skill_written": str(skill_path) if skill_path else None}, indent=1))


if __name__ == "__main__":
    main()
