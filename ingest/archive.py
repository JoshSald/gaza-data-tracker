"""Download a document once, keep a copy, and fingerprint it."""
from __future__ import annotations

import datetime as dt
import hashlib
import mimetypes
import os
from dataclasses import dataclass

import requests

from .paths import ARCHIVE, ROOT

USER_AGENT = "gaza-tracker/0.1 (+https://github.com/; data archiving for a public tracker)"


@dataclass
class Document:
    url: str
    content: bytes
    content_type: str
    sha256: str
    retrieved_at: str
    archive_path: str | None = None
    archive_note: str | None = None

    def meta(self, publisher: str) -> dict:
        meta = {"url": self.url, "publisher": publisher, "retrieved_at": self.retrieved_at, "sha256": self.sha256}
        if self.archive_path:
            meta["archive"] = self.archive_path
        if self.archive_note:
            meta["note"] = self.archive_note
        return meta


def _ext(content_type: str, url: str) -> str:
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return ".pdf"
    if "json" in content_type:
        return ".json"
    return mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".html"


def fetch(url: str, timeout: int = 60) -> Document:
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    content = resp.content
    return Document(
        url=url,
        content=content,
        content_type=resp.headers.get("content-type", ""),
        sha256=hashlib.sha256(content).hexdigest(),
        retrieved_at=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    )


# Above this size only the document's text is kept, so the repository stays small enough to clone.
MAX_ARCHIVE_BYTES = 5_000_000


def keep(doc: Document, text: str | None = None) -> Document:
    """Save a copy under archive/YYYY/MM/. Set ARCHIVE_DISABLED=1 to skip, for example in tests.

    For documents over MAX_ARCHIVE_BYTES, pass `text` (the extracted text) and that is kept instead;
    `sha256` still identifies the original file, which can be fetched again from its URL."""
    if os.environ.get("ARCHIVE_DISABLED") == "1":
        return doc
    now = dt.datetime.now(dt.timezone.utc)
    folder = ARCHIVE / f"{now:%Y}" / f"{now:%m}"
    folder.mkdir(parents=True, exist_ok=True)
    if len(doc.content) > MAX_ARCHIVE_BYTES and text is not None:
        path = folder / f"{doc.sha256[:16]}.txt"
        if not path.exists():
            path.write_text(text, encoding="utf-8")
        doc.archive_note = f"Original is {len(doc.content) / 1e6:.0f} MB; the archive keeps its extracted text. sha256 is of the original file."
    else:
        path = folder / f"{doc.sha256[:16]}{_ext(doc.content_type, doc.url)}"
        if not path.exists():
            path.write_bytes(doc.content)
    doc.archive_path = str(path.relative_to(ROOT))
    return doc
