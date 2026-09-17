"""Bouw een omgekeerde index van officiële verwijzingen tussen de zes regelingen."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "graph"
OUTPUT = ROOT / "data" / "back_references.json"
REGULATIONS = {
    "BWBR0037885": "OW", "BWBR0041330": "BAL", "BWBR0041297": "BBL",
    "BWBR0041313": "BKL", "BWBR0041278": "OB", "BWBR0045528": "OR",
}
FILES = {"OW": "ow", "BAL": "bal", "BBL": "bbl", "BKL": "bkl", "OB": "ob", "OR": "or"}


def number(node: dict) -> str:
    return str(node.get("number_display") or node.get("number") or "").strip().lower()


def label(node: dict) -> str:
    title = str(node.get("title") or "").strip()
    return f"Artikel {number(node)} {title}".strip()


def article_for(node: dict, by_id: dict[str, dict]) -> dict | None:
    current = node
    seen: set[str] = set()
    while current and str(current.get("id")) not in seen:
        seen.add(str(current.get("id")))
        if current.get("type") == "article":
            return current
        current = by_id.get(str(current.get("parent") or ""))
    return None


def main() -> None:
    graphs: dict[str, list[dict]] = {}
    targets: dict[tuple[str, str], dict] = {}
    for reg, stem in FILES.items():
        path = GRAPH / f"{stem}_legal_graph.json"
        if not path.exists():
            raise SystemExit(f"Graph ontbreekt: {path}")
        nodes = json.loads(path.read_text(encoding="utf-8")).get("nodes", [])
        graphs[reg] = nodes
        for node in nodes:
            if node.get("type") == "article" and number(node):
                targets[(reg, number(node))] = node

    found: dict[str, list[dict]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for source_reg, nodes in graphs.items():
        by_id = {str(node.get("id")): node for node in nodes}
        for node in nodes:
            source_article = article_for(node, by_id)
            if not source_article:
                continue
            for ref in node.get("external_refs") or []:
                target_reg = REGULATIONS.get(str(ref.get("bwb_id") or "").upper())
                target = ref.get("target") or {}
                target_number = str(target.get("number") or "").strip().lower()
                if not target_reg or target.get("type") != "article" or not target_number:
                    continue
                target_article = targets.get((target_reg, target_number))
                if not target_article:
                    continue
                key = f"{target_reg}:{target_article['id']}"
                unique = (key, source_reg, str(source_article["id"]))
                if unique in seen:
                    continue
                seen.add(unique)
                found[key].append({
                    "regulation": source_reg,
                    "article_id": str(source_article["id"]),
                    "label": label(source_article),
                    "anchor": str(ref.get("anchor") or "").strip(),
                })

    for rows in found.values():
        rows.sort(key=lambda row: (row["regulation"], row["label"].casefold()))
    payload = {"references": found, "count": sum(len(rows) for rows in found.values())}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Terugverwijzingen: {payload['count']} naar {len(found)} artikelen.")


if __name__ == "__main__":
    main()
