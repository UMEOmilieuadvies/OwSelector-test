"""Controleer compatibiliteit tussen release.json en Supabase releases.notes."""
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("record_release", ROOT / "tools" / "record_release.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def main() -> None:
    assert MODULE.release_notes({"user_notes": ["Zichtbare wijziging."], "technical_notes": ["Beheer."]}) == ["Zichtbare wijziging."]
    assert MODULE.release_notes({"notes": ["Oude zichtbare wijziging."]}) == ["Oude zichtbare wijziging."]
    try:
        MODULE.release_notes({"user_notes": "geen lijst"})
    except ValueError:
        pass
    else:
        raise AssertionError("Ongeldige gebruikersnotities moeten de registratie blokkeren.")
    print("Releaseregistratie verwerkt oud en nieuw notitieformaat veilig.")


if __name__ == "__main__":
    main()
