---
name: tau3-search-once-then-act
description: Customer-service agent tasks driven by MCP tools (start_conversation, send_message_to_user, KB_search, domain tools). Pass/fail is decided by the exact tool calls made, not by prose. Verify and log first, search the knowledge base with a budget and stop when the answer is on screen, copy discoverable tool names exactly, unlock before calling, hand the user their tool, then end the conversation.
---

# Tool-use customer service: the record is the answer

The grader never reads your messages. It checks the final database state and the list of
tool calls (yours and the user's) against an expected list. One missing `log_verification`,
one guessed tool name, or one conversation that never ends scores zero. Every step below
exists to make one of those calls happen, or to stop a step that wastes context.

## 1. Step discipline

- One thing per step: either one `send_message_to_user`, or one domain tool call. Never both.
- `start_conversation` exactly once, first.
- Tool results are long (10–20k characters each). Your context is the scarce resource; each
  extra search makes every later step more expensive and pushes you toward the step limit.

## 2. Verification comes first whenever you will touch the user's records

If the request needs any account, transaction, referral or profile data:

1. Ask for name plus two of: date of birth, email, phone, address. Do not reveal anything
   from their record before this.
2. Look the user up (`get_user_information_by_name` or equivalent). Check that two supplied
   values match the record.
3. Immediately call `log_verification` with the fields exactly as they appear in the
   record you retrieved (user_id, name, address, email, phone_number, date_of_birth, and
   the method/values you checked). This call is expected by the grader; skipping it fails
   the task even if everything else is right. Do it once per conversation.

If the request is only product advice and the user does not want anything done on their
account, do not verify.

## 3. Knowledge-base search: budget it, then act

The KB is BM25 over many near-duplicate documents (personal vs business variants of the
same product, promos, FAQs). Rephrasing the same question returns the same documents.

- Before searching, write down (to yourself) the one question this search must answer,
  e.g. "everyday cash-back rate of each personal card", "which tool files a cash-back
  dispute", "APY of Green savings account for $5,000".
- Query with the exact product name and the word `personal` or `business` as appropriate,
  plus the attribute: `"Gold Rewards Card personal cash back rate annual fee"`.
- Read the whole result before searching again; the answer is often lower down in a
  document that ranked first for a different reason.
- Budget: at most 2 searches per question, and at most 6 searches per conversation unless
  a search result explicitly points you to another document. When the budget is spent,
  act on what you have; tell the user plainly if something is not in the KB. Do not search
  for the same product a third time with different wording.
- When the user must choose between products, build a small table (product, the metric
  they care about, fee, eligibility) from the documents you already have, apply their
  constraints (no annual fee, deposit size, subscription, income), and recommend one card
  or account by its exact name. Ask at most the 1–2 questions whose answer changes the
  recommendation (e.g. "Do you have a Rho-Bank+ subscription?", "Would you accept an
  annual fee?"), then recommend.

## 4. Discoverable tools: exact names, unlock before call, give before asking the user to act

The KB names special tools with a numeric suffix (`open_bank_account_4821`,
`submit_cash_back_dispute_0589`). Only names copied verbatim from a KB document work.

- Agent tool: `unlock_discoverable_agent_tool(name)` first, then
  `call_discoverable_agent_tool(name, arguments)`. Never call without unlocking; never
  unlock a tool you will not call.
- User tool: when the KB says the customer performs the action themselves, call
  `give_discoverable_user_tool(name)` and in your next message tell the user the tool
  name, its arguments, and the exact values to use (their user_id, the transaction_id(s)
  you identified, the account type). Do this for every item they need to act on, in one
  message.
- If the user has their own tool (apply for a card, submit a referral), your job is to
  give them the exact product name and values to use, then let them act. Do not offer to
  apply for them.

## 5. Investigations: identify the specific records, then hand over

For "something is wrong with my rewards/interest/fees": fetch the account and its
transactions, compute what the KB says each should have been, list the specific
transaction IDs that differ with the expected vs actual value, and then either apply the
correction with the agent tool the KB names, or give the user the dispute tool for exactly
those IDs. The user will not diagnose it for you.

## 6. Transfers and endings

- Transfer to a human only after asking the user, and only if nothing in the KB or your
  tools covers the request. If the request is within your capability, keep helping; the
  policy sets how many repeated requests it takes before you may transfer — count them.
- When the user has done their action, has what they asked for, or says goodbye, send one
  short closing message and then call `end_conversation` (or emit `###STOP###`). Do not
  keep searching after the case is resolved.
