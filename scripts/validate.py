"""Check all data against the schema and rules. Used in CI on every pull request.

  python scripts/validate.py                 check the data as it is
  python scripts/validate.py --base DIR      also check that nothing stored in DIR (the main
                                             branch's data/) was edited or removed
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import checks, store  # noqa: E402
from ingest.paths import DATA  # noqa: E402


def _strip(o: dict) -> dict:
    return {k: v for k, v in o.items() if not k.startswith("_")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, help="data/ directory of the branch being merged into")
    args = ap.parse_args()

    obs = store.load_observations(DATA)
    result = checks.check(obs, store.load_metrics(DATA), store.load_sources(DATA))
    errors = list(result.errors)

    if args.base and (args.base / "observations").exists():
        current = {o["id"]: _strip(o) for o in obs}
        for old in store.load_observations(args.base):
            new = current.get(old["id"])
            if new is None:
                errors.append(f"{old['id']}: removed. Observations are never deleted; add a correction with `supersedes` instead.")
            elif new != _strip(old):
                errors.append(f"{old['id']}: edited after it was merged. Add a new observation with `supersedes` instead.")

    lists = DATA / "lists"
    load = lambda name: store.load_json(lists / name) if (lists / name).exists() else None  # noqa: E731
    errors += checks.check_hospitals(load("hospitals.json"), load("hospital-status.json"))
    errors += checks.check_oct7(load("oct7-victims.json"))
    if args.base and (args.base / "lists" / "hospital-status.json").exists():
        # Statements are append-only, like observations.
        current = {json.dumps(s, sort_keys=True) for s in (load("hospital-status.json") or {}).get("statements", [])}
        for old in store.load_json(args.base / "lists" / "hospital-status.json").get("statements", []):
            if json.dumps(old, sort_keys=True) not in current:
                errors.append(f"hospital-status.json: a merged statement about {old.get('hospital')} was edited or removed.")

    print(f"{len(obs)} observations checked.")
    for oid, reasons in sorted(result.flags.items()):
        print(f"flag  {oid}: {'; '.join(reasons)}")
    for e in errors:
        print(f"error {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
