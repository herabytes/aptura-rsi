# tau3 results — exact, per task (devin-curator)

Learner: zai-glm-5-3-flash via openhands-sdk 1.47.0, max_iterations 100, eval_budget_tokens 4M
per `stbench eval` invocation. Source for every row: `agent/tau3_runtime_state.json`,
`agent/trajectory.json`, `agent/openhands_sdk.txt`, `verifier/reward.txt` under the run dirs
named below.

## Baseline arm (`runs/tau-v1`, 4 tasks in one process, shared 4M pool; aborted by 402)

| task | reward | msgs in sim | KB_search | protocol calls made | ended how |
|---|---|---|---|---|---|
| 001 | **1.0** | 24 | 8 | — (none needed) | user called `apply_for_credit_card(Gold Rewards Card, …)` = expected action; `end_conversation` |
| 017 | none recorded | 34 | 11 | `get_user_information_by_name` → `log_verification` (correct fields) → `get_credit_card_accounts_by_user` → `get_credit_card_transactions_by_user` | still searching when the pool ran out; `submit_cash_back_dispute_0589` was present in search #7's result, agent searched 4 more times |
| 059 | none recorded | 78 | 40+ | none — never asked for verification | 40+ rephrasings of "Diamond Elite / Platinum savings APY" |
| 098 | none recorded | 24 | 6 | `get_user_information_by_name` → `log_verification` (correct) → `get_referrals_by_user` → `unlock_discoverable_agent_tool(get_all_user_accounts_by_user_id_3847)` (correct order) | pool ran out before `call_discoverable_agent_tool` |

Tokens for 001: 365k input (330k cached), 1.9k output.

## Skill arm (`tau3-search-once-then-act`; one task per process, `runs/tau-s-017`, `runs/tau-s-059`, `runs/tau-s-098`)

| task | reward | msgs in sim | KB_search | what happened |
|---|---|---|---|---|
| 017 | **0.0** | 2 | 0 | Agent step 3: no tool call. Step 4: wrote the "please provide name + two of DOB/email/phone/address" request as a **plain chat message**, not via `send_message_to_user` → episode ended, simulated user never saw it. 4 steps, 66k tokens. |
| 098 | **0.0** | 6 | 2 | Two `KB_search` calls (referral docs, good queries), then the same verification request as a **plain chat message** → episode ended. |
| 059 | none recorded (402) | 88 | 43 | Ignored the §3 search budget entirely: 43 searches on Diamond Elite / Platinum eligibility, then one search for "apply_for_credit_card user discoverable". Never verified. Same loop as baseline, 10 messages longer. |

Skill: 0/3 (2 recorded fails, 1 budget abort). Baseline on the same 3: 0/3 (3 budget aborts).

## Prediction vs observed

| prediction | result |
|---|---|
| each task finishes ≤4M with ≤10 searches | **false** (059: 43 searches, 402 again) |
| 098 pass | **false** (0.0, new failure mode) |
| 017 50/50 | fail |
| 059 fail | fail, but for the mechanism I said the skill would fix, not the ordering slip I predicted |
| 3/3 finish with a recorded result | **false** (2/3) |

## What the evidence says

1. **New failure introduced by the skill (2/2 tasks that got past search):** the learner emitted
   its customer-facing message as ordinary assistant output instead of calling
   `send_message_to_user`. In the baseline 4/4 trajectories used `send_message_to_user` every
   time. Nothing in the skill says to do this, but §1 says "either one `send_message_to_user`
   or one domain tool call" — the model appears to have read "message" as "reply", and a reply
   is how it normally ends a turn. This is the tau version of the health `mkdir → answer in
   chat` delivery failure: the model treats its own final text as the deliverable.
2. **The targeted mechanism (search loop) was not moved by a written budget.** 059 did 43
   searches under a rule that says "at most 6". A number in a skill is not a constraint this
   learner enforces on itself (same as the 2–4 question quota in health being over-executed,
   just in the other direction). Whatever fixes the loop has to change *what it does with a
   result* (read it and answer) rather than *how many* it may do.
3. §2 (verification) and §4–§6 (unlock/give/end) were never exercised: no skill trajectory
   reached them. §5 — flagged as possibly overfit — untested; no evidence either way.

## Verdict on the skill as written

Worse than baseline on the two tasks it changed the behaviour of, no change on the loop task.
Not submittable. The only reusable findings are (1) and (2) above.

## Skill v2 arm (`tau3-ask-before-search`, 3 environment facts; `runs/tau-v2-059`, `runs/tau-v2-098`)

