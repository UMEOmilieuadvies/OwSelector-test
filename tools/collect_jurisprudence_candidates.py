#!/usr/bin/env python3
"""Verzamel hervatbaar jurisprudentiekandidaten voor de Omgevingswet Zoeker.

De Rechtspraak Open Data-service levert eerst ECLI's en daarna één uitspraak
per ECLI. Dit programma werkt daarom in begrensde batches. Het publiceert
niets: alleen kandidaten met een bronverwijzing en tekstcontext komen lokaal
in data/jurisprudence_candidates.json terecht. Zichtbare koppelingen blijven
handmatig gecontroleerd in data/jurisprudence.json.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "jurisprudence_candidates.json"
STATE = ROOT / "data" / "jurisprudence_collection_state.json"
INDEX_URL = "https://data.rechtspraak.nl/uitspraken/zoeken"
CONTENT_URL = "https://data.rechtspraak.nl/uitspraken/content"
NS = {"atom": "http://www.w3.org/2005/Atom"}
ARTICLE = re.compile(r"\bartikel(?:en)?\s+([0-9]+(?:\.[0-9]+)+[a-z]?)\b", re.I)
ENVIRONMENT_SUBJECT = "http://psi.rechtspraak.nl/rechtsgebied#bestuursrecht_omgevingsrecht"

# Alleen duidelijke, regelinggebonden benamingen. 'de wet' of een los
# artikelnummer is te onbepaald en wordt nooit automatisch gekoppeld.
REGULATIONS = {
    "OW": ("Omgevingswet", (r"\bOmgevingswet\b",)),
    "BAL": ("Besluit activiteiten leefomgeving (BAL)", (r"\bBesluit activiteiten leefomgeving\b", r"\bBAL\b")),
    "BBL": ("Besluit bouwwerken leefomgeving (BBL)", (r"\bBesluit bouwwerken leefomgeving\b", r"\bBBL\b")),
    "BKL": ("Besluit kwaliteit leefomgeving (BKL)", (r"\bBesluit kwaliteit leefomgeving\b", r"\bBKL\b")),
    "OB": ("Omgevingsbesluit (OB)", (r"\bOmgevingsbesluit\b", r"\bOB\b")),
    "OR": ("Omgevingsregeling (OR)", (r"\bOmgevingsregeling\b", r"\bOR\b")),
    "IWO": ("Invoeringswet Omgevingswet", (r"\bInvoeringswet Omgevingswet\b", r"\bIWO\b")),
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "OwSelector-test/1.0 (jurisprudence candidate collection)"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def load_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def index_page(start_date: str, end_date: str, offset: int, page_size: int, subject: str | None) -> list[str]:
    query = urllib.parse.urlencode([
        ("date", start_date), ("date", end_date), ("return", "DOC"),
        ("max", str(page_size)), ("from", str(offset)), ("sort", "ASC"),
    ] + ([("subject", subject)] if subject else []))
    root = ET.fromstring(fetch(f"{INDEX_URL}?{query}"))
    return [
        entry.findtext("atom:id", default="", namespaces=NS).strip()
        for entry in root.findall("atom:entry", NS)
        if entry.findtext("atom:id", default="", namespaces=NS).startswith("ECLI:")
    ]


def text_for(ecli: str) -> str:
    root = ET.fromstring(fetch(f"{CONTENT_URL}?{urllib.parse.urlencode({'id': ecli})}"))
    return " ".join(" ".join(root.itertext()).split())


def excerpt(text: str, centre: int, length: int = 360) -> str:
    start = max(0, centre - length // 2)
    end = min(len(text), centre + length // 2)
    return ("…" if start else "") + text[start:end].strip() + ("…" if end < len(text) else "")


def matches_for(text: str) -> list[dict]:
    found: list[dict] = []
    for regulation, (name, aliases) in REGULATIONS.items():
        articles: dict[str, str] = {}
        for alias in aliases:
            for mention in re.finditer(alias, text, re.I):
                # Een koppeling is alleen kandidaat als artikel en regeling in
                # dezelfde passage voorkomen. Dat voorkomt brede schijnhits.
                window_start = max(0, mention.start() - 900)
                window_end = min(len(text), mention.end() + 900)
                window = text[window_start:window_end]
                for article in ARTICLE.finditer(window):
                    articles.setdefault(article.group(1), excerpt(text, window_start + article.start()))
        if articles:
            found.append({
                "regulation": regulation,
                "name": name,
                "articles": [
                    {
                        "article": article,
                        "context": context,
                        # Een uitspraak kan meerdere artikelen en regelingen
                        # raken. Elke koppeling wordt dus afzonderlijk
                        # beoordeeld en gemeld.
                        "review_status": "te_beoordelen",
                        "review_reason": "",
                        "review_note": "",
                    }
                    for article, context in sorted(articles.items())
                ],
                "match_rule": "regeling en artikel in dezelfde tekstpassage",
            })
    return found


def candidate(ecli: str, text: str) -> dict | None:
    matches = matches_for(text)
    if not matches:
        return None
    return {
        "ecli": ecli,
        "official_url": "https://uitspraken.rechtspraak.nl/details?id=" + urllib.parse.quote(ecli, safe=""),
        "matches": matches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verzamel hervatbare kandidaten voor handmatige jurisprudentiebeoordeling.")
    parser.add_argument("--from-date", required=True, help="Begindatum uitspraak, bijvoorbeeld 2024-01-01")
    parser.add_argument("--to-date", default=date.today().isoformat(), help="Einddatum uitspraak, bijvoorbeeld 2024-12-31; standaard vandaag")
    parser.add_argument("--max-eclis", type=int, default=200, choices=range(1, 501), metavar="1..500")
    parser.add_argument("--page-size", type=int, default=100, choices=range(1, 1001), metavar="1..1000")
    parser.add_argument("--requests-per-second", type=float, default=4.0, help="Maximaal 8; standaard bewust 4")
    parser.add_argument("--all-rechtsgebieden", action="store_true", help="Verwerk ook uitspraken buiten het rechtsgebied omgevingsrecht.")
    parser.add_argument("--output", type=Path, default=OUT, help="Bestand voor kandidaten; standaard de lokale, genegeerde werkuitvoer.")
    parser.add_argument("--state", type=Path, default=STATE, help="Bestand voor hervatbare voortgang; standaard de lokale, genegeerde werkuitvoer.")
    args = parser.parse_args()
    subject = None if args.all_rechtsgebieden else ENVIRONMENT_SUBJECT
    pause = 1 / max(1.0, min(args.requests_per_second, 8.0))
    state = load_json(args.state, {"runs": {}})
    run_key = f"{args.from_date}..{args.to_date}::{subject or 'alle-rechtsgebieden'}"
    run = state.setdefault("runs", {}).setdefault(run_key, {"processed_eclis": [], "next_offset": 0})
    run["completed"] = False
    processed = set(run.get("processed_eclis", []))
    existing = load_json(args.output, {"candidates": []})
    known = {row.get("ecli") for row in existing.get("candidates", [])}
    offset = int(run.get("next_offset", 0))
    handled = 0

    while handled < args.max_eclis:
        ids = index_page(args.from_date, args.to_date, offset, min(args.page_size, args.max_eclis - handled), subject)
        if not ids:
            run["completed"] = True
            break
        offset += len(ids)
        for ecli in ids:
            if ecli in processed:
                continue
            time.sleep(pause)
            try:
                row = candidate(ecli, text_for(ecli))
            except Exception as error:
                print(f"Overgeslagen {ecli}: {error}")
                continue
            processed.add(ecli)
            handled += 1
            if row and row["ecli"] not in known:
                existing.setdefault("candidates", []).append(row)
                known.add(row["ecli"])
            if handled >= args.max_eclis:
                break
        if len(ids) < args.page_size:
            run["completed"] = True
            break

    run.update({
        "from_date": args.from_date,
        "to_date": args.to_date,
        "subject": subject or "alle-rechtsgebieden",
        "next_offset": offset,
        "processed_eclis": sorted(processed),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    state["source"] = "Rechtspraak Open Data"
    existing.update({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Rechtspraak Open Data",
        "notice": "Kandidaten zijn niet zichtbaar in de zoeker. Alleen handmatig gecontroleerde koppelingen worden gepubliceerd.",
        "selection_rule": "Alleen regeling en artikel in dezelfde tekstpassage.",
    })
    save_json(args.state, state)
    save_json(args.output, existing)
    print(f"{handled} ECLI's verwerkt; {len(existing.get('candidates', []))} kandidaten lokaal beschikbaar; volgende indexpositie: {offset}.")


if __name__ == "__main__":
    main()
