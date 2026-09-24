#!/usr/bin/env bash
cd "$(dirname "$0")"
TASKS="003 006 014 018 019 020 021 029 032 035 036 039 043 044 047 050 057 059 098 099 100 101"
for t in $TASKS; do
  while [ "$(pgrep -fc 'stbench eval --domain tau3')" -ge 4 ]; do sleep 20; done
  out="runs/tau-v9-$t"
  STBENCH_RAW_DUMP="$PWD/$out.raw.jsonl" nohup uv run stbench eval --domain tau3 --skill submissions/devin-curator/variants/tau3-v9-verb --arms skill --concurrency 1 \
    --tasks "tau3-bench__tau3-banking_knowledge-task-$t" --out "$out" > "$out.log" 2>&1 &
  sleep 15
done
wait
echo ALLDONE
