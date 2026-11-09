#!/usr/bin/env python3
"""Bouw een doorzoekbare, brongetrouwe NVT-weergave uit officiële HTML-documenten."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'nvt_catalog.json'
SOURCE = ROOT / 'data' / 'nvt'
OUT = SOURCE / 'integrated'
INDEX = SOURCE / 'integrated_index.json'
SPACE = re.compile(r'\s+')
ARTICLE = re.compile(r'^(?:artikel|artikelen)\s+([0-9]+(?:\.[0-9]+)*[a-z]?)', re.I)


def clean(value: str) -> str:
    return SPACE.sub(' ', value).strip()


class OfficialNoteParser(HTMLParser):
    """Leest koppen en lopende tekst vanaf de officiële kop 'Nota van toelichting'."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.events: list[dict] = []
        self.tag: str | None = None
        self.level = 0
        self.parts: list[str] = []
        self.anchor = ''
        self.pending_anchor = ''

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get('id') or attributes.get('name'):
            self.pending_anchor = attributes.get('id') or attributes.get('name') or ''
        if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li'}:
            self.tag = tag
            self.level = int(tag[1]) if tag.startswith('h') else 0
            self.parts = []
            self.anchor = attributes.get('id') or attributes.get('name') or self.pending_anchor

    def handle_data(self, data):
        if self.tag:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag != self.tag:
            return
        text = clean(''.join(self.parts))
        if text:
            self.events.append({
                'type': 'heading' if tag.startswith('h') else 'text',
                'level': self.level,
                'anchor': self.anchor,
                'text': text,
            })
        self.tag = None
        self.parts = []


def sections_for_document(raw: bytes, document: dict) -> list[dict]:
    parser = OfficialNoteParser()
    parser.feed(raw.decode('utf-8', errors='replace'))
    started = False
    article_mode = False
    sequence = 0
    current: dict | None = None
    result: list[dict] = []

    def flush():
        nonlocal current
        if current and current['paragraphs']:
            current['paragraphs'] = [clean(item) for item in current['paragraphs'] if clean(item)]
            current['text'] = clean(' '.join(current['paragraphs']))
            result.append(current)
        current = None

    for event in parser.events:
        text = event['text']
        lowered = text.lower()
        if event['type'] == 'heading' and (lowered == 'toelichting' or 'nota van toelichting' in lowered or 'memorie van toelichting' in lowered):
            started = True
            continue
        if not started:
            continue
        if event['type'] == 'heading':
            flush()
            if 'artikelsgewijze' in lowered or 'artikelsgewijs' in lowered or 'toelichting op de artikelen' in lowered or lowered.startswith('ii. de artikelen'):
                article_mode = True
            sequence += 1
            article = ARTICLE.match(text)
            current = {
                'id': f"{document['file']}:{sequence}",
                'title': text,
                'kind': 'article' if article_mode else 'general',
                'article': article.group(1) if article else '',
                'level': event['level'],
                'anchor': event['anchor'],
                'paragraphs': [],
                'source': document['title'],
                'publication': document['publication'],
                'date': document['date'],
                'official_url': document['url'],
                'document_file': document['file'],
            }
        elif current:
            current['paragraphs'].append(text)
    flush()
    return result


def main():
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    index = {'schema': 1, 'regulations': []}
    for regulation in catalog['regulations']:
        documents = []
        total = general = article = 0
        for document in regulation['documents']:
            path = SOURCE / document['file']
            if not path.exists():
                raise RuntimeError(f"Officiële NVT-bron ontbreekt: {path}")
            sections = sections_for_document(path.read_bytes(), document)
            total += len(sections)
            general += sum(item['kind'] == 'general' for item in sections)
            article += sum(item['kind'] == 'article' for item in sections)
            documents.append({**document, 'sections': sections})
        payload = {
            'schema': 1,
            'regulation': {key: regulation[key] for key in ('id', 'short', 'name', 'bwb')},
            'documents': documents,
        }
        filename = f"{regulation['id'].lower()}.json"
        (OUT / filename).write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        index['regulations'].append({
            'id': regulation['id'], 'short': regulation['short'], 'name': regulation['name'],
            'file': filename, 'sections': total, 'general_sections': general,
            'article_sections': article,
        })
        print(f"[{regulation['id']}] {total} NVT-blokken ({general} algemeen, {article} artikelsgewijs)")
    INDEX.write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
