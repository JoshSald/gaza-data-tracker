"""Checks that an extracted figure really is in the archived document."""
from __future__ import annotations

import re
import unicodedata

from .numbers import quote_supports


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("­", "")
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_in_document(quote: str, document_text: str) -> bool:
    q = normalize(quote)
    return len(q) >= 20 and q in normalize(document_text)


def verify_figure(value: float, quote: str, document_text: str) -> list[str]:
    """Problems that should stop a figure from being proposed. Empty means it passed."""
    problems = []
    if not quote_in_document(quote, document_text):
        problems.append("quote not found word for word in the archived document")
    if not quote_supports(value, quote):
        problems.append(f"the quote does not state the value {value:g}")
    return problems
