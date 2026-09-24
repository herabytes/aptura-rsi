#!/usr/bin/env bash
# Re-launch the NO_TRAJECTORY (infra-failed) replicates of a t1-<tag> arm, then re-watch.
# usage: ./turn1_rerun.sh <skill_dir> <tag>
set -u
SKILL=$1; TAG=$2
cd "$(dirname "$0")"
rm -f "runs/t1-$TAG.pids"
for out in runs/t1-$TAG-*-r[0-9]*; do
  [[ "$out" == *.log ]] && continue
  if ! compgen -G "$out/harbor-jobs/*/task__*/agent/trajectory.json" > /dev/null; then
    t=$(echo "$out" | sed -E 's/.*-([0-9]{3})-r[0-9]+$/\1/')
    rm -rf "$out" "$out.log"
    nohup uv run stbench eval --domain tau3 --skill "$SKILL" --arms skill --concurrency 1 \
      --tasks "tau3-bench__tau3-banking_knowledge-task-$t" --out "$out" > "$out.log" 2>&1 &
    echo "$! $out" >> "runs/t1-$TAG.pids"
  fi
done
wc -l < "runs/t1-$TAG.pids"
