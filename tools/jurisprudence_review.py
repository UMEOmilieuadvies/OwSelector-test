"""Gedeelde gegevensregels voor de GitHub-jurisprudentiebeoordeling."""
from __future__ import annotations

REVIEW_STATUSES = ("te_beoordelen", "goedgekeurd", "afgewezen", "later_bekijken")
REVIEW_REASONS = {
    "inhoudelijk_behandeld": "De uitspraak behandelt dit artikel inhoudelijk.",
    "alleen_terloops_genoemd": "Het artikel wordt alleen genoemd, zonder inhoudelijke behandeling.",
    "verkeerde_regeling": "De gevonden regeling hoort niet bij deze artikelverwijzing.",
    "verkeerd_artikel": "De gevonden artikelkoppeling klopt niet.",
    "historische_verwijzing": "De verwijzing betreft oud recht of een voorganger, niet dit artikel.",
    "onvoldoende_duidelijk": "De relevantie kan nog niet betrouwbaar worden beoordeeld.",
}


def references(candidate: dict) -> list[tuple[dict, dict]]:
    """Geef alle afzonderlijk te beoordelen uitspraak-artikelkoppelingen.

    Oude kandidaatbestanden met één status op uitspraakniveau blijven leesbaar.
    Nieuwe kandidaatbestanden leggen status en meldmoment per artikelkoppeling
    vast, omdat één uitspraak meerdere regelingen kan raken.
    """
    rows: list[tuple[dict, dict]] = []
    legacy_status = candidate.get("review_status", "te_beoordelen")
    legacy_notified = candidate.get("notified_at")
    for match in candidate.get("matches", []):
        for article in match.get("articles", []):
            article.setdefault("review_status", legacy_status)
            article.setdefault("review_reason", "")
            article.setdefault("review_note", "")
            if legacy_notified and "notified_at" not in article:
                article["notified_at"] = legacy_notified
            rows.append((match, article))
    return rows
