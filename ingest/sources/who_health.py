"""WHO figures on Gaza's hospitals and attacks on health care.

Two WHO publications, read as PDFs:
- oPt Emergency Situation Updates ("sitreps", Oct 2023 to Oct 2025): hospitals partially functioning out of 36,
  and from 2024 the attack figures of WHO's Surveillance System for Attacks on Health Care (SSA). WHO keeps only the
  latest issue on its own site; earlier issues are found on UNISPAL, the UN's Question of Palestine site.
- HeRAMS Gaza infographics (monthly, from Nov 2024): status of the hospitals WHO evaluates (35), including
  non-functioning and destroyed. Kept as their own series (dimension monitoring=herams), because the count of
  hospitals differs from the sitreps.

The wording changed several times, so each pattern below matches one layout. A document none of them match is
reported as "no figures found" rather than guessed at.
"""
from __future__ import annotations

import calendar
import datetime as dt
import re
from urllib.parse import urljoin

import requests
from requests.utils import requote_uri

from ..archive import USER_AGENT, fetch, keep
from ..text import pdf_text
from .base import Proposal, Rejected, discover, make_id

PUBLISHER_SITREP = "World Health Organization (oPt Emergency Situation Update)"
PUBLISHER_HERAMS = "World Health Organization (HeRAMS)"
WAR_START = dt.date(2023, 10, 7)
MONTHS = {m.lower()[:3]: i for i, m in enumerate(calendar.month_name) if m}
WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
    "eighteen nineteen twenty".split())}


def _date(s: str) -> dt.date | None:
    m = re.match(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s.strip())
    if not m or m.group(2).lower()[:3] not in MONTHS:
        return None
    try:
        return dt.date(int(m.group(3)), MONTHS[m.group(2).lower()[:3]], int(m.group(1)))
    except ValueError:
        return None


def _num(s: str) -> int:
    s = s.strip().lower()
    return WORDS[s] if s in WORDS else int(s.replace(",", ""))


# --- Situation reports -------------------------------------------------------------------------------------------

# "18/ 36 (50%) ... Hospitals partially functional (HPF)" (issues 32 to 66; the dashboard puts other text between)
PARTIAL_DASHBOARD = re.compile(r"(\d{1,2})\s*/\s*36\s*\(\d+%\)(?:(?!\d+\s*/\s*36).){0,160}?Hospitals partially function(?:al|ing)", re.I)
# "Only 14 of 36 (39%) hospitals in the Gaza strip are partially functioning" (issues 16 to 21)
PARTIAL_ONLY = re.compile(r"Only (\d{1,2}) of 36 \(\d+%\) hospitals in the Gaza strip are partially functioning", re.I)
# "Fifteen out of 36 hospitals are currently partially functional" (issue 31)
PARTIAL_WORDS = re.compile(r"\b([A-Za-z]+|\d{1,2}) out of 36 hospitals are (?:currently )?partially functional", re.I)
# "50% (18/36) of hospitals and two outpatient specialist centres are not functioning" (issues 9 to 12)
NOT_FUNCTIONING = re.compile(r"\d+% \((\d{1,2})/(3[56])\) of hospitals(?: [^.]{0,140}?)? not functioning", re.I)
# Attack figures from WHO's Surveillance System for Attacks on Health Care
SSA_ATTACKS = re.compile(r"(\d[\d,]*) Health Attacks As of (\d{1,2} [A-Za-z]+ \d{4}) Source: SSA", re.I)
SSA_KILLED = re.compile(r"(\d[\d,]*) People killed in attacks", re.I)
SSA_HOSPITALS = re.compile(r"Including (\d[\d,]*) Hospitals damaged", re.I)
HEADER = re.compile(r"Issue\s*(\d+)\s*7 Oct 2023\s*[-–]\s*(\d{1,2} [A-Za-z]+ \d{4})")
AS_OF = re.compile(r"[Aa]s of (\d{1,2} [A-Za-z]+ \d{4})")


def _obs(metric: str, value: int, as_of: str, quote: str, meta: dict, caveat: str, dims: dict | None = None) -> dict:
    return {
        "id": make_id("who", metric, as_of, None, dims),
        "metric": metric,
        "value": value,
        "kind": "count",
        "bound": "exact",
        "source": "who",
        "as_of": as_of,
        "period_start": None,
        "period_end": as_of,
        **({"dimensions": dims} if dims else {}),
        "document": meta,
        "quote": quote.strip(),
        "caveat": caveat,
        "added_by": "importer:who",
    }


