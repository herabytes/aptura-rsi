# aptura-rsi — τ³ / HealthBench skill-curation hackathon work

Work from the RSI hackathon on [SkillTrainBench](https://github.com/iamrohithrnair/rsi-hackathon):
training a weak learner (GLM-5.3-flash under OpenHands) via in-context skills, with a human curator.

Start here:
- `curator/casestudy/HANDOFF.md` — the finding, every number with its denominator/source, and the spec for the
  **Failure-to-Fix Workbench** prototype (to be built; no new benchmark runs needed).
- `curator/casestudy/failure-to-fix.html` — first (long) case-study artifact; open in a browser.
- `curator/TAU3_NOTES.md` — full experiment log: search-loop diagnosis, turn-1 plain-reply cluster, header
  ablation (null), emphasis-only (worse), hidden-reasoning dump, verb-binding (20/20 tuning, partial held-out transfer).
- `curator/LEARNINGS.md` — general lessons (Lesson 14 = state rules in the vocabulary of the model's plan).
- `curator/tau3/SKILL.md`, `curator/health/SKILL.md` — final skills; `curator/variants/` — every wording arm.
- `hera-skill/health/` — Hera's HealthBench skill.
- `scripts/` — turn-1 rate tables, death/reasoning extraction, batch runners (run from the SkillTrainBench repo root).
- `patches/` — local gateway patch: strips the `prompt_cache_key` field Runware now rejects; dumps raw upstream
  responses (`*.raw.jsonl`) so the model's hidden `reasoning` is captured.

Raw run artifacts (`runs/`, ~130 MB) are not included; the notes and scripts reference them by run id.
