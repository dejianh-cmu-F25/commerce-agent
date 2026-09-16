You rewrite a shopper's request into a search query for a product catalog, and you
extract any hard constraints.

The shopper often describes a task or a situation rather than naming a product
("something to keep dog hair off my clothes while grooming him"). Rewrite it into
the words a product's own description or customer reviews would use, so a keyword
or embedding search can match it. Keep it short (a phrase, not a sentence). Do not
invent brand names or product names that the shopper did not mention.

Extract a maximum price only when the shopper states one ("under $30", "cheaper
than 20"). Otherwise use null.

Shopper request: {query}

Answer with JSON only, no prose:
{"query": "<rewritten search query>", "max_price": <number or null>}
