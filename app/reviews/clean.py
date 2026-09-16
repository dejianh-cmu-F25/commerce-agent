"""Clean Amazon review text before it is read or indexed (feature 046, step C).

The Reviews'23 text is real user input, so it carries what real user input carries:
inline video markers (``[[VIDEOID:...]]``), HTML entities, runs of punctuation and
reviews that are a rating with no content ("5 stars", "Very tight"). Indexing that
verbatim puts noise in the retrieval signal and in the model's context, so it is
cleaned once here and reused everywhere a review is consumed.

Cleaning is deliberately conservative: it removes markup and empty reviews, and never
rewrites what a customer said - a review is evidence, and paraphrasing evidence would
make the citation worthless.
"""

from __future__ import annotations

import html
import re

_VIDEO = re.compile(r"\[\[VIDEOID:[^\]]*\]\]?", re.I)
_IMAGE = re.compile(r"\[\[IMAGEID:[^\]]*\]\]?", re.I)
_MARKUP = re.compile(r"<[^>]{1,80}>")
_URL = re.compile(r"https?://\S+")
_PUNCT_RUN = re.compile(r"([!?.,])\1{2,}")

# A review shorter than this carries no retrievable claim (``Very tight`` does, but it
# is the review *title* that carries it - the body is what this threshold applies to).
MIN_REVIEW_CHARS = 40

# Bodies that are only a rating: no claim to retrieve or quote.
_RATING_ONLY = re.compile(
    r"^(?:\s*(?:[1-5](\.0)?\s*stars?|five|four|three|two|one)\s*stars?[.!]?\s*)+$",
    re.I,
)


def clean_review_text(text: str) -> str:
    """Markup and formatting removed, whitespace collapsed."""
    cleaned = html.unescape(text or "")
    cleaned = _VIDEO.sub(" ", cleaned)
    cleaned = _IMAGE.sub(" ", cleaned)
    cleaned = _MARKUP.sub(" ", cleaned)
    cleaned = _URL.sub(" ", cleaned)
    cleaned = _PUNCT_RUN.sub(r"\1", cleaned)
    return " ".join(cleaned.split())


def is_usable_body(text: str, *, min_chars: int = MIN_REVIEW_CHARS) -> bool:
    """True when a cleaned body is worth indexing: long enough and not a bare rating."""
    if len(text) < min_chars:
        return False
    return not _RATING_ONLY.match(text)


def clean_review(body: str, title: str = "") -> str:
    """The text to index for one review: its cleaned title and body together.

    The title is often where the claim lives ("Very tight"), so it is kept rather than
    discarded as metadata.
    """
    cleaned_title = clean_review_text(title)
    cleaned_body = clean_review_text(body)
    if cleaned_title and cleaned_body and cleaned_title.lower() not in cleaned_body.lower():
        return f"{cleaned_title}. {cleaned_body}"
    return cleaned_body or cleaned_title
