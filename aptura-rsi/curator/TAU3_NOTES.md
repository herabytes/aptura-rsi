# tau3 curation log (devin-curator)

## How tau3 differs from health (from reading 67 task dirs, instruction.md, task_config.json, evaluate.py)

| | health | tau3 (all 67 tasks are `banking_knowledge`) |
|---|---|---|
| interaction | one-shot: write reply to a file | multi-turn: MCP tools `start_conversation`, `send_message_to_user`, domain tools; simulated customer is Claude Sonnet 4.6 with a hidden script |
| iterations | 4 | 100 |
| what is scored | rubric points, partial credit | binary: final DB state / set of expected actions must match exactly (`reward_basis` DB or ACTION); no partial credit |
| what decides pass | content of prose | which tool calls happen, with which exact args, and which tools the *user* is led to call |
| hidden info | none | the KB (BM25 `KB_search`) holds policy, product facts and the names of "discoverable" tools with random suffixes (`submit_cash_back_dispute_0589`, `open_bank_account_4821`); expected actions reference them exactly |
| policy | none | verify identity (2 of DOB/email/phone/address) before any account access, then `log_verification`; unlock agent tools before calling; give user tools via `give_discoverable_user_tool`; do not unlock tools you will not use; transfer only after asking; user must ask for a human 4× before transfer (8× in one task) |
| failure cost | a wrong sentence loses a few points | one skipped `log_verification` or one wrong tool argument = 0 |

So the health skill's levers (asking, not inventing prose) mostly don't apply. The
plausible tau3 mechanisms to check: (a) does the learner verify + log at all, (b) does it
search the KB before acting or guess tool names, (c) does it unlock-then-call correctly,
(d) does it hand the right *user* tool and tell the user to run it, (e) does it end the
conversation cleanly within 100 steps, (f) does it recommend the product the KB actually
ranks best (the expected `apply_for_credit_card` args are the answer to a comparison).

## Run 1 — `runs/tau-v1`, baseline arm, 4 tasks

- task-001: advice only, user applies (1 expected action, DB basis). Tests (f).
- task-017: verify → give user dispute tool → user disputes 2 txns (4 actions). Tests (a)(b)(d).
- task-059: verify → unlock+call get_all_user_accounts → user applies for card → unlock+call open_bank_account (6 actions). Tests (a)(b)(c)(f).
- task-098: verify → get_referrals → user submits referral with the recommended account (3 actions). Tests (a)(f).

### Prediction, written before the run

- Pass rate 1/4 at most. task-001 is the only likely pass (no verification, a single
  comparison the KB answers directly). task-017 and task-059 fail on (b)/(c): the learner
  either never finds the suffixed tool names or calls without unlocking / doesn't call
  `log_verification`. task-098 fails on (f) (wrong account_type string) or on skipping
  `log_verification`.
- Expect at least one trajectory to burn many steps re-searching the KB or to end without
  `end_conversation`.

## Baseline (runs/tau-v1, 4 tasks, one shared 4M-token pool) — aborted by budget

| task | outcome | steps | tokens | what happened |
|---|---|---|---|---|
| 001 | **pass 1.0** | 24 msgs | 365k | 8 KB_searches, compared cards, user applied for Gold Rewards Card |
| 017 | unfinished | 34 msgs | – | verified + `log_verification` correct; fetched txns; 11 KB_searches; found `submit_cash_back_dispute_0589` in a result and kept searching |
| 059 | unfinished | 78 msgs | – | 40+ KB_searches for Diamond Elite / Platinum APY, rephrasing the same question; never verified, never recommended |
| 098 | unfinished | 24 msgs | – | verified + `log_verification` correct; found and unlocked `get_all_user_accounts_by_user_id_3847` (right order) |

Harness raised `learner budget pool exhausted (gateway 402)` so no eval_result.json; the table
is from `agent/tau3_runtime_state.json`.

Prediction check: 1/4 pass ✓ (001, as predicted). *Wrong* about the mechanism: I predicted
protocol failures (skip `log_verification`, call without unlock). Observed: protocol was
right on both tasks that got there. The failure is one thing — **KB_search loop**: each
result is 10–20k chars of near-duplicate docs (business/personal variants), the learner
re-queries the same question with new wording instead of acting on what it has. Context
grows per step, cost per step grows, pool dies. Same commit-avoidance as the health "list
instead of ask", different surface: here it is "search again instead of answer".

## Intervention: `tau3/SKILL.md` (tau3-search-once-then-act)

