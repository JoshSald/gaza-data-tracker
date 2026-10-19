"""Press releases and reports in free text (OHCHR, WHO, OCHA, MSF...), read by a language model.

Every figure the model proposes must pass verify.verify_figure against the archived
document: its quote has to appear word for word, and the quote has to state the value.
"""
from __future__ import annotations

import datetime as dt

from ..archive import fetch, keep
from ..llm import extract_figures
from ..text import document_text
from ..verify import verify_figure
from .base import Proposal, Rejected, discover, make_id


def _iso(s: str | None) -> str | None:
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10]).isoformat()
    except ValueError:
        return None


def run(entry: dict, metrics: list[dict], state: dict, sources: list[dict] | None = None) -> Proposal:
    prop = Proposal()
    allowed = [m for m in metrics if m["id"] in set(entry["metrics"])]
    if not allowed:
        prop.notes.append(f"{entry['id']}: no known metrics listed, skipped.")
        return prop
    names = {s["id"]: s["name"] for s in (sources or [])}
    source = entry["source"]
    publisher = entry.get("publisher") or names.get(source, source)
    for url in discover(entry):
        try:
            doc = fetch(url)
        except Exception as e:  # noqa: BLE001
            prop.rejected.append(Rejected(url, "could not download", str(e)))
            continue
        prop.seen[url] = doc.sha256
        if state.get(url) == doc.sha256:
            continue
        keep(doc)
        text = document_text(doc.content, doc.content_type, url)
        try:
            figures = extract_figures(text, source_name=publisher, metrics=allowed)
        except Exception as e:  # noqa: BLE001
            prop.rejected.append(Rejected(url, "extraction failed", str(e)))
            prop.seen.pop(url, None)  # try this document again next run
            continue
        for f in figures:
            metric, value, quote = f.get("metric"), f.get("value"), f.get("quote", "")
            as_of, start = _iso(f.get("as_of")), _iso(f.get("period_start"))
            if metric not in {m["id"] for m in allowed}:
                prop.rejected.append(Rejected(url, "unknown metric", f"{metric}: {quote[:160]}"))
                continue
            if not isinstance(value, (int, float)) or not as_of:
                prop.rejected.append(Rejected(url, "missing value or date", quote[:160]))
                continue
            problems = verify_figure(value, quote, text)
            if problems:
                prop.rejected.append(Rejected(url, "; ".join(problems), f"{metric} = {value:g}: “{quote[:200]}”"))
                continue
            dims = f.get("dimensions") or None
            prop.observations.append({
                "id": make_id(source, metric, as_of, start, dims),
                "metric": metric,
                "value": value,
                "kind": entry.get("kind", "count"),
                "bound": f.get("bound") if f.get("bound") in ("exact", "at_least", "approximate") else "exact",
                "source": source,
                "as_of": as_of,
                "period_start": start,
                "period_end": as_of,
                **({"dimensions": dims} if dims else {}),
                "document": doc.meta(publisher),
                "quote": quote.strip(),
                "added_by": "importer:press",
            })
    return prop
