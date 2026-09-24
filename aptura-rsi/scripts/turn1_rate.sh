#!/usr/bin/env bash
# First-turn survival rate: launch N replicate runs per task per skill, kill each run once its runtime
# state shows the learner got past the first customer-facing turn (>=3 messages) or it exits.
# usage: ./turn1_rate.sh <reps> <skill_dir|baseline> <tag> task...
set -u
REPS=$1; SKILL=$2; TAG=$3; shift 3
cd "$(dirname "$0")"
for t in "$@"; do
  for r in $(seq 1 "$REPS"); do
    out="runs/t1-$TAG-$t-r$r"
    if [ "$SKILL" = baseline ]; then
      nohup uv run stbench eval --domain tau3 --arms baseline --concurrency 1 \
        --tasks "tau3-bench__tau3-banking_knowledge-task-$t" --out "$out" > "$out.log" 2>&1 &
    else
      STBENCH_RAW_DUMP="$PWD/$out.raw.jsonl" nohup uv run stbench eval --domain tau3 --skill "$SKILL" --arms skill --concurrency 1 \
        --tasks "tau3-bench__tau3-banking_knowledge-task-$t" --out "$out" > "$out.log" 2>&1 &
    fi
    echo "$! $out" >> runs/t1-$TAG.pids
  done
done
