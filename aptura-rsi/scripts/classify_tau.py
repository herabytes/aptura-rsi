"""Per-run failure summary: python classify_tau.py runs/tau-v4-018 ..."""
import glob
import json
import sys


def run(d: str) -> None:
    ver = glob.glob(f"{d}/harbor-jobs/*/task__*/verifier/*.json")
    st = glob.glob(f"{d}/harbor-jobs/*/task__*/agent/tau3_runtime_state.json")
    tr = glob.glob(f"{d}/harbor-jobs/*/task__*/agent/trajectory.json")
    if not ver:
        print(f"{d}: no verifier result")
        return
    r = json.load(open(ver[0]))
    ms = json.load(open(st[0]))["messages"] if st else []
    n_search = sum(1 for m in ms for tc in m.get("tool_calls") or [] if tc["name"] == "KB_search")
    n_agent_msgs = sum(1 for m in ms if m.get("role") == "assistant" and m.get("content") and not m.get("tool_calls"))
    term = json.load(open(st[0])).get("termination_reason") if st else None
    plain_reply = False
    got_time = False
    tv = None
    if tr:
        t = json.load(open(tr[0]))
        steps = t.get("steps", t) if isinstance(t, dict) else t
        for s in steps:
            for tc in s.get("tool_calls") or []:
                if tc["function_name"] == "get_current_time":
                    got_time = True
                if tc["function_name"] == "log_verification":
                    tv = tc["arguments"]["data"].get("time_verified")
        last = steps[-1] if steps else {}
        plain_reply = not (last.get("tool_calls")) and len(ms) <= 4
    ri = r["reward_info"]
    dbm = ri.get("db_check", {}).get("db_match")
    note = ri.get("info", {}).get("note", "")
    print(f"== {d} reward={r['reward']} db_match={dbm} msgs={len(ms)} term={term} searches={n_search} agent_msgs={n_agent_msgs} get_time={got_time} tv={tv} plain_reply_end={plain_reply} {note}")
    for c in ri.get("action_checks", []):
        if not c["action_match"]:
            a = c["action"]
            arg = a["arguments"].get("arguments") or json.dumps(a["arguments"])
            print(f"   MISS {a['requestor']:9s} {a['name']} {arg[:110]}")


for d in sys.argv[1:]:
    run(d)
