"""Poll t1-* runs; record first-turn outcome and kill runs that survived turn 1.
usage: python turn1_watch.py <tag> [<tag> ...]   (loops until all runs resolved)"""
import glob
import json
import os
import signal
import subprocess
import sys
import time

tags = sys.argv[1:]
resolved: dict[str, str] = {}


def pids_for(tag: str) -> list[tuple[int, str]]:
    p = f"runs/t1-{tag}.pids"
    if not os.path.exists(p):
        return []
    return [(int(l.split()[0]), l.split()[1]) for l in open(p) if l.strip()]


def kill_tree(pid: int) -> None:
    subprocess.run(["pkill", "-TERM", "-P", str(pid)], capture_output=True)
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass


while True:
    pending = 0
    for tag in tags:
        for pid, out in pids_for(tag):
            if out in resolved:
                continue
            st = glob.glob(f"{out}/harbor-jobs/*/task__*/agent/tau3_runtime_state.json")
            tr = glob.glob(f"{out}/harbor-jobs/*/task__*/agent/trajectory.json")
            alive = os.path.exists(f"/proc/{pid}")
            msgs = json.load(open(st[0]))["messages"] if st else []
            n = len(msgs)
            # runtime state: msgs[0] agent greeting, msgs[1] customer opening; a later
            # assistant message with content and no tool_calls == send_message_to_user
            if any(
                m.get("role") == "assistant" and m.get("content") and not m.get("tool_calls")
                for m in msgs[2:]
            ):
                resolved[out] = "SURVIVED"
                kill_tree(pid)
            elif not alive and tr:
                resolved[out] = "DIED_TURN1"
            elif not alive:
                resolved[out] = "NO_TRAJECTORY"
            else:
                pending += 1
    done = sum(1 for _ in resolved)
    print(f"resolved {done}, pending {pending}", flush=True)
    if pending == 0 and done:
        break
    time.sleep(15)

summary: dict[str, dict[str, int]] = {}
for out, res in sorted(resolved.items()):
    key = out.split("/t1-")[1].rsplit("-r", 1)[0]
    summary.setdefault(key, {}).setdefault(res, 0)
    summary[key][res] += 1
    print(out, res)
print()
for k, v in sorted(summary.items()):
    print(k, v)
