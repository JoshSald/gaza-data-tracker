"""List sentences in archived WHO situation reports that name a hospital together with a status word.

    python scripts/hospital_mentions.py [--hospital NAME] [--since YYYY-MM-DD]

This only finds candidates. A person (or agent) reads each one and records the hospital's status with
ingest.sources.hospitals.add_status only when WHO states it for that hospital; see the statuses in that module.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import store  # noqa: E402
from ingest.sources.who_health import sitrep_date  # noqa: E402
from ingest.text import pdf_text  # noqa: E402

# Spellings WHO uses for each hospital in data/lists/hospitals.json.
ALIASES = {
 "Yaffa Hospital": [
  "Yaffa",
  "Yafa"
 ],
 "Psychiatric hospital": [
  "Psychiatric Hospital",
  "psychiatric hospital"
 ],
 "Ophthalmic hospital": [
  "MOH Ophthalmic",
  "MoH Ophthalmic",
  "Ophthalmic Hospital"
 ],
 "Turkish Friendship Hospital": [
  "Turkish"
 ],
 "Mohamed Al Durrah Hospital": [
  "Durra",
  "Durrah"
 ],
 "Al Wafaa Rehabilitation Hospital": [
  "Wafa"
 ],
 "Patient Friends Association Hospital": [
  "Patient Friends",
  "Patients Friends",
  "Patients' Friends",
  "Patient's Friends"
 ],
 "Sheikh Hamad Hospital for Rehabilitation and Prosthetics": [
  "Sheikh Hamad",
  "Hamad Hospital"
 ],
 "Public Aid - Cardiovascular Hospital": [
  "Public Aid",
  "Cardiovascular"
 ],
 "Haifa Charity Hospital": [
  "Haifa"
 ],
 "St. John's Eye Hospital": [
  "St. John",
  "St John",
  "Saint John"
 ],
 "International Ophthalmic Hospital": [
  "International Ophthalmic",
  "International Eye"
 ],
 "Al Hayat Specialized Hospital": [
  "Al Hayat",
  "Al-Hayat"
 ],
 "Al-Khair Hospital": [
  "Al-Khair",
  "Al Khair"
 ],
 "Dar Essalam Hospital": [
  "Dar Essalam",
  "Dar Al Salam",
  "Dar Al-Salam",
  "Dar El Salam",
  "Dar As-Salam"
 ],
 "Al Awda Hospital - North": [
  "Al Awda Hospital - North",
  "Al-Awda Hospital in Jabalia",
  "Al Awda Hospital in Jabalia",
  "Al-Awda Jabalia",
  "Al Awda (Jabalia)",
  "Al-Awda Hospital - North",
  "Al-Awda hospital in north Gaza",
  "Al-Awda Hospital in North Gaza"
 ],
 "Beit Hanoun Hospital": [
  "Beit Hanoun Hospital",
  "Beit Hanoun and Kuwait"
 ],
 "Al Karama Specialized Hospital": [
  "Karama"
 ],
 "Al Aqsa Hospital": [
  "Al Aqsa",
  "Al-Aqsa"
 ],
 "Al Awda Hospital - Nuseirat": [
  "Al-Awda Hospital in Nuseirat",
  "Al Awda Hospital in Nuseirat",
  "Al-Awda Nuseirat",
  "Al Awda Nuseirat",
  "Al-Awda hospital (Nuseirat)",
  "Al-Awda Nusseirat",
  "Awda Nusseirat"
 ],
 "Al Shifa Medical Hospital": [
  "Shifa"
 ],
 "Al-Ranteesi Al-Naser Paediatric Hospital": [
  "Al-Nasr",
  "Al Nasr",
  "Al-Naser",
  "Al Naser",
  "Nasr Pediatric",
  "Nasser Pediatric",
  "Nasser Paediatric"
 ],
 "Al-Rantisi Specialized Hospital": [
  "Rantisi",
  "Rantissi",
  "Ranteesi"
 ],
 "Al-Quds Hospital": [
  "Al-Quds Hospital",
  "Al Quds Hospital",
  "Al-Quds hospital"
 ],
 "Al Ahli Arab Hospital": [
  "Ahli"
 ],
 "Assahaba Medical Complex": [
  "Sahaba"
 ],
 "Al Helou International Hospital": [
  "Helou"
 ],
 "Nasser Hospital": [
  "Nasser Medical Complex",
  "Nasser Hospital",
  "Nasser hospital",
  "Nasser Complex"
 ],
 "European Hospital": [
  "European Hospital",
  "European Gaza Hospital",
  "European hospital",
  "Gaza European"
 ],
 "Algerian Hospital": [
  "Algerian"
 ],
 "Al-Amal Hospital": [
  "Al-Amal",
  "Al Amal"
 ],
 "Indonesian Hospital": [
  "Indonesian"
 ],
 "Kamal Adwan Hospital": [
  "Kamal Adwan"
 ],
 "AL Najjar Hospital": [
  "Najjar"
 ],
 "Al-Helal Al-Emarati Hospital": [
  "Emirati",
  "Al-Helal",
  "Helal"
 ],
 "Kuwait Hospital": [
  "Kuwait Hospital",
  "Kuwaiti Hospital",
  "Kuwait Specialized",
  "Kuwaiti Specialized",
  "Kuwait Specialized Hospitals"
 ]
}

STATUS = re.compile(r"partially function|partly function|minimally function|non-?functional|non-operational|not functioning|"
                    r"out of service|resumed|reopened|destroyed|evacuated|operational", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hospital", help="only this hospital (name as in hospitals.json)")
    ap.add_argument("--since", default="2023-10-07")
    args = ap.parse_args()
    docs = {}
    for o in store.load_observations():
        d = o["document"]
        if o["source"] == "who" and "Situation Update" in d.get("publisher", "") and d.get("archive"):
            docs.setdefault(d["url"], d["archive"])
    found = []
    for url, path in docs.items():
        p = Path(path)
        text = pdf_text(p.read_bytes()) if p.suffix == ".pdf" else p.read_text()
        date = sitrep_date(text)[0]
        if not date or date < args.since:
            continue
        t = re.sub(r"\s+", " ", text)
        for sentence in re.split(r"(?<=[.;])\s+|\s[•◦▪]\s", t):
            if len(sentence) > 600 or not STATUS.search(sentence):
                continue
            for name, spellings in ALIASES.items():
                if (not args.hospital or name == args.hospital) and any(s in sentence for s in spellings):
                    found.append((name, date, sentence.strip(), url))
    for name, date, sentence, url in sorted(set(found), key=lambda f: (f[0], f[1]), reverse=True):
        print(f"{name} | {date} | {sentence} | {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
