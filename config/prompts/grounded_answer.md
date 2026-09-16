You answer a shopper's request using ONLY the product passages below. Each passage
is prefixed with its product id in square brackets.

Shopper request: {query}

Passages:
{passages}

Pick the ONE product that best serves the request, using only these passages.
Quote the exact sentence from a passage that supports your choice - verbatim, do
not paraphrase or invent. Do not use any knowledge outside the passages.

Answer with JSON only, no prose:
{{"product_id": "<the id in square brackets>", "quote": "<verbatim sentence from a passage>"}}
