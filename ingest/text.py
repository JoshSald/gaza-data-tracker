"""Turn a fetched document into plain text for extraction and quote checks."""
from __future__ import annotations

import io

from bs4 import BeautifulSoup


def pdf_text(content: bytes) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def html_text(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "form", "svg"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    return main.get_text("\n", strip=True)


def document_text(content: bytes, content_type: str, url: str = "") -> str:
    if "pdf" in content_type or url.lower().endswith(".pdf") or content[:5] == b"%PDF-":
        return pdf_text(content)
    return html_text(content)
