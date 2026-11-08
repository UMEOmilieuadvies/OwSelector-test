#!/usr/bin/env python3
"""Maak een leesbaar GitHub-beoordelingsdossier van jurisprudentiekandidaten.

Het dossier bevat uitsluitend nog niet gepubliceerde kandidaten. Een beslissing
wordt door een beoordelaar vastgelegd in het JSON-bestand op de aparte
``jurisprudence-review``-tak; deze tool brengt zelf nooit gegevens naar de
publieke jurisprudentiegegevens.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from jurisprudence_review import REVIEW_REASONS, references


def load(path: Path) -> dict:
    if not path.exists():
        return {"candidates": []}
    return json.loads(path.read_text(encoding="utf-8"))


def bullet_matches(candidate: dict) -> list[str]:
    rows: list[str] = []
    for match in candidate.get("matches", []):
        articles = ", ".join(
            f"artikel {item['article']} (**{item.get('review_status', 'te_beoordelen')}"
            f"{': ' + item['review_reason'] if item.get('review_reason') else ''}**)"
            for item in match.get("articles", [])
        )
        rows.append(f"- **{match['name']}** — {articles}")
        for item in match.get("articles", []):
            rows.append(f"  - Context: {item['context']}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Maak een Markdown-dossier voor GitHub-beoordeling.")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = load(args.candidates)
    candidates = sorted(data.get("candidates", []), key=lambda item: item.get("ecli", ""))
    links = [item for candidate in candidates for item in references(candidate)]
    status_counts = Counter(article.get("review_status", "te_beoordelen") for _, article in links)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Jurisprudentiekandidaten ter beoordeling",
        "",
        f"Bijgewerkt: **{generated}**.",
        "",
        "Dit dossier bevat automatisch gevonden kandidaten uit Rechtspraak Open Data. "
        "Ze zijn **niet zichtbaar in de Omgevingswet Zoeker** en vormen geen juridische duiding.",
        "",
        "## Zo beoordeelt u een kandidaat",
        "",
        "1. Open de officiële uitspraak via de ECLI-link.",
        "2. Controleer of de uitspraak inhoudelijk werkelijk over het genoemde artikel gaat.",
        "3. Wijzig bij het afzonderlijke artikel in `jurisprudence_candidates.json` alleen `review_status` naar `goedgekeurd`, `afgewezen` of `later_bekijken`.",
        "4. Voeg bij een beslissing ook `review_reason` toe; `review_note` is optioneel voor een korte toelichting.",
        "5. Een afzonderlijke, gecontroleerde publicatiestap zet uitsluitend goedgekeurde koppelingen in de zoeker.",
        "",
        "Beschikbare redenen: " + ", ".join(f"`{key}`" for key in REVIEW_REASONS) + ".",
        "",
        "## Overzicht",
        "",
        f"- Uitspraken: **{len(candidates)}**",
        f"- Afzonderlijke artikelkoppelingen: **{len(links)}**",
        f"- Te beoordelen koppelingen: **{status_counts['te_beoordelen']}**",
        f"- Goedgekeurde koppelingen: **{status_counts['goedgekeurd']}**",
        f"- Afgewezen koppelingen: **{status_counts['afgewezen']}**",
        f"- Later te bekijken koppelingen: **{status_counts['later_bekijken']}**",
        "",
    ]
    if not candidates:
        lines.extend(["Er zijn nog geen kandidaten gevonden.", ""])
    for position, item in enumerate(candidates, start=1):
        lines.extend([
            f"## {position}. {item.get('ecli', 'Onbekende ECLI')}",
            "",
            f"[Open de officiële uitspraak]({item.get('official_url', '')})",
            "",
            "Mogelijke koppelingen:",
            *bullet_matches(item),
            "",
        ])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Beoordelingsdossier gemaakt: {args.output} ({len(candidates)} kandidaten).")


if __name__ == "__main__":
    main()
