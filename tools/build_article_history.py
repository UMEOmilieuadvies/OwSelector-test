#!/usr/bin/env python3
"""Build a compact, cached index of official article change records from wetten.nl.

The index contains metadata only: no historic statutory text is copied.  A record is
refreshed only when the article's legal graph subtree changed.  The first run builds
the cache once; later runs keep unchanged records from the previously published file.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
import threading
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
GRAPH = DATA / "graph"
OUT = DATA / "article_history.json"
VERSION_FILE = DATA / "regulation_versions.json"
REGS = {
    "OW": ("BWBR0037885", "ow_legal_graph.json"),
    "BAL": ("BWBR0041330", "bal_legal_graph.json"),
    "BBL": ("BWBR0041297", "bbl_legal_graph.json"),
    "BKL": ("BWBR0041313", "bkl_legal_graph.json"),
    "OB": ("BWBR0041278", "ob_legal_graph.json"),
    "OR": ("BWBR0045528", "or_legal_graph.json"),
}
USER_AGENT = "Omgevingswet-Zoeker-history/1.0 (public statutory metadata index)"
_request_lock = threading.Lock()
_last_request = 0.0
REQUEST_INTERVAL = 0.20  # At most five requests a second across all workers.


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


class ChangeTableParser(HTMLParser):
    """Read the table in Wetten.nl's article-specific wijzigingenoverzicht."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_overview = False
        self.in_row = False
        self.current_key = ""
        self.current_parts: list[str] = []
        self.current_href = ""
        self.row: dict[str, str] = {}
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and attrs.get("id") == "tab-wijzigingenoverzicht":
            self.in_overview = True
        if not self.in_overview:
            return
        if tag == "tr":
            self.in_row = True
            self.row = {}
        elif self.in_row and tag == "td":
            self.current_key = clean(attrs.get("data-before", "")).lower()
            self.current_parts = []
            self.current_href = ""
        elif self.in_row and tag == "a" and self.current_key and attrs.get("href"):
            self.current_href = attrs["href"]

    def handle_data(self, data):
        if self.in_overview and self.in_row and self.current_key:
            self.current_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.in_row and self.current_key:
            value = clean("".join(self.current_parts))
            if value:
                self.row[self.current_key] = value
            if self.current_href:
                self.row[f"{self.current_key}_url"] = self.current_href
            self.current_key = ""
            self.current_parts = []
            self.current_href = ""
        elif tag == "tr" and self.in_row:
            if self.row:
                self.rows.append(self.row)
            self.in_row = False
        elif tag == "div" and self.in_overview:
            # The overview is one self-contained panel; subsequent divs are irrelevant.
            self.in_overview = False


def official_url(bwb: str, version_date: str, article: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", version_date or ""):
        return f"https://wetten.overheid.nl/{bwb}/{version_date}/0/Artikel{article}/informatie"
    return f"https://wetten.overheid.nl/{bwb}/informatie"


def fetch(url: str) -> str:
    global _last_request
    with _request_lock:
        delay = REQUEST_INTERVAL - (time.monotonic() - _last_request)
        if delay > 0:
            time.sleep(delay)
        _last_request = time.monotonic()
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(request, timeout=35) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_history(html: str, url: str) -> list[dict[str, str]]:
    parser = ChangeTableParser()
    parser.feed(html)
    records = []
    seen = set()
    for row in parser.rows:
        item = {
            "effective_date": row.get("datum van inwerkingtreding", ""),
            "subject": row.get("betreft", ""),
            "signed_date": row.get("ondertekening", ""),
            "published_date": row.get("bekendmaking", ""),
            "source": row.get("bekendmaking", ""),
            "source_url": row.get("bekendmaking_url", ""),
        }
        key = tuple(item.values())
        if key not in seen and (item["effective_date"] or item["subject"] or item["source"]):
            seen.add(key)
            records.append(item)
    return records


def article_fingerprints(graph: dict) -> dict[str, str]:
    nodes = {str(node.get("id")): node for node in graph.get("nodes", [])}
    memo: dict[str, str] = {}
    def fingerprint(node_id: str) -> str:
        if node_id in memo:
            return memo[node_id]
        node = nodes.get(node_id, {})
        content = {
            "number": node.get("number_display", node.get("number", "")),
            "title": node.get("title", ""), "text": node.get("text", ""),
            "children": [fingerprint(str(child)) for child in node.get("children", [])],
        }
        memo[node_id] = hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        return memo[node_id]
    out = {}
    for node_id, node in nodes.items():
        if str(node.get("type", "")).lower() == "article":
            number = clean(str(node.get("number_display", node.get("number", "")))).lower()
            if number:
                out[number] = fingerprint(node_id)
    return out


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parse-file", type=Path, help="test only: parse one saved official HTML page")
    args = parser.parse_args()
    if args.parse_file:
        print(json.dumps(parse_history(args.parse_file.read_text(encoding="utf-8"), ""), ensure_ascii=False, indent=2))
        return 0

    versions = load_json(VERSION_FILE, {}).get("regulations", {})
    cached = load_json(OUT, {}).get("articles", {})
    candidates: list[tuple[str, str, str, str, str]] = []
    result = dict(cached)
    for reg, (bwb, filename) in REGS.items():
        graph = load_json(GRAPH / filename, {})
        for article, fingerprint in article_fingerprints(graph).items():
            key = f"{reg}:{article}"
            old = cached.get(key, {})
            if old.get("fingerprint") == fingerprint and old.get("official_url"):
                continue
            date = str(versions.get(reg, {}).get("official_version_date", ""))
            candidates.append((key, reg, bwb, date, article))
            result.pop(key, None)

    print(f"Artikelhistorie: {len(candidates)} nieuwe of gewijzigde artikelen; {len(result)} uit cache.", flush=True)
    fingerprints = {key: article_fingerprints(load_json(GRAPH / REGS[reg][1], {})).get(article, "") for key, reg, _, _, article in candidates}
    def build(item):
        key, reg, bwb, date, article = item
        url = official_url(bwb, date, article)
        try:
            entries = parse_history(fetch(url), url)
            modifications = sum(1 for entry in entries if "nieuwe-regeling" not in entry.get("subject", "").lower())
            return key, {"regulation": reg, "article": article, "fingerprint": fingerprints[key], "official_url": url, "modification_count": modifications, "entries": entries}, None
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            return key, None, str(error)

    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for key, record, error in pool.map(build, candidates):
            if record:
                result[key] = record
            else:
                errors.append(f"{key}: {error}")
    payload = {"schema_version": 1, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "articles": dict(sorted(result.items()))}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Artikelhistorie geschreven: {len(result)} artikelen, {len(errors)} fouten.", flush=True)
    if errors:
        print("Eerste fouten: " + " | ".join(errors[:5]), file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
