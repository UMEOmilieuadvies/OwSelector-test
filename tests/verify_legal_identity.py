#!/usr/bin/env python3
"""Regression tests for the legal graph identity gate."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "verify_legal_identity.py"
SPEC = importlib.util.spec_from_file_location("verify_legal_identity", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def problems(nodes, issues=None):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "graph.json"
        path.write_text(json.dumps({"nodes": nodes, "validation_issues": issues or []}), encoding="utf-8")
        return MODULE.validate_graph(path)


assert not problems([{"id": "a", "type": "article", "number": "1.2"}])
assert any("dubbele interne id" in item for item in problems([
    {"id": "a", "type": "article", "number": "1.2"},
    {"id": "a", "type": "article", "number": "1.3"},
]))
assert any("dubbele juridische sleutel" in item for item in problems([
    {"id": "a", "type": "article", "number": "1.2"},
    {"id": "b", "type": "article", "number": "1.2"},
]))
assert any("dubbele juridische sleutel" in item for item in problems([
    {"id": "a", "type": "paragraph", "number": "1.2"},
    {"id": "b", "type": "subparagraph", "number": "1.2"},
]))
assert any("dubbelzinnige tabelverwijzing" in item for item in problems(
    [{"id": "a", "type": "article", "number": "1.2"}],
    [{"kind": "ambiguous_table_reference", "source_article": "a", "target": "1.2", "reason": "2 kandidaten"}],
))
print("Identiteitscontrole herkent dubbele sleutels en dubbelzinnige tabellen.")
