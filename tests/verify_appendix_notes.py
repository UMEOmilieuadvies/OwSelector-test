#!/usr/bin/env python3
"""Controleer dat bijlagen voor alle regelingen een veilige NVT-index krijgen."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / "data" / "article_notes.json").read_text(encoding="utf-8"))["regulations"]
index = json.loads((ROOT / "data" / "appendix_notes_index.json").read_text(encoding="utf-8"))["regulations"]

for regulation in ("OW", "BAL", "BBL", "BKL", "OB", "OR", "IWO"):
    assert regulation in records, f"{regulation} ontbreekt in de toelichtingsgegevens."
    assert regulation in index, f"{regulation} ontbreekt in de bijlage-index."
    appendices = records[regulation].get("appendices", {})
    assert set(appendices) == set(index[regulation]), f"{regulation}: index en bijlagerecords wijken af."
    for key, record in appendices.items():
        assert index[regulation][key] == bool(record.get("notes")), f"{regulation} {key}: knopindex klopt niet."

assert index["BAL"].get("i"), "BAL Bijlage I mist een officiële toelichting."
assert index["BKL"].get("vii"), "BKL Bijlage VII mist een officiële toelichting."
assert not index["OR"].get("i"), "OR Bijlage I mag zonder officiële bijlagekop geen schijntoelichting krijgen."
print("Bijlage-NVT-index is volledig, brongebonden en consistent.")
