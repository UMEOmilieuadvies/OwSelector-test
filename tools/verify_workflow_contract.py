#!/usr/bin/env python3
"""Blokkeer workflowfouten die test- en productiegrenzen doorbreken.

De controle is bewust klein en zonder externe afhankelijkheden. Hij verifieert
de vaste omgevingswaarden, alle lokaal aangeroepen scripts en de daadwerkelijke
ESLint-doelen voordat de tijdrovende bronophaalstappen beginnen.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / ".github" / "workflows" / "pages.yml"
CONFIG = ROOT / "js" / "app-config.js"
CONTRACT = ROOT / "ci" / "environment-contract.json"


def fail(message: str) -> None:
    print(f"FOUT workflowcontract: {message}", file=sys.stderr)
    raise SystemExit(1)


def invoked_scripts(workflow: str) -> set[str]:
    return set(re.findall(r"\b(?:python|node)\s+([A-Za-z0-9_./-]+\.(?:py|mjs))\b", workflow))


def eslint_targets(workflow: str) -> list[str]:
    match = re.search(r"\bnpx\s+eslint\s+([^\n#]+)", workflow)
    if not match:
        fail("de workflow bevat geen ESLint-opdracht")
    return [target for target in match.group(1).split() if not target.startswith("-")]


def has_javascript(directory: Path) -> bool:
    return any(path.suffix in {".js", ".mjs", ".cjs"} for path in directory.rglob("*"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", required=True)
    args = parser.parse_args()
    try:
        profiles = json.loads(CONTRACT.read_text(encoding="utf-8"))
        profile = profiles[args.environment]
    except (OSError, KeyError, json.JSONDecodeError) as error:
        fail(f"omgevingsmanifest is ongeldig of mist {args.environment}: {error}")

    if not PAGES.exists() or not CONFIG.exists():
        fail("pages.yml of js/app-config.js ontbreekt")
    workflow = PAGES.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")

    for required in profile["config_values"]:
        if required not in config:
            fail(f"configuratie mist verplichte omgevingswaarde {required}")
    for required in profile["workflow_values"]:
        if required not in workflow:
            fail(f"workflow mist verplichte omgevingswaarde {required}")
    for forbidden in profile["forbidden_values"]:
        if forbidden in workflow or forbidden in config:
            fail(f"niet-toegestane andere-omgevingswaarde {forbidden} aangetroffen")
    for required in profile["required_files"]:
        if not (ROOT / required).is_file():
            fail(f"verplicht omgevingsbestand ontbreekt: {required}")

    missing = sorted(script for script in invoked_scripts(workflow) if not (ROOT / script).is_file())
    if missing:
        fail("workflow roept ontbrekende scripts aan: " + ", ".join(missing))

    targets = eslint_targets(workflow)
    if targets != profile["eslint_targets"]:
        fail("ESLint-doelen wijken af van het omgevingsmanifest: " + ", ".join(targets))
    for target in targets:
        directory = ROOT / target
        if not directory.is_dir():
            fail(f"ESLint-doel bestaat niet: {target}")
        if not has_javascript(directory):
            fail(f"ESLint-doel bevat geen JavaScript: {target}")

    print(f"Workflowcontract voor {args.environment} is gecontroleerd: omgeving, scripts en lintdoelen zijn consistent.")


if __name__ == "__main__":
    main()
