"""Command line: python -m ingest <command>

  run [--only ID] [--dry-run]     run every enabled watchlist entry and propose new observations
  add-url URL --source ID --metrics a,b [--kind count|claim|estimate] [--publisher NAME]
                                  read one document now, for example a press release you found
  names [--dry-run]               update data/lists/named-victims.json from the Ministry's list of names
  hospitals [--dry-run]           update data/lists/hospitals.json, the list of Gaza's 36 hospitals
  oct7 [--dry-run]                update data/lists/oct7-victims.json, people killed in the 7 October attack
  memorials [--dry-run]           update data/lists/gaza-memorial-links.json, links from Gaza names to memorial pages
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import checks, store
from .paths import REPORT, WATCH_STATE, WATCHLIST
from .sources import cogat_updates, hospitals, memorials, names, oct7, press, techforpalestine, un2720, unosat, who_health
from .sources.base import Proposal

ROW_LIMIT = 100  # above this many new rows, the report summarises instead of listing each one

IMPORTERS = {
    "techforpalestine": techforpalestine.run,
    "techforpalestine-daily": techforpalestine.run_daily,
    "techforpalestine-infrastructure": techforpalestine.run_infrastructure,
    "who-sitreps": who_health.run_sitreps,
    "who-herams": who_health.run_herams,
    "unosat": unosat.run,
    "un2720": un2720.run,
    "press": press.run,
    "cogat-updates": cogat_updates.run,
}


def _load_state() -> dict:
    return json.loads(WATCH_STATE.read_text()) if WATCH_STATE.exists() else {}


def _save_state(state: dict) -> None:
    WATCH_STATE.write_text(json.dumps(dict(sorted(state.items())), indent=2) + "\n")


def _run_entries(entries: list[dict], dry_run: bool) -> int:
    metrics, sources = store.load_metrics(), store.load_sources()
    existing = store.load_observations()
    by_id = {o["id"]: o for o in existing}
    state = _load_state()

    proposals: list[tuple[dict, Proposal]] = []
    failed: list[str] = []
    for entry in entries:
        fn = IMPORTERS.get(entry["importer"])
        if not fn:
            print(f"! {entry['id']}: unknown importer {entry['importer']}", file=sys.stderr)
            continue
        print(f"→ {entry['id']}", file=sys.stderr)
        try:
            prop = fn(entry, metrics, state, sources) if fn is press.run else fn(entry, metrics, state)
        except Exception as e:  # noqa: BLE001 - one broken source must not stop the others
            prop = Proposal(notes=[f"{entry['id']} failed: {e}"])
            failed.append(entry["id"])
        proposals.append((entry, prop))

    candidates, conflicts, notes = [], [], []
    for entry, prop in proposals:
        notes += prop.notes
        for o in prop.observations:
            # The same figure can arrive twice in one run (a report uploaded twice, or repeated in the next issue):
            # keep the first, and treat a different value for the same id as a conflict.
            old = by_id.get(o["id"])
            if old is None:
                candidates.append(o)
                by_id[o["id"]] = o
            elif old["value"] != o["value"]:
                conflicts.append((old, o))

    # Run every rule over the stored data plus the candidates; drop candidates that break one.
    result = checks.check(existing + candidates, metrics, sources)
    bad = {c["id"] for c in candidates if any(f" {c['id']}:" in f" {e}" or e.startswith(c["id"] + ":") for e in result.errors)}
    errors = [e for e in result.errors if any(f" {b}:" in f" {e}" or e.startswith(b + ":") for b in bad)]
    accepted = [c for c in candidates if c["id"] not in bad]
    checks.flag_new(accepted, result)

    added = accepted if dry_run else store.append(accepted)
    if not dry_run:
        for _, prop in proposals:
            state.update(prop.seen)
        _save_state(state)

    report = _report(added, result.flags, errors, conflicts, proposals, notes, dry_run)
    REPORT.write_text(report)
    print(report)
    # A failed source exits non-zero so the scheduled run shows as failed and GitHub notifies you.
    return 1 if failed else 0


def _report(added, flags, errors, conflicts, proposals, notes, dry_run) -> str:
    lines = ["# Data update" + (" (dry run)" if dry_run else ""), ""]
    flagged = [o for o in added if o["id"] in flags]
    lines.append(f"**{len(added)}** new observation(s), **{len(flagged)}** flagged for a closer look.")
    lines.append("")
    if len(added) > ROW_LIMIT:
        # A backfill can add thousands of rows; list them per measure so the report fits in a pull request.
        lines += [f"## New observations, by measure", "",
                  f"More than {ROW_LIMIT} rows, so they are summarised. Each row's quote and document are in the data files.", "",
                  "| Metric | Source | Rows | First | Last | Read in |", "|---|---|---|---|---|---|"]
        groups: dict[tuple, list[dict]] = {}
        for o in added:
            groups.setdefault((o["metric"], o["source"], o["document"]["publisher"], o["document"]["url"]), []).append(o)
        for (metric_id, source_id, publisher, url), rows in groups.items():
            rows.sort(key=lambda r: r["as_of"])
            first, last = rows[0], rows[-1]
            lines.append(f"| `{metric_id}` | {source_id} | {len(rows):,} | {first['value']:,g} ({first['as_of']}) | {last['value']:,g} ({last['as_of']}) | [{publisher}]({url}) |")
        lines.append("")
    elif added:
        lines += ["## New observations", "", "| | Metric | Value | As of | Source | Quote |", "|---|---|---|---|---|---|"]
        for o in added:
            mark = "⚠️" if o["id"] in flags else ""
            dims = " " + ", ".join(f"{k}={v}" for k, v in o.get("dimensions", {}).items()) if o.get("dimensions") else ""
            quote = (o.get("quote") or "").replace("|", "\\|")[:180]
            lines.append(f"| {mark} | `{o['metric']}`{dims} | {o['value']:,g} ({o['bound']}) | {o['as_of']} | [{o['document']['publisher']}]({o['document']['url']}) | {quote} |")
        lines.append("")
    if flagged:
        lines += ["## Flags", ""]
        # "headline figure" alone on many rows (a backfill) is collapsed to one line per measure.
        headline_only = [o for o in flagged if flags[o["id"]] == ["headline figure"]]
        collapse = len(headline_only) > ROW_LIMIT
        for o in flagged:
            if collapse and o in headline_only:
                continue
            lines.append(f"- `{o['id']}`: " + "; ".join(flags[o["id"]]))
        if collapse:
            per_metric: dict[str, list[dict]] = {}
            for o in headline_only:
                per_metric.setdefault(o["metric"], []).append(o)
            for metric_id, rows in sorted(per_metric.items()):
                newest = max(rows, key=lambda r: r["as_of"])
                lines.append(f"- headline figure: {len(rows):,} new `{metric_id}` rows, newest `{newest['id']}` = {newest['value']:,g}")
        lines.append("")
    if conflicts:
        lines += ["## Conflicts (not added)", "", "Same source, metric and date as a stored observation, but a different value. Decide which is right and add a correction with `supersedes` if needed.", ""]
        for old, new in conflicts:
            lines.append(f"- `{old['id']}`: stored {old['value']:,g}, new document says {new['value']:,g} ({new['document']['url']})")
        lines.append("")
    rejected = [(e, r) for e, p in proposals for r in p.rejected]
    if rejected or errors:
        lines += ["## Rejected", ""]
        for entry, r in rejected:
            lines.append(f"- {entry['id']}: {r.reason}. {r.detail} ({r.url})")
        for e in errors:
            lines.append(f"- rule: {e}")
        lines.append("")
    if notes:
        lines += ["## Notes", ""] + [f"- {n}" for n in notes] + [""]
    lines += ["---", "Review each new figure against its source before merging. Merging publishes it."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m ingest")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--only", help="run one watchlist entry by id")
    r.add_argument("--dry-run", action="store_true", help="show what would be added without writing")
    a = sub.add_parser("add-url")
    a.add_argument("url")
    a.add_argument("--source", required=True, help="an id from data/sources.json")
    a.add_argument("--metrics", required=True, help="comma-separated metric ids to look for")
    a.add_argument("--kind", default="count", choices=["count", "claim", "estimate"])
    a.add_argument("--publisher", help="where you read it, if not the source itself")
    a.add_argument("--dry-run", action="store_true")
    n = sub.add_parser("names")
    n.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    hp = sub.add_parser("hospitals")
    hp.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    o7 = sub.add_parser("oct7")
    o7.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    mem = sub.add_parser("memorials")
    mem.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    args = ap.parse_args(argv)
    if args.dry_run:
        os.environ["ARCHIVE_DISABLED"] = "1"  # a dry run leaves no copies in archive/

    if args.cmd == "oct7":
        lines = oct7.run(args.dry_run)
        print("\n".join(lines))
        return 1 if lines[0].endswith("not updated:") else 0
    if args.cmd == "memorials":
        print("\n".join(memorials.run(args.dry_run)))
        return 0
    if args.cmd == "hospitals":
        print("\n".join(hospitals.run(args.dry_run)))
        return 0
    if args.cmd == "names":
        state = _load_state()
        lines, seen = names.run(state, args.dry_run)
        if seen:
            state.update(seen)
            _save_state(state)
        print("\n".join(lines))
        # Added to the scheduled run's report, so the pull request shows it.
        if REPORT.exists() and not args.dry_run:
            REPORT.write_text(REPORT.read_text() + "\n## Named victims list\n\n" + "\n".join(lines) + "\n")
        return 1 if lines and lines[0].endswith("not updated:") else 0
    if args.cmd == "run":
        entries = [e for e in json.loads(WATCHLIST.read_text()) if e.get("enabled", True)]
        if args.only:
            entries = [e for e in json.loads(WATCHLIST.read_text()) if e["id"] == args.only]
        return _run_entries(entries, args.dry_run)
    entry = {
        "id": f"add-url:{args.source}",
        "importer": "press",
        "urls": [args.url],
        "source": args.source,
        "metrics": [m.strip() for m in args.metrics.split(",") if m.strip()],
        "kind": args.kind,
        **({"publisher": args.publisher} if args.publisher else {}),
    }
    return _run_entries([entry], args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
