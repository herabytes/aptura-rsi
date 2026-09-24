"""Estimate hidden (reasoning) tokens on the first customer-facing step by comparing the gateway
ledger's completion_tokens with the visible output (message text or tool-call JSON)."""
import glob, json, os, re, sys

from turn1_sdklog import parse

tags = sys.argv[1:] or ["v4", "v4nf", "v5", "v6", "v7a-content", "v7b-emphasis", "v7c-noguidance"]
agg = {}
for tag in tags:
    for d in sorted(glob.glob(f"runs/t1-{tag}-*-r*/")):
        logs = sorted(glob.glob(d + "harbor-jobs/*/task__*/agent/openhands_sdk.txt"), key=os.path.getmtime)
        led = d + "learner_ledger.jsonl"
        if not logs or not os.path.exists(led):
            continue
        rows = [json.loads(l) for l in open(led)]
        ev = parse(open(logs[0]).read())
        m = re.search(rf"t1-{re.escape(tag)}-(\d+)-r(\d+)", d)
        task, rep = m.group(1), m.group(2)
        llm_idx, fate, fatal, seq = -1, None, None, []
        for e in ev:
            if e["kind"] in ("action", "message"):
                llm_idx += 1
            if e["kind"] == "action":
                seq.append(e["name"])
                if e["name"] == "send_message_to_user":
                    fate, fatal = "LIVE", e
                    break
            if e["kind"] == "message":
                fate, fatal = "DEAD", e
                break
        if fate is None or llm_idx >= len(rows):
            continue
        row = rows[llm_idx]
        if fate == "DEAD":
            vis = fatal["body"].split("Tokens:")[0].strip()
        else:
            mm = re.search(r"data: (\{.*?\})\n  kind:", fatal["body"], re.S)
            vis = mm.group(1) if mm else fatal["body"]
        vis_tok = len(vis) / 4  # rough
        hidden = row["completion_tokens"] - vis_tok
        print(f"{tag:15} {task} r{rep} {fate:4} steps={len(seq):2} completion={row['completion_tokens']:4} visible~{vis_tok:5.0f} hidden~{hidden:5.0f} finish={row['finish_reason']}")
        a = agg.setdefault((tag, fate), [])
        a.append(hidden)
print()
for k, v in sorted(agg.items()):
    v = sorted(v)
    print(k, f"n={len(v)} median hidden~{v[len(v)//2]:.0f} min~{v[0]:.0f} max~{v[-1]:.0f}")
