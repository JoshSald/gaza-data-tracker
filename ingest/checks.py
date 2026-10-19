"""Rules every observation must follow (errors) and patterns a reviewer should look at (flags)."""
from __future__ import annotations

import datetime as dt
import json
import statistics
from dataclasses import dataclass, field

from jsonschema import Draft202012Validator, FormatChecker

from .paths import SCHEMA

# Figures shown at the top of the site. Any change to these is flagged for a closer look.
HEADLINE_METRICS = {
    "gaza.killed.total",
    "gaza.killed.since_ceasefire",
    "gaza.killed.children",
    "gaza.deaths.malnutrition",
    "aid.trucks.entered",
}


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    flags: dict[str, list[str]] = field(default_factory=dict)  # observation id -> reasons

    def flag(self, obs_id: str, reason: str) -> None:
        self.flags.setdefault(obs_id, []).append(reason)

    @property
    def ok(self) -> bool:
        return not self.errors


def _validator(name: str) -> Draft202012Validator:
    with open(SCHEMA / name, encoding="utf-8") as f:
        return Draft202012Validator(json.load(f), format_checker=FormatChecker())


def _date(s: str | None) -> dt.date | None:
    return dt.date.fromisoformat(s) if s else None


def _series_key(o: dict) -> tuple:
    dims = tuple(sorted((o.get("dimensions") or {}).items()))
    return (o["metric"], o["source"], o.get("period_start"), dims)


def check(observations: list[dict], metrics: list[dict], sources: list[dict], today: dt.date | None = None) -> Result:
    today = today or dt.date.today()
    res = Result()

    for name, rows in (("source.schema.json", sources), ("metric.schema.json", metrics)):
        for err in _validator(name).iter_errors(rows):
            res.errors.append(f"{name}: {err.json_path}: {err.message}")

    metric_by_id = {m["id"]: m for m in metrics}
    source_ids = {s["id"] for s in sources}
    obs_validator = _validator("observation.schema.json")
    seen: dict[str, str] = {}

    for o in observations:
        oid = o.get("id", "<no id>")
        where = f"{o.get('_file', '?')} {oid}"
        clean = {k: v for k, v in o.items() if not k.startswith("_")}
        for err in obs_validator.iter_errors(clean):
            res.errors.append(f"{where}: {err.json_path}: {err.message}")
        if oid in seen:
            res.errors.append(f"{where}: duplicate id (also in {seen[oid]})")
        seen[oid] = o.get("_file", "?")
        if o.get("_file") and o.get("metric") and o["_file"] != f"{o['metric']}.json":
            res.errors.append(f"{where}: stored in the wrong file for metric {o['metric']}")
        if o.get("metric") not in metric_by_id:
            res.errors.append(f"{where}: unknown metric {o.get('metric')!r}")
        if o.get("source") not in source_ids:
            res.errors.append(f"{where}: unknown source {o.get('source')!r}")
        try:
            as_of, start, end = _date(o.get("as_of")), _date(o.get("period_start")), _date(o.get("period_end"))
        except (TypeError, ValueError):
            res.errors.append(f"{where}: dates must be YYYY-MM-DD")
            continue
        if as_of and as_of > today:
            res.errors.append(f"{where}: as_of {as_of} is in the future")
        if start and end and start > end:
            res.errors.append(f"{where}: period_start is after period_end")
        if o.get("kind") == "estimate" and ("low" not in o or "high" not in o):
            res.errors.append(f"{where}: an estimate needs low and high")
        if "low" in o and "high" in o and not (o["low"] <= o["value"] <= o["high"]):
            res.errors.append(f"{where}: value is outside low–high")
        added_by = o.get("added_by", "")
        if added_by.startswith(("importer:", "agent:")):
            if not o.get("quote"):
                res.errors.append(f"{where}: automated observations need a quote")
            if not o.get("document", {}).get("sha256"):
                res.errors.append(f"{where}: automated observations need the archived document's sha256")

    for o in observations:
        sup = o.get("supersedes")
        if sup and sup not in seen:
            res.errors.append(f"{o['id']}: supersedes unknown id {sup!r}")

    # Flags: things a person should look at before merging.
    superseded = {o["supersedes"] for o in observations if o.get("supersedes")}
    series: dict[tuple, list[dict]] = {}
    for o in observations:
        if o.get("id") in superseded or o.get("metric") not in metric_by_id:
            continue
        series.setdefault(_series_key(o), []).append(o)

    for key, rows in series.items():
        metric = metric_by_id[key[0]]
        rows = sorted(rows, key=lambda r: r["as_of"])
        if not metric["cumulative"]:
            continue
        for prev, cur in zip(rows, rows[1:]):
            if cur["value"] < prev["value"] and not cur.get("supersedes"):
                res.flag(cur["id"], f"lower than the {prev['as_of']} value ({prev['value']:,g} → {cur['value']:,g}) for a running total")
        rates = []
        for prev, cur in zip(rows, rows[1:]):
            days = (_date(cur["as_of"]) - _date(prev["as_of"])).days
            if days > 0:
                rates.append(((cur["value"] - prev["value"]) / days, cur))
        for i in range(3, len(rates)):
            baseline = statistics.median(r for r, _ in rates[i - 3 : i])
            rate, cur = rates[i]
            if baseline > 0 and rate > 5 * baseline and rate > 10:
                res.flag(cur["id"], f"rises {rate:,.0f}/day against a recent {baseline:,.0f}/day")
    return res


def flag_new(added: list[dict], result: Result) -> None:
    """Flags that only apply to observations being proposed now."""
    for o in added:
        if o["metric"] in HEADLINE_METRICS:
            result.flag(o["id"], "headline figure")
        if o.get("bound") != "exact":
            result.flag(o["id"], f"source qualifies the number ({o['bound'].replace('_', ' ')})")


HOSPITAL_STATUSES = ("partially_functioning", "not_functioning", "destroyed", "services_reported")


def check_hospitals(hospital_list: dict | None, status_file: dict | None, today: dt.date | None = None) -> list[str]:
    """Rules for data/lists/hospitals.json and data/lists/hospital-status.json."""
    today = today or dt.date.today()
    errors: list[str] = []
    if hospital_list is None:
        return errors if status_file is None else ["hospital-status.json exists without hospitals.json"]
    names = [h.get("name") for h in hospital_list.get("hospitals", [])]
    if len(names) != len(set(names)):
        errors.append("hospitals.json: duplicate hospital names")
    for h in hospital_list.get("hospitals", []):
        if not h.get("name") or not h.get("governorate"):
            errors.append(f"hospitals.json: incomplete entry {h}")
    seen = set()
    for i, st in enumerate((status_file or {}).get("statements", [])):
        where = f"hospital-status.json #{i + 1} ({st.get('hospital')})"
        if st.get("hospital") not in names:
            errors.append(f"{where}: not in hospitals.json")
        if st.get("status") not in HOSPITAL_STATUSES:
            errors.append(f"{where}: unknown status {st.get('status')!r}")
        if not st.get("quote") or not st.get("document", {}).get("sha256") or not st.get("document", {}).get("url"):
            errors.append(f"{where}: needs a quote, document url and sha256")
        try:
            if _date(st.get("as_of")) > today:
                errors.append(f"{where}: as_of is in the future")
        except (TypeError, ValueError):
            errors.append(f"{where}: as_of must be YYYY-MM-DD")
        key = (st.get("hospital"), st.get("document", {}).get("sha256"), st.get("quote"))
        if key in seen:
            errors.append(f"{where}: duplicate statement")
        seen.add(key)
    return errors
