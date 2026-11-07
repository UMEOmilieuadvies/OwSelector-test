#!/usr/bin/env python3
"""Haal begrensd kandidaten voor jurisprudentiekoppelingen op.

Dit hulpmiddel publiceert niets. Het schrijft uitsluitend een lokaal
beoordelingsbestand naar data/jurisprudence_candidates.json. Een kandidaat
wordt pas zichtbaar in de zoeker nadat die handmatig in
data/jurisprudence.json is gecontroleerd en opgenomen.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "jurisprudence_candidates.json"
INDEX_URL = "https://data.rechtspraak.nl/uitspraken/zoeken"
CONTENT_URL = "https://data.rechtspraak.nl/uitspraken/content"
REGULATIONS = {
    "OW": ("Omgevingswet", ("omgevingswet",)),
    "BAL": ("Besluit activiteiten leefomgeving (BAL)", ("besluit activiteiten leefomgeving", "bal")),
    "BBL": ("Besluit bouwwerken leefomgeving (BBL)", ("besluit bouwwerken leefomgeving", "bbl")),
    "BKL": ("Besluit kwaliteit leefomgeving (BKL)", ("besluit kwaliteit leefomgeving", "bkl")),
    "OB": ("Omgevingsbesluit (OB)", ("omgevingsbesluit", "ob")),
    "OR": ("Omgevingsregeling (OR)", ("omgevingsregeling", "or")),
    "IWO": ("Invoeringswet Omgevingswet (IWO)", ("invoeringswet omgevingswet", "iwo")),
}
ARTICLE = re.compile(r"\bartikel(?:en)?\s+([0-9]+(?:\.[0-9]+)+[a-z]?)\b", re.I)
NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "OwSelector-test/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def eclis(since: str, maximum: int) -> list[str]:
    query = urllib.parse.urlencode({"modified": since, "return": "DOC", "max": maximum, "sort": "DESC"})
    root = ET.fromstring(fetch(f"{INDEX_URL}?{query}"))
    return [entry.findtext("atom:id", default="").strip() for entry in root.findall("atom:entry", NS) if entry.findtext("atom:id", default="").startswith("ECLI:")]


def text_for(ecli: str) -> str:
    query = urllib.parse.urlencode({"id": ecli})
    root = ET.fromstring(fetch(f"{CONTENT_URL}?{query}"))
    return " ".join(" ".join(root.itertext()).split())


def candidates(ecli: str, text: str) -> list[dict]:
    lowered = text.lower()
    rows = []
    for regulation, (name, aliases) in REGULATIONS.items():
        if not any(re.search(rf"\b{re.escape(alias)}\b", lowered) for alias in aliases):
            continue
        articles = sorted(set(match.group(1) for match in ARTICLE.finditer(text)))
        if articles:
            rows.append({"regulation": regulation, "name": name, "articles": articles})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Maak lokale kandidaten voor handmatige jurisprudentiebeoordeling.")
    parser.add_argument("--since", required=True, help="Wijzigingen vanaf datum/tijd, bijvoorbeeld 2026-01-01T00:00:00")
    parser.add_argument("--max-eclis", type=int, default=100, choices=range(1, 501), metavar="1..500")
    parser.add_argument("--requests-per-second", type=float, default=5.0)
    args = parser.parse_args()
    pause = 1 / max(1.0, min(args.requests_per_second, 8.0))
    rows = []
    for number, ecli in enumerate(eclis(args.since, args.max_eclis), start=1):
        if number > 1:
            time.sleep(pause)
        try:
            found = candidates(ecli, text_for(ecli))
        except Exception as error:  # Een individuele publicatie mag de beoordeling niet stoppen.
            print(f"Overgeslagen {ecli}: {error}")
            continue
        if found:
            rows.append({
                "ecli": ecli,
                "official_url": "https://uitspraken.rechtspraak.nl/details?id=" + urllib.parse.quote(ecli, safe=""),
                "matches": found,
                "review_status": "te_beoordelen",
            })
    document = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Rechtspraak Open Data",
        "notice": "Dit zijn kandidaten. Zij worden niet in de zoeker getoond voordat een inhoudelijke controle is vastgelegd.",
        "candidates": rows,
    }
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(rows)} kandidaten geschreven naar {OUT}")


if __name__ == "__main__":
    main()
