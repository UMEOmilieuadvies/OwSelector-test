"""Prepare every fixed GitHub Pages page from the central release version."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"1\.\d+[a-z]*(?:-test)?\Z")
CONFIG_PATTERN = re.compile(r"version\s*:\s*'([^']+)'")
ENVIRONMENT_PATTERN = re.compile(r"environment\s*:\s*'([^']+)'")
STATIC_PAGES = (
    "index.html",
    "help.html",
    "qna.html",
    "nvt.html",
    "beheer.html",
    "historie.html",
    "article-notes.html",
)


def read_release_context() -> tuple[str, str]:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Ongeldig versienummer: {version!r}")
    config = (ROOT / "js" / "app-config.js").read_text(encoding="utf-8")
    match = CONFIG_PATTERN.search(config)
    if not match or match.group(1) != version:
        raise ValueError("VERSION en js/app-config.js hebben niet hetzelfde versienummer.")
    environment = ENVIRONMENT_PATTERN.search(config)
    if not environment or environment.group(1) not in {"test", "production"}:
        raise ValueError("js/app-config.js bevat geen geldige omgeving.")
    if (environment.group(1) == "test") != version.endswith("-test"):
        raise ValueError("Versienummer en omgeving horen niet bij elkaar.")
    return version, environment.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-dir", default="_site")
    args = parser.parse_args()
    try:
        version, environment = read_release_context()
        placeholders = {
            "__OWZ_VERSION__": None,
            "__OWZ_ENVIRONMENT_LABEL__": "testomgeving" if environment == "test" else "productieomgeving",
            "__OWZ_FAVORITES_STORAGE__": "in de testdatabase" if environment == "test" else "online in de productieomgeving",
        }
        rendered_pages = {}
        for page_name in STATIC_PAGES:
            source = (ROOT / page_name).read_text(encoding="utf-8")
            if "__OWZ_VERSION__" not in source:
                raise ValueError(f"{page_name} bevat geen versieplaatsaanduiding.")
            rendered = source.replace("__OWZ_VERSION__", version)
            for placeholder, value in placeholders.items():
                if value is not None:
                    rendered = rendered.replace(placeholder, value)
            if environment == "production":
                rendered = rendered.replace('<body><div class="environmentBanner" role="status">Testomgeving — wijzigingen zijn nog niet definitief.</div>', '<body>')
            if any(placeholder in rendered for placeholder in placeholders) or version not in rendered:
                raise ValueError(f"{page_name} bevat geen volledig ingevuld versienummer.")
            rendered_pages[page_name] = rendered
        if not args.check:
            output_dir = ROOT / args.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            for page_name, rendered in rendered_pages.items():
                (output_dir / page_name).write_text(rendered, encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"Releasepagina kan niet worden voorbereid: {error}", file=sys.stderr)
        return 1
    print(f"Release {version} ({environment}) is consistent voorbereid voor {len(STATIC_PAGES)} vaste pagina's.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
