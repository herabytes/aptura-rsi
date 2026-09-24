"""Tabulate turn-1 runs: action sequence before first customer-facing text, and whether the
learner emitted reasoning (from openhands_sdk.txt) on each action."""
import glob, json, os, re, sys
from collections import Counter, defaultdict

tags = sys.argv[1:] or ["v4", "v4nf", "v5", "v6", "v7a-content", "v7b-emphasis", "v7c-noguidance"]
rows = []
for tag in tags:
    for tr in sorted(glob.glob(f"runs/t1-{tag}-*-r*/harbor-jobs/*/task__*/agent/trajectory.json")):
        m = re.search(rf"t1-{re.escape(tag)}-(\d+)-r(\d+)", tr)
        task, rep = m.group(1), m.group(2)
        steps = json.load(open(tr))["steps"]
        seq, fate = [], "?"
        for s in steps[2:]:
            if s["source"] != "agent":
                continue
            tc = s.get("tool_calls") or []
            if tc:
                n = tc[0]["function_name"]
                seq.append(n)
                if n == "send_message_to_user":
                    fate = "LIVE"
                    break
            elif s.get("message"):
                seq.append("PLAIN")
                fate = "DEAD"
                break
        log = open(os.path.join(os.path.dirname(tr), "openhands_sdk.txt")).read()
        acts = re.findall(r"Agent Action ─+\n\nSummary: (\S+?):.*?\n\n(Reasoning:|Action:)", log, re.S)
        reasoned = [a[0] + (":R" if a[1] == "Reasoning:" else "") for a in acts]
        # output tokens on the fatal/first-message call
        toks = re.findall(r"↓ \s*\noutput (\d+)|↓ output (\d+)", log)
        rows.append((tag, task, rep, fate, " > ".join(seq), reasoned))

by = defaultdict(Counter)
for tag, task, rep, fate, seq, reasoned in rows:
    print(f"{tag:15} {task} r{rep} {fate:4} {seq:60} {reasoned}")
    first_is_msg = seq.split(" > ")[1:2] in (["PLAIN"], ["send_message_to_user"]) if " > " in seq else False
    by[tag][(fate, "direct" if first_is_msg else "tool-first")] += 1
print()
for tag, c in by.items():
    print(tag, dict(c))
