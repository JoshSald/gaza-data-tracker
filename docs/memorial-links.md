# Memorial links and named victims

How Gaza Data Tracker links names on its lists to memorial pages kept by others, and which sources it uses. Anyone
adding or changing memorial links, by hand or through `python -m ingest memorials`, follows this document.

## Purpose

Gaza Data Tracker may link to external memorial pages to help visitors learn about the individuals represented in
its named-victims records.

The purpose of these links is to make individuals visible as people, preserve access to their stories and
photographs, and provide additional context beyond aggregate statistics.

The project does not need to create its own memorial pages. Linking to an existing memorial is sufficient.

Apply the same principles to Israeli and Palestinian victims. Differences in the availability of memorials,
photographs, biographies, and other information must be reported honestly rather than artificially corrected to
create visual symmetry.

## Memorials are not a source of figures

Memorial links help identify people. They never supply a count, a date, a cause of death or any other figure on
this site. Figures come only from the bodies that publish them, as set out in `AGENTS.md`. A memorial page that
quotes a figure does not make that figure a source.

## External memorials are not endorsements

External memorials are maintained by third parties and may contain emotional, religious, national, political, or
advocacy-oriented language.

Do not assume that an external source is neutral. Equally, do not reject a potentially useful memorial solely
because it expresses a political perspective.

Assess the suitability of each source for its intended purpose.

A memorial may be useful for identifying an individual, locating a photograph, or understanding a family's
testimony without being suitable as the sole source for a contested factual claim.

The presence of a link does not mean that Gaza Data Tracker endorses every statement, interpretation, or political
position expressed on the linked website.

Do not reproduce an external source's political language as the project's own editorial voice. Preserve quotations
accurately and attribute them to their original speaker or publisher when quoting them is necessary.

Do not rewrite, selectively edit, or misrepresent a source's testimony to make it appear more neutral than it is.

## Standard disclaimer

Use the following disclaimer near the named-victims list or wherever the site's external memorial links are
introduced:

> **About external memorials**
>
> Gaza Data Tracker links to external memorial pages to help visitors learn more about the individuals represented
> in its records, including their lives, photographs, and personal stories.
>
> These memorials are maintained by third parties and may reflect their own perspectives, interpretations, and
> political viewpoints. Their content is not produced or controlled by Gaza Data Tracker, and linking to a page does
> not constitute endorsement of every statement or claim it contains.
>
> Our aim is to acknowledge the individuals behind the statistics while maintaining a consistent, evidence-based
> approach to the information published on this website.

On the site, the named victims page shows it in one box above the lists. A short notice in red stays visible at all
times: memorial pages are kept by third parties, their views are not necessarily held by Gaza Data Tracker, and a link
is not an endorsement. The first two paragraphs and the full explanation of how links are made sit in a dropdown
beneath it. The statement of aim is on the method page, under "Memorial links".

Do not imply that every linked memorial has been independently verified or assessed for neutrality.

## Source selection

Candidate memorials and victim databases may include sources with different editorial perspectives.

For each candidate source:

1. Identify the organisation or individual responsible for publishing it.
2. Determine whether the resource is a memorial, a casualty database, a journalistic investigation, a family
   testimony collection, or an advocacy project.
3. Check whether the individual can be identified confidently.
4. Record the source of any relevant name, photograph, age, biography, or account of the circumstances of death.
5. Distinguish first-hand family testimony from independently corroborated factual information.
6. Note significant uncertainties or conflicting accounts.
7. Check whether the specific page is accessible and relevant.
8. Apply the same selection criteria to Israeli and Palestinian memorials.

Political perspective alone is not grounds for automatic exclusion. However, explicit incitement to violence,
dehumanisation, material that raises serious safety concerns, or demonstrably deceptive content requires individual
review before linking.

Do not label a source neutral merely because its language is restrained, or unreliable merely because its language
is emotional.

## Linking and attribution

Prefer linking directly to the individual's memorial page rather than reproducing the entire memorial on Gaza Data
Tracker.

Where possible, retain the source's original title and identify the publisher.

Do not imply that a memorial page verifies every field in the corresponding Gaza Data Tracker record.

A memorial may support the identification of a person without independently establishing the circumstances of their
death.

Keep the following distinctions clear:

- Identity: evidence that the named individual is correctly identified.
- Death: evidence that the individual died.
- Circumstances: evidence about when, where, and how the death occurred.
- Attribution: evidence identifying the alleged or established responsible actor.
- Personal testimony: information attributed to relatives, friends, colleagues, or other witnesses.

Do not infer one of these facts solely from evidence establishing another. A link on this site asserts identity
only.

## How links are made

- **By the matcher.** `python -m ingest memorials` reads each project in use and links a page only when exactly one
  person on the Ministry of Health's list fits the name, a name of two parts is backed by a second fact on the page,
  and nothing on the page disagrees with the record. The rules are in `ingest/sources/memorials.py`. Every proposed
  link is printed for review before it is published.
- **By ID number.** Some pages give a person's Ministry ID number. The matcher may compare it with the Ministry's list
  in memory to confirm a match, but ID numbers are never stored in this repository, printed or published.
- **By hand.** A page the rules cannot link may be linked by hand in `data/lists/gaza-memorial-links-by-hand.json`,
  with the basis written out, any source beyond the page cited, and the date added. The site marks these links
  "linked by hand".

