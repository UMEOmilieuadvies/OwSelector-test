#!/usr/bin/env python3
"""Controleer dat technische releasenotities niet als gebruikerswijziging landen."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    (root / "tools").mkdir()
    (root / "js").mkdir()
    shutil.copy2(ROOT / "tools" / "release.py", root / "tools" / "release.py")
    (root / "VERSION").write_text("1.4x-test\n", encoding="utf-8")
    (root / "js" / "app-config.js").write_text("window.OWZ_CONFIG={version:'1.4x-test'};\n", encoding="utf-8")
    (root / "README.md").write_text("# OwSelector — Omgevingswet Zoeker 1.4x-test\nGitHub Pages-uitgave van Omgevingswet Zoeker 1.4x-test.\n", encoding="utf-8")
    (root / "RELEASE_NOTES.md").write_text("# Releasenotities\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, "tools/release.py", "klein", "--technical-note", "Alleen beheer."],
        cwd=root,
        check=True,
    )
    release = json.loads((root / "release.json").read_text(encoding="utf-8"))
    assert release["version"] == "1.4y-test"
    assert release["user_notes"] == []
    assert release["technical_notes"] == ["Alleen beheer."]

print("Technische releasenotities worden niet als gebruikerswijziging gepubliceerd.")
