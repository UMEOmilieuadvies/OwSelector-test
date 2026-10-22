"""Prepare the GitHub Pages entry page from the central release version."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"1\.\d+[a-z]*-test\Z")
CONFIG_PATTERN = re.compile(r"version\s*:\s*'([^']+)'")
PLACEHOLDER = "__OWZ_VERSION__"


def read_version() -> str:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Ongeldig testversienummer: {version!r}")
    config = (ROOT / "js" / "app-config.js").read_text(encoding="utf-8")
    match = CONFIG_PATTERN.search(config)
    if not match or match.group(1) != version:
        raise ValueError("VERSION en js/app-config.js hebben niet hetzelfde testversienummer.")
    return version


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", default="_site/index.html")
    args = parser.parse_args()
    try:
        version = read_version()
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        if PLACEHOLDER not in source:
            raise ValueError("index.html bevat geen versieplaatsaanduiding.")
        rendered = source.replace(PLACEHOLDER, version)
        if PLACEHOLDER in rendered:
            raise ValueError("Niet alle versieplaatsaanduidingen zijn ingevuld.")
        if not args.check:
            output = ROOT / args.output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"Releasepagina kan niet worden voorbereid: {error}", file=sys.stderr)
        return 1
    print(f"Testrelease {version} is consistent voorbereid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
