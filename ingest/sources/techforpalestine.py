"""Tech for Palestine API: Gaza Ministry of Health figures as structured JSON.

Two endpoints:
- summary.json: the age/sex breakdown of named victims (known_killed_in_gaza).
- casualties_daily.json: every daily report since 7 October 2023.

Tech for Palestine fills days without a report by carrying the last value forward ("ext_" fields, and
the totals in summary.json). Only values the Ministry stated on that day are imported, dated that day.
"""
from __future__ import annotations

import json

from ..archive import fetch, keep
from .base import Proposal, make_id

URL = "https://data.techforpalestine.org/api/v3/summary.json"
DAILY_URL = "https://data.techforpalestine.org/api/v2/casualties_daily.json"
INFRA_URL = "https://data.techforpalestine.org/api/v3/infrastructure-damaged.json"
PUBLISHER = "Tech for Palestine"
START = "2023-10-07"

# metric id -> field in casualties_daily.json. Never the "ext_" variants, which are filled in by Tech for Palestine.
DAILY_FIELDS = {
    "gaza.killed.total": "killed_cum",
    "gaza.injured.total": "injured_cum",
    "gaza.killed.children": "killed_children_cum",
    "gaza.killed.women": "killed_women_cum",
    "gaza.killed.medical": "med_killed_cum",
    "gaza.killed.press": "press_killed_cum",
    "gaza.killed.civil_defence": "civdef_killed_cum",
    "gaza.deaths.malnutrition": "famine_cum",
    "gaza.killed.seeking_aid": "aid_seeker_killed_cum",
}
# report_source values that are the Ministry's own channel. Others ("gmotel" = Government Media Office,
# "missing" = unknown) are skipped: they are a different body, or one we cannot name.
MOH_CHANNELS = {"mohtel"}


def _get(obj: dict, path: tuple):
    for key in path:
        if not isinstance(obj, dict) or key not in obj:
            return None
        obj = obj[key]
    return obj


def parse(summary: dict, doc_meta: dict) -> list[dict]:
    """Named victims by age and sex. The daily totals in summary.json are carried forward, so they come from parse_daily."""
    out = []
    names = summary.get("known_killed_in_gaza", {})
    until = names.get("includes_until")
    if until:
        for sex in ("male", "female"):
            for age in ("child", "adult", "senior"):
                value = _get(names, (sex, age))
                if not isinstance(value, (int, float)):
                    continue
                dims = {"age_group": age, "sex": sex}
                out.append({
                    "id": make_id("gaza-moh", "gaza.named_victims", until, None, dims),
                    "metric": "gaza.named_victims",
                    "value": value,
                    "kind": "count",
                    "bound": "exact",
                    "source": "gaza-moh",
                    "as_of": until,
                    "period_start": START,
                    "period_end": until,
                    "dimensions": dims,
                    "document": {**doc_meta, "note": f"List revision of {names.get('last_update')}, covering deaths to {until}"},
                    "quote": f"known_killed_in_gaza.{sex}.{age} = {value} (includes_until {until})",
                    "added_by": "importer:techforpalestine",
                })
    return out


def parse_daily(rows: list[dict], doc_meta: dict) -> tuple[list[dict], dict[str, int]]:
    """One observation per field the Ministry reported on each day. Returns the observations and counts of skipped reports."""
    out, skipped = [], {}
    for row in rows:
        date, channel = row.get("report_date"), row.get("report_source")
        if not date:
            continue
        if channel not in MOH_CHANNELS:
            skipped[channel] = skipped.get(channel, 0) + 1
            continue
        for metric, key in DAILY_FIELDS.items():
            value = row.get(key)
            if not isinstance(value, (int, float)):
                continue
            out.append({
                "id": make_id("gaza-moh", metric, date),
                "metric": metric,
                "value": value,
                "kind": "count",
                "bound": "exact",
                "source": "gaza-moh",
                "as_of": date,
                "period_start": START,
                "period_end": date,
                "document": doc_meta,
                "quote": f"{key} = {value} (report_date {date}, report_source {channel})",
                "added_by": "importer:techforpalestine",
            })
    return out, skipped


def run_daily(entry: dict, metrics: list[dict], state: dict) -> Proposal:
    prop = Proposal()
    url = entry.get("url", DAILY_URL)
    doc = fetch(url)
    prop.seen[url] = doc.sha256
    if state.get(url) == doc.sha256:
        prop.notes.append("Tech for Palestine daily casualties unchanged since the last run.")
        return prop
    keep(doc)
    prop.observations, skipped = parse_daily(json.loads(doc.content), doc.meta(PUBLISHER))
    for channel, n in sorted(skipped.items()):
        prop.notes.append(f"{entry['id']}: skipped {n} daily report(s) with report_source {channel!r} (not the Ministry's own channel).")
    return prop


def run(entry: dict, metrics: list[dict], state: dict) -> Proposal:
    prop = Proposal()
    url = entry.get("url", URL)
    doc = fetch(url)
    prop.seen[url] = doc.sha256
    if state.get(url) == doc.sha256:
        prop.notes.append("Tech for Palestine summary unchanged since the last run.")
        return prop
    keep(doc)
    prop.observations = parse(json.loads(doc.content), doc.meta(PUBLISHER))
    return prop


# metric id -> path in infrastructure-damaged.json. These are the Gaza Government Media Office's figures; the
# "ext_" variants are Tech for Palestine's carried-forward values and are never used.
INFRA_FIELDS = {
    "infra.housing_units.destroyed": ("residential", "destroyed"),
    "infra.schools.destroyed": ("educational_buildings", "destroyed"),
    "infra.schools.damaged": ("educational_buildings", "damaged"),
    "infra.mosques.destroyed": ("places_of_worship", "mosques_destroyed"),
    "infra.mosques.damaged": ("places_of_worship", "mosques_damaged"),
    "infra.churches.destroyed": ("places_of_worship", "churches_destroyed"),
    "infra.government_buildings.destroyed": ("civic_buildings", "destroyed"),
}
GMO_CAVEAT = ("Stated by the Gaza Government Media Office, which does not publish a method; Tech for Palestine, which "
              "republishes the figures, advises treating them as estimates.")


def parse_infrastructure(rows: list[dict], doc_meta: dict) -> list[dict]:
    out = []
    for row in rows:
        date = row.get("report_date")
        for metric, path in INFRA_FIELDS.items():
            value = _get(row, path)
            if not date or not isinstance(value, (int, float)):
                continue
            out.append({
                "id": make_id("gaza-gmo", metric, date),
                "metric": metric,
                "value": value,
                "kind": "claim",
                "bound": "exact",
                "source": "gaza-gmo",
                "as_of": date,
                "period_start": START,
                "period_end": date,
                "document": doc_meta,
                "quote": f"{'.'.join(path)} = {value} (report_date {date})",
                "caveat": GMO_CAVEAT,
                "added_by": "importer:techforpalestine",
            })
    return out


def run_infrastructure(entry: dict, metrics: list[dict], state: dict) -> Proposal:
    prop = Proposal()
    url = entry.get("url", INFRA_URL)
    doc = fetch(url)
    prop.seen[url] = doc.sha256
    if state.get(url) == doc.sha256:
        prop.notes.append("Tech for Palestine infrastructure data unchanged since the last run.")
        return prop
    keep(doc)
    prop.observations = parse_infrastructure(json.loads(doc.content), doc.meta(PUBLISHER))
    return prop
