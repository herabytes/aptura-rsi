"""Per-run turn-1 analysis from openhands_sdk.txt (exists for killed survivors too).
Prints: fate, customer opening line, whether the model emitted reasoning on the fatal/first
customer-facing step, output tokens of that step, and the actions before it."""
import glob, os, re, sys
from collections import Counter, defaultdict

tags = sys.argv[1:] or ["v4", "v4nf", "v5", "v6", "v7a-content", "v7b-emphasis", "v7c-noguidance"]
EVT = re.compile(r"^(Agent Action|Observation|Message from Agent) ─+$", re.M)


def parse(log):
    parts = EVT.split(log)
    events = []
    for i in range(1, len(parts), 2):
        kind, body = parts[i], parts[i + 1]
        if kind == "Agent Action":
            m = re.search(r"Summary: (\S+?):", body)
            ma = re.search(r"data: \{'(\w+)'", body)
            events.append(dict(kind="action", name=m.group(1) if m else ("send_message_to_user" if ma and ma.group(1)=="message" else "?"),
                               reasoning=bool(re.search(r"^Reasoning:", body, re.M)),
                               out=int((re.search(r"output (\d+)", body.replace("\n", " ")) or [0, 0])[1] or 0),
                               body=body))
        elif kind == "Observation":
            events.append(dict(kind="obs", body=body))
            mt = re.search(r"^Tool: (\S+)", body, re.M)
            if mt and events[-2:-1] and events[-2]["kind"] == "action" and events[-2]["name"] == "?":
                events[-2]["name"] = mt.group(1)
        else:
            events.append(dict(kind="message",
                               reasoning=bool(re.search(r"^Reasoning:", body, re.M)),
                               out=int((re.search(r"output (\d+)", body.replace("\n", " ")) or [0, 0])[1] or 0),
                               body=body))
    return events


def main():
    stats = defaultdict(Counter)
    for tag in tags:
        for d in sorted(glob.glob(f"runs/t1-{tag}-*-r*/")):
            logs = sorted(glob.glob(d + "harbor-jobs/*/task__*/agent/openhands_sdk.txt"), key=os.path.getmtime)
            if not logs:
                continue
            ev = parse(open(logs[0]).read())
            m = re.search(rf"t1-{re.escape(tag)}-(\d+)-r(\d+)", d)
            task, rep = m.group(1), m.group(2)
            opening = ""
            fate, seq, fatal = "NOSTART", [], None
            for i, e in enumerate(ev):
                if e["kind"] == "obs" and "start_conversation" in e["body"] and not opening:
                    opening = re.sub(r"\s+", " ", e["body"].split("executed.]", 1)[-1]).strip()[:110]
                if e["kind"] == "action":
                    seq.append(e["name"])
                    if e["name"] == "send_message_to_user":
                        fate, fatal = "LIVE", e
                        break
                if e["kind"] == "message":
                    fate, fatal = "DEAD", e
                    seq.append("PLAIN")
                    break
            if fate == "NOSTART" and seq:
                fate = "UNRESOLVED"
            r = fatal["reasoning"] if fatal else None
            out = fatal["out"] if fatal else None
            start_r = next((e["reasoning"] for e in ev if e["kind"] == "action" and e["name"] == "start_conversation"), None)
            print(f"{tag:15} {task} r{rep} {fate:10} startR={start_r!s:5} fatalR={r!s:5} out={out!s:4} {' > '.join(seq[1:]):45} | {opening}")
            if fate in ("LIVE", "DEAD"):
                stats[tag][(fate, "R" if r else "noR")] += 1
                stats[tag][(fate, "toolfirst" if len(seq) > 2 else "direct")] += 1
    print()
    for tag, c in stats.items():
        print(tag, dict(sorted(c.items())))

if __name__ == '__main__':
    main()
