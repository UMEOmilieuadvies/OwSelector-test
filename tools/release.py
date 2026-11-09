"""Bereid de volgende versie voor.

Voorbeeld: python tools/release.py klein --note "Tekstcorrectie" --issue 12
"""
from __future__ import annotations

import argparse, json, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def next_letters(value: str) -> str:
    if not value:
        return "a"
    chars = list(value)
    index = len(chars) - 1
    while index >= 0 and chars[index] == "z":
        chars[index] = "a"
        index -= 1
    if index < 0:
        return "a" + "".join(chars)
    chars[index] = chr(ord(chars[index]) + 1)
    return "".join(chars)


def next_version(current: str, kind: str) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)([a-z]*)(-test)?", current.strip())
    if not match:
        raise ValueError(f"Ongeldig versienummer: {current!r}")
    major, minor, suffix, environment = match.groups()
    label = environment or ''
    return (f"{major}.{int(minor) + 1}" if kind == "groot" else f"{major}.{int(minor)}{next_letters(suffix)}") + label


def replace_once(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"Versieaanduiding niet gevonden in {path.name}")
    path.write_text(updated, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("groot", "klein"))
    parser.add_argument("--version", help="Stel een expliciete versie in, bijvoorbeeld 0.1 beta.")
    parser.add_argument("--note", action="append", default=[], help="Gebruikerswijziging: zichtbaar in 'Wat is er veranderd?'.")
    parser.add_argument("--technical-note", action="append", default=[], help="Technische beheerwijziging: alleen in RELEASE_NOTES.md.")
    parser.add_argument("--issue", action="append", default=[])
    args = parser.parse_args()
    if not args.note and not args.technical_note:
        parser.error("Geef ten minste één --note of --technical-note op.")
    version = args.version or next_version((ROOT / "VERSION").read_text(encoding="utf-8"), args.kind)
    cache_version = re.sub(r"[^A-Za-z0-9._-]+", "-", version).strip("-")
    (ROOT / "VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")
    replace_once(ROOT / "js/app-config.js", r"(version\s*:\s*')[^']+", rf"\g<1>{version}")
    # index.html is tijdens de testpublicatie vanuit __OWZ_VERSION__ opgebouwd.
    # Andere pagina's hebben eigen inhoud en worden niet door een release
    # overschreven; zo blijft een releasestap beperkt tot centrale metadata.
    replace_once(ROOT / "README.md", r"(# OwSelector — Omgevingswet Zoeker )[^\n]+", rf"\g<1>{version}")
    replace_once(ROOT / "README.md", r"(GitHub Pages-uitgave van Omgevingswet Zoeker )[^\n]+", rf"\g<1>{version}.")
    record = {
        "version": version,
        "kind": args.kind,
        "released_at": date.today().isoformat(),
        "user_notes": args.note,
        "technical_notes": args.technical_note,
        "resolved_comment_ids": args.issue,
    }
    (ROOT / "release.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = [f"## {version} — {record['released_at']}", "", f"**{'Grote' if args.kind == 'groot' else 'Kleine'} wijziging.**", ""]
    if args.note:
        lines.extend(["**Voor gebruikers**", "", *[f"- {note}" for note in args.note], ""])
    if args.technical_note:
        lines.extend(["**Technisch beheer**", "", *[f"- {note}" for note in args.technical_note], ""])
    notes = ROOT / "RELEASE_NOTES.md"
    notes.write_text(notes.read_text(encoding="utf-8").rstrip() + "\n\n" + "\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Versie {version} is voorbereid.")


if __name__ == "__main__":
    main()
