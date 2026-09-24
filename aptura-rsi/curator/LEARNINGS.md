# Learnings: steering a general (coding-tuned) model with a skill file

Running log. Each entry names the evidence it came from (health = HealthBench runs
h3-v1/v2, hera-v1, h9-v1/v3; tau = tau3 runs tau-v1, tau-s-*). General claims only;
domain detail lives in NOTES.md / TAU3_NOTES.md / TAU3_RESULTS.md.

## 1. The model executes; it does not weigh

- A rule stated as a procedure ("open with 2–4 questions", "deliver the document first")
  is carried out literally and maximally: four questions before "call 911", a filler
  question to reach the quota, a definitive checklist where hedging was wanted. (health
  h9-v1, h9-v3)
- A rule stated as a test the model can apply to its own sentence ("a list of thresholds is
  not a question", "record only facts the user supplied; everything else is 'not
  documented'") generalised to unseen tasks and did not overshoot. (health h3-v2 → h9-v1,
  the parts that held)
- Numeric limits do not bind it. "≤6 searches" → 43 searches. "2–4 questions" → always 4.
  The number becomes a target or is ignored; it never functions as a budget. (tau tau-s-059,
  health h9-v1)
- Corollary: write skills as *criteria the model checks per action*, not as *plans it runs*.
  If you find yourself writing an ordering or a count, you are writing something that will
  be over-obeyed or unobeyed.

## 2. Its own final text is, to it, the deliverable

- Health baseline: 2/9 attempts ran `mkdir`, then wrote the answer in chat, never in the
  required file. Score 0 with correct content. (h3-v1)
- Tau with skill: 2/2 attempts wrote the correct customer message as a plain reply instead
  of through `send_message_to_user`. Episode ended at step 4. Baseline had used the tool
  4/4 times. (tau-s-017, tau-s-098)
- The word "message" in my skill ("either one `send_message_to_user` or one tool call") was
  enough to pull it back to its default channel. Any skill for a tool-mediated environment
  must say, in the first lines, *what the model's own reply does* (ends the episode / is
  unseen) and name the only channel that counts. Never use the environment's word for the
  channel ("message", "response", "answer") to mean anything else in the skill.

## 3. Knowing when to stop gathering is a judgement gap, not a vocabulary gap

- Tau 059: 40+ searches (baseline) and 43 (skill) for facts it had already quoted from
  earlier results. It understood the results; it could not decide it had enough. Health
  mirror: it names the missing facts but does not act on them (ask). Both are failures to
  commit at the boundary between gathering and producing.
