"""SQLite-backed real review store (feature 046).

Reviews come from Amazon Reviews'23 (see ``scripts/import_reviews.py``) and live in
``data/reviews/reviews.sqlite`` (gitignored: the dataset is research-licensed and is
not redistributed). Read-only from the app's perspective.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.ports.reviews import Review
from app.reviews.clean import clean_review_text

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    product_id TEXT NOT NULL,
    rating REAL NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    helpful_votes INTEGER NOT NULL DEFAULT 0,
    verified INTEGER NOT NULL DEFAULT 0,
    timestamp_ms INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
"""


class SqliteReviewStore:
    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as conn:
            conn.executescript(_SCHEMA)

    def add(self, reviews: list[Review]) -> int:
        if not reviews:
            return 0
        rows = [
            (
                r.product_id,
                r.rating,
                r.title,
                r.text,
                r.helpful_votes,
                int(r.verified),
                r.timestamp_ms,
            )
            for r in reviews
        ]
        with sqlite3.connect(self._path) as conn:
            conn.executemany(
                "INSERT INTO reviews (product_id, rating, title, text, helpful_votes, verified,"
                " timestamp_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
        return len(rows)

    def count(self) -> int:
        with sqlite3.connect(self._path) as conn:
            return int(conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0])

    def get_reviews(self, product_id: str, limit: int = 5) -> list[Review]:
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(
                "SELECT product_id, rating, title, text, helpful_votes, verified, timestamp_ms"
                " FROM reviews WHERE product_id = ?"
                " ORDER BY helpful_votes DESC, timestamp_ms DESC LIMIT ?",
                (product_id, limit),
            ).fetchall()
        return [
            Review(
                product_id=row[0],
                rating=row[1],
                # Cleaned on read: the store keeps the raw dataset, every consumer sees
                # markup-free text (C).
                title=clean_review_text(row[2]),
                text=clean_review_text(row[3]),
                helpful_votes=row[4],
                verified=bool(row[5]),
                timestamp_ms=row[6],
            )
            for row in rows
        ]
