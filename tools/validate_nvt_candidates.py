#!/usr/bin/env python3
"""Classificeer officiële NvT-kandidaten zonder ze al te publiceren.

Dit is poort 1 en 2: een kandidaat moet een officiële publicatie zijn die
daadwerkelijk een nota van toelichting bevat. De regelingen volgen uitsluitend
uit de officiële wijzigingsoverzichten waarop de inventaris is gebaseerd.
"""
from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import argparse
import json
import re
import time

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'data' / 'nvt' / 'source_inventory.json'
OUT = ROOT / 'data' / 'nvt' / 'candidate_validation.json'
OFFICIAL = re.compile(r'^https://zoek\.officielebekendmakingen\.nl/(?:stb|stcrt|kst)-', re.I)


def fetch(url: str) -> str:
    request = Request(url, headers={'User-Agent': 'Omgevingswet-Zoeker-NvT-validation/1.0'})
    with urlopen(request, timeout=60) as response:
        return response.read().decode('utf-8', errors='replace')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0, help='Alleen voor een lokale proef; 0 controleert alles.')
    args = parser.parse_args()
    inventory = json.loads(INVENTORY.read_text(encoding='utf-8'))['regulations']
    grouped: dict[str, dict] = {}
    for regulation, record in inventory.items():
        for source in record['sources']:
            entry = grouped.setdefault(source['url'], {'publication': source['publication'], 'url': source['url'], 'regulations': []})
            entry['regulations'].append(regulation)
    candidates = list(grouped.values())
    if args.limit:
        candidates = candidates[:args.limit]
    validated = []
    for item in candidates:
        result = {**item, 'regulations': sorted(item['regulations'])}
        if not OFFICIAL.match(item['url']):
            result['status'] = 'rejected_non_official'
        else:
            try:
                page = fetch(item['url'])
                result['status'] = 'has_nvt' if 'nota van toelichting' in page.lower() else 'no_nvt'
            except (HTTPError, URLError, TimeoutError, OSError) as error:
                result['status'] = 'unreachable'
                result['error'] = str(error)
        validated.append(result)
        print(f"{result['publication']}: {result['status']}")
    OUT.write_text(json.dumps({'schema_version': 1, 'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'candidates': validated}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Geschreven: {OUT} ({len(validated)} kandidaten)')


if __name__ == '__main__':
    main()
