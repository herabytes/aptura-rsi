# Handoff: Failure-to-Fix Workbench (τ³ hackathon prototype)

Status: the first artifact `failure-to-fix.html` (compiled from `body.html`) exists but is a long case study,
not the tool. Hera wants it REBUILT as a compact, click-around workbench. Nothing below needs new benchmark
runs — credits are nearly gone. Build only from the numbers in this file and the source files listed at the end.

## What to build (one standalone HTML file, plain HTML/CSS/JS, no server, no framework, <150 KB)

Name: **Failure-to-Fix Workbench** — label it "prototype · exploratory · built from τ³ hackathon data".
Audience: a technical founder opening an email on a Thursday afternoon, no knowledge of τ³ or mech-interp.
Must be understood in ~2 minutes. Punchy. Not an Arize clone, not a slide deck, not neuronpedia.

Layout: top bar with 3 tabs. **Workbench** (default) · **What happened (60 s)** · **Why it matters**.

### Tab 1 — Workbench
Left sidebar: failure-cluster list (name + affected-run count + status pill). Clicking a cluster fills the main pane:
1. **Cluster header**: one-sentence description, affected tasks, how it was measured (the proxy), status.
2. **Intervention records** (THE central object), one card per attempt, shown as a vertical sequence:
   Failure · Hypothesis · Intervention (exact wording/version) · Prediction (written before the run) ·
   Baseline vs result (always `k/n`, never only %) · Transfer · Decision (keep / revise / reject / bigger model) ·
   Evidence badge (`exploratory` | `replicated proxy result` | `held-out result` | `infrastructure failure` | `pending`).
3. **Trace comparison**: two columns, died vs survived, steps as a short arrow list; clicking a step expands
   tool name, text, visible-to-customer yes/no, finish_reason, hidden reasoning if any, task/run id.
4. **Arms bar chart** for the cluster (k/n bars, unresolved shown separately).
5. **Next test** panel: current evidence / remaining uncertainty / next experiment (text only).

### Tab 2 — What happened (60 s)
The causal chain as a short animated arrow list (one fade-in per step, nothing else animated):
HealthBench rubric explained missed points → τ³ pass/fail hid the mechanism → trajectory showed 43 near-identical
searches, 0 questions → built proxy metrics per failure → fixing one mechanism exposed the next → biggest cluster:
first message typed as plain reply, never reaching the customer → header removal did nothing (10/20→10/20),
emphasis-only was worse (5/20) → hidden reasoning: model planned the words, never the channel → bound the verbs
("'ask the customer' = call `send_message_to_user`") → 20/20 on tuning set → held-out: deaths halved, pass rate
unchanged → decision point: next mechanism or bigger model?
Button "Open in workbench" → Tab 1 with cluster A selected.

### Tab 3 — Why it matters
Business loop: expert feedback → instruction → model partly ignores it → expert reads failures → rewrite → re-eval.
The question: **when is it cheaper to improve the skill, use a larger model, change the harness, or accept the failure?**
Four short answers (copy from `body.html` section 6). Value: less expert review time, fewer iterations,
no unnecessary model upgrades, a written reason to abandon a fix that didn't transfer, negative results preserved.

### Honesty rules (non-negotiable)
- Turn-1 survival is a PROXY (first reply after `start_conversation` went out as a `send_message_to_user` call).
  It is the ONLY measure for arms v5–v9. Say so.
- The 4 tuning tasks (018, 044, 050, 101) were chosen BECAUSE they died at turn 1 → biased sample, not random.
- 20-run arms wobble ±3–4 (same content gave 13, 15, 14/18, 10). Emphasis "worse" (5 vs 10) may be partly noise.
- 20/20 is a tuning-set proxy result, not a benchmark gain. Held-out pass rate did NOT improve (5/20 vs 5/22).
- Header was NOT the cause. Emphasis does NOT help. No larger-model comparison exists — say "not tested".
- Infrastructure failures are never in learner denominators.

## Data (every number with source)

Setup: learner GLM-5.3-flash via Runware, harness OpenHands SDK, customer simulator Claude Sonnet 4.6,
benchmark τ³ retail-banking (30 tasks; 8 harness-invalid → 22 valid). Source: TAU3_NOTES.md.

### Full end-to-end pass (held-out result)
| arm | pass | notes | source |
|---|---|---|---|
| baseline (no skill) | 3/24 | several budget-exhausted (4M pool) | TAU3_RESULTS.md |
| v4 skill | 5/22 (006, 019, 035, 050, 059) | | TAU3_RESULTS.md |
| v9 verb binding | 5/20 (006, 021, 032, 099, 100) | 019 & 059 exhausted token budget mid-run (41 / 37 searches), unscored | runs/tau-v9-*, TAU3_NOTES.md |
| v9 turn-1 plain-reply deaths | 5/22 (029, 036, 047, 050, 057) | 050 was 5/5 in tuning set | runs/tau-v9-* |
| baseline / v4 turn-1 deaths | 8/12 and 4/12 documented runs | not a full census | TAU3_NOTES.md |
| harness-invalid tasks | 034 083 085 087 089 091 093 094 | simulator crashes on empty tool schema → `infrastructure failure` | TAU3_NOTES.md |

