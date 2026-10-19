"""Shared pieces for importers."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
from requests.utils import requote_uri

from ..archive import USER_AGENT


@dataclass
class Rejected:
    url: str
    reason: str
    detail: str = ""


@dataclass
class Proposal:
    observations: list[dict] = field(default_factory=list)
    rejected: list[Rejected] = field(default_factory=list)
    seen: dict[str, str] = field(default_factory=dict)  # url -> sha256 of the version processed
    notes: list[str] = field(default_factory=list)


def make_id(source: str, metric: str, as_of: str, period_start: str | None = None, dims: dict | None = None) -> str:
    parts = [source, metric, as_of]
    if dims:
        parts += [f"{k}-{v}" for k, v in sorted(dims.items())]
    if period_start and period_start != "2023-10-07":
        parts.append(period_start.replace("-", ""))
    return re.sub(r"[^a-z0-9]+", "-", "-".join(parts).lower()).strip("-")


def discover(entry: dict) -> list[str]:
    """Document URLs for a watchlist entry: listed urls, links found on an index page, ReliefWeb results."""
    urls = list(entry.get("urls", []))
    if entry.get("url"):
        urls.append(entry["url"])
    if entry.get("index_url") and entry.get("link_pattern"):
        html = requests.get(entry["index_url"], timeout=60, headers={"User-Agent": USER_AGENT}).text
        for m in re.finditer(entry["link_pattern"], html):
            # requote_uri escapes the spaces some file names contain and leaves escaped ones alone.
            urls.append(requote_uri(urljoin(entry["index_url"], m.group(0).replace("&amp;", "&"))))
    if entry.get("reliefweb"):
        urls += reliefweb_reports(entry["reliefweb"])
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[: entry.get("max_documents", 20)]


def reliefweb_reports(query: dict) -> list[str]:
    """Recent report URLs from the ReliefWeb API. Needs RELIEFWEB_APPNAME (an approved app name)."""
    appname = os.environ.get("RELIEFWEB_APPNAME")
    if not appname:
        return []
    body = {
        "limit": query.get("limit", 10),
        "sort": ["date.original:desc"],
        "fields": {"include": ["url_alias", "title", "date.original"]},
        "filter": {
            "operator": "AND",
            "conditions": [
                {"field": "primary_country.iso3", "value": "pse"},
                {"field": "source.shortname", "value": query["source"]},
            ],
        },
    }
    resp = requests.post(f"https://api.reliefweb.int/v2/reports?appname={appname}", json=body, timeout=60)
    resp.raise_for_status()
    return [item["fields"]["url_alias"] for item in resp.json().get("data", []) if item["fields"].get("url_alias")]
