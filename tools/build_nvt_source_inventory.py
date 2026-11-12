#!/usr/bin/env python3
"""Inventariseer officiële wijzigingsbronnen voor artikelgewijze NvT-koppeling.

De inventaris is nadrukkelijk een tussenlaag: een gevonden bron is nog geen
gepubliceerde toelichting. Alleen documenten die daarna brongetrouw zijn
gecontroleerd en een gerichte koppelingstest hebben, mogen naar nvt_catalog.json.
"""
from __future__ import annotations

from collections import OrderedDict
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import re
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'nvt' / 'source_inventory.json'
CATALOG = ROOT / 'nvt_catalog.json'
REGS = {
    'OW': 'BWBR0037885', 'BAL': 'BWBR0041330', 'BBL': 'BWBR0041297',
    'BKL': 'BWBR0041313', 'OB': 'BWBR0041278', 'OR': 'BWBR0045528',
    'IWO': 'BWBR0043660',
}
PUBLICATION = re.compile(r'^(?:Stb\.|Stcrt\.|Kst\.)')
USER_AGENT = 'Omgevingswet-Zoeker-NvT-inventory/1.0'


class ChangeOverviewParser(HTMLParser):
    """Lees alleen officiële bekendmakingslinks uit het regelingsoverzicht."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.href = ''
        self.parts: list[str] = []
        self.sources: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and attrs.get('id') == 'tab-wijzigingenoverzicht':
            self.depth = 1
            return
        if self.depth and tag == 'div':
            self.depth += 1
        href = attrs.get('href', '')
        if self.depth and tag == 'a' and 'zoek.officielebekendmakingen.nl' in href:
            self.href, self.parts = href, []

    def handle_data(self, data):
        if self.href:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href:
            label = ' '.join(''.join(self.parts).split())
            if PUBLICATION.match(label):
                self.sources.append((label, self.href))
            self.href, self.parts = '', []
        if self.depth and tag == 'div':
            self.depth -= 1


def read_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return fallback


def fetch_sources(bwb: str) -> list[dict[str, str]]:
    url = f'https://wetten.overheid.nl/{bwb}/informatie'
    request = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html'})
    with urlopen(request, timeout=45) as response:
        parser = ChangeOverviewParser()
        parser.feed(response.read().decode('utf-8', errors='replace'))
    unique = OrderedDict((url, label) for label, url in parser.sources)
    return [{'publication': label, 'url': url, 'status': 'candidate'} for url, label in unique.items()]


def registered_sources() -> dict[str, set[str]]:
    result = {reg: set() for reg in REGS}
    for regulation in read_json(CATALOG, {}).get('regulations', []):
        reg = regulation.get('id')
        if reg not in result:
            continue
        result[reg].update(str(doc.get('url', '')) for doc in regulation.get('documents', []))
    return result


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    previous = read_json(OUT, {}).get('regulations', {})
    registered = registered_sources()
    regulations = {}
    for reg, bwb in REGS.items():
        try:
            sources = fetch_sources(bwb)
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            cached = previous.get(reg, {}).get('sources', [])
            if not cached:
                raise RuntimeError(f'{reg}: wijzigingsoverzicht niet beschikbaar') from error
            sources = cached
            print(f'[{reg}] WAARSCHUWING: broninventaris uit cache hergebruikt ({error}).')
        for source in sources:
            if source['url'] in registered[reg]:
                source['status'] = 'registered'
        regulations[reg] = {'bwb': bwb, 'sources': sources}
        print(f'[{reg}] {len(sources)} officiële kandidaatbronnen')
    payload = {
        'schema_version': 1,
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'publication_rule': 'Alleen status verified én een geslaagde koppelingstest mag naar de publieke NvT-catalogus.',
        'regulations': regulations,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Geschreven: {OUT}')


if __name__ == '__main__':
    main()
