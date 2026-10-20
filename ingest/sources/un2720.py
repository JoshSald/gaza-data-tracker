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
# Trucks collected from the crossings, and of those, how many arrived and how many were intercepted in transit.
# Reported from May to November 2025, in three layouts whose extracted text orders labels and numbers differently:
#   Aug-Nov 2025: "Arrived 589 Trucks Intercepted 2,797 Trucks" and "3,387 Collected 36K t"
#   Jul 2025:     "Arrived Intercepted 73Trucks 1,055 Trucks" (labels first, numbers in the same order)
#   Jun 2025:     "1,090 Trucks Collected" and "1,043 Trucks Intercepted 47 Trucks Arrived"
#   May 2025:     "330 Trucks Collected" and "212 Intercepted 118 Arrived Trucks Trucks" (numbers before labels)
# In each month the arrived and intercepted trucks add up to the collected trucks the report states.
TRUCKS_LABELLED = re.compile(r"Arrived (?P<arrived>[\d,]+) Trucks Intercepted (?P<intercepted>[\d,]+) Trucks")
TRUCKS_LABELS_FIRST = re.compile(r"Arrived Intercepted (?P<arrived>[\d,]+) ?Trucks (?P<intercepted>[\d,]+) Trucks")
TRUCKS_UNITS_FIRST = re.compile(r"(?P<intercepted>[\d,]+) Trucks Intercepted (?P<arrived>[\d,]+) Trucks Arrived")
TRUCKS_NUMBERS_FIRST = re.compile(r"(?P<intercepted>[\d,]+) Intercepted (?P<arrived>[\d,]+) Arrived Trucks Trucks")
COLLECTED = re.compile(r"(?P<collected>[\d,]+) (?:Trucks Collected|Collected [\d.,]+K? t\b)")
TRUCK_CAVEAT = "Only UN-manifested aid. Collected trucks are those picked up from Gaza's crossings; arrived and intercepted split them."
LAYOUT_CAVEAT = "The report's text places these labels and numbers apart; the reading follows its layout."

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
        out += _trucks(t, year, month, doc_meta)
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


def _trucks(t: str, year: int, month: int, doc_meta: dict) -> list[dict]:
    """Monthly trucks collected, arrived and intercepted, when the report gives them."""
    last = calendar.monthrange(year, month)[1]
    as_of, start = f"{year}-{month:02d}-{last:02d}", f"{year}-{month:02d}-01"
    found: dict[str, tuple[int, str, str]] = {}
    layouts = [(TRUCKS_LABELLED, ""), (TRUCKS_UNITS_FIRST, ""), (TRUCKS_LABELS_FIRST, LAYOUT_CAVEAT),
               (TRUCKS_NUMBERS_FIRST, LAYOUT_CAVEAT)]
    for pattern, note in layouts:
        m = pattern.search(t)
        if m:
            for key in ("arrived", "intercepted"):
                found[key] = (int(_num(m.group(key))), m.group(0), note)
            break
    if found:
        c = COLLECTED.search(t)
        if c:
            found["collected"] = (int(_num(c.group("collected"))), c.group(0), "")
    rows = []
    for key, (value, quote, note) in found.items():
        metric = f"aid.un2720.trucks_{key}"
        rows.append({
            "id": make_id("un2720", metric, as_of, start),
            "metric": metric,
            "value": value,
            "kind": "count",
            "bound": "exact",
            "source": "un2720",
            "as_of": as_of,
            "period_start": start,
            "period_end": as_of,
            "document": doc_meta,
            "quote": quote,
            "caveat": " ".join(filter(None, [TRUCK_CAVEAT, note])),
            "added_by": "importer:un2720",
        })
    return rows


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