| metric | 059 baseline | 059 v1 | 059 v2 **predicted** | 059 v2 **observed** | 098 v1 | 098 v2 predicted | 098 v2 observed |
|---|---|---|---|---|---|---|---|
| customer msgs before first KB_search | 0 | 0 | ≥1 | **1** (asked spend + fee tolerance; user answered both) | 0 | ≥1 | **0** (searched first, then asked via the tool — allowed by prediction) |
| total KB_search | 40+ | 43 | ≤10 | **9** | 2 | ≤6 | **4** |
| max repeats of same top-hit doc | 6+ | 6+ | ≤2 | **2** | – | – | 1 |
| reaches `log_verification` | no | no | yes | **yes** (after one wrong-name lookup "Daniel Kim", then correct) | no | yes | **yes** |
| unlock → call discoverable tools in order | – | – | – | **yes, both** (`get_all_user_accounts…3847`, `open_bank_account_4821`) | – | – | n/a (task has none) |
| customer performed their action | – | – | – | yes (`apply_for_credit_card`) | no | – | yes (`submit_referral`) |
| finished within 4M, `end_conversation` | no | no | yes | **yes** (34 msgs) | yes | yes | **yes** (24 msgs) |
| reward | – | – | 30% | **0.0** | 0.0 | 50% | **0.0** |

Why 0 despite a complete, correctly ordered chain (DB-state grading, exact match):
- **059:** recommended **Bronze Rewards Card + Silver Plus Account**; expected **Silver Rewards Card + Green Account**. Green Account appeared only as a line in a cross-product list in search #3; the agent never opened its spec doc. Silver Rewards Card ($0 fee) was never searched. So the product comparison was done over the ~4 products it happened to retrieve, not the category.
- **098:** recommended **Light Blue Account** ($30+$20); expected **Blue Account**. The task's required-document list has 19 docs (every checking account's referral program). The agent retrieved 3 programs in 4 searches and compared those. Same cause: comparison over the retrieved subset, not the category.

Read: v2 removed every mechanism it targeted (delivery channel, ask-before-search, search loop) — all five proxy predictions held on 059 — and the remaining failure is a **coverage** failure: "best X for constraint C" requires knowing all X, and the agent stops enumerating as soon as it has *some* candidates. This is the opposite sign to the 059 baseline (searched forever) and shows the model has no notion of "have I seen the whole category" in either direction. Not a channel or protocol problem any more.

## v3 (specific "whole category" rule) and v4 (general provenance rule) vs baseline — 10 tasks

