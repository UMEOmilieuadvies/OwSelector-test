#!/usr/bin/env python3
"""Maak een dekkingsrapport voor een afgebakende jurisprudentieverzameling.

Het rapport is uitsluitend voor de beoordelingsstroom. Het keurt niets goed
en schrijft nooit gegevens naar de openbare jurisprudentie-index.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from collect_jurisprudence_candidates import REGULATIONS
from jurisprudence_review import references


def load(path: Path, fallback: dict) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def main() -> None:
    parser = argparse.ArgumentParser(description="Maak dekkingsoverzicht voor jurisprudentiekandidaten.")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--to-date", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidates = load(args.candidates, {"candidates": []}).get("candidates", [])
    state = load(args.state, {"runs": {}})
    subject = "http://psi.rechtspraak.nl/rechtsgebied#bestuursrecht_omgevingsrecht"
    run_key = f"{args.from_date}..{args.to_date}::{subject}"
    run = state.get("runs", {}).get(run_key, {})

    eclis = defaultdict(set)
    links = Counter()
    for candidate in candidates:
        for match, _article in references(candidate):
            regulation = match.get("regulation")
            if regulation in REGULATIONS:
                eclis[regulation].add(candidate.get("ecli", ""))
                links[regulation] += 1

    completed = bool(run.get("completed"))
    status = "voltooid" if completed else "nog in uitvoering; volgende batch hervat vanaf indexpositie " + str(run.get("next_offset", 0))
    lines = [
        "# Dekkingsrapport jurisprudentiekandidaten",
        "",
        f"Periode: **{args.from_date} t/m {args.to_date}**.",
        "Bronselectie: Rechtspraak Open Data, rechtsgebied omgevingsrecht.",
        "",
        f"Verzamelstand: **{status}**.",
        f"Verwerkte uitspraken in deze run: **{len(run.get('processed_eclis', []))}**.",
        "",
        "Deze aantallen zijn kandidaten op grond van een regeling en artikel in dezelfde tekstpassage. Zij zijn nog niet inhoudelijk beoordeeld en verschijnen niet in de zoeker.",
        "",
        "| Regeling | Uitspraken met kandidaat | Te beoordelen artikelkoppelingen |",
        "| --- | ---: | ---: |",
    ]
    for code, (name, _aliases) in REGULATIONS.items():
        lines.append(f"| {name} ({code}) | {len(eclis[code])} | {links[code]} |")
    lines.extend([
        "",
        "## Vervolg",
        "",
        "Start dezelfde workflow opnieuw met dezelfde periode om de volgende batch te verwerken. De voortgang wordt op deze beoordelingsbranch bewaard; reeds verwerkte ECLI's worden niet opnieuw opgehaald.",
        "",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Dekkingsrapport gemaakt: {args.output} ({len(candidates)} kandidaten).")


if __name__ == "__main__":
    main()
