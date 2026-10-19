"""Read and append observations. Nothing here edits or deletes an existing record."""
from __future__ import annotations

import json
from pathlib import Path

from .paths import DATA, OBSERVATIONS


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_sources(data_dir: Path = DATA) -> list[dict]:
    return load_json(data_dir / "sources.json")


def load_metrics(data_dir: Path = DATA) -> list[dict]:
    return load_json(data_dir / "metrics.json")


def load_observations(data_dir: Path = DATA) -> list[dict]:
    out: list[dict] = []
    obs_dir = data_dir / "observations"
    if not obs_dir.exists():
        return out
    for path in sorted(obs_dir.glob("*.json")):
        rows = load_json(path)
        for row in rows:
            row["_file"] = path.name
        out.extend(rows)
    return out


def _write(path: Path, rows: list[dict]) -> None:
    rows = sorted(rows, key=lambda r: (r["as_of"], r["id"]))
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)
        f.write("\n")


def append(new: list[dict], obs_dir: Path = OBSERVATIONS) -> list[dict]:
    """Add observations whose id is not already stored. Returns the ones added."""
    obs_dir.mkdir(parents=True, exist_ok=True)
    added: list[dict] = []
    by_metric: dict[str, list[dict]] = {}
    for o in new:
        by_metric.setdefault(o["metric"], []).append(o)
    for metric, rows in by_metric.items():
        path = obs_dir / f"{metric}.json"
        existing = load_json(path) if path.exists() else []
        ids = {r["id"] for r in existing}
        fresh = [r for r in rows if r["id"] not in ids]
        if fresh:
            _write(path, existing + fresh)
            added.extend(fresh)
    return added
