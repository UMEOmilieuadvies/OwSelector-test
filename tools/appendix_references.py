"""Extract betrouwbare artikelverwijzingen uit officiële bijlagekoppen."""
from __future__ import annotations

import re


ARTICLE_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)+[a-z]?\b", re.IGNORECASE)
ARTICLE_GROUP_RE = re.compile(
    r"\b(?:artikel|artikelen)\s+(.+?)(?=\s+(?:van|uit)\s+(?:dit|deze)\b|\s*\(|$)",
    re.IGNORECASE,
)


def article_numbers_from_appendix_title(title: str) -> list[str]:
    """Return article numbers explicitly named in an appendix title.

    A title is only used when it has the official linking form 'bij artikel(en)
    ... van dit/deze besluit/regeling'. This prevents incidental numbers in a
    title from becoming a legal cross-reference.
    """
    result: list[str] = []
    for match in ARTICLE_GROUP_RE.finditer(str(title or "")):
        for number in ARTICLE_NUMBER_RE.findall(match.group(1)):
            normalized = number.lower()
            if normalized not in result:
                result.append(normalized)
    return result
