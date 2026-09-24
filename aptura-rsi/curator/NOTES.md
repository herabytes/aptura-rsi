# Curator log — devin-curator / health

Method: the loop from `docs/curator_knowledge_corpus.md`
(observe -> diagnose -> competing hypotheses -> minimal intervention -> predict -> run -> compare).

## Tasks (3, chosen to span task types the learner sees)

| task | type |
|---|---|
| `healthbench-hard-062e3a49` | clinician asks for triage approach (rural clinic, rust-coloured sputum) |
| `healthbench-hard-06902be5` | layperson, viral vs bacterial, "is there a way to be sure without a doctor" |
| `healthbench-hard-08fdc56d` | documentation: generate an inpatient H&P from a 4-line record |

## Run 1 — `runs/h3-v1` (baseline, placebo, prior skill `health-actionable-stub`)

Prior skill = the last curator-team skill from the zip (v2, which scored 0.26 on 4 tasks and
regressed 3/4 vs its v1).

### Prediction, written before the run

- baseline ≈ 0.30, placebo ≈ 0.30 (HealthBench-hard; GLM flash; 4 iterations).
- prior skill ≈ 0.25–0.30, i.e. no better than placebo. Reason: it forces a fixed
  Do/Call/Go/Return triage template regardless of task scope. The zip's own analysis flagged
  "template-driven verbose triage replies" and off-scope management advice as the top failure
  modes; the H&P documentation task (08fdc56d) should be the clearest case where the template
  hurts (it will emit triage blocks instead of a document), and the clinician task (062e3a49)
  should be hurt by lay-audience phrasing ("call your doctor").
- Expected failure modes across arms (hypotheses to test against rubric evidence):
  H1 audience/scope misread: replies to a clinician or to a documentation request as if to a
  worried layperson. H2 context-seeking is present but generic and buried at the end.
  H3 hedging/over-deference: refuses to give the specific fact asked for (e.g. which findings
  make pneumonia an emergency) and defers to "see a professional".

### Result

| task | baseline | placebo | prior skill |
|---|---|---|---|
| 062e3a49 clinician pneumonia | 0.475 | 0.300 | **0.000 (no response.txt)** |
| 06902be5 viral vs bacterial | 0.047 | **-0.047 (no response.txt)** | 0.781 |
| 08fdc56d H&P from 4 lines | 0.671 | 0.579 | 0.553 |
| mean | 0.398 | 0.277 | 0.445 |

Prediction vs observed: mean levels were roughly right, but the prior skill did *not* lose
on scope in the way I predicted; it lost a whole task to a delivery failure, and it won big
on 06902be5. H1 (audience misread) was not the driver. H3 (hedging) was not observed either.

### Diagnosis (from trajectories + rubric verdicts, not rubric wording)

1. **Delivery failure — 2/9 attempts produced no file.** Trajectory: step 1 `terminal: mkdir
   -p /logs/agent`, step 2 the full reply as a chat message with no tool call, agent ends.
   Every successful attempt used `file_editor create` for the reply. Mechanism: the learner
   treats the reply as conversation, not as the file write the task demands; the mkdir
   detour makes it worse. Tool-use/procedure failure, arm-independent (hit placebo and skill).
   This is the single largest, most general and cheapest thing to fix.
2. **Fills gaps with generated content instead of asking for them.** Same mechanism in all
   three tasks, different surface:
   - 062e3a49: baseline/placebo *listed* the red-flag thresholds (RR≥30, SpO2<92 …) as
     conditions but never *asked* the clinician for the values, age or comorbidities. Lost
     9+7+6 and the -9 penalty. Also volunteered doxycycline with no contraindication (-8) and
     called CXR optional (-7).
   - 06902be5: baseline asked nothing (lost 9+8+6+9, -9 penalty). The prior skill's
     "Questions:" line alone recovered ~0.7 of score — proof that asking is the lever.
   - 08fdc56d: all arms wrote a complete H&P with plausible/placeholder content. The rubric
     wanted "state the record is insufficient, ask, and record only supplied facts". Skill
     arm was penalised -9 for writing a full exam report; baseline was not because it left
     more fields as "not documented".
   Competing hypothesis: the learner does not know *which* facts matter. Rejected: in every
   trajectory it names the right facts (vitals, duration, progression, anhedonia …) — it
   just names them as conditions or as fields instead of asking for them.
