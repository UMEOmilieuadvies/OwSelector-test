#!/usr/bin/env python3
"""Controleer dat herkenbare EU-verwijzingen één precies extern doel hebben."""
from __future__ import annotations

import json
from pathlib import Path

from eu_references import plain_eu_refs

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "graph"


def main() -> None:
    checked = 0
    problems: list[str] = []
    for path in sorted(GRAPH.glob("*_legal_graph.json")):
        graph = json.loads(path.read_text(encoding="utf-8"))
        for node in graph.get("nodes", []):
            wanted = {(ref["anchor"].casefold(), ref["doc"]) for ref in plain_eu_refs(node.get("text", ""))}
            generated = {
                (str(ref.get("anchor", "")).casefold(), str(ref.get("doc", "")))
                for ref in node.get("external_refs", [])
                if ref.get("source") == "plain_eu_name"
            }
            checked += len(wanted)
            if wanted != generated:
                missing = wanted - generated
                extra = generated - wanted
                if missing:
                    problems.append(f"{path.name} {node.get('id')}: ontbreekt {next(iter(missing))[0]}")
                if extra:
                    problems.append(f"{path.name} {node.get('id')}: overlappende of overbodige link {next(iter(extra))[0]}")
    if problems:
        raise SystemExit("FOUTE EU-VERWIJZINGEN:\n" + "\n".join(problems[:30]))
    print(f"EU-verwijzingen gecontroleerd: {checked}; alle herkenbare verwijzingen zijn volledig en niet-overlappend.")


if __name__ == "__main__":
    main()