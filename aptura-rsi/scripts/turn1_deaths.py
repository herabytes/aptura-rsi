"""Classify t1-<tag>-* runs from their runtime state / trajectory and print what the learner
emitted at the first customer-facing turn in the runs that died there.
usage: python3 turn1_deaths.py <tag> [--all]"""
import glob
import json
import sys

tag = sys.argv[1]
show_all = "--all" in sys.argv
rows = []
for out in sorted(glob.glob(f"runs/t1-{tag}-*-r[0-9]*")):
    if out.endswith(".log"):
        continue
    st = glob.glob(f"{out}/harbor-jobs/*/task__*/agent/tau3_runtime_state.json")
    tr = glob.glob(f"{out}/harbor-jobs/*/task__*/agent/trajectory.json")
    msgs = json.load(open(st[0]))["messages"] if st else []
    survived = any(
        m.get("role") == "assistant" and m.get("content") and not m.get("tool_calls")
        for m in msgs[2:]
    )
    status = "SURVIVED" if survived else ("DIED_TURN1" if tr else "NO_TRAJECTORY")
    rows.append((out, status))
    if status == "DIED_TURN1" or show_all:
        steps = json.load(open(tr[0])) if tr else []
        if isinstance(steps, dict):
            steps = steps.get("steps") or steps.get("events") or []
        print(f"\n=== {out} [{status}] ===")
        opening = msgs[1].get("content") if len(msgs) > 1 else None
        print(f"customer: {str(opening)[:160]!r}")
        for s in steps:
            for k in ("message", "content", "text", "output", "response"):
                v = s.get(k) if isinstance(s, dict) else None
                if isinstance(v, str) and ("verify" in v.lower() or "help you" in v.lower()):
                    print(f"learner (kind={s.get('kind') or s.get('type') or s.get('source')}): {v[:400]!r}")
                    break
            tc = s.get("tool_calls") if isinstance(s, dict) else None
            if tc:
                print(f"tool_calls: {[c.get('name') or c.get('function', {}).get('name') for c in tc]}")

print()
from collections import Counter
print(Counter(s for _, s in rows))
