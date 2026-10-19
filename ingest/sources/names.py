"""The Gaza Ministry of Health's list of people killed, identified by name, as republished by Tech for Palestine.

This is a list of people, not figures, so it is stored apart from observations, in data/lists/named-victims.json.
Kept: the Arabic name from the Ministry, Tech for Palestine's English translation, age, sex, and which
Ministry list release added the record. Left out on purpose: national ID numbers and dates of birth,
which the site does not need and which put the victims' families at risk of identity misuse.

The list has no cause or date of death.
"""
from __future__ import annotations

import json

from ..archive import fetch, keep
from ..paths import DATA

URL = "https://data.techforpalestine.org/api/v3/killed-in-gaza.min.json"
SUMMARY_URL = "https://data.techforpalestine.org/api/v3/summary.json"
PUBLISHER = "Tech for Palestine"
LIST_FILE = DATA / "lists" / "named-victims.json"
FIELDS = ["en_name", "ar_name", "age", "sex", "update"]


def parse(rows: list[list], summary: dict) -> tuple[list[list], list[str]]:
    """Records in FIELDS order, and problems that should stop the update."""
    header, body = rows[0], rows[1:]
    missing = [f for f in FIELDS if f not in header]
    if missing:
        return [], [f"the list no longer has the field(s) {', '.join(missing)}"]
    idx = [header.index(f) for f in FIELDS]
    records = [[row[i] for i in idx] for row in body]
    problems = []
    expected = (summary.get("known_killed_in_gaza") or {}).get("records")
    if isinstance(expected, int) and expected != len(records):
        problems.append(f"the list has {len(records):,} records but summary.json says {expected:,}; they may be mid-update")
    for n, (en, ar, age, sex, _) in enumerate(records):
        if not (en or ar) or not isinstance(age, int) or sex not in ("m", "f"):
            problems.append(f"record {n + 1} is incomplete: {[en, ar, age, sex]}")
            if len(problems) > 5:
                break
    return records, problems


def run(state: dict, dry_run: bool) -> tuple[list[str], dict[str, str]]:
    """Update data/lists/named-victims.json if the published list changed. Returns report lines and state updates."""
    doc = fetch(URL)
    if state.get(URL) == doc.sha256 and LIST_FILE.exists():
        return ["Named victims list unchanged since the last run."], {}
    summary_doc = fetch(SUMMARY_URL)
    summary = json.loads(summary_doc.content)
    records, problems = parse(json.loads(doc.content), summary)
    if problems:
        return ["Named victims list not updated:"] + [f"- {p}" for p in problems], {}
    names = summary.get("known_killed_in_gaza") or {}
    previous = json.loads(LIST_FILE.read_text())["records"] if LIST_FILE.exists() else []
    lines = [f"Named victims list: {len(records):,} records (was {len(previous):,}), covering deaths to {names.get('includes_until')}."]
    if dry_run:
        return lines + ["(dry run: nothing written)"], {}
    # The raw list is not copied into archive/: it holds ID numbers and dates of birth, and archive/ is published
    # with the repository. Its sha256 still pins exactly which version was read.
    keep(summary_doc)
    LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "source": "gaza-moh",
        "document": doc.meta(PUBLISHER),
        "includes_until": names.get("includes_until"),
        "list_updated": names.get("last_update"),
        "dates_from": summary_doc.meta(PUBLISHER),
        "note": "English names are Tech for Palestine's translations; the Arabic name is the Ministry's record. "
        "National ID numbers and dates of birth are left out on purpose. The list has no cause or date of death.",
        "fields": FIELDS,
    }
    # One record per line keeps git diffs readable when a new list release arrives.
    body = ",\n".join("    " + json.dumps(r, ensure_ascii=False) for r in records)
    head = json.dumps(meta, indent=2, ensure_ascii=False)[:-2]
    LIST_FILE.write_text(f'{head},\n  "records": [\n{body}\n  ]\n}}\n', encoding="utf-8")
    return lines, {URL: doc.sha256}
