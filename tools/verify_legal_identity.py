#!/usr/bin/env python3
"""Reject legal graphs with ambiguous identities or table references."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "graph"
REGULATIONS = ("ow", "bal", "bbl", "bkl", "ob", "or", "iwo")
LEGAL_TYPES = {"article", "chapter", "section", "paragraph", "subparagraph", "appendix", "table"}


def number(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "").strip().lower()).rstrip(".)")


def legal_type(node: dict) -> str:
    # The viewer deliberately resolves a subparagraph as a paragraph too.
    return "paragraph" if node.get("type") == "subparagraph" else str(node.get("type") or "")


def validate_graph(path: Path) -> list[str]:
    graph = json.loads(path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes") or []
    problems: list[str] = []
    ids: dict[str, int] = {}
    keys: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for position, node in enumerate(nodes):
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            problems.append(f"node zonder interne id op positie {position}")
        elif node_id in ids:
            problems.append(f"dubbele interne id {node_id!r} op posities {ids[node_id]} en {position}")
        else:
            ids[node_id] = position
        kind = legal_type(node)
        no = number(node.get("number_display") or node.get("number"))
        if kind in LEGAL_TYPES and no:
            keys[(kind, no)].append(node)
    for (kind, no), entries in sorted(keys.items()):
        if len(entries) > 1:
            labels = ", ".join(str(item.get("id") or "?") for item in entries)
            problems.append(f"dubbele juridische sleutel {kind}:{no} ({labels})")
    for issue in graph.get("validation_issues") or []:
        if str(issue.get("kind") or "") == "ambiguous_table_reference":
            problems.append(
                f"dubbelzinnige tabelverwijzing {issue.get('source_article') or '?'} -> "
                f"{issue.get('target') or '?'} ({issue.get('reason') or 'onbekende oorzaak'})"
            )
    return problems


def main() -> int:
    failures: list[str] = []
    checked = 0
    for stem in REGULATIONS:
        path = GRAPH / f"{stem}_legal_graph.json"
        if not path.exists():
            failures.append(f"{stem}: graph ontbreekt")
            continue
        checked += 1
        failures.extend(f"{stem}: {problem}" for problem in validate_graph(path))
    if failures:
        print("Identiteitscontrole van juridische grafen is mislukt:", file=sys.stderr)
        print(*[f"- {failure}" for failure in failures], sep="\n", file=sys.stderr)
        return 1
    print(f"Juridische identiteiten en tabelverwijzingen zijn eenduidig gecontroleerd in {checked} regelingen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