def sitrep_date(text: str) -> tuple[str | None, str | None]:
    """The report's 'as of' date, or (None, reason)."""
    t = re.sub(r"\s+", " ", text)
    h = HEADER.search(t)
    d = _date(h.group(2)) if h else None
    if d is None:
        a = AS_OF.search(t)
        d = _date(a.group(1)) if a else None
    if d is None:
        return None, "no report date found"
    if d < WAR_START:
        return None, f"the report's date reads {d.isoformat()}, before the war began, so it is probably a typo"
    return d.isoformat(), None


def parse_sitrep(text: str, meta: dict) -> list[dict]:
    t = re.sub(r"\s+", " ", text)
    as_of, _ = sitrep_date(text)
    if not as_of:
        return []
    issue = HEADER.search(t) or re.search(r"Issue\s*(\d+)", t)
    label = f"WHO situation report issue {issue.group(1)}." if issue else "WHO situation report."
    out = []
    for pattern in (PARTIAL_DASHBOARD, PARTIAL_ONLY, PARTIAL_WORDS):
        m = pattern.search(t)
        if m and (m.group(1).isdigit() or m.group(1).lower() in WORDS):
            out.append(_obs("health.hospitals.partially_functional", _num(m.group(1)), as_of, m.group(0), meta,
                            f"Out of 36 hospitals. {label}"))
            break
    n = NOT_FUNCTIONING.search(t)
    if n:
        out.append(_obs("health.hospitals.not_functioning", int(n.group(1)), as_of, n.group(0), meta,
                        f"Out of {n.group(2)} hospitals. {label}"))
    a = SSA_ATTACKS.search(t)
    if a and _date(a.group(2)):
        ssa_as_of = _date(a.group(2)).isoformat()
        ssa = "Recorded by WHO's Surveillance System for Attacks on Health Care since 7 October 2023. " + label
        out.append(_obs("health.attacks.total", _num(a.group(1)), ssa_as_of, a.group(0), meta, ssa))
        k = SSA_KILLED.search(t)
        if k:
            out.append(_obs("health.attacks.killed", _num(k.group(1)), ssa_as_of, k.group(0), meta, ssa))
        h = SSA_HOSPITALS.search(t)
        if h:
            out.append(_obs("health.hospitals.damaged", _num(h.group(1)), ssa_as_of, h.group(0), meta, ssa))
    for o in out:
        if o["metric"].startswith("health.attacks") or o["metric"] == "health.hospitals.damaged":
            o["period_start"] = WAR_START.isoformat()
            o["id"] = make_id("who", o["metric"], o["as_of"], o["period_start"])
    return out


def unispal_sitreps(query: dict) -> list[str]:
    """WHO situation reports that UNISPAL (un.org/unispal) hosts, found through its WordPress media API."""
    urls: list[str] = []
    for term in query.get("search", ["sitrep"]):
        resp = requests.get(
            "https://www.un.org/unispal/wp-json/wp/v2/media",
            params={"search": term, "per_page": 100, "mime_type": "application/pdf"},
            headers={"User-Agent": USER_AGENT}, timeout=60,
        )
        resp.raise_for_status()
        for item in resp.json():
            u = item.get("source_url", "")
            if re.search(query["filename_pattern"], u.rsplit("/", 1)[-1]):
                urls.append(u)
    return sorted(set(urls))


def run_sitreps(entry: dict, metrics: list[dict], state: dict) -> Proposal:
    prop = Proposal()
    urls = discover(entry) + (unispal_sitreps(entry["unispal"]) if entry.get("unispal") else [])
    for url in dict.fromkeys(urls):
        try:
            doc = fetch(url)
        except Exception as e:  # noqa: BLE001 - report and move on to the next document
            prop.rejected.append(Rejected(url, "could not download", str(e)))
            continue
        prop.seen[url] = doc.sha256
        if state.get(url) == doc.sha256:
            continue
        if not doc.content.startswith(b"%PDF"):
            prop.rejected.append(Rejected(url, "not a PDF", "The address may have moved."))
            continue
        text = pdf_text(doc.content)
        keep(doc, text)
        found = parse_sitrep(text, doc.meta(PUBLISHER_SITREP))
        if not found:
            _, why = sitrep_date(text)
            prop.rejected.append(Rejected(url, why or "no figures found", "Update the patterns in ingest/sources/who_health.py if the layout changed."))
        prop.observations += found
    return prop


# --- HeRAMS monthly infographics ---------------------------------------------------------------------------------