- A limit on gathering did nothing (see §1). Untested but the natural next lever: a rule
  about *what to do immediately after each result* ("state the answer to your question
  from this result before doing anything else; if the result does not contain it, say what
  it did contain"), i.e. force the commit step rather than cap the gathering step.

## 4. Skill text is a lever with a sign you do not know in advance

- The same skill produced +0.44 and −0.66 on different tasks in the same domain. (h9-v1)
- Adding one section to fix an ordering problem (v3) fixed it and broke two previously
  winning tasks, in one run. (h9-v3)
- Adding a protocol skill to tau broke the one protocol behaviour the baseline had right.
  (tau-s-*)
- So: run a baseline on the exact tasks first; pre-register per-task directions; treat any
  section that changes behaviour on a task you didn't target as a regression until shown
  otherwise. Single-sample per-task swings of ±0.4 are common; do not read sub-0.1 mean
  changes on <10 tasks.

## 5. Write skills from observed failures, not from expected outputs

- Health v2 §0–§4 came from reading trajectories and rubric misses → generalised.
- Tau §5 ("identify the specific records, then hand over") came from reading one task's
  expected-action list, not from a failure → flagged by the user as likely overfit before
  running; never exercised, so no evidence either way. Rule: if a section cannot point at a
  trajectory where its absence caused the loss, leave it out until it can.

## 6. Shorter is not automatically safer, but longer is reliably riskier

- The 15k-character user skill fixed delivery and nothing else (0.398 = baseline): the model
  fills a long checklist rather than following its intent. (hera-v1)
- The 5.5k tau skill introduced a failure with one ambiguous word. Every sentence is a
  chance to collide with the model's defaults; keep only sentences with an observed reason.

## 7. Domain-general shape of what worked

Across both domains the parts that helped had the form:
*"[thing the model produces] only counts if [condition]; here is how to tell."*
("A reply not in the file scores zero." "A threshold list is not a question." "A field not
supplied by the user is 'not documented'.") The parts that hurt had the form:
*"Do X, then Y, then Z"* or *"Do at most N X."*

## 8. A gathering loop is usually a missing question (tau-s-059 anatomy, TAU3_NOTES.md)

- 43 searches, 0 messages to the customer. The customer was scripted to reveal the two
  constraints that pick the answer *when asked*. The model substituted exhaustive lookup
  for one question. Same mechanism as health "lists facts instead of asking" — the
  coding-model default is to resolve uncertainty by reading more, not by asking.
- The facts it hunted were already in its context (no condensation, 149k tokens); it did
  not re-read them. A capped budget cannot fix "does not read what it has".
- It treated a BM25 retriever as semantic: rewording the same question six times returned
  the same top doc. If the skill says anything about search, it should say what kind of
  retriever it is and that rewording does not change the ranking — that is environment
  vocabulary the model lacks, the kind of thing a skill *can* supply.
- Lesson for skill design: when you see a loop, look for the question the model should
  have asked a human/user before the loop began; put *that* in the skill, not a cap on the
  loop.

## 9. Environment facts beat procedures (tau v2, TAU3_RESULTS.md)

- v1 (5.5k chars of procedure, counts, protocol) → 0/3, introduced a new failure. v2 (three
  sentences about the environment: reply channel, ask before searching, retriever is
  keyword) → both trajectories completed the full 6-step protocol chain in the right order
  for the first time, searches 43 → 9, and the model asked the customer first. Same
  learner, same tasks. The protocol behaviour was never mentioned in v2 — it was already
  there once the model wasn't looping or ending the episode.
- Still 0/2 on reward: the residual failure is *coverage* — "best product for constraint
  C" computed over whichever 3–4 products happened to be retrieved. The model has no
  representation of "have I seen the whole category", in either direction (43 searches
  without noticing it had the answer; 4 searches without noticing it lacked 7 of 10
  candidates). A skill can state the fact ("a recommendation is over the category, and a
  category is bigger than one search"), but this is the point where the gap looks like
  reasoning rather than vocabulary.
- Method note: with binary reward the pre-registered proxies (messages before first
  search, search count, repeated top hits, chain completion) were what made the run
  informative — reward alone would have read as "no change from v1".

## 10. Run the baseline on every task you test the skill on (tau v4, TAU3_RESULTS.md)

- Before the controls, 032/036 ending in a plain reply looked like a skill regression (the
  v1 failure again). Baseline controls showed 4/5 unseen tasks die the same way *without*
  any skill — it is the model's default on "verify me first" tasks, and the skill fixed it
  on 2 of 4, not caused it on 2. With binary reward and n=1 per task, the sign of an effect
  is unreadable without the per-task control.
- Specific vs general rule, same slot: the narrow "a recommendation is over the whole
  category" rule passed 098 (the task it was written from) and not 059; the general "every
  fact you act on has a source" rule passed 059 and 050 (a task type it was never written
  for) and not 098. Both are n=1 per cell. The general rule transferred to a new task type;
  the specific one has no path to. Prefer general, and accept losing the tailored win.
- Harness failures look like learner failures in the reward column (3 runs at 0 where the
  user simulator crashed). Check the SDK log for exceptions before reading any 0 as
  evidence.

## 11. The first turn is a different regime from every later turn (tau, 24 runs)

- Every plain-reply failure in 24 tau runs was on the model's *first* customer-facing
  turn. Once it has called `send_message_to_user` once, it never reverts. So a fact stated
  in the skill ("the customer only sees…") is read and applied on turn 2+, but on turn 1 the
  model is still in its default "answer the message I was just given" mode. Rules that
  need to hold on turn 1 have to be about turn 1 explicitly ("your first action is…"), not
  general facts the model is expected to apply from the start.
- Failure modes cluster into few mechanisms even across many task types: 9 failures → 3
  mechanisms (channel on turn 1, partial candidate set, dropped procedure step). Breadth
  (12 tasks × 2 arms) found the third mechanism that 4 tasks never showed; depth on 059
  (five variants) never would have.

## 13. Read the frame the harness puts around your skill — check it, then test it

The OpenHands harness injects the skill into the system prompt under a header saying the text may be used "for
coding style, project conventions, and documentation guidance only". A hard environmental fact (the customer
only receives `send_message_to_user`) written as a fact, then rewritten as a first-action anchor, gave identical
turn-1 survival (10/20, 9/20). Rewriting it a third time as "HARD CONSTRAINT, not style guidance: a property of
the runtime" gave 14/18. Same content, same length; the only change was contradicting the wrapper's framing.
**Revised after a post-hackathon ablation** (TAU3_NOTES.md): the v4 wording with the header removed from the
prompt still gave 10/20, so the header was not what suppressed the rule — v6 worked because of how it states the
fact (a runtime property whose violation ends the episode), not because it contradicted the wrapper. The
tempting causal story from a suggestive correlation was wrong; the ablation was the only way to find out.
Lessons: (a) find where and how your text lands in the learner's context before iterating on wording;
(b) when a correct fact is ignored, ask whether something in the surrounding prompt licenses ignoring it — then
*test* that by removing it, rather than inferring it from a rewrite that changed several things at once;
(c) one sample per task cannot detect a change in a ~50% stochastic behaviour — replicate cheaply (kill the run
as soon as the behaviour of interest is observed) and compare rates.

## 14. When a rule is read but not obeyed, look at what the learner's plan is *about* (tau v9, TAU3_NOTES.md)

With the hidden reasoning captured, the residual turn-1 deaths were not the model missing the channel rule — it
quoted the skill in the same reasoning that preceded the death. The plan was about content ("ask for name and two
identity fields") and the channel was never part of it, so the chat default filled the gap; runs that skipped
reasoning went straight to the tool (8/8), runs that reasoned died 5/12. A rule stated as a fact about the world
gets weighed against the plan; a rule stated as *what your verbs mean* ("'ask the customer' is a
`send_message_to_user` call") enters the plan itself. That change took the same 4×5 from 13–15/20 to 20/20 with
the reasoning text unchanged. Lessons: (a) a fact and a decision-rule are different interventions — if the learner
can recite the fact and still fail, restate it as the mapping from its own likely thought to the required action;
(b) hidden reasoning is the cheapest diagnostic for "read but ignored": rendered logs showed identical steps for
deaths and survivals, the raw response showed the plan; (c) a skill's other rules compete — fact #2 ("ask first")
made the model think harder about asking, which was the failure path, and the fix was to bind, not to weaken it.
