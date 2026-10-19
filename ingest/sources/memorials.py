"""Links from names on the Gaza list to memorial pages written by independent projects.

Israel publishes an official memorial page for almost everyone killed on 7 October, so the 7 October list can link
each name to one. Nothing official exists for people killed in Gaza. Two independent projects write about them:

- Martyrs of Gaza (gazashaheed.com): stories sent in by families and friends, one page per person, in Arabic.
- The Living Record (newyorkwarcrimes.com/livingrecord/), by Writers Against the War on Gaza: Gaza's journalists
  remembering colleagues who were killed, in English and Arabic.

Neither project gives the Ministry's ID numbers, so the only way to connect a page to a name on the Ministry's list
is by the name itself. Names in Gaza are often shared, spelled in more than one way, and given with fewer parts
than the Ministry records (often just a first and family name). A wrong link would attach someone's story to a
different person, so a page is linked only when the evidence points to exactly one person:

1. The name on the page, normalised (vowel marks, alef forms, taa marbuta, compounds such as عبد and أبو), must have
   the same first and family name as the Ministry's record, with every part of it found, in order, in that record.
2. Exactly one record on the Ministry's list may fit. If two or more fit, the page is not linked.
3. A name of three or more parts is enough on its own. A name of only two parts also needs a second, independent fact
   that agrees: an age stated on the page, a year of birth, or the father's name given in the page's English text.
4. Anything on the page that disagrees with the record (a different age, the other sex) rules the link out.

Pages about several people (a family, a couple) are skipped, since the page cannot be tied to one name.

Run with `python -m ingest memorials`; it is not part of the scheduled import. It writes
data/lists/gaza-memorial-links.json and prints every proposed link for review.
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field

from ..archive import fetch
from ..paths import DATA

NAMES_FILE = DATA / "lists" / "named-victims.json"
LIST_FILE = DATA / "lists" / "gaza-memorial-links.json"
FIELDS = ["ar_name", "age", "sex", "url", "project", "basis"]

GS_API = "https://gazashaheed.com/ar/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=id,link,title,content"
GS_SITE = "https://gazashaheed.com/"
LR_SITE = "https://newyorkwarcrimes.com/livingrecord/"
LR_NOT_PEOPLE = {"about", "journalists-as-a-collective", "contributors", "donate", "ar"}

# Death dates are not on the Ministry's list; everyone on it died between October 2023 and the list's cut-off.
FIRST_YEAR, LAST_YEAR = 2023, 2026

# Titles and words that come before a name but are not part of it.
HONORIFICS = {"الشهيد", "الشهيده", "شهيد", "شهيده", "الطفل", "الطفله", "الدكتور", "الدكتوره", "د", "المهندس",
              "المهندسه", "الصحفي", "الصحفيه", "الحاج", "الحاجه", "الاستاذ", "الاستاذه", "الشيخ", "الفنان", "الفنانه"}
FEMALE_TITLES = {"الشهيده", "شهيده", "الطفله", "الدكتوره", "المهندسه", "الصحفيه", "الحاجه", "الاستاذه", "الفنانه"}
MALE_TITLES = {"الشهيد", "شهيد", "الطفل", "الدكتور", "المهندس", "الصحفي", "الحاج", "الاستاذ", "الشيخ", "الفنان"}
COMPOUNDS = {"عبد", "ابو", "ابن", "بن", "ام", "بنت", "ال"}
# Words that show a page is about more than one person.
GROUP_WORDS = ["عائلة", "أسرة", "وزوجته", "وزوجها", "وأطفاله", "وأبناؤه", "وأبنائه", "وعائلته", "وأطفالها"]

AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")


def normalise_ar(s: str) -> list[str]:
    """Arabic name to comparable tokens: no vowel marks, one alef, ة→ه, ى→ي, compounds joined to the next word."""
    s = TASHKEEL.sub("", html.unescape(s))
    s = re.sub("[أإآٱ]", "ا", s).replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    s = re.sub(r"[^ء-ي\s]", " ", s)
    words, out = s.split(), []
    i = 0
    while i < len(words):
        w = words[i]
        if w in COMPOUNDS and i + 1 < len(words):
            out.append(w + words[i + 1])
            i += 2
            continue
        out.append(w)
        i += 1
    return out


GROUP_WORDS = {w for g in GROUP_WORDS for w in normalise_ar(g)}


def normalise_en(s: str) -> list[str]:
    """English transliteration to a rough consonant skeleton, so Mohammed/Muhammad or Abdel/Abdul compare equal."""
    s = re.sub(r"['’`]", "", html.unescape(s).lower().replace("\u2011", "-"))
    s = re.sub(r"\b(al|el)[-\s]", "al", s)
    s = re.sub(r"\b(abd|abdel|abdul|abdal|abed)[-\s]?", "abd", s)
    s = re.sub(r"\babu[-\s]", "abu", s)
    tokens = re.sub(r"[^a-z\s]", " ", s).split()
    return [_skeleton(t) for t in tokens]


def _skeleton(t: str) -> str:
    t = t.replace("ph", "f").replace("ou", "u").replace("ee", "i").replace("oo", "u")
    t = t[0] + re.sub(r"[aeiouyw'h]", "", t[1:]) if t else t
    t = t.replace("q", "k").replace("j", "g")
    return re.sub(r"(.)\1+", r"\1", t)


def father_agrees(page_en: str, record_en: str) -> bool:
    """The page's English name has a middle name (the father's), and the record has the same first and middle names."""
    a, b = normalise_en(page_en), normalise_en(record_en)
    return len(a) >= 3 and len(b) >= 3 and a[0] == b[0] and is_subsequence(a[1:-1], b[1:-1])


def is_subsequence(short: list[str], long: list[str]) -> bool:
    it = iter(long)
    return all(any(x == y for y in it) for x in short)


@dataclass
class Page:
    url: str
    project: str
    ar_name: str
    text: str = ""
    en_name: str = ""
    sex: str | None = None
    ages: set[int] = field(default_factory=set)
    birth_year: int | None = None


@dataclass
class Result:
    page: Page
    status: str  # "linked", "ambiguous", "no match", "skipped", "not corroborated", "contradicted"
    record: int | None = None
    basis: str = ""
    candidates: int = 0


def ages_in(text: str) -> set[int]:
    """Ages stated in Arabic or English text: "27 عامًا", "(27 سنة)", "aged 27", "27 years old"."""
    t = TASHKEEL.sub("", text).translate(AR_DIGITS)
    found = re.findall(r"(\d{1,3})\s*(?:عاما|عام|سنه|سنة|سنوات|ربيعا)", t)
    found += re.findall(r"(?:عمره|عمرها|العمر)\s*(\d{1,3})", t)
    found += re.findall(r"\b(?:aged|age)\s+(\d{1,3})\b|\b(\d{1,3})[- ]years?[- ]old\b", t)
    flat = [int(x) for f in found for x in (f if isinstance(f, tuple) else (f,)) if x]
    return {a for a in flat if a < 120}


def birth_year_in(text: str) -> int | None:
    t = text.translate(AR_DIGITS)
    years = set(re.findall(r"(?:born|مواليد|ولد|ولدت)[^.؟!]{0,60}?\b(19\d\d|20[0-2]\d)\b", t))
    return int(years.pop()) if len(years) == 1 else None


class Index:
    def __init__(self, records: list[list]):
        self.records = records
        self.tokens = [normalise_ar(r[1]) for r in records]
        self.by_ends: dict[tuple[str, str], list[int]] = {}
        for i, t in enumerate(self.tokens):
            if len(t) >= 2:
                self.by_ends.setdefault((t[0], t[-1]), []).append(i)

    def candidates(self, tokens: list[str]) -> list[int]:
        if len(tokens) < 2:
            return []
        return [i for i in self.by_ends.get((tokens[0], tokens[-1]), []) if is_subsequence(tokens, self.tokens[i])]


def judge(page: Page, index: Index) -> Result:
    if not page.ar_name:
        return Result(page, "skipped", basis="no reliable Arabic name on the page")
    tokens = [t for t in normalise_ar(page.ar_name) if t not in HONORIFICS]
    if len(tokens) < 2:
        return Result(page, "skipped", basis="first name only")
    cands = index.candidates(tokens)
    if not cands:
        return Result(page, "no match")
    narrowed = ""
    if len(cands) > 1 and page.en_name:
        # The Arabic heading may give two names where the English biography gives the father's name too.
        fits = [i for i in cands if father_agrees(page.en_name, index.records[i][0])]
        if len(fits) == 1:
            narrowed = f"{len(cands)} records share the name on the page; only one has the father's name given in its English text"
            cands = fits
    if len(cands) > 1:
        return Result(page, "ambiguous", candidates=len(cands))
    i = cands[0]
    _, _, age, sex, _ = index.records[i]
    if page.sex and sex != page.sex:
        return Result(page, "contradicted", i, "the page gives the other sex", 1)
    ok_ages = {age, age + 1, age - 1}  # the page may give the age at a birthday either side of the Ministry's record
    if page.ages and not page.ages & ok_ages:
        return Result(page, "contradicted", i, f"the page gives age {sorted(page.ages)}, the list {age}", 1)
    if page.birth_year and not (FIRST_YEAR - page.birth_year - 1 <= age <= LAST_YEAR - page.birth_year):
        return Result(page, "contradicted", i, f"born {page.birth_year}, but the list gives age {age}", 1)

    basis = [narrowed or f"{len(tokens)}-part name, one record fits"]
    corroborated = len(tokens) >= 3
    if page.ages & ok_ages:
        basis.append(f"age {age} agrees with the page")
        corroborated = True
    if page.birth_year:
        basis.append(f"born {page.birth_year} agrees with age {age}")
        corroborated = True
    if page.en_name and father_agrees(page.en_name, index.records[i][0]):
        if not narrowed:
            basis.append("the father's name in the page's English text agrees")
        corroborated = True
    if not corroborated:
        return Result(page, "not corroborated", i, "two-part name with nothing else to confirm it", 1)
    return Result(page, "linked", i, "; ".join(basis), 1)


# --- the two projects ---

def _text(h: str) -> str:
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def gaza_shaheed_pages(posts: list[dict]) -> list[Page]:
    pages = []
    for p in posts:
        title = html.unescape(p["title"]["rendered"]).strip()
        words = set(normalise_ar(title))
        if words & GROUP_WORDS or re.search(r"[،,&+/]|\sو\s", title):
            pages.append(Page(p["link"], "gaza-shaheed", title, text="(several people)"))
            continue
        text = _text(p["content"]["rendered"])
        sex = "f" if words & FEMALE_TITLES else "m" if words & MALE_TITLES else None
        # An age is only trusted when the page states one age; stories often mention relatives' ages too.
        ages = ages_in(text)
        pages.append(Page(p["link"], "gaza-shaheed", title, text, sex=sex, ages=ages if len(ages) == 1 else set(),
                          birth_year=birth_year_in(text)))
    return pages


def fetch_gaza_shaheed() -> list[dict]:
    posts, page = [], 1
    while True:
        batch = json.loads(fetch(GS_API.format(page=page)).content)
        posts += batch
        if len(batch) < 100:
            return posts
        page += 1


def living_record_slugs(index_html: str) -> list[str]:
    slugs = re.findall(r'href="/livingrecord/([a-z0-9-]+)/?"', index_html)
    return sorted({s for s in slugs if s not in LR_NOT_PEOPLE})


def biography_name(text: str) -> str:
    """The full name that opens the biography: "Anas Jamal Mahmoud al-Sharif was born..." gives the first four words."""
    m = re.search(r"Biography (.*)", text)
    if not m:
        return ""
    words = []
    for w in m.group(1).split():
        if not (w[:1].isupper() or re.match(r"(al|el|abu|bin|abd)\b|(al|el)[-\u2011]", w)):
            break
        words.append(w.rstrip(",.;"))
    return " ".join(words)


def living_record_page(slug: str, en_html: str, ar_html: str) -> Page:
    h1 = lambda h: html.unescape(re.sub(r"<[^>]+>", "", re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S).group(1))).strip()
    text = _text(en_html)
    return Page(LR_SITE + slug, "living-record", h1(ar_html), text, en_name=biography_name(text) or h1(en_html),
                birth_year=birth_year_in(text[:600]))


def fetch_living_record() -> list[Page]:
    slugs = living_record_slugs(fetch(LR_SITE).content.decode("utf-8"))
    pages = []
    for s in slugs:
        en = fetch(f"{LR_SITE}{s}").content.decode("utf-8")
        ar = fetch(f"{LR_SITE}{s}/ar/").content.decode("utf-8")
        pages.append(living_record_page(s, en, ar))
    # The Arabic page of one person can carry another's name by mistake; a name on two pages is not trusted.
    seen: dict[str, int] = {}
    for p in pages:
        seen[p.ar_name] = seen.get(p.ar_name, 0) + 1
    for p in pages:
        if seen[p.ar_name] > 1:
            p.ar_name = ""
    return pages


def match(pages: list[Page], records: list[list]) -> list[Result]:
    index = Index(records)
    results = [judge(p, index) if p.text != "(several people)" else Result(p, "skipped", basis="page about several people")
               for p in pages]
    # One person can have pages on both projects; two pages pointing at one record are both fine. But one page
    # must never point at two records, and a record linked twice by the same project is suspicious: drop both.
    by_record: dict[tuple[int, str], list[Result]] = {}
    for r in results:
        if r.status == "linked":
            by_record.setdefault((r.record, r.page.project), []).append(r)
    for rs in by_record.values():
        if len(rs) > 1:
            for r in rs:
                r.status, r.basis = "ambiguous", "two pages fit the same record"
    return results


def run(dry_run: bool) -> list[str]:
    names = json.loads(NAMES_FILE.read_text())
    records = names["records"]
    pages = gaza_shaheed_pages(fetch_gaza_shaheed()) + fetch_living_record()
    results = match(pages, records)
    linked = [r for r in results if r.status == "linked"]

    lines = [f"Memorial pages read: {len(pages)}; linked to one name on the Gaza list: {len(linked)}."]
    for status in ["ambiguous", "no match", "not corroborated", "contradicted", "skipped"]:
        lines.append(f"- {status}: {sum(1 for r in results if r.status == status)}")
    lines.append("")
    lines.append("| Page | Name on page | Ministry record | Age | Basis |")
    lines.append("|---|---|---|---|---|")
    for r in linked:
        rec = records[r.record]
        lines.append(f"| {r.page.url} | {r.page.ar_name} | {rec[1]} ({rec[0]}) | {rec[2]} | {r.basis} |")
    if dry_run:
        return lines + ["", "(dry run: nothing written)"]

    # The Gaza list stores no ID, so a link is keyed by the Ministry's Arabic name, age and sex; check that is unique.
    keys: dict[tuple, int] = {}
    for rec in records:
        k = (rec[1], rec[2], rec[3])
        keys[k] = keys.get(k, 0) + 1
    out = []
    for r in sorted(linked, key=lambda r: r.record):
        rec = records[r.record]
        if keys[(rec[1], rec[2], rec[3])] == 1:
            out.append([rec[1], rec[2], rec[3], r.page.url, r.page.project, r.basis])
    meta = {
        "projects": {
            "gaza-shaheed": {"name": "Martyrs of Gaza", "url": GS_SITE},
            "living-record": {"name": "The Living Record", "url": LR_SITE,
                              "by": "Writers Against the War on Gaza"},
        },
        "names_list_sha256": names["document"]["sha256"],
        "pages_read": len(pages),
        "counts": {s: sum(1 for r in results if r.status == s)
                   for s in ["linked", "ambiguous", "no match", "not corroborated", "contradicted", "skipped"]},
        "note": ("Links from names on the Ministry of Health's list to memorial pages kept by independent projects. "
                 "The projects do not give ID numbers, so pages are matched by name, and only where exactly one record "
                 "fits and nothing on the page disagrees with it. See ingest/sources/memorials.py for the rules."),
        "fields": FIELDS,
    }
    body = ",\n".join("    " + json.dumps(r, ensure_ascii=False) for r in out)
    head = json.dumps(meta, indent=2, ensure_ascii=False)[:-2]
    LIST_FILE.write_text(f'{head},\n  "records": [\n{body}\n  ]\n}}\n', encoding="utf-8")
    return lines
