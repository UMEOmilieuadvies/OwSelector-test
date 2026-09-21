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
    match = re.fullmatch(r"(\d+)\.(\d+)([a-z]*)", current.strip())
    if not match:
        raise ValueError(f"Ongeldig versienummer: {current!r}")
    major, minor, suffix = match.groups()
    return f"{major}.{int(minor) + 1:02d}" if kind == "groot" else f"{major}.{int(minor):02d}{next_letters(suffix)}"


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
    parser.add_argument("--note", action="append", required=True)
    parser.add_argument("--issue", action="append", default=[])
    args = parser.parse_args()
    version = args.version or next_version((ROOT / "VERSION").read_text(encoding="utf-8"), args.kind)
    cache_version = re.sub(r"[^A-Za-z0-9._-]+", "-", version).strip("-")
    (ROOT / "VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")
    replace_once(ROOT / "js/app.js", r"const VERSION='[^']+';", f"const VERSION='{version}';")
    replace_once(ROOT / "index.html", r"<title>Omgevingswet Zoeker [^<]+</title>", f"<title>Omgevingswet Zoeker {version}</title>")
    replace_once(ROOT / "index.html", r"(<span id=\"version\">)[^<]+", rf"\g<1>{version}")
    replace_once(ROOT / "index.html", r"(<dialog id=\"aboutModal\"><form method=\"dialog\"><h2>Over</h2><p>Omgevingswet Zoeker <strong>)[^<]+", rf"\g<1>{version}")
    replace_once(ROOT / "index.html", r"(css/app\.css\?revision=)[^\"]+", rf"\g<1>release-{cache_version}")
    replace_once(ROOT / "index.html", r"(js/app\.js\?revision=)[^\"]+", rf"\g<1>release-{cache_version}")
    replace_once(ROOT / "README.md", r"(# OwSelector — Omgevingswet Zoeker )[^\n]+", rf"\g<1>{version}")
    replace_once(ROOT / "README.md", r"(GitHub Pages-uitgave van Omgevingswet Zoeker )[^\n]+", rf"\g<1>{version}.")
    replace_once(ROOT / "help.html", r"(<title>Help — Omgevingswet Zoeker )[^<]+", rf"\g<1>{version}")
    replace_once(ROOT / "help.html", r"(<span class=\"helpVersion\">)[^<]+", rf"\g<1>Versie {version}")
    replace_once(ROOT / "help.html", r"(Omgevingswet Zoeker )[^<]+(?= · <a href=\"index.html\">)", rf"\g<1>{version}")
    replace_once(ROOT / "help.html", r"(css/app\.css\?revision=)[^\"]+", rf"\g<1>release-{cache_version}")
    record = {"version": version, "kind": args.kind, "released_at": date.today().isoformat(), "notes": args.note, "resolved_comment_ids": args.issue}
    (ROOT / "release.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = [f"## {version} — {record['released_at']}", "", f"**{'Grote' if args.kind == 'groot' else 'Kleine'} wijziging.**", "", *[f"- {note}" for note in args.note], ""]
    notes = ROOT / "RELEASE_NOTES.md"
    notes.write_text(notes.read_text(encoding="utf-8").rstrip() + "\n\n" + "\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Versie {version} is voorbereid.")


if __name__ == "__main__":
    main()
