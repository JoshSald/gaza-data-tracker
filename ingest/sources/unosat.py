"""UNOSAT comprehensive damage assessments of the Gaza Strip, from satellite images.

Each product's summary on unosat.org states counts of destroyed, severely, moderately and possibly damaged
structures and their share of all structures. The product pages are built in the browser, but their data comes
from https://unosat.org/our_products/<id> as JSON, which is what is archived. New products are found with the
site's own search.
"""
from __future__ import annotations

import calendar
import datetime as dt
import json
import re

import requests

from ..archive import USER_AGENT, fetch, keep
from .base import Proposal, Rejected, make_id

PUBLISHER = "UNOSAT"
MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
COUNTS = re.compile(
    r"UNOSAT identified (?P<destroyed>[\d,]+) destroyed structures, (?P<severe>[\d,]+) severely damaged structures,? "
    r"(?:and )?(?P<moderate>[\d,]+) moderately damaged structures,? (?:and (?P<possible>[\d,]+) possibly damaged structures,? )?"
    r"for a total of (?P<total>[\d,]+) (?:affected )?structures\.")
SHARE = re.compile(r"(?:around|approximately) (\d+) ?% of (?:the total|all) structures in the Gaza Strip")
IMAGE_DATE = re.compile(r"based on (?:an )?images? collected on (?:(?:\d{1,2})(?:-| and )(?=\d))?(\d{1,2}) ([A-Za-z]+) (\d{4})")
METRICS = [("destroyed", "infra.structures.destroyed"), ("severe", "infra.structures.severely_damaged"),
           ("moderate", "infra.structures.moderately_damaged"), ("possible", "infra.structures.possibly_damaged"),
           ("total", "infra.structures.affected")]


def _n(s: str) -> int:
    return int(s.replace(",", ""))


def parse(product: dict, meta: dict) -> list[dict]:
    desc = re.sub(r"\s+", " ", product.get("description", ""))
    m, d = COUNTS.search(desc), IMAGE_DATE.search(desc)
    if not m or not d or d.group(2).lower() not in MONTHS:
        return []
    as_of = dt.date(int(d.group(3)), MONTHS[d.group(2).lower()], int(d.group(1))).isoformat()
    caveat = ("Satellite images compared with images from before the war; UNOSAT marks this a preliminary analysis "
              "not validated on the ground.")
    if not m.group("possible"):
        caveat += " Before May 2024 UNOSAT did not count 'possibly damaged' structures, so totals are lower than later ones on the same basis."
    if "area of interest" in desc and as_of < "2024-01-01":
        caveat += " Early assessments may not cover the whole Strip."
    out = []
    for group, metric in METRICS:
        if m.group(group):
            out.append(_obs(metric, _n(m.group(group)), as_of, m.group(0), meta, caveat, "exact"))
    s = SHARE.search(desc)
    if s:
        out.append(_obs("infra.structures.affected_share", int(s.group(1)), as_of, s.group(0), meta, caveat, "approximate"))
    return out


def _obs(metric, value, as_of, quote, meta, caveat, bound) -> dict:
    return {
        "id": make_id("unosat", metric, as_of),
        "metric": metric,
        "value": value,
        "kind": "count",
        "bound": bound,
        "source": "unosat",
        "as_of": as_of,
        "period_start": "2023-10-07",
        "period_end": as_of,
        "document": meta,
        "quote": quote,
        "caveat": caveat,
        "added_by": "importer:unosat",
    }


def product_ids(entry: dict) -> list[int]:
    ids = set(entry.get("product_ids", []))
    for term in entry.get("search", []):
        r = requests.post("https://unosat.org/searchServer/", json={"search_term": term}, timeout=60, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        for p in r.json().get("products", []):
            if re.search(entry["title_pattern"], p.get("title", "")):
                ids.add(p["id"])
    return sorted(ids)


def run(entry: dict, metrics: list[dict], state: dict) -> Proposal:
    prop = Proposal()
    for pid in product_ids(entry):
        url = f"https://unosat.org/our_products/{pid}"
        try:
            doc = fetch(url)
            product = json.loads(doc.content)["map_event"]
        except Exception as e:  # noqa: BLE001
            prop.rejected.append(Rejected(url, "could not download", str(e)))
            continue
        prop.seen[url] = doc.sha256
        if state.get(url) == doc.sha256:
            continue
        if pid not in entry.get("product_ids", []) and not re.search(entry["title_pattern"], product.get("title", "")):
            continue
        keep(doc)
        meta = {**doc.meta(PUBLISHER), "note": f"Product page: https://unosat.org/products/{pid}"}
        found = parse(product, meta)
        if not found:
            prop.rejected.append(Rejected(url, "no figures found", f"{product.get('title')}: the summary's wording may have changed."))
        prop.observations += found
    return prop
