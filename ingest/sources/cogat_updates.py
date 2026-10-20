"""COGAT's daily humanitarian updates, from the archive on its aid site (gaza-aid-data.gov.il).

COGAT posted a short update most days from December 2023 to 16 January 2025, then stopped. Each update is a list of
bullets in English. Two kinds of figure are read, both only when the update states them outright:

- trucks that entered Gaza "yesterday": "260 trucks carrying humanitarian goods were transferred to Gaza yesterday",
  "Yesterday, 161 humanitarian aid trucks entered Gaza". The date is the day before the update.
- trucks that entered since the war began: "Since the outbreak of the war, over 64,000 trucks ... entered".

Bullets about trucks coordinated, collected, distributed, sent to northern Gaza or along a single route (the Jordanian
route, JLOTS, Route 96), and fuel or water trucks, are not read: they count something else. An update that does not
match is left out rather than guessed; one, on 30 December 2023, gives "XXX" in place of a number.

These are COGAT's own counts of its own activity, recorded as counts like COGAT's other truck figures, with a caveat.

The archive page loads its updates with a POST request to the site's own data endpoint; the response is archived as the
document, and each quote is checked against it.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re

import requests

from ..archive import USER_AGENT, Document, keep
from ..verify import verify_figure
from .base import Proposal, Rejected, make_id

PAGE = "https://gaza-aid-data.gov.il/mainhome/archive/"
API = "https://gaza-aid-data.gov.il/umbraco/api/faq/GetFAQ"
# The archive component's query and page, as set in the page's HTML.
REQUEST = {"id": "72136", "CurrentPageId": "72943", "Query": "", "Skip": 0, "Limit": 0}
PUBLISHER = "COGAT (Israel Humanitarian Efforts site)"

N = r"(?P<n>\d{1,3}(?:,\d{3})+|\d+)"
TRUCKS = r"(?:[Hh]umanitarian )?(?:aid )?trucks(?: carrying humanitarian (?:goods|aid))?"
MOVED = r"(?:were|was) (?:inspected and )?transferr?ed (?:in)?to (?:the )?Gaza(?: [Ss]trip)?|entered (?:the )?Gaza(?: [Ss]trip)?"
DAILY = [
    re.compile(r"(?:A total of )?" + N + r" " + TRUCKS + r",? (?:" + MOVED + r"),? \(?yesterday"),
    re.compile(r"[Yy]esterday, ?" + N + r" " + TRUCKS + r",? (?:" + MOVED + r")"),
]
SINCE_WAR = re.compile(
    r"(?:over|more than) " + N + r" (?:humanitarian )?(?:aid )?trucks[^.]{0,60}? entered (?:the Gaza Strip|Gaza)[^.]{0,40}? "
    r"since the (?:outbreak|start|beginning) of the war"
    r"|[Ss]ince the (?:outbreak|start|beginning) of the war,? (?:over|more than) (?P<n2>\d{1,3}(?:,\d{3})+|\d+) "
    r"(?:humanitarian )?(?:aid )?trucks[^.]{0,60}? entered"
)
OTHER_COUNTS = re.compile(r"coordinat|collect|distribut|northern Gaza|Jordanian|JLOTS|Route 96|fuel|gas |water truck|empty", re.I)
DATE = re.compile(r"(?P<month>[A-Za-z]{3,9})\.? (?P<day>\d{1,2}) ?,? ?(?P<year>\d{4})")
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
CAVEAT_DAILY = "COGAT's own count of trucks it says entered Gaza that day; it covers all goods, including commercial."
CAVEAT_SINCE = "COGAT's own running total since the war began; all goods, including commercial."


def text(answer_html: str) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", " ", answer_html)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def update_date(question: str) -> dt.date | None:
    m = DATE.search(question)
    if not m or m.group("month")[:3].lower() not in MONTHS:
        return None
    return dt.date(int(m.group("year")), MONTHS[m.group("month")[:3].lower()], int(m.group("day")))


def daily(t: str) -> re.Match | None:
    # Bullets run together once tags are stripped; split at sentence ends and at "Heading:" starts.
    for part in re.split(r"(?<=[.;])\s+|\s(?=[A-Z][A-Za-z ]{2,30}:\s)", t):
        for p in DAILY:
            m = p.search(part)
            # Judge only the claim and what leads into it: a later clause may be about distribution or fuel.
            if m and not OTHER_COUNTS.search(part[max(0, m.start() - 40):m.end()]):
                return m
    return None


def _num(s: str) -> int:
    return int(s.replace(",", ""))


def parse(items: list[dict], doc_meta: dict) -> tuple[list[dict], list[str]]:
    """Observations from the archive's items, and notes on updates that could not be dated."""
    out, notes, seen = [], [], set()
    for it in items:
        day = update_date(it.get("question", ""))
        t = text(it.get("answer", ""))
        if day is None:
            notes.append(f"COGAT update without a readable date: {it.get('question')!r}")
            continue
        m = daily(t)
        if m:
            as_of = (day - dt.timedelta(days=1)).isoformat()
            oid = make_id("cogat", "aid.trucks.entered_daily", as_of)
            value = _num(m.group("n"))
            if oid not in seen and not verify_figure(value, m.group(0), t):
                seen.add(oid)
                out.append(_obs(oid, "aid.trucks.entered_daily", value, "exact", as_of, as_of, m.group(0), CAVEAT_DAILY,
                                doc_meta, it["question"]))
        s = SINCE_WAR.search(t)
        if s:
            as_of = day.isoformat()
            oid = make_id("cogat", "aid.trucks.entered", as_of)
            value = _num(s.group("n") or s.group("n2"))
            if oid not in seen and not verify_figure(value, s.group(0), t):
                seen.add(oid)
                out.append(_obs(oid, "aid.trucks.entered", value, "at_least", "2023-10-07", as_of, s.group(0), CAVEAT_SINCE,
                                doc_meta, it["question"]))
    return out, notes


def _obs(oid, metric, value, bound, start, as_of, quote, caveat, doc_meta, question) -> dict:
    return {
        "id": oid,
        "metric": metric,
        "value": value,
        "kind": "count",
        "bound": bound,
        "source": "cogat",
        "as_of": as_of,
        "period_start": start,
        "period_end": as_of,
        "document": {**doc_meta, "note": f"COGAT's update headed \"{question.strip()}\", in the archive of daily updates."},
        "quote": quote,
        "caveat": caveat,
        "added_by": "importer:cogat-updates",
    }


def fetch_archive() -> Document:
    resp = requests.post(API, json=REQUEST, timeout=60, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    resp.raise_for_status()
    content = resp.content
    return Document(url=PAGE, content=content, content_type="application/json", sha256=hashlib.sha256(content).hexdigest(),
                    retrieved_at=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat())


def run(entry: dict, metrics: list[dict], state: dict) -> Proposal:
    prop = Proposal()
    try:
        doc = fetch_archive()
    except Exception as e:  # noqa: BLE001 - report and carry on with other sources
        prop.rejected.append(Rejected(API, "could not download", str(e)))
        return prop
    prop.seen[PAGE] = doc.sha256
    if state.get(PAGE) == doc.sha256:
        return prop
    items = json.loads(doc.content).get("fqaItems", [])
    if not items:
        prop.rejected.append(Rejected(API, "no updates found", "The archive request may have changed; see ingest/sources/cogat_updates.py."))
        return prop
    keep(doc)
    found, notes = parse(items, doc.meta(PUBLISHER))
    prop.observations += found
    prop.notes += notes
    prop.notes.append(f"COGAT updates: {len(items)} read, {len(found)} figures found.")
    return prop
