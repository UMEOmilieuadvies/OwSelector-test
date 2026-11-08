#!/usr/bin/env python3
"""Maak een transparant inzichtsrapport uit menselijke beoordelingsredenen.

Dit hulpmiddel wijzigt geen zoekregels en keurt niets automatisch goed. Het
maakt alleen patronen zichtbaar waarop later een expliciet verbeterbesluit kan
worden gebaseerd.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from jurisprudence_review import REVIEW_REASONS, REVIEW_STATUSES, references


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"candidates": []}


def main() -> None:
    parser = argparse.ArgumentParser(description="Maak inzicht uit menselijke jurisprudentiebeoordelingen.")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = load(args.candidates)
    links = [
        (candidate, match, article)
        for candidate in data.get("candidates", [])
        for match, article in references(candidate)
    ]
    statuses = Counter(article.get("review_status", "te_beoordelen") for _, _, article in links)
    reasons = Counter(
        article.get("review_reason", "")
        for _, _, article in links
        if article.get("review_reason", "")
    )
    by_regulation: dict[str, Counter] = defaultdict(Counter)
    for _, match, article in links:
        if article.get("review_reason"):
            by_regulation[match.get("regulation", "onbekend")][article["review_reason"]] += 1

    lines = [
        "# Inzichten uit jurisprudentiebeoordelingen",
        "",
        f"Bijgewerkt: **{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}**.",
        "",
        "Dit rapport beschrijft uitsluitend menselijke beoordelingen. Het past geen zoekregels aan en publiceert geen jurisprudentie.",
        "",
        "## Stand van beoordeling",
        "",
        *[f"- {status}: **{statuses[status]}**" for status in REVIEW_STATUSES],
        "",
        "## Redenen bij beoordelingen",
        "",
    ]
    if reasons:
        for reason, amount in reasons.most_common():
            description = REVIEW_REASONS.get(reason, "Vrije of nog onbekende reden.")
            lines.append(f"- `{reason}`: **{amount}** — {description}")
    else:
        lines.append("Nog geen beoordelingsredenen vastgelegd.")
    lines.extend(["", "## Patronen per regeling", ""])
    if by_regulation:
        for regulation in sorted(by_regulation):
            values = ", ".join(f"`{reason}`: {amount}" for reason, amount in by_regulation[regulation].most_common())
            lines.append(f"- **{regulation}** — {values}")
    else:
        lines.append("Nog geen patronen beschikbaar.")
    lines.extend([
        "",
        "## Gebruik van dit rapport",
        "",
        "Gebruik terugkerende afwijzingsredenen als aanleiding voor een voorstel tot verfijning. Pas de zoekregel pas aan na expliciete beoordeling en test; een patroon is geen automatische beslisregel.",
        "",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Inzichtsrapport gemaakt: {args.output} ({len(links)} artikelkoppelingen).")


if __name__ == "__main__":
    main()
