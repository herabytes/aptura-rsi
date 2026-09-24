---
name: tau3-ask-before-search-sourced
description: Customer-service tasks run through MCP tools with a simulated customer. The customer only sees text sent with send_message_to_user. Before looking anything up, ask the customer the one constraint that removes the most options. The knowledge base is keyword search, not semantic search. Every fact you act on must have a source - the customer, a tool result, or a document you read.
---

# Four facts about this environment

1. **There is no chat channel to the customer.** The customer process receives exactly
   one input: the `message` argument of the tool `send_message_to_user`. A plain assistant
   reply is not delivered to anyone; the harness treats it as "agent finished" and
   terminates the episode with nothing done. So after `start_conversation` returns the
   customer's opening line, the greeting / "please verify your identity" / first question
   is emitted as a `send_message_to_user` tool call, the same way you would call any other
   tool, and so is every later thing you say to the customer. In this environment the
   verbs "ask the customer", "tell the customer", "greet", "request verification" all name
   the same single action: a `send_message_to_user` call. When your plan ends in "let me
   ask them ...", the next thing you emit is that tool call, not the sentence itself.

2. **A question to the customer is cheaper than a search, and usually removes more
   options.** Before your first `KB_search`, ask the customer the one thing whose answer
   would eliminate the most products or paths: how much they have to deposit, whether they
   will accept an annual fee, what they spend per month, whether they hold a subscription.
   Then search only for what survives. If a search result raises a new question the
   customer can answer, ask them instead of searching again.

3. **`KB_search` is keyword (BM25) search.** It ranks documents by how often your words
   appear in them, not by meaning. Rewording the same question returns the same ranking.
   If the top hit is the wrong document, the fix is different words — the exact product
   name plus the words a document title would use ("specifications and requirements",
   "how is interest calculated", "complete guide", "internal: opening") — not a longer
   version of the same query. Read the whole result before deciding you need another one;
   what you need is often in a result you already have.

4. **Every fact you act on has a source.** There are exactly three: the customer said it,
   a tool returned it, or a document you have read states it. Before any step that commits
   — a recommendation, a lookup by name, opening or filing something, telling the customer
   a number — name to yourself the source of each fact that step rests on. A fact with no
   source is not an assumption to make; it is a question to the customer or one search.
   A claim of the form "best", "cheapest", "all", "only" or "none" rests on the whole
   list, so its source has to be the list — a category overview or one document per
   member — not the first few items a search happened to return. If you cannot source the
   whole list, say which items you compared.
