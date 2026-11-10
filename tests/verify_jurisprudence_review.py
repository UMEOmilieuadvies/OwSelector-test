#!/usr/bin/env python3
"""Controleer beoordeling en e-mailselectie per uitspraak-artikelkoppeling."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "tools" / "build_jurisprudence_review_dossier.py"
INSIGHTS = ROOT / "tools" / "build_jurisprudence_review_insights.py"
COVERAGE = ROOT / "tools" / "build_jurisprudence_coverage.py"


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


with tempfile.TemporaryDirectory() as temporary:
    folder = Path(temporary)
    candidates = folder / "candidates.json"
    dossier = folder / "dossier.md"
    insights = folder / "insights.md"
    coverage = folder / "coverage.md"
    state = folder / "state.json"
    candidates.write_text(json.dumps({"candidates": [{
        "ecli": "ECLI:NL:TEST:2026:1",
        "official_url": "https://uitspraken.rechtspraak.nl/details?id=ECLI%3ANL%3ATEST%3A2026%3A1",
        "matches": [
            {"regulation": "BAL", "name": "BAL", "articles": [
                {"article": "3.1", "context": "BAL artikel 3.1"},
                {"article": "3.2", "context": "BAL artikel 3.2"},
            ]},
            {"regulation": "BKL", "name": "BKL", "articles": [
                {"article": "5.4", "context": "BKL artikel 5.4"},
            ]},
        ],
    }]}), encoding="utf-8")

    run(str(DOSSIER), "--candidates", str(candidates), "--output", str(dossier))
    rendered = dossier.read_text(encoding="utf-8")
    assert "Afzonderlijke artikelkoppelingen: **3**" in rendered
    assert "Te beoordelen koppelingen: **3**" in rendered
    assert rendered.count("artikel 3.1") == 2
    assert rendered.count("artikel 3.2") == 2
    assert rendered.count("artikel 5.4") == 2
    saved = json.loads(candidates.read_text(encoding="utf-8"))
    articles = [article for match in saved["candidates"][0]["matches"] for article in match["articles"]]
    articles[0]["review_status"] = "goedgekeurd"
    articles[0]["review_reason"] = "inhoudelijk_behandeld"
    articles[1]["review_status"] = "afgewezen"
    articles[1]["review_reason"] = "alleen_terloops_genoemd"
    candidates.write_text(json.dumps(saved), encoding="utf-8")
    run(str(INSIGHTS), "--candidates", str(candidates), "--output", str(insights))
    overview = insights.read_text(encoding="utf-8")
    assert "goedgekeurd: **1**" in overview
    assert "`inhoudelijk_behandeld`: **1**" in overview
    assert "`alleen_terloops_genoemd`: **1**" in overview
    state.write_text(json.dumps({"runs": {
        "2024-01-01..2024-12-31::http://psi.rechtspraak.nl/rechtsgebied#bestuursrecht_omgevingsrecht": {
            "processed_eclis": ["ECLI:NL:TEST:2024:1"], "next_offset": 1, "completed": False
        }
    }}), encoding="utf-8")
    run(str(COVERAGE), "--candidates", str(candidates), "--state", str(state),
        "--from-date", "2024-01-01", "--to-date", "2024-12-31", "--output", str(coverage))
    report = coverage.read_text(encoding="utf-8")
    assert "Besluit activiteiten leefomgeving (BAL)" in report
    assert "Besluit kwaliteit leefomgeving (BKL)" in report
    assert "nog in uitvoering" in report

print("Jurisprudentiebeoordeling gebruikt afzonderlijke artikelkoppelingen.")
