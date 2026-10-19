# Gaza Data Tracker

An open, source-first record of the war in Gaza: deaths and injuries, hospitals, aid, food security, damage to buildings,
and Israeli casualties. Every figure is taken from the body that published it, linked to the document it came from,
and labelled as a **count**, a **claim** or an **estimate**. The project produces no figures of its own.

## Principles

- **Attribution over aggregation.** Bodies often count different things (COGAT counts every truck it clears; the UN2720
  mechanism counts only UN-manifested cargo). Their figures are shown side by side, never merged or averaged.
- **Three kinds of figure.** A *count* is a tally a named body recorded. A *claim* is a party's figure with no names or
  method others can check. An *estimate* is a modelled number with an uncertainty range. The label describes what can be
  checked, not whether a figure is right.
- **Qualifiers are kept.** "At least" and "about" stay with the number.
- **Primary sources.** Figures are read from the body's own report, dataset, transcript or channel, not from news coverage.
- **Append-only.** Stored figures are never edited or deleted; a correction is a new record that supersedes the old one.

## How it works

```
sources ──► importers ──► pull request ──► review ──► merge ──► static site rebuilds
            (scheduled)   (data + report)
```

Importers run twice a day in GitHub Actions. They download each source, archive a copy, extract only the values the
document states, check every rule, and open a pull request with a report. A person reviews and merges; merging publishes.

## Repository layout

```
data/
  sources.json          who publishes figures, and their affiliation
  metrics.json          what each measure means
  observations/         one JSON file per measure, append-only
  lists/                named victims (no ID numbers or dates of birth), hospitals, WHO statements per hospital
  watchlist.json        what the importers check, and how
schema/                 JSON Schema for sources, metrics and observations
archive/                copies of the documents importers read (PDFs via Git LFS)
ingest/                 Python importers, checks and tests
scripts/                validate.py (every rule, used in CI), hospital_mentions.py
site/                   Next.js static site, built from data/
AGENTS.md               rules for AI agents and contributors
```

## Sources

| Source | What | How |
|---|---|---|
| Gaza Ministry of Health (via Tech for Palestine) | Daily deaths and injuries since 7 Oct 2023, named victims | `techforpalestine`, `techforpalestine-daily`, `names` |
| WHO | Hospital status (situation reports, HeRAMS), attacks on health care | `who-sitreps`, `who-herams` |
| UN2720 mechanism (UNOPS) | Monthly aid deliveries and pipeline | `un2720` |
| UNOSAT | Damage to structures from satellite images | `unosat` |
| Gaza Government Media Office (via Tech for Palestine) | Destroyed and damaged buildings, labelled claims | `techforpalestine-infrastructure` |
| OCHA (HDX) | List of Gaza's 36 hospitals | `hospitals` |
| oct7database (volunteer compilation, checked against Israeli official memorial lists) | People killed in the 7 October 2023 attack | `oct7` |
| Martyrs of Gaza and The Living Record (independent memorial projects) | Links from Gaza names to memorial pages, matched by name under strict rules | `memorials` |
| OHCHR, WHO and others (press releases) | Figures in free text, verified against the document | `press`, `add-url` (optional, see below) |
| IPC, COGAT, IDF, Israeli ministries, peer-reviewed studies | Food security, aid, Israeli casualties, estimates | Added by hand with quotes |

## Getting started

Requirements: Python 3.11+, Node 22+, [Git LFS](https://git-lfs.com) for the archived documents.

```bash
git lfs install
git clone https://github.com/JoshSald/gaza-data-tracker.git
cd gaza-data-tracker

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python scripts/validate.py

cd site
npm install
npm run dev        # http://localhost:3000
npm run build      # static output in site/out/
```

## Running the importers

```bash
python -m ingest run --dry-run            # show what would be added, without writing
python -m ingest run                      # add new figures and write .ingest-report.md
python -m ingest run --only who-herams    # one source from data/watchlist.json
python -m ingest names                    # update the named-victims list
python -m ingest hospitals                # update the hospital list
python -m ingest oct7                     # update the list of people killed in the 7 October attack (run by hand)
python -m ingest memorials                # link Gaza names to independent memorial pages, printing each link for review (run by hand)
```

**Optional: reading press releases.** The `press` importer and `add-url` use a language model to propose figures from
free text; each is kept only if its quote appears word for word in the archived document. They need the extra package
and an API key:

```bash
pip install -r requirements-llm.txt
cp .env.example .env      # add ANTHROPIC_API_KEY
python -m ingest add-url "https://..." --source ohchr --metrics gaza.killed.seeking_aid --dry-run
```

## Contributing

- One feature per branch and pull request. Commit messages and PR titles follow
  [Conventional Commits](https://www.conventionalcommits.org) (`feat(ingest): ...`, `fix(site): ...`).
- Read [AGENTS.md](AGENTS.md) for the data rules: every new figure needs a source document, an archived copy and a quote.
- Before opening a pull request, run `pytest -q`, `python scripts/validate.py` and `npm run build` in `site/`.

## Licence

To be decided. The archived documents remain under their publishers' own terms.
