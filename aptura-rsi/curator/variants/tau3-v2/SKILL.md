---
name: tau3-ask-before-search
description: Customer-service tasks run through MCP tools with a simulated customer. The customer only sees text sent with send_message_to_user. Before looking anything up, ask the customer the one constraint that removes the most options. The knowledge base is keyword search, not semantic search.
---

# Three facts about this environment

1. **The customer cannot see your replies.** The only text that reaches them is the
   argument of `send_message_to_user`. A plain assistant reply is invisible and ends the
   task with nothing done. Every time you want to say something, it goes through that tool.

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