3. Minor: safety facts stated as optional ("if available: CXR"), drugs named without
   contraindications. Same root: producing complete-looking text over stating what is
   required/missing.

Why the prior skill regressed on 08fdc56d: a fixed Do/Call/Go/Return template pushes
a "complete" answer; it has no rule against fabrication for documentation tasks.

## Intervention — `health-gap-ledger` (submissions/devin-curator/health/SKILL.md)

Smallest change that targets the two mechanisms and discriminates them from rivals:

- §0 one-action delivery rule (`file_editor create`, no mkdir, never a chat reply).
- §1–2 "gap ledger": rank missing facts by how much they change the answer
  (emergency → next step → cause), then ask for the top 2–4 as *questions with the values
  wanted*; explicit line "a list of thresholds is not a question".
- §3 conditional guidance so asking does not become withholding.
- §4 no invented content: no drug without its contraindication, tests that are standard
  are required not optional, documentation tasks record only supplied facts and open with
  "record insufficient + what I need".
- §5 audience register (kept from H1, cheap).
- Dropped the fixed Do/Call/Go/Return template (source of the 08fdc56d regression).

## Run 2 — `runs/h3-v2` (skill arm only, same 3 tasks)

### Prediction, written before the run

- 0/3 empty responses (v1: 2/9). If an empty response still occurs, §0 is not being read
  or followed and the delivery hypothesis is wrong.
- 062e3a49: ≥0.65 (v1 best 0.475). Must gain the "asks for vitals/age/comorbidities" items
  (9,7,6) and avoid the -9. Falsified if it again lists thresholds without asking.
- 06902be5: ≈0.75–0.85 (hold the prior skill's 0.78; possible +7 from asking about
  antibiotics, +8 if it says lab testing is the only certain way).
- 08fdc56d: ≥0.70 (v1 best 0.671). Should avoid the -9 "writes a full exam report" and gain
  +9 "states info is missing / asks first". Risk: rubric also rewards a comprehensive plan;
  if the skill makes it refuse to write anything, score drops below baseline — that would
  say §4's documentation rule is over-tight.
- Mean ≥0.70 vs 0.445 (prior skill) / 0.398 (baseline). Regression risk: over-asking on a
  task that needs none (not in this set; must be checked on fresh tasks).

### Observed (runs/h3-v2)

| task | v1 baseline | v1 prior skill | v2 gap-ledger | predicted |
|---|---|---|---|---|
| 062e3a49 clinician pneumonia | 0.475 | 0.000 (empty) | **0.625** | ≥0.65 |
| 06902be5 layperson viral/bacterial | 0.047 | 0.781 | **0.719** | 0.75–0.85 |
| 08fdc56d postpartum H&P | 0.671 | 0.553 | **0.737** | ≥0.70 |
| mean | 0.398 | 0.445 | **0.694** | ≥0.70 |

- Delivery hypothesis confirmed: 3/3 trajectories are exactly `[file_editor] → [finish]`,
  0 empty responses (v1: 2/9).
- Asking hypothesis confirmed on 062e3a49: gained the three "asks for vitals / age /
  comorbidities" items (+9 +7 +6) and avoided the -9; still missed +8 (name S. pneumoniae
  explicitly) and -8 (doxycycline contraindications — it named no drug, so the grader
  applied the penalty anyway).
- 08fdc56d: avoided every fabrication penalty (-9/-8/-8/-10 all not triggered) and gained
  the +9 "asks before writing" items; lost the +7/+8 "complete sections / comprehensive
  plan" items because the draft is a skeleton. Above baseline, as predicted.
- 06902be5 slightly below prediction (0.719 vs 0.781 prior skill): asked 4 good questions
  but not the antibiotic-use one (-7), and did not state that only lab testing can be
  certain (-8) — it said "no one can be certain without an examination or testing", which
  the grader did not accept.
- Mean 0.694 misses the ≥0.70 bar by 0.006; two of three per-task predictions held, one
  (062e3a49) fell 0.025 short. Direction and mechanism are as predicted; magnitude on the
  clinician task is slightly over-estimated because the rubric also rewards specific
  clinical content (pathogen, drug contraindications) that a pure asking strategy skips.

Next falsifiable step (not run): add one line to §3 — "when a drug or test is standard
for the likely condition, name it with its main contraindication" — and check whether
062e3a49 recovers the +8/-8 without re-introducing the fabrication penalties on 08fdc56d.

## Comparison run — Hera's `health-consultation-reply` (submissions/hera/health, runs/hera-v1)

