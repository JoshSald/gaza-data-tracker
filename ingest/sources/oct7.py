"""People killed in the 7 October 2023 attack on Israel, from oct7database.

oct7database is a volunteer-run database of people killed and abducted since 7 October 2023. It links each
person to their official memorial record (National Insurance Institute, IDF, Israel Police, Shin Bet, Ministry of
Defence) and publishes its data as a CSV. It is a secondary source: the site labels the list as a volunteer
compilation checked against those official lists, the way the Gaza list is labelled as republished by Tech for
Palestine.

Kept: English and Hebrew names as oct7database spells them, age, sex, role (civilian, soldier, police...), date of
death (as stated: a full date, or only the month or year when the exact date is not known), whether the person was killed in
captivity, and the link to the official memorial record. Left out: home
town, place of death, party attended, library catalogue numbers.

Scope: people whose event date is 7 October 2023 on the Gaza front and who were killed, that day or later in
captivity. Hostages who were released or rescued are not included.

Run once with `python -m ingest oct7`; it is not part of the scheduled import.
"""
from __future__ import annotations

import csv
import io
import json

from ..archive import fetch
from ..paths import DATA

URL = "https://raw.githubusercontent.com/yuval-harpaz/alarms/refs/heads/master/data/oct7database.csv"
SITE = "https://www.oct7database.com/"
LIST_FILE = DATA / "lists" / "oct7-victims.json"
FIELDS = ["en_name", "he_name", "age", "sex", "role", "died", "in_captivity", "memorial"]

# The Role column, in Hebrew, as oct7database writes it.
ROLES = {
    "אזרח": "civilian",
    "חייל": "soldier",
    "שוטר": "police officer",
    "כיתת כוננות": "local security squad",
    "צוות רפואי": "medical staff",
    'שב"כ': "Shin Bet",
    "כבאי": "firefighter",
}


def _join(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip())


def parse(content: bytes) -> tuple[list[list], list[str]]:
    """Records in FIELDS order, and problems that should stop the update."""
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    needed = ["first name", "last name", "שם פרטי", "שם משפחה", "Gender", "Age", "Role", "Status", "Event date",
              "Death date", "front", "הנצחה"]
    missing = [c for c in needed if rows and c not in rows[0]]
    if missing:
        return [], [f"the CSV no longer has the column(s) {', '.join(missing)}"]
    records, problems = [], []
    for r in rows:
        if r["Event date"] != "2023-10-07" or r["front"] != "Gaza" or "killed" not in r["Status"]:
            continue
        role = ROLES.get(r["Role"].strip())
        if role is None:
            problems.append(f"unknown role {r['Role']!r} for {r['first name']} {r['last name']}")
            continue
        age = int(r["Age"]) if r["Age"].strip().isdigit() else None
        records.append([
            _join(r["first name"], r.get("middle name", ""), r["last name"]),
            _join(r["שם פרטי"], r.get("שם נוסף", ""), r["שם משפחה"]),
            age,
            {"M": "m", "F": "f"}.get(r["Gender"].strip()),
            role,
            r["Death date"] or None,
            # Abducted first and killed afterwards ("kidnapped; killed; ..."), as opposed to killed and then taken.
            r["Status"].startswith("kidnapped") and r["Death date"] != "2023-10-07",
            r["הנצחה"] if r["הנצחה"].startswith("https://") else None,
        ])
    records.sort(key=lambda x: (x[0].split(" ")[-1].lower(), x[0].lower()))
    return records, problems


def run(dry_run: bool) -> list[str]:
    doc = fetch(URL)
    records, problems = parse(doc.content)
    if problems:
        return ["7 October list not updated:"] + [f"- {p}" for p in problems[:10]]
    captivity = sum(1 for r in records if r[6])
    linked = sum(1 for r in records if r[7])
    lines = [f"7 October list: {len(records):,} people ({captivity} killed in captivity); {linked:,} link to an official memorial record."]
    if dry_run:
        return lines + ["(dry run: nothing written)"]
    meta = {
        "source_note": ("Compiled by oct7database, a volunteer-run database that links each person to their official "
                        "memorial record (National Insurance Institute, IDF, Israel Police, Shin Bet, Ministry of Defence)."),
        "document": {**doc.meta("oct7database"), "page": SITE},
        "scope": ("People killed in the 7 October 2023 attack on Israel from Gaza: those killed that day and those "
                  "abducted that day and killed in captivity. Released or rescued hostages are not included."),
        "note": ("English and Hebrew names are as oct7database spells them; English spellings are not official. "
                 "The raw file is not copied into archive/; its sha256 pins the version read."),
        "fields": FIELDS,
    }
    body = ",\n".join("    " + json.dumps(r, ensure_ascii=False) for r in records)
    head = json.dumps(meta, indent=2, ensure_ascii=False)[:-2]
    LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    LIST_FILE.write_text(f'{head},\n  "records": [\n{body}\n  ]\n}}\n', encoding="utf-8")
    return lines
