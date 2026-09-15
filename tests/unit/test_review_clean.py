"""Review cleaning: remove markup, keep the customer's words (feature 046, step C)."""

from __future__ import annotations

from app.reviews.clean import clean_review, clean_review_text, is_usable_body


def test_inline_video_and_image_markers_are_removed():
    """42 of 6,548 real reviews carry these; they are noise in retrieval."""
    text = "[[VIDEOID:8c2dfbecd661603dc7f2f3171b526ccf]] The panel is smaller than I expected."
    assert "VIDEOID" not in clean_review_text(text)
    assert clean_review_text(text).startswith("The panel is smaller")


def test_html_entities_are_decoded():
    assert clean_review_text("It&#39;s great &amp; cheaper.") == "It's great & cheaper."


def test_markup_and_urls_are_stripped_but_the_claim_survives():
    cleaned = clean_review_text("<p>Runs small.</p> See https://example.com/abc for sizing.")
    assert "<p>" not in cleaned and "example.com" not in cleaned
    assert "Runs small." in cleaned


def test_repeated_punctuation_is_collapsed():
    assert clean_review_text("Amazing!!!! Really???") == "Amazing! Really?"


def test_a_bare_rating_body_is_not_usable():
    assert not is_usable_body("5 stars")
    assert not is_usable_body("Five stars!!!!")
    assert not is_usable_body("Too short")


def test_a_short_body_with_a_claim_is_usable_only_when_long_enough():
    assert not is_usable_body("Very tight")
    assert is_usable_body("The insole made them super tight, almost too small.")


def test_the_title_is_kept_when_it_carries_the_claim():
    """The complaint often lives in the title, not the body."""
    assert clean_review("It was fine I guess, nothing special here at all.", "Very tight") == (
        "Very tight. It was fine I guess, nothing special here at all."
    )


def test_the_title_is_not_duplicated_when_it_opens_the_body():
    assert clean_review("Very tight, had to return.", "Very tight") == "Very tight, had to return."
