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


def article_label(node: dict) -> str:
    title = str(node.get("title") or "").strip()
    return f"Artikel {number(node)} {title}".strip()


def parent_of(node: dict, by_id: dict[str, dict]) -> dict | None:
    return by_id.get(str(node.get("parent") or node.get("parent_id") or ""))


def ancestor_of_type(node: dict, by_id: dict[str, dict], kind: str) -> dict | None:
    current = node
    seen: set[str] = set()
    while current and str(current.get("id")) not in seen:
        seen.add(str(current.get("id")))
        if current.get("type") == kind:
            return current
        current = parent_of(current, by_id)
    return None


def source_label(node: dict, by_id: dict[str, dict]) -> str:
    """Geef de inhoudelijke vindplaats weer, ook buiten een artikel."""
    appendix = ancestor_of_type(node, by_id, "appendix")
    if appendix:
        return f"Bijlage {number(appendix).upper()}".strip()
    article = ancestor_of_type(node, by_id, "article")
    if article:
        return article_label(article)
    title = str(node.get("title") or "").strip()
    return title or str(node.get("type") or "Vindplaats").capitalize()


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
    seen: set[tuple[str, str, str, str]] = set()
    for source_reg, nodes in graphs.items():
        by_id = {str(node.get("id")): node for node in nodes}
        for source in nodes:
            source_id = str(source.get("id") or "")
            if not source_id:
                continue
            for ref in source.get("external_refs") or []:
                target_reg = REGULATIONS.get(str(ref.get("bwb_id") or "").upper())
                target = ref.get("target") or {}
                target_number = str(target.get("number") or "").strip().lower()
                if not target_reg or target.get("type") != "article" or not target_number:
                    continue
                target_article = targets.get((target_reg, target_number))
                if not target_article:
                    continue
                key = f"{target_reg}:{target_article['id']}"
                anchor = str(ref.get("anchor") or "").strip()
                unique = (key, source_reg, source_id, anchor)
                if unique in seen:
                    continue
                seen.add(unique)
                found[key].append({
                    "regulation": source_reg,
                    "source_id": source_id,
                    "source_type": str(source.get("type") or ""),
                    "label": source_label(source, by_id),
                    "anchor": anchor,
                })

    for rows in found.values():
        rows.sort(key=lambda row: (row["regulation"], row["label"].casefold(), row["anchor"].casefold()))
    payload = {"references": found, "count": sum(len(rows) for rows in found.values())}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Terugverwijzingen: {payload['count']} naar {len(found)} artikelen.")


if __name__ == "__main__":
    main()
