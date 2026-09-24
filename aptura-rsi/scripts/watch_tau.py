"""Live view of tau3 trajectories: python watch_tau.py runs/tau-v2-059 [runs/tau-v2-098 ...]"""
import glob
import json
import re
import sys


def summarise(run_dir: str) -> None:
    files = glob.glob(f"{run_dir}/harbor-jobs/*/task__*/agent/tau3_runtime_state.json")
    if not files:
        print(f"{run_dir}: no runtime state yet")
        return
    s = json.load(open(files[0]))
    ms = s["messages"]
    print(f"== {run_dir}: {len(ms)} msgs, term={s.get('termination_reason')}")
    n_search = n_msg = 0
    first_search_seen = False
    msgs_before_search = 0
    tops: dict[str, int] = {}
    for m in ms:
        r = m.get("role")
        if m.get("tool_calls"):
            for tc in m["tool_calls"]:
                name = tc["name"]
                args = json.dumps(tc.get("arguments"))[:120]
                if name == "KB_search":
                    n_search += 1
                    first_search_seen = True
                print(f"  {r:9s} CALL {name} {args}")
        elif r == "tool":
            c = m.get("content") or ""
            t = re.search(r"^\s*1\.\s+(.+?)\s*$", c, re.M)
            if t:
                tops[t.group(1)] = tops.get(t.group(1), 0) + 1
                print(f"            -> top: {t.group(1)[:70]}")
        elif r == "assistant":
            n_msg += 1
            if not first_search_seen:
                msgs_before_search += 1
            print(f"  ASSISTANT: {(m.get('content') or '')[:160]!r}")
        elif r == "user":
            print(f"  USER     : {(m.get('content') or '')[:160]!r}")
    rep = max(tops.values()) if tops else 0
    print(f"  -- searches={n_search} agent_msgs={n_msg} msgs_before_first_search={msgs_before_search} max_same_top_hit={rep}")


for d in sys.argv[1:]:
    summarise(d)
