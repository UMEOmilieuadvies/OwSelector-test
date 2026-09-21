"""Eenduidige, controleerbare verwijzingen naar veelgebruikte EU-regelgeving.

De BWB-bron markeert deze namen niet altijd met ``extref``.  Daarom wordt de
officiële CELEX-code hier centraal beheerd, zodat een bijlage nooit per
ongeluk als een lokale bijlage wordt geopend.
"""
from __future__ import annotations

import re


# Naam in de Nederlandse BWB-tekst -> CELEX-code en leesbare officiële titel.
# Nieuwe namen worden alleen toegevoegd nadat de CELEX-code is gecontroleerd.
EU_INSTRUMENTS = (
    ("richtlijn industriële emissies", "32010L0075", "Richtlijn industriële emissies"),
    ("seveso-richtlijn", "32012L0018", "Seveso-richtlijn"),
    ("clp-verordening", "32008R1272", "CLP-verordening"),
    ("habitatrichtlijn", "31992L0043", "Habitatrichtlijn"),
    ("vogelrichtlijn", "32009L0147", "Vogelrichtlijn"),
    ("prtr-verordening", "32006R0166", "PRTR-verordening"),
    ("kaderrichtlijn water", "32000L0060", "Kaderrichtlijn water"),
    ("kaderrichtlijn afvalstoffen", "32008L0098", "Kaderrichtlijn afvalstoffen"),
    ("grondwaterrichtlijn", "32006L0118", "Grondwaterrichtlijn"),
    ("richtlijn omgevingslawaai", "32002L0049", "Richtlijn omgevingslawaai"),
    ("zwemwaterrichtlijn", "32006L0007", "Zwemwaterrichtlijn"),
    ("mer-richtlijn", "32011L0092", "MER-richtlijn"),
    ("smb-richtlijn", "32001L0042", "SMB-richtlijn"),
    ("richtlijn winningsafval", "32006L0021", "Richtlijn winningsafval"),
    ("verordening persistente organische verontreinigende stoffen", "32019R1021", "POP-verordening"),
    ("verordening governance van de energie-unie", "32018R1999", "Governanceverordening energie-unie"),
)

_BY_NAME = {name.casefold(): (celex, title) for name, celex, title in EU_INSTRUMENTS}
_NAMES = "|".join(re.escape(name) for name, _, _ in sorted(EU_INSTRUMENTS, key=lambda x: len(x[0]), reverse=True))
_EU_NAME_RE = re.compile(r"\b(" + _NAMES + r")\b", re.IGNORECASE)
_ANNEX_PREFIX_RE = re.compile(
    r"\bbijlage\s+[IVXLCDM]+(?:[a-z]+)?(?:\s*,\s*[^.;:]{0,90}?)?\s+bij\s+(?:de|het)\s+$",
    re.IGNORECASE,
)


def eu_url(celex: str) -> str:
    return f"https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:{celex}"


def plain_eu_refs(text: str) -> list[dict]:
    """Vind niet-gemarkeerde EU-verwijzingen, inclusief eventuele bijlage ervoor.

    De hele zinsnede ``bijlage I bij de ...`` wordt doelbewust één link. Dat
    voorkomt dat de browser eerst ``bijlage I`` als bijlage I van de actuele
    Nederlandse regeling oplost.
    """
    raw = str(text or "")
    found: list[dict] = []
    for match in _EU_NAME_RE.finditer(raw):
        start, end = match.span()
        before = raw[max(0, start - 180):start]
        prefix = _ANNEX_PREFIX_RE.search(before)
        if prefix:
            start = max(0, start - 180) + prefix.start()
        name = match.group(1).casefold()
        celex, title = _BY_NAME[name]
        found.append({
            "anchor": raw[start:end],
            "doc": celex,
            "bwb_id": None,
            "target": {},
            "source": "plain_eu_name",
            "title": title,
        })
    # Langste eerst: bijvoorbeeld een bijlageverwijzing vóór alleen de naam.
    return sorted(found, key=lambda item: (raw.find(item["anchor"]), -len(item["anchor"])))


def known_eu_name(text: str) -> bool:
    return bool(_EU_NAME_RE.search(str(text or "")))