Runs: `runs/tau-v3-*`, `runs/tau-v4-*`, `runs/tau-b-*` (baseline controls, one process per task).
Skill texts: `variants/tau3-v2` (3 facts), `tau3/` = v3 (v2 + #4 "recommendation is over the whole category"),
`variants/tau3-v4` (v2 + #4 "every fact you act on has a source").

| task | type | baseline | v2 | v3 | v4 | v4 notes |
|---|---|---|---|---|---|---|
| 059 | recommend card+savings | 0 (43 searches, budget) | 0 (wrong products) | 0 (24 searches, wrong) | **1.0** | asked first; 28 searches; Silver Rewards Card + Green Account, full chain |
| 098 | recommend referral acct | 0 (budget) | 0 (Light Blue) | **1.0** (Blue) | 0 (Green Fee-Free) | 9 searches, one top-hit repeated 4× |
| 099 | recommend business referral | 0 (21 searches, Lime Green) | – | – | 0 (Lime Green) | same wrong answer as baseline |
| 050 | credit limit increase | 0 (**plain reply at step 4**) | – | – | **1.0** | 13-action chain, all unlock→call pairs |
| 043 | close Platinum card | 0 (**plain reply at step 4**) | – | – | 0 | reached closure tools but skipped dispute-history / pending-replacement / pay-balance prerequisites (1 KB search) |
| 032 | card declined | 0 (**plain reply at step 4**) | – | – | 0 (**plain reply at step 4**) | identical to baseline |
| 036 | cc balance / transactions | 0 (**plain reply at step 3**) | – | – | 0 (**plain reply at step 3**) | identical to baseline |
| 085, 087, 093 | disputes / declines / interest | – | – | – | invalid | harness: user-simulator call fails `Invalid value for 'tools[1].schema.properties'` 8–12×; agent loops start_conversation → not learner evidence |

Valid tasks: baseline 0/7, v4 2/7 (both first recorded skill passes). v3 1/2 on its two tasks.

**What moved (v4 vs baseline, same tasks):**
- Plain-reply ending: baseline 4/5 unseen tasks died there — it is the *dominant* baseline failure on tasks whose first move is "ask for verification", not the loop. v4 fixed it on 043/050 (and 059/098/099 where baseline had got past it), not on 032/036. Fact #1 helps but is not robust; both survivors' openings were "I need help / show me" with no product question the model could ask first, and the verification request was the first thing it wanted to say.
- Search loop: baseline 059 43 → v4 28 (still high, but with 2 customer questions first and a correct answer); baseline 099 21 → v4 7.
- Product choice: v4 fixed 059 (Silver card + Green savings correct for the first time), not 098/099 (same wrong answer as baseline on 099).
- Multi-step internal procedures (043 closure prerequisites): not addressed by any fact in the skill; the agent did one KB search and never read the internal closure procedure doc.

**Prediction check (pre-registered in TAU3_NOTES):** ≥3/10 pass → 2/7 valid (miss, but 3 tasks were harness-invalid); 0 plain-reply endings → **falsified** (2); no task >20 searches → **falsified** (059: 28); 059/098 retrieve the expected product doc → 059 yes, 098 no.

## Second batch (v4 vs baseline, 10 more tasks) and cumulative tally

Invalid (user-simulator schema crash, `request_human_agent_transfer` has empty `properties`): 034, 083, 089, 091, 094 (+ 085, 087, 093 earlier). 12/67 tasks in the dataset have this tool.

| task | type | baseline | v4 | v4 divergence from expected |
|---|---|---|---|---|
| 003 | recommend a card (conservationist) | 0 (12 searches, Gold) | 0 (14 searches, Gold) | expected Silver Rewards Card; same wrong pick as baseline |
| 019 | account/product task, 5 required docs | 0 (**plain reply at step 2**) | **1.0** | 84 msgs, 15 searches, 5 customer msgs before first search |
| 044 | close Gold card | 0 (plain reply) | 0 (**plain reply at step 2**) | identical to baseline |
| 047 | close Silver Zoom + apply Business Platinum + statement credit | 0 (plain reply) | 0 | 14 of 15 expected actions in order; skipped `log_credit_card_closure_reason` for the *second* card before applying the credit |
| 101 | four referrals before year end | 0 (plain reply) | 0 (**plain reply at step 2**) | identical to baseline |

**Cumulative, 12 valid tasks** (001 not rerun; 017 only in v1): baseline **0/12**, v4 **3/12** (019, 050, 059).

Failure modes across the 9 v4 failures, by mechanism:
- **A. Plain reply on the first customer-facing turn** — 032, 036, 044, 101 (4). Baseline: 8/12. Always the *first* assistant turn, always a verification request or a clarifying question; never occurs later in a trajectory once the model has used the tool once. Fact #1 halves it but does not anchor the first action.
- **B. Recommendation from a partial candidate set** — 003, 098, 099 (3). Same wrong product as baseline on 003/099. v3's tailored "whole category" rule fixed 098 once (1/1); v4's general rule fixed 059 (1/1) and none of these.
- **C. Dropped one step of an internal multi-step procedure** — 043 (skipped 3 prerequisite lookups, 1 KB search, never read the closure procedure), 047 (ran the 5-step closure checklist correctly for card 1, skipped step 4 of it for card 2). Not addressed by any fact in the skill.

## Re-reading C against the verifier's per-action checks (047, 043, 098) — three findings

Checked `verifier/*.json` `action_checks` rather than the trajectory alone.

**1. Fabricated `time_verified` (a provenance failure the v4 rule did not catch).** `log_verification` requires
`time_verified`; the environment tool `get_current_time` returns `2025-11-14 03:40:00 EST`, which is what the gold
action contains. Runs that never called it wrote the *harness's* wall-clock date instead (OpenHands system prompt:
"The current date and time is: 2026-09-19T16:37", `openhands_sdk.txt` line 447 in tau-v4-047) → `log_verification`
action_match false and the verification record ID (derived from the timestamp) mismatches the gold DB.

| run | called get_current_time before log_verification | time_verified written | log_verification match |
|---|---|---|---|
| v2-059 | no | 2026-09-19 15:57 | false |
| v4-047 | no | 2026-09-19 16:37 | false |
| v4-098 | no (called it at step 15, *after* logging at step 7) | 2026-09-19 16:12 | false |
| v3-059, v3-098, v4-019, v4-043, v4-050, v4-059, v4-099, b-099 | yes | 2025-11-14 03:40 | true |

Consequence: **v4-098's referral (`Blue Account`) was the expected product** — it failed on the timestamp (and the
`submit_referral` check that follows), not on candidate coverage. Cluster B is therefore 003, 099 (2), and the
fabricated timestamp is a fourth cluster **D** present in ≥3 failing runs. The fact *had* a source — the wrong
frame (harness prompt, not the environment). The v4 wording "a tool returned it" was read as satisfied by the
system prompt's date.

**2. Dropped step on the second item (047), skipped prerequisites (043).** 047: for card 1 (raised at the start) the
learner ran dispute → replacement → reason-history → log-reason in order; for card 2 (raised by the customer
mid-conversation, after the card application) it ran replacement → reason-history → statement credit and omitted
`log_credit_card_closure_reason`. No re-read of the closure doc between the two (10 steps apart); the customer then
kept the card, and the learner appears to have treated "log the reason" as part of closing rather than of the
customer stating a closure intent. 043: read the closure doc once, then jumped to reason-history → log → flag,
skipping dispute check, replacement check, and `pay_credit_card_from_checking` (balance was non-zero).

**3. Grader brittleness (not learner).** `call_discoverable_agent_tool.arguments` is compared as a *string*
(`tau2/data_model/tasks.py:195`, `tool_args == action_args`). 047's `apply_statement_credit` call was correct
but wrote `"amount": 50.00`; gold is `50.0` → mismatch. Key order or float formatting inside the JSON string
fails the action regardless of correctness.

Revised clusters over the 9 v4 failures: A turn-1 plain reply (032, 036, 044, 101); B partial candidate set
(003, 099); C dropped procedure step (043, 047); D fabricated environment fact (047, 098; also v2-059).
