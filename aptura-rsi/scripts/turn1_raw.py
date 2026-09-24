"""Turn-1 fate + hidden reasoning from gateway raw dumps. usage: python3 turn1_raw.py <tag>"""
import glob, json, sys
tag = sys.argv[1]
live = dead = 0; withR = {"LIVE": 0, "DEAD": 0}
for f in sorted(glob.glob(f"runs/t1-{tag}-*-r*.raw.jsonl")):
    steps = []
    for l in open(f):
        d = json.loads(l); ch = (d["choices"] or [{}])[0]; m = ch.get("message", {})
        tc = m.get("tool_calls"); rc = m.get("reasoning_content") or m.get("reasoning") or ""
        kind = tc[0]["function"]["name"] if tc else "PLAIN"
        if d["n_msgs"] == 2 and kind == "PLAIN":
            continue  # customer simulator call
        steps.append((kind, rc, m.get("content") or ""))
    for i, (k, rc, c) in enumerate(steps[1:]):
        if k in ("PLAIN", "send_message_to_user"):
            fate = "DEAD" if k == "PLAIN" else "LIVE"
            live += fate == "LIVE"; dead += fate == "DEAD"; withR[fate] += bool(rc)
            path = " > ".join(s[0] for s in steps[1:1 + i])
            print(f"{f.split('/')[-1][3:].replace('.raw.jsonl',''):22} {fate} [{path}] R={'Y' if rc else '-'} | {rc[:300].replace(chr(10), ' ')}")
            if fate == "DEAD":
                print("     TEXT:", c[:160].replace(chr(10), " "))
            break
    else:
        print(f, "unresolved", [s[0] for s in steps])
print(f"\n{tag}: LIVE {live} DEAD {dead}; with reasoning: LIVE {withR['LIVE']} DEAD {withR['DEAD']}")