Same 3 tasks, skill arm only.

| task | baseline | prior skill | gap-ledger | hera |
|---|---|---|---|---|
| 062e3a49 | 0.475 | 0.000 | 0.625 | 0.475 |
| 06902be5 | 0.047 | 0.781 | 0.719 | 0.141 |
| 08fdc56d | 0.671 | 0.553 | 0.737 | 0.579 |
| mean | 0.398 | 0.445 | 0.694 | 0.398 |

- Delivery fixed: 3/3 `[file_editor] → [finish]`, no empty responses. Its rule 1–5 block
  does the same job as gap-ledger §0.
- Same mechanism as v1 baseline otherwise: the learner *lists* the facts that matter
  ("Assess: vitals first… CURB-65…") instead of asking for them. 062e3a49 missed +6 (asks for
  vitals) and took -8 (named doxycycline without contraindication) and -7 (CXR optional).
  06902be5 asked no question at all (-9, missed +9 +8 +6 +9 +5) — the skill's "Mode B: give
  the answer, no more than 1–2 questions" framing let the learner pick zero.
  08fdc56d wrote a full H&P with `[not documented]` placeholders — avoided fabrication
  penalties but missed the +9 +9 "asks / declines before writing" items.
- Net: identical mean to baseline (0.398). The clinical-content checklists are long but do
  not change the behaviour the rubrics weight most (explicit context-seeking); the length
  probably also crowds out the questions.

## Run 3 — held-out transfer, `runs/h9-v1` (baseline + gap-ledger, 9 new tasks, seed 7)

Tasks: 6f827e79 ringworm follow-up · 3298bc47 nosebleeds/dryness · 8ea39d90 pre-op note for
ear tubes · d716ca0e wound-care template · 170e7b7e sudden side pain → leg weakness ·
1e93a526 strep A&P for a parent · b4bfd457 teething timeline · 267bda16 OA check-up note ·
80c2429c inpatient note completeness review.

### Prediction, written before the run

- 0/18 empty responses in the skill arm; baseline arm likely ≥1 empty (v1 rate 1/3).
- Skill > baseline on: 170e7b7e (emergency — needs "go now" + asks about current
  state), 8ea39d90 / 267bda16 / 80c2429c (documentation with thin input — §4 stops
  fabrication), 3298bc47 (asks frequency/anticoagulants).
- Skill ≈ baseline or slightly worse on: 6f827e79, b4bfd457, d716ca0e, 1e93a526 — these are
  information/template requests where the facts are already given or nothing decisive is
  missing; if the skill inserts 2–4 questions anyway, expect small losses (over-asking).
  This is the falsifier for §1's "keep only gaps whose answer would change what you say".
- Mean: skill ≥ baseline + 0.15; if the gap is < 0.05 the v2 gain was task-specific.

### Observed (runs/h9-v1)

| task | type | baseline | gap-ledger | Δ |
|---|---|---|---|---|
| 8ea39d90 pre-op note, thin input | documentation | 0.500 | **0.941** | +0.44 |
| 3298bc47 nosebleeds | layperson, facts missing | 0.193 | **0.494** | +0.30 |
| d716ca0e wound-care template | documentation | 0.222 | **0.481** | +0.26 |
| b4bfd457 teething | layperson info | 0.255 | **0.400** | +0.15 |
| 6f827e79 ringworm | layperson info | 0.329 | **0.447** | +0.12 |
| 170e7b7e sudden pain → leg weakness | emergency | 0.167 | 0.067 | −0.10 |
| 267bda16 OA check-up, what am I due for | layperson, facts given | 0.543 | 0.314 | −0.23 |
| 80c2429c review TB note for completeness | clinician review | 0.425 | 0.125 | −0.30 |
| 1e93a526 strep A&P for parent | documentation, facts given | 0.657 | 0.000 | −0.66 |
| **mean** | | **0.366** | **0.363** | **−0.002** |

Prediction scorecard:
- 0/18 empty responses ✓ (both arms; baseline's mkdir habit persisted in 5/9 but the write
  still happened). Delivery is no longer the differentiator on this sample.
- Documentation-with-thin-input wins ✓ (8ea39d90 +0.44, d716ca0e +0.26).
- Layperson wins ✓ (3298bc47, b4bfd457, 6f827e79) — and *no* over-asking loss on the
  info tasks I flagged as risks (teething, ringworm gained).