## Photographs and personal information

Prefer linking to a photograph hosted by its original publisher.

Do not download, mirror, or republish a photograph merely because it is publicly accessible. Check applicable
copyright, licensing, privacy, and other relevant requirements before reproducing it.

Do not expose unnecessary personal information, including identification numbers, private contact details, or
sensitive information about relatives.

Take particular care when matching common names, transliterations, and records with incomplete identifying
information.

If a match is uncertain, do not present it as confirmed.

Visitors can report mistaken identities, incorrect biographical details, broken links, and privacy concerns through
the "Report a mistake" link on the named victims page, which opens a GitHub issue form.

## External-source reuse and permissions

Linking to a public resource is distinct from importing its data or reproducing its content.

Before copying, scraping, bulk importing, or redistributing an external dataset, review the applicable licence,
terms, attribution requirements, and any permission requirements.

If permission is required or the reuse terms are unclear, do not import the material until the requirements have
been resolved.

A source being publicly accessible does not automatically mean its data, photographs, or text may be republished.

Reading a project's pages to find which names to link is reuse too. Check each project's robots rules and terms
before adding it to the matcher, and keep only what a link needs: the page's address, the name it matched, and why.

## Sources in use

Each was checked against the steps above before it was added.

- **Martyrs of Gaza** (https://gazashaheed.com/): stories sent in by families and friends, one page per person, in
  Arabic and English.
- **The Living Record** (https://newyorkwarcrimes.com/livingrecord/), by Writers Against the War on Gaza: Gaza's
  journalists remembering colleagues who were killed. It uses explicit political framing; its testimony is
  attributed, not adopted.
- **Palestinians Are Not Numbers** (https://www.aintnumbers.com/): one page per person, often with a photograph, and
  accounts from families or quotations from the Ministry. It describes people as martyrs and Israel as the
  occupation; that is its language, not this site's. It also covers some people killed in the West Bank, who are
  not on the Gaza list and are never linked.
- **Official Israeli memorial records**, linked from the 7 October list through oct7database: the National Insurance
  Institute for civilians, and the IDF, Israel Police, Shin Bet and Ministry of Defence for security personnel.

## Sources considered and not used

- **Airwars** (https://airwars.org/): matches names to incidents using ID numbers, but states no terms for reusing
  its data, and permission has not been requested.
- **Find a Grave**: its terms forbid automated access beyond normal human use, its search is closed to crawlers, and
  its memorials are written by volunteers, often from news coverage.
- **Personal fundraising pages** (for example reemfund.org and the matching Save the Children personal page): written
  by one fundraiser, with details that disagree with the family's own account.

## Candidate source directory

The following resources are research leads, not automatically approved sources. Review their current content,
methodology, editorial perspective, and reuse conditions before relying on them.

Palestinian memorials and personal stories:

- Palestinian Children Memorial: https://palestinianchildren.com/
  A volunteer memorial focused on Palestinian children, with names, photographs, and individual stories. Its
  introductory language openly expresses a political perspective. Assess individual records and corroborate factual
  details where possible.
- Until: https://until.radicaldata.org/en
  A community-led database of Palestinians killed in Gaza. Individual records can include personal testimonials and
  photographs. Distinguish community contributions from independently corroborated facts.
- Visualizing Palestine, Remember Their Names: https://visualizingpalestine.org/gaza-names/en.html
  A memorial-style presentation of Palestinian names. Useful as a reference for collective remembrance; not a
  substitute for a detailed individual biography.
- Palestinian Children Memorial Organization: https://palestinianchildrenmemorial.org/
  A strongly advocacy-oriented memorial project focused on children. Review its claims, methodology, and individual
  entries carefully before using it as a source.

Palestinian casualty records and research:

- Shireen Observatory: https://www.shireen.ps/en/martyrs/year/2026
  Searchable victim records with demographic and event information. Its terminology and classifications express a
  particular political perspective. Treat its records as a research source, not automatically as independently
  verified findings.
- Al Jazeera, A-Z of the children killed in Gaza:
  https://www.aljazeera.com/news/longform/2024/11/20/an-a-z-of-the-children-israel-killed-in-gaza
  Journalistic reporting that provides individual names and context. It is news coverage: use it only as a lead for
  finding a name, never as a source for this site, and do not treat it as a complete victim register.

Israeli memorial reference:

- Izkor (https://www.izkor.gov.il/): Israel's official memorial database for fallen soldiers and security personnel.
  Its scope and inclusion criteria differ from those of a civilian-casualty database. The 7 October list already
  links each person to their official memorial record, including Ministry of Defence pages, so check for overlap
  before adding Izkor links.

These sources are not equivalent in purpose, coverage, or methodology. Do not present them as interchangeable or
assume that every source has the same level of verification.

## Editorial independence

Gaza Data Tracker's own descriptions must remain factual, appropriately attributed, and proportionate to the
available evidence.

Do not artificially equalise the number of memorial links or the amount of available biographical information for
different groups.

Do not suppress a relevant source simply because its findings or perspective are politically inconvenient.

Do not promote an unverified allegation into an established fact merely because it appears on a memorial page.

The objective is consistent dignity, transparent attribution, and consistent evidentiary standards, not forced
symmetry or endorsement of any source's political position.
