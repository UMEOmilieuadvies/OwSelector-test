"""Controleer dat bijlagekoppen met artikelen als terugverwijzing landen."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from appendix_references import article_numbers_from_appendix_title

references = json.loads((ROOT / "data" / "back_references.json").read_text(encoding="utf-8"))["references"]
checked = 0
for graph_path in sorted((ROOT / "data" / "graph").glob("*_legal_graph.json")):
    regulation = graph_path.name.split("_")[0].upper()
    nodes = json.loads(graph_path.read_text(encoding="utf-8"))["nodes"]
    articles = {str(node.get("number_display") or node.get("number") or "").lower(): node for node in nodes if node.get("type") == "article"}
    for appendix in (node for node in nodes if node.get("type") == "appendix"):
        for number in article_numbers_from_appendix_title(str(appendix.get("title") or "")):
            target = articles.get(number)
            if not target:
                continue
            checked += 1
            rows = references.get(f"{regulation}:{target['id']}", [])
            assert any(str(row.get("source_id")) == str(appendix["id"]) for row in rows), (
                f"{regulation} Bijlage {appendix.get('number')} -> artikel {number} ontbreekt in terugverwijzingen."
            )

assert checked > 0, "Geen bijlagekopverwijzingen gevonden; de proef kan niets controleren."
print(f"Bijlagekopverwijzingen gecontroleerd: {checked} artikelkoppelingen.")
