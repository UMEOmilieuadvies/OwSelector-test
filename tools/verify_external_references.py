#!/usr/bin/env python3
"""Controleer dat herkenbare EU-verwijzingen een precies extern doel hebben."""
from __future__ import annotations

import json
from pathlib import Path

from eu_references import plain_eu_refs

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "graph"


def main() -> None:
    checked = 0
    missing: list[str] = []
    for path in sorted(GRAPH.glob("*_legal_graph.json")):
        graph = json.loads(path.read_text(encoding="utf-8"))
        for node in graph.get("nodes", []):
            wanted = plain_eu_refs(node.get("text", ""))
            actual = {(str(ref.get("anchor", "")).casefold(), str(ref.get("doc", "")))
                      for ref in node.get("external_refs", [])}
            for ref in wanted:
                checked += 1
                pair = (ref["anchor"].casefold(), ref["doc"])
                if pair not in actual:
                    missing.append(f"{path.name} {node.get('id')}: {ref['anchor']}")
    if missing:
        raise SystemExit("ONTBREKENDE EU-VERWIJZINGEN:\n" + "\n".join(missing[:20]))
    print(f"EU-verwijzingen gecontroleerd: {checked}; alle herkenbare verwijzingen hebben een CELEX-doel.")


if __name__ == "__main__":
    main()