HERAMS_SECTION = re.compile(r"All hospitals\* \(excluding field hospitals\) HOSPITAL STATUS")
HERAMS_PARTIAL = re.compile(r"(?:Only )?(\d+) \(\d+%\) out of (\d+) hospitals evaluated are (?:at least )?partially functioning\.?", re.I)
HERAMS_NON = re.compile(r"(\d+) Non-Functioning")
HERAMS_FULL = re.compile(r"(\d+) Functioning (?=\d+ Partially Functioning)")
HERAMS_DESTROYED = re.compile(r"Non-Functioning Functionality (\d+) Destroyed")
HERAMS_DATE = re.compile(r"Date data: (\d{1,2} [A-Za-z]+ \d{4})")


def parse_herams(text: str, meta: dict) -> list[dict]:
    t = re.sub(r"\s+", " ", text)
    d = HERAMS_DATE.search(t)
    s = HERAMS_SECTION.search(t)
    if not d or not s or not _date(d.group(1)):
        return []
    as_of = _date(d.group(1)).isoformat()
    section = t[s.start(): s.start() + 3500]
    dims = {"monitoring": "herams"}
    out = []
    p = HERAMS_PARTIAL.search(section)
    if not p:
        return []
    total = p.group(2)
    note = f"Out of {total} hospitals WHO evaluated, excluding field hospitals. HeRAMS monthly snapshot."
    out.append(_obs("health.hospitals.partially_functional", int(p.group(1)), as_of, p.group(0), meta, note, dims))
    out.append(_obs("health.hospitals.evaluated", int(total), as_of, p.group(0), meta, note, dims))
    f = HERAMS_FULL.search(section)
    if f:
        out.append(_obs("health.hospitals.fully_functional", int(f.group(1)), as_of, f.group(0), meta, note, dims))
    n = HERAMS_NON.search(section)
    if n:
        out.append(_obs("health.hospitals.not_functioning", int(n.group(1)), as_of, n.group(0), meta,
                        note + " Destroyed hospitals are counted separately.", dims))
    x = HERAMS_DESTROYED.search(section)
    if x:
        out.append(_obs("health.hospitals.destroyed", int(x.group(1)), as_of, x.group(0), meta, note, dims))
    return out


def herams_pages(entry: dict) -> list[str]:
    """Monthly publication pages on who.int: those linked from the index page, plus any month after the newest."""
    html = requests.get(entry["index_url"], timeout=60, headers={"User-Agent": USER_AGENT}).text
    slugs = set(re.findall(r"herams-opt-gaza-infographics-\d{4}-\d{2}(?:-en)?", html))
    slugs.add(entry["index_url"].rstrip("/").rsplit("/", 1)[-1])
    # Newer months are not linked yet from an older page, so try each month up to now.
    year, month = max((int(s[-7:-3]), int(s[-2:])) if not s.endswith("-en") else (int(s[-10:-6]), int(s[-5:-3])) for s in slugs)
    today = dt.date.today()
    while (year, month) < (today.year, today.month):
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        for slug in (f"herams-opt-gaza-infographics-{year}-{month:02d}", f"herams-opt-gaza-infographics-{year}-{month:02d}-en"):
            r = requests.get(urljoin(entry["index_url"], slug), timeout=60, headers={"User-Agent": USER_AGENT})
            if r.status_code == 200 and "cdn.who.int" in r.text:
                slugs.add(slug)
                break
    return [urljoin(entry["index_url"], s) for s in sorted(slugs, key=lambda s: s.replace("-en", ""))]


def run_herams(entry: dict, metrics: list[dict], state: dict) -> Proposal:
    prop = Proposal()
    for page in herams_pages(entry)[-entry.get("max_documents", 40):]:
        try:
            html = requests.get(page, timeout=60, headers={"User-Agent": USER_AGENT}).text
        except Exception as e:  # noqa: BLE001
            prop.rejected.append(Rejected(page, "could not download", str(e)))
            continue
        m = re.search(r"https://cdn\.who\.int/[^\"'\s]+\.pdf[^\"'\s]*", html)
        if not m:
            prop.rejected.append(Rejected(page, "no PDF link on the page"))
            continue
        url = requote_uri(m.group(0).replace("&amp;", "&"))
        if state.get(page) and state.get(page) == state.get(url):
            continue
        try:
            doc = fetch(url)
        except Exception as e:  # noqa: BLE001
            prop.rejected.append(Rejected(url, "could not download", str(e)))
            continue
        prop.seen[url] = doc.sha256
        prop.seen[page] = doc.sha256
        if state.get(url) == doc.sha256:
            continue
        text = pdf_text(doc.content)
        keep(doc, text)
        found = parse_herams(text, doc.meta(PUBLISHER_HERAMS))
        if not found:
            prop.rejected.append(Rejected(url, "no figures found", "The HeRAMS layout may have changed; update the patterns in ingest/sources/who_health.py."))
        prop.observations += found
    return prop
