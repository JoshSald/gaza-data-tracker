"""UN2720 monthly infographics (PDF). A fixed template, so plain patterns are enough.

When UNOPS changes the layout these patterns stop matching. The run then reports
"no figures found" for that PDF instead of guessing, and the pattern needs updating.
"""
from __future__ import annotations

import calendar
import datetime as dt
import re

from ..archive import fetch, keep
from ..text import pdf_text
from .base import Proposal, Rejected, discover, make_id

PUBLISHER = "UN2720 Mechanism (UNOPS)"
MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}

DELIVERED = re.compile(
    r"in (?P<month>[A-Za-z]+) (?P<year>\d{4}), (?:a total of )?(?P<value>[\d.,]+)(?P<k> ?k)? metric tonnes \(t\) of humanitarian aid "
    r"processed through the un ?2720 mechanism (?:were|was) delivered",
    re.IGNORECASE,
)
# "As of 30 June, a total of over 105,000 t (over 151,000 pallets) of aid are in the pipeline"
# "As of 30 April 2025, a total of over 124,000 t of aid (over 182,000 pallets) were in the pipeline"
PIPELINE = re.compile(
    r"as of (?P<day>\d{1,2}) (?P<month>[A-Za-z]+)(?: (?P<year>\d{4}))?, a total of over (?P<value>[\d.,]+)(?P<k> ?k)? t "
    r"(?:\((?:over|nearly) [\d.,]+ ?k? pallets\) of aid|of aid \((?:over|nearly) [\d.,]+ ?k? pallets\)) (?:are|is|were) in the pipeline",
    re.IGNORECASE,
)
NO_AID = re.compile(r"in (?P<month>[A-Za-z]+) (?P<year>\d{4}), no humanitarian aid processed through the un ?2720 mechanism was delivered", re.IGNORECASE)
# The separate pipeline infographics reuse a "delivered" sentence whose figure does not match the
# monthly overview for the same month (31 Aug 2025: 73K t against 30.4K t), so they are not parsed.
PIPELINE_INFOGRAPHIC = "overview of humanitarian aid in the pipeline"


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def _tonnes(m: re.Match) -> tuple[float, str, str]:
    """Value, bound and a note on how the report states it. "12.7K" is stated in thousands."""
    if m.group("k"):
        return round(_num(m.group("value")) * 1000), "approximate", f"Stated as {m.group('value')}K t in the report."
    value = _num(m.group("value"))
    return (int(value) if value.is_integer() else value), "exact", ""


def parse(text: str, doc_meta: dict) -> list[dict]:
    t = re.sub(r"\s+", " ", text)
    out = []
    if PIPELINE_INFOGRAPHIC in t.lower():
        return out
    year = None
    m = DELIVERED.search(t)
    if m and m.group("month").lower() in MONTHS:
        year, month = int(m.group("year")), MONTHS[m.group("month").lower()]
        last = calendar.monthrange(year, month)[1]
        as_of = f"{year}-{month:02d}-{last:02d}"
        start = f"{year}-{month:02d}-01"
        value, bound, stated = _tonnes(m)
        out.append({
            "id": make_id("un2720", "aid.un2720.delivered_tonnes", as_of, start),
            "metric": "aid.un2720.delivered_tonnes",
            "value": value,
            "kind": "count",
            "bound": bound,
            "source": "un2720",
            "as_of": as_of,
            "period_start": start,
            "period_end": as_of,
            "document": doc_meta,
            "quote": m.group(0),
            "caveat": " ".join(filter(None, [stated, "Only UN-manifested aid, not all aid."])),
            "added_by": "importer:un2720",
        })
    elif n := NO_AID.search(t):
        year = int(n.group("year"))
    p = PIPELINE.search(t)
    if p and p.group("month").lower() in MONTHS and (p.group("year") or year):
        as_of = dt.date(int(p.group("year") or year), MONTHS[p.group("month").lower()], int(p.group("day"))).isoformat()
        value, _, stated = _tonnes(p)
        out.append({
            "id": make_id("un2720", "aid.un2720.pipeline_tonnes", as_of),
            "metric": "aid.un2720.pipeline_tonnes",
            "value": value,
            "kind": "count",
            "bound": "at_least",
            "source": "un2720",
            "as_of": as_of,
            "period_start": None,
            "period_end": as_of,
            "document": doc_meta,
            "quote": p.group(0),
            "caveat": " ".join(filter(None, ["Approved by COGAT but not yet delivered to Gaza.", stated])),
            "added_by": "importer:un2720",
        })
    return out


def run(entry: dict, metrics: list[dict], state: dict) -> Proposal:
    prop = Proposal()
    for url in discover(entry):
        try:
            doc = fetch(url)
        except Exception as e:  # noqa: BLE001 - report and move on to the next document
            prop.rejected.append(Rejected(url, "could not download", str(e)))
            continue
        prop.seen[url] = doc.sha256
        if state.get(url) == doc.sha256:
            continue
        keep(doc)
        text = pdf_text(doc.content)
        found = parse(text, doc.meta(PUBLISHER))
        no_aid = NO_AID.search(re.sub(r"\s+", " ", text))
        if no_aid:
            prop.notes.append(f"{url}: states that no aid was delivered in {no_aid.group('month')} {no_aid.group('year')}; no delivered figure recorded.")
        elif not found:
            prop.rejected.append(Rejected(url, "no figures found", "The report layout may have changed; update the patterns in ingest/sources/un2720.py."))
        prop.observations += found
    return prop