### Turn-1 survival arms (4 tasks 018/044/050/101 × 5 reps; replicated proxy result) — `python turn1_table.py`
| arm | what changed | survived |
|---|---|---|
| v4 | fact: "the customer cannot see your replies…" | 10/20 |
| v4 no-header | same wording, harness REPO_CONTEXT/"guidance only" header stripped | 10/20 |
| v5 | first-action anchor | 9/20 |
| v6 | consequence + timing + emphasis (caps, "HARD CONSTRAINT, not style guidance") | 14/18 (2 unresolved when stopped) |
| v7a | v6 content, calm prose | 13/20; rerun with raw dump 15/20 |
| v7b | v4 + emphasis only, no new content | 5/20 |
| v7c | v6 minus "not style guidance" clause | 10/20 |
| v9 | v7a + verb binding | 20/20 (prediction was ≥17/20) |
| infra | ~10 runs of the 60-run v7 launch died in docker compose, relaunched | excluded |

Hidden-reasoning split, v7a rerun (runs/t1-v8raw-*.raw.jsonl, `turn1_hidden.py`): no reasoning → 8/8 survived;
reasoning → 7/12, all 5 deaths there. v9: 16/20 still reasoned, same words, all survived.

### Wording (exact) — tau3/SKILL.md and variants/tau3-*/SKILL.md
v4 fact #1: "**The customer cannot see your replies.** The only text that reaches them is the argument of
`send_message_to_user`. A plain assistant reply is invisible and ends the task with nothing done. Every time you
want to say something, it goes through that tool."
v7b adds only: "HARD CONSTRAINT, not style guidance: … This is not a preference."
v6/v7a add content: the harness treats a plain reply as "agent finished" and terminates the episode; the first
reply after `start_conversation` returns is itself a `send_message_to_user` call, like any other tool.
v9 adds: "'ask the customer', 'tell the customer', 'greet', 'request verification' all name the same single action,
a `send_message_to_user` call. When your plan ends in 'let me ask them…', the next thing you emit is that tool call,
not the sentence."

### Trace pairs for the viewer (real, from body.html §3)
DIED — v7a, task 018, rep 4: start_conversation → customer: "Hi, I've been looking at my credit card statements and
I think some of my cash back rewards might be wrong. Can you help me check?" → hidden reasoning: "The customer wants
to check cash back rewards. I need to verify identity first. Ask for name and two identity fields." → PLAIN
ASSISTANT REPLY (finish_reason: stop, visible to customer: NO): "I'd be happy to help you check your cash back
rewards! Before I can access your account details, I'll need to verify your identity…" → episode terminated.
SURVIVED — v9, task 018, rep 4: same opening → reasoning: "Ask for name + verification details before accessing
account." → send_message_to_user (finish_reason: tool_calls, visible: YES), same sentence → customer replies with
name, DOB, phone → run continues.
Also: 101 deaths quote the skill's own fact #2 ("ask one question first") then type it as chat.
Survivor 044-r5 reasoning said "Let's *send a message* asking for verification" → used the tool.

### Other clusters (thin data — show as "diagnosed, no replicated intervention")
- Search loop: task 059 KB_search calls baseline 43 / v1 43 / v2 9 / v4 28 / v9 37; questions before first search 0/0/1/1. Exploratory (1 run each).
- Partial candidate list: v2 recommended Bronze over Silver on 059 after seeing only 3–4 products; v4 provenance rule
  ("a claim about the whole category needs the whole list as its source") passed 059 and 050. Exploratory.
- Skipped protocol step / wrong date (used harness date instead of `get_current_time`): observed in trajectories,
  no intervention tested. Details in TAU3_NOTES.md.

### Next-test panel content
Cluster A: evidence = v9 20/20 tuning, 17/22 held-out turn-1, pass 5/20 unchanged. Uncertainty = does anything in
cluster A still limit pass rate, or are downstream mechanisms (search loop, partial list) the bottleneck? Next =
(a) rerun the 5 held-out deaths ×5 to see if it's the same ~25% coin flip; (b) run baseline vs v9 with a larger
learner on the same 22 tasks to price "bigger model" against "next fix"; (c) harness guard: reject a plain reply at
turn 1 and retry. Costs: turn-1 arm ≈ 20 runs / 10 min; end-to-end 22 tasks ≈ 45 min at 4 concurrent.

## Source files
- submissions/devin-curator/TAU3_NOTES.md, TAU3_RESULTS.md, LEARNINGS.md (Lesson 14 = verb binding)
- submissions/devin-curator/casestudy/body.html (previous artifact; reuse text, not structure)
- turn1_table.py, turn1_deaths.py, turn1_sdklog.py, turn1_hidden.py (how numbers were computed)
- runs/t1-*/ (turn-1 arms), runs/tau-v9-*/ (held-out), runs/t1-v8raw-*.raw.jsonl (hidden reasoning)

## Email line this supports
"The fix worked on the proxy it was designed for, half-transferred, and didn't move the benchmark — exactly the
moment a team must decide between the next mechanism and a bigger model. The workflow: a per-failure proxy,
a prediction written first, replication, then a held-out test."
