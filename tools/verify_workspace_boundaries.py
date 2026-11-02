"""Block test builds that point outside their own workspace."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "js" / "app-config.js"
CHECKED_SUFFIXES = {".py", ".mjs", ".yml", ".yaml"}
ABSOLUTE_WINDOWS_PATH = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]")
PARENT_PATH = re.compile(r"(?:['\"]|\b)\.\.[\\/]")


def main() -> int:
    errors: list[str] = []
    required_root_files = ("VERSION", "index.html", ".github/workflows/pages.yml")
    for relative_path in required_root_files:
        if not (ROOT / relative_path).is_file():
            errors.append(f"Testprojectbestand ontbreekt: {relative_path}")

    config = CONFIG.read_text(encoding="utf-8")
    if "environment:'test'" not in config:
        errors.append("De actieve configuratie is niet expliciet als testomgeving gemarkeerd.")
    if "pqpsajcjydvagrfxfeye" in config:
        errors.append("De productie-Supabase staat in de testconfiguratie.")

    for folder in (ROOT / "tools", ROOT / "tests", ROOT / ".github"):
        for file_path in folder.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in CHECKED_SUFFIXES:
                continue
            content = file_path.read_text(encoding="utf-8")
            if ABSOLUTE_WINDOWS_PATH.search(content):
                errors.append(f"Absoluut Windows-pad gevonden: {file_path.relative_to(ROOT)}")
            if PARENT_PATH.search(content):
                errors.append(f"Pad buiten de testmap gevonden: {file_path.relative_to(ROOT)}")

    if errors:
        print("Werkruimtegrens niet veilig:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    print("Werkruimtegrens gecontroleerd: testbouw gebruikt alleen de eigen testmap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
