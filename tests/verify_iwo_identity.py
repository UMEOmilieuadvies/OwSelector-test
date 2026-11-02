#!/usr/bin/env python3
"""Controleer dat de Invoeringswet haar eigen officiële BWB-identiteit houdt."""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source" / "invoeringswet_omgevingswet.xml"
GRAPH = ROOT / "data" / "graph" / "iwo_legal_graph.json"
EXPECTED = "BWBR0043660"

def fail(message: str) -> None:
    print(f"FOUT Invoeringswet-identiteit: {message}")
    raise SystemExit(1)

if not SOURCE.exists():
    fail("bron-XML ontbreekt")
if not GRAPH.exists():
    fail("juridische graaf ontbreekt")

try:
    root = ET.parse(SOURCE).getroot()
except ET.ParseError as error:
    fail(f"bron-XML is ongeldig: {error}")

if root.get("bwb-id") != EXPECTED:
    fail(f"bron-XML heeft {root.get('bwb-id')!r}; verwacht {EXPECTED}")

try:
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as error:
    fail(f"juridische graaf is onleesbaar: {error}")

if graph.get("bwb_id") != EXPECTED:
    fail(f"graaf heeft {graph.get('bwb_id')!r}; verwacht {EXPECTED}")

print("Invoeringswet-identiteit gecontroleerd: BWBR0043660.")