Targets, in order of expected effect:
1. §3 search budget (≤2 per question, ≤6 per conversation; query = exact product name + personal/business + attribute; read the whole result) — the mechanism above.
2. §2 verify → `log_verification` immediately with fields from the record (baseline already did this; kept as insurance).
3. §4 unlock-before-call, give-user-tool with exact values, §6 end_conversation — protocol items the baseline never reached, so untested; kept short.

Not in the skill: any task content, product facts, or suffixed tool names.

## Prediction for skill arm (runs/tau-s-017, tau-s-059, tau-s-098; one task per process so a loop cannot drain the others)

- Each task finishes inside 4M tokens with ≤10 KB_searches. Falsifier: any trajectory with >10 searches means §3 is not being followed and the loop is not a prompt-fixable behaviour.
- 098: pass (verification already worked; remaining risk = exact `account_type` string in the user's `submit_referral`).
- 017: 50/50 — needs the learner to compute which transactions are wrong and pass the right IDs to the user's dispute tool; §5 is the only lever and it is untested.
- 059: fail — longest expected sequence (verify, unlock+call account lookup, user applies for card, unlock+call open account); ordering across two discoverable tools is where I expect a slip.
- Overall ≥1/3, and — the claim I actually care about — 3/3 finish with a recorded result.

## Anatomy of the search loop (task-059, skill arm, 43 searches, 0 messages to the user)

Ground truth (from the KB documents inside the runtime container and the expected actions):
the intended answer is Silver Rewards Card ($0 fee) + Green savings account ($100 min open,
$500 min balance); Diamond Elite/Platinum are red herrings the scripted user raises ("what
about premium accounts?"), but the user is scripted to reveal "$5,000 is all I have" and "no
annual fee" *when asked*.

What the trajectory shows:

1. **It never asked.** 43 tool calls, zero `send_message_to_user`. The user's constraints
   (deposit size, spend level, fee tolerance) would have pruned the product space to one or
   two candidates in one turn. Instead it tried to enumerate every product's full spec sheet
   — the health "list the facts instead of asking for them" mechanism, in tool form:
   exhaustive search substituting for one question.
2. **The answers were in its context early and it kept searching.** Searches #2–#3 returned
   the cross-product "Linked Checking + Savings APY boosts" docs listing every savings tier.
   #24 returned "Diamond Elite: How is interest calculated" (7.5%). #29's top hit was
   "Diamond Elite Account — summary" (min balance $250,000). Searches #37–#42 then ask for
   the Diamond Elite minimum balance again, six times. No context condensation occurred
   (input grew 14k → 149k tokens linearly, everything stayed in context), so this is not
   forgetting — it is not reading what it already has.
3. **It models the retriever as semantic; it is BM25.** "Diamond Elite … APY" ranks the
   *credit-card APY-bonus* doc first every time because that doc repeats "APY" and "Diamond
   Elite" most. The model reacted to a wrong top hit by rewording (#5, #6, #7, #16, #22, #26
   are the same question), which returns the same doc. It found the right doc only when it
   accidentally used the doc's own title words ("how is interest calculated", "summary").
4. **Cost is quadratic and it does not notice.** Each result adds ~3.5k tokens to every
   later call; by search #41 a single step cost 149k input tokens and the run had spent
   3.3M. Nothing in the loop gets cheaper, and the model has no signal that it is burning
   the budget.
5. **Skill §3 ("≤2 per question, ≤6 per conversation, read the whole result") had no
   effect on any of 1–4.** The one place the skill visibly acted: query #1 used the
   suggested shape ("personal credit card cash back rate annual fee"). Then the default
   behaviour took over.

So the loop = (no question to the user) × (BM25 treated as semantic) × (not re-reading
context). Only the first is a decision the skill could plausibly change, and the lever is
not "search less" but "before any search, ask the user the constraint that would remove
the most products" — the same gap-ledger idea that worked in health, aimed at the customer
instead of the KB.

## v2: `tau3/SKILL.md` (tau3-ask-before-search) — v1 moved to variants/tau3-v1

Three environment facts, no procedure, no counts: (1) customer only sees `send_message_to_user`
text; (2) ask the most eliminatory constraint before the first search; (3) KB is BM25 —
rewording keeps the ranking, use title words, re-read what you have.

Pre-registered (runs/tau-v2-059, runs/tau-v2-098; proxies measured from tau3_runtime_state.json):

| metric | 059 baseline | 059 v1 | 059 v2 prediction | 098 v1 | 098 v2 prediction |
|---|---|---|---|---|---|
| customer messages before first KB_search | 0 | 0 | ≥1 | 0 (2 searches, then chat reply) | ≥1 or first search then tool message |
| total KB_search | 40+ | 43 | ≤10 | 2 | ≤6 |
| max repeats of the same top-hit doc | 6+ | 6+ | ≤2 | – | – |
| reaches `log_verification` | no | no | yes | no (ended step 4) | yes |
| finishes within 4M | no | no | yes | yes | yes |
| pass | – | – | 30% (chain of 6 exact actions; Green Account string) | 0 | 50% |

Falsifiers: 059 with 0 customer messages before searching → #2 not followed, "asking" is not a
prompt-reachable lever. 098 ending on a plain reply again → #1 wording still insufficient.

## v3: v2 + fact #4 (recommendation is over the whole category; list names, then one search per unseen candidate)

v2 kept at variants/tau3-v2. Pre-registered for runs/tau-v3-059, runs/tau-v3-098:
- proxies from v2 stay within range (msgs-before-search ≥1 on 059, searches ≤15, repeats ≤2, chain complete).
- new proxy: distinct product spec docs retrieved before the recommendation — 059 ≥5 savings tiers incl. Green Account, ≥3 cards incl. Silver Rewards; 098 ≥6 referral programs incl. Blue Account.
- reward: 059 40%, 098 50%. Falsifier: if searches go back above 20, fact #4 has re-opened the loop (the v1 §3 counter-risk) and should be dropped.

## v4 = v2 + provenance rule (variants/tau3-v4), 10 tasks one process each (runs/tau-v4-<id>)

Tasks: 059, 098 (seen) + unseen 032 (card declined, ACTION), 036 (cc balance), 043 (close Platinum card),
050 (limit increase), 085 (debit disputes), 087 (three declines), 093 (interest dispute), 099 (business referral).
Pre-registered: baseline-known pass 001 not rerun. Predictions: ≥3/10 pass; 0 plain-reply endings; no task >20 searches;
059/098 retrieve the expected product's doc (Green Account / Blue Account) before recommending.
Falsifiers: any plain-reply ending → fact #1 insufficient; >20 searches on any task → provenance rule re-opened the loop;
0/8 on unseen → rule does not transfer beyond recommendation tasks. Hypothesis under test: the unifying failure is
"acts on unsourced facts", and stating that as a per-action check moves behaviour across task types.

## Belief update after batch 2 + verifier re-read

- Hypothesis "acts on unsourced facts" survives but the *wording* failed on the timestamp: the learner had a source
  (the harness system prompt's date) and treated it as valid. The rule must distinguish "this environment's tools"
  from "anything in my context". Candidate v5 line: "Facts about *this* environment — the time, IDs, balances,
  what exists — come only from its tools and documents; your own context, memory and system prompt are not sources."
- Turn-1 channel failure (A) is the largest single cluster and is not about sourcing. Candidate: anchor the first
  action explicitly.
- Dropped procedure steps (C) need a rule of the "re-read the document for each item, do not re-derive from memory"
  kind; not yet tested.
- Grader compares nested-argument JSON as a string; nothing a skill should target (would be teaching to the grader),
  but it caps the reachable pass rate.

## Batch 3 (randomised, seed 42 over the 41 untested non-crash tasks): 006 014 018 020 021 029 035 039 057 100

v4 unchanged, baseline control on each. Pre-registered: v4 ≥ 2/10; baseline ≤ 1/10; turn-1 plain replies in
v4 ≤ 4/10; at least one further failing run writes a 2026 timestamp (D generalises); no task > 30 searches.
Falsifiers: v4 0/10 → the 3/12 was luck; no 2026 timestamps and no A failures → v5 should target B/C instead.

## v5 = v4 with fact #1 rewritten as a first-action anchor (variants/tau3-v5)

Only change: #1 now says the reply to the customer's opening message *is* a `send_message_to_user` call.
Tasks: 018, 044, 101 (all turn-1 plain-reply deaths on both arms) + 050 (v4 pass, regression check).
Pre-registered: ≥2/3 of the A-tasks get past turn 1 through the tool; 050 still passes.
Falsifiers: 0/3 past turn 1 → the wording is not the lever for the first-turn regime; 050 fails at turn 1 → the
rewrite broke a case it previously handled.

Result (1 sample each): 018 ✓ 101 ✓ 044 ✗ 050 ✗ — prediction met, regression falsifier tripped. But v4-050 had
passed with the *identical* opening customer line and the identical verification sentence at step 4; the only
difference was tool-call vs chat wrapper. One sample per task cannot separate v4 from v5 → measure a rate.

## First-turn survival rate (runs/t1-*, 5 replicates × 4 tasks × arm; run killed once it survives turn 1)

Survived = the first customer-facing text went out via `send_message_to_user` (runs that did a KB_search first and
then chat-replied count as died). Pre-registered for v5 vs v4: v5 ≥ v4 + 4/20 or the rewrite is not a lever.

| task | v4 | v5 |
|---|---|---|
| 018 | 1/5 | 1/5 |
| 044 | 3/5 | 4/5 |
| 050 | 3/5 | 1/5 |
| 101 | 3/5 | 3/5 |
| total | 10/20 | 9/20 |

Null. Fact-#1 wording does not move turn-1 survival; the earlier "v5 fixed 018/101, broke 050" was sampling noise.
Survival is ~50% and task-dependent (018 hard on both arms).

Found while reading the prompt: the harness injects the skill into the system prompt under OpenHands' repo-context
header — "You may use these instructions for coding style, project conventions, and documentation guidance only."
So every skill is framed to the learner as style guidance. Hera's suggestion: test whether framing fact #1 inside
the skill as a hard runtime constraint (not guidance) changes the rate → v6 (variants/tau3-v6), same 4×5 design,
plus a 20-run baseline arm to learn whether any skill text moves turn 1 at all.
Pre-registered: v6 ≥ 14/20 → framing is the lever; v6 ≈ 10/20 → turn-1 is governed by the harness prior and no
skill text reaches it; baseline ≈ 10/20 → fact #1 has never done anything at turn 1.

Result (baseline arm cancelled at Hera's request to save budget; 2 of the v6-101 replicates unresolved):

| task | v4 | v5 | v6 |
|---|---|---|---|
| 018 | 1/5 | 1/5 | 4/5 |
| 044 | 3/5 | 4/5 | 4/5 |
| 050 | 3/5 | 1/5 | 4/5 |
| 101 | 3/5 | 3/5 | 2/3 |
| total | 10/20 | 9/20 | **14/18** |

Pre-registered threshold (≥14/20) met. Same fact, third wording: v4 stated it, v5 anchored it to the first action,
v6 declared it a runtime property and explicitly disclaimed the "style guidance" frame the harness wraps it in.
Only v6 moved the rate. Interpretation: the failure at turn 1 was not the learner lacking the fact but the harness
telling it the fact was optional. v6 promoted to submissions/devin-curator/tau3/SKILL.md.
Caveat: 18–20 samples per arm; 018 going 1/5 → 4/5 is the strongest single signal. v6 has not been run to the end
for full reward, so clusters B/C/D are untouched by it.

### Post-hackathon ablation: is the harness header the cause? (variants/tau3-v4-noframe)
Decisive test of the "harness framing" interpretation: v4 wording unchanged, but the OpenHands repo-context
preamble (UNTRUSTED_CONTENT block + "coding style, project conventions, and documentation guidance only")
removed from the system prompt via a local patch of the harbor openhands-sdk runner (toggled by a NOFRAME file in
the skill dir; confirmed absent in the agent log). Same 4 tasks × 5 replicates, same turn-1 criterion.
Pre-registered: ≈14/20 → the header was suppressing the rule; ≈10/20 → the header is not the cause and v6 won
by wording salience alone.

| task | v4 (header) | v4 (no header) | v6 (header) |
|---|---:|---:|---:|
| 018 | 1/5 | 2/5 | 4/5 |
| 044 | 3/5 | 1/5 | 4/5 |
| 050 | 3/5 | 3/5 | 4/5 |
| 101 | 3/5 | 4/5 | 2/3 |
| total | 10/20 | **10/20** | 14/18 |

Result: removing the header changed nothing. The interpretation above ("the harness told it the fact was
optional") is **not supported**; v6's effect comes from the paragraph itself (declaring a runtime property,
saying a plain reply terminates the episode, "the same way you would call any other tool"), not from
contradicting the wrapper. Lesson 13 in LEARNINGS.md revised accordingly.

### Post-hackathon decomposition of v6: emphasis vs content (variants/tau3-v7a/b/c)
v6 changed emphasis and content at once. Three arms, same 4 tasks × 5 replicates, same turn-1 criterion:
- v7a-content: v6's information in calm prose (no caps, no "hard constraint", no "not style guidance").
- v7b-emphasis: v4's original sentence with v6's emphasis bolted on ("HARD CONSTRAINT, not style guidance",
  "This is not a preference") and nothing new said.
- v7c-noguidance: v6 verbatim minus the "not style guidance" / "not a preference" clauses.

| arm | 018 | 044 | 050 | 101 | total |
|---|---:|---:|---:|---:|---:|
| v4 (reference) | 1/5 | 3/5 | 3/5 | 3/5 | 10/20 |
| v6 (reference) | 4/5 | 4/5 | 4/5 | 2/3 | 14/18 |
| v7a content, calm | 4/5 | 4/5 | 3/5 | 4/5 | **13/20** |
| v7b emphasis only | 1/5 | 2/5 | 2/5 | 0/5 | **5/20** |
| v7c v6 minus anti-guidance clause | — | — | — | — | 10/20 |

Reading: the content carried the effect (13/20 ≈ v6); emphasis alone did not help and may have hurt (5/20,
all 15 deaths the usual plain "please verify your identity" reply). v7c at 10/20 is inconsistent with both
v6 (14/18) and v7a (13/20) that contain the same content, which is a warning that 20-sample arms move by
±3–4 on their own; the header-removal result (10/20) should be read with the same width. Net: what
distinguishes v6/v7a from v4 is *what is said* — that the runtime terminates on a plain reply and that the
first reply after `start_conversation` is itself a tool call — not how loudly it is said.
Infra: the 60-run launch overloaded Docker (compose failures); infra-failed replicates were relaunched
(turn1_rerun.sh), which also re-sampled killed-survivor runs of those arms.

Infra note: Runware began rejecting requests carrying the OpenAI-only `prompt_cache_key` field ("The request was
rejected", 400); the local gateway now strips it before forwarding.

### Post-hackathon: why the residual deaths happen (raw reasoning) → v9-verb, 20/20
The gateway can now dump the upstream response (`STBENCH_RAW_DUMP`), which exposes GLM's hidden `reasoning`
field that the SDK log does not render for message events. Rerun of v7a on the same 4×5 (`runs/t1-v8raw-*`):
15/20 survived. Split by whether the learner emitted reasoning before its first customer-facing step:

| first step after `start_conversation` | survived | died |
|---|---:|---:|
| no reasoning (straight to a tool call) | 8 | 0 |
| reasoning emitted | 7 | 5 |

Every death's reasoning plans *what* to say and never the channel: "I need to verify identity first. Ask for
name and two identity fields." (018-r4) → typed as a plain reply. Task 101 (3/5 dead) is worst because fact #2
dominates the thinking ("per skill: ask the customer first… let me ask") and "ask" resolves to the chat default.
The one reasoning survivor that wrote "Let's *send a message* asking…" (044-r5) called the tool. Prompt length
(~13.7k tokens) and skill position are identical across fates, so it is not a context/decay effect; the model
quotes the skill in the very reasoning that precedes the death.

Intervention v9-verb (variants/tau3-v9-verb, promoted to tau3/SKILL.md): v7a + three sentences binding the
verbs to the action — "'ask the customer', 'tell the customer', 'greet', 'request verification' all name the
same single action: a `send_message_to_user` call. When your plan ends in 'let me ask them…', the next thing
you emit is that tool call, not the sentence itself." Prediction: ≥17/20, deaths concentrated in reasoning
runs. Result (`runs/t1-v9verb-*`): **20/20** (018 5/5, 044 5/5, 050 5/5, 101 5/5); 16 of 20 emitted reasoning,
and that reasoning reads exactly like the earlier deaths ("Ask for name + verification details…") — the
binding changed the action chosen after the plan, not the plan. Caveat: one 20-run arm, same 4 tasks; ±3–4
noise applies, but 20/20 vs 13–15/20 is outside it. End-to-end pass/fail under v9 not yet run.

### v9 end to end, 22 valid tasks (runs/tau-v9-*) — held-out test of the verb binding
Pass 5/20 recorded (006, 021, 032, 099, 100); 019 and 059 exhausted the learner token budget mid-run (41 and 37
searches — the search loop v4 had tamed on 059 is back) and are unscored. Reference: v4 5/22 (006, 019, 035, 050,
059), baseline 3/24. Turn-1 plain-reply deaths: 5/22 (029, 036, 047, 050, 057) — roughly half the v4/baseline
rate, not zero; 050 was 5/5 in the tuning set and died here with the same content-only reasoning ("I need to
verify identity first. Ask for name and two identity fields."). Net: the intervention transfers partially on its
own proxy and does not move the pass rate, because the remaining mechanisms (B partial candidate set, C dropped
procedure step, search loops) are untouched. Decision: retain with stated scope; the 20/20 is a tuning-set result.
Case study + workbench: casestudy/failure-to-fix.html (compiled from casestudy/body.html).