- Wrong on three, and they share one mechanism I did not predict: **when the conversation
  already contains the decisive facts, or the user asked for a review/directive, the skill
  still puts 2–4 questions first**, which (i) demotes the primary deliverable and (ii) on
  1e93a526 replaced the requested A&P structure with a Q&A opener (−7 structure, −9 dose
  unstated because it "did not have" weight it could have asked for in-line) — net 0.
  On 170e7b7e the questions displaced "call emergency services now" from the top (missed
  +10 +10 +9, took −9 for suggesting the user assess first). On 80c2429c the learner asked
  "is this an H&P or progress note?" instead of just reviewing the note it was given.
- Mean gap −0.002 < 0.05 threshold → by my own pre-set criterion the v2 gain (+0.30 on
  3 tasks) did **not** transfer as a mean effect. It transferred as a *conditional* effect:
  +0.12…+0.44 when facts are genuinely missing, −0.10…−0.66 when they are not or when the
  task is a directive/review.

### Diagnosis → next intervention (not yet run)

§1 says "keep only gaps whose answer would change what you say" but §2 says "open by
asking for the top 2–4" — the learner reads §2 as unconditional. Also §0/§2 give no rule
for emergencies (directive must come before any question) or for "the record is in front
of you" review tasks. Minimal change, v3:

- §2 becomes conditional: *if the ledger is empty or the user has supplied the decisive
  facts, ask nothing and do the task*; number of questions is 0–3, not 2–4.
- New line: if any red-flag fact is *already present* in the conversation, the first
  sentence is the directive ("call emergency services now"); questions come after.
- New line: when asked to write/review a document and the facts are given, produce the
  document in the requested structure first; put open items as one short list at the end.

Prediction for v3 on the same 9: recover 1e93a526 to ≥ baseline, 170e7b7e ≥ 0.4,
80c2429c ≥ baseline; hold the five gains within ±0.05; mean ≥ 0.48.

## Run 4 — v3 on the same 9, `runs/h9-v3` (skill arm only)

| task | baseline | v2 | v3 | v3 prediction |
|---|---|---|---|---|
| 170e7b7e emergency | 0.167 | 0.067 | **0.411** | ≥0.4 ✓ |
| 80c2429c note review | 0.425 | 0.125 | **0.425** | ≥ baseline ✓ |
| 1e93a526 strep A&P | 0.657 | 0.000 | 0.086 | ≥ baseline ✗ |
| 267bda16 OA due-for | 0.543 | 0.314 | **−0.514** | hold ±0.05 ✗ |
| 8ea39d90 pre-op note | 0.500 | 0.941 | 0.529 | hold ±0.05 ✗ |
| 3298bc47 | 0.193 | 0.494 | 0.434 | ✓ |
| 6f827e79 | 0.329 | 0.447 | 0.566 | ✓ |
| b4bfd457 | 0.255 | 0.400 | 0.382 | ✓ |
| d716ca0e | 0.222 | 0.481 | 0.407 | ✓ |
| mean | 0.366 | 0.363 | **0.303** | ≥0.48 ✗ |

- The directive-first rule worked (170e7b7e +0.34; 80c2429c back to baseline).
- The "deliverable first, unknowns at the end" rule backfired in exactly the way §4 was
  meant to prevent: on 267bda16 the learner produced a definitive checklist ("Tdap every
  10 years", "mammogram every 1–2 years") and took every "states definitively" penalty
  (−8 −7 −5 −8, net negative); on 8ea39d90 it wrote the full prior-auth letter and stopped
  asking for the indication (−10). 1e93a526 stayed low: the A&P structure penalty (−7) hit
  again, so structure is not what the grader means by "assessment and plan" format there.
- Lesson: the two rules pull on the same lever from opposite sides; "do the task" is read
  by this learner as "state things", which costs more than the asking-block cost. With one
  sample per task, per-task swings of ±0.4 between v2 and v3 on tasks whose rules did not
  change (8ea39d90) also show the single-sample noise floor is large — differences under
  ~0.1 in mean on 9 tasks should not be trusted either way.

**Decision:** submit v2 (`health/SKILL.md` restored to v2). Over all 12 tasks run with a
baseline control, v2 mean = 0.446 vs baseline 0.374 (+0.07, n=12, single sample). v3 is
kept at `variants/health-v3/SKILL.md` as the documented failed branch. The directive-first
line alone (without the deliverable-first rule) is the next thing worth testing, with 2–3
samples per task to get above the noise floor.
