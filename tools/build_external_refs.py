"""Bouw een register van de externe verwijzingen uit de zes officiële XML-bestanden."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET
from eu_references import EU_INSTRUMENTS, eu_url

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source"
OUTPUT = ROOT / "data" / "external_refs.json"
FILES = ("omgevingswet.xml", "bal.xml", "bbl.xml", "bkl.xml", "ob.xml", "or.xml")
KNOWN_TITLES = {
    "BWBR0037885": "Omgevingswet",
    "BWBR0041330": "Besluit activiteiten leefomgeving",
    "BWBR0041297": "Besluit bouwwerken leefomgeving",
    "BWBR0041313": "Besluit kwaliteit leefomgeving",
    "BWBR0041278": "Omgevingsbesluit",
    "BWBR0045528": "Omgevingsregeling",
}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def title_from_anchor(anchor: str) -> str:
    """Neem een regelingnaam uit de zichtbare officiële verwijzing."""
    text = clean(anchor)
    # Veel verwijzingen bevatten eerst alleen artikelnummers en de BWB-code.
    # Een andere verwijzing naar dezelfde BWB-code bevat vaak ook de regelingnaam.
    match = re.search(
        r"\b(?:van\s+(?:de|het)\s+)?"
        r"((?:(?:Wet|Besluit|Regeling|Verordening|Richtlijn)\s+[A-Za-zÀ-ÿ0-9'’\- ]+|"
        r"(?:[A-Z][A-Za-zÀ-ÿ'’\-]+\s+)*[A-Z][A-Za-zÀ-ÿ'’\-]*?(?:wet|besluit|regeling|verordening|richtlijn)))"
        r"(?:\s*\(BWBR\d+\)|[;,.]|$)",
        text,
        flags=re.IGNORECASE,
    )
    return clean(match.group(1)) if match else ""


def main() -> None:
    found: dict[str, dict] = {}
    for filename in FILES:
        path = SOURCE / filename
        if not path.exists():
            raise SystemExit(f"Bronbestand ontbreekt: {path}")
        for element in ET.parse(path).getroot().iter():
            if local(element.tag) != "extref":
                continue
            anchor = clean(" ".join(element.itertext()))
            bwb_id = clean(element.get("bwb-id") or "").upper()
            doc = clean(element.get("doc") or "")
            if bwb_id:
                key = bwb_id
                kind = "bwb"
                url = f"https://wetten.overheid.nl/{bwb_id}"
            elif re.fullmatch(r"[0-9]{5}[LR][0-9]{4}", doc):
                key = doc
                kind = "eu"
                url = f"https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:{doc}"
            elif doc.startswith(("http://", "https://")):
                key = doc
                kind = "web"
                url = doc
            else:
                key = doc or anchor
                kind = "other"
                url = ""
            item = found.setdefault(key, {"key": key, "kind": kind, "url": url, "count": 0, "sample": anchor, "title": ""})
            item["count"] += 1
            if len(anchor) > len(item["sample"]):
                item["sample"] = anchor
            if kind == "bwb":
                candidate = title_from_anchor(anchor)
                if candidate and (not item["title"] or len(candidate) < len(item["title"])):
                    item["title"] = candidate

    # De browser ontvangt ook de officiële doelen voor EU-namen die de BWB-XML
    # als gewone tekst heeft opgenomen in plaats van als <extref>.
    for _name, celex, title in EU_INSTRUMENTS:
        found.setdefault(celex, {
            "key": celex, "kind": "eu", "url": eu_url(celex), "count": 0,
            "sample": title, "title": title,
        })

    for item in found.values():
        if item["kind"] == "bwb":
            item["title"] = KNOWN_TITLES.get(item["key"], item["title"] or item["key"])
        else:
            item["title"] = item["sample"]
    entries = sorted(found.values(), key=lambda item: (item["kind"], item["title"].casefold()))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"generated_on": date.today().isoformat(), "references": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(item["kind"] for item in entries)
    print("Extern register:", ", ".join(f"{kind}={counts[kind]}" for kind in sorted(counts)))


if __name__ == "__main__":
    main()
