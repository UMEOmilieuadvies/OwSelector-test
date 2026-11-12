#!/usr/bin/env python3
"""Koppel officiële BAL-wijzigingsnota's automatisch aan actuele artikelen.

Deze eerste herbruikbare laag leest uitsluitend bronnen uit nvt_catalog.json.
Een koppeling ontstaat alleen als een huidige BAL-artikelnummer of -paragraaf
letterlijk in een artikelsgewijze sectie van de officiële bron voorkomt.
"""
from __future__ import annotations

from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'nvt_catalog.json'
NVT = ROOT / 'data' / 'nvt'
SOURCE = ROOT / 'data' / 'source' / 'bal.xml'
OUT = ROOT / 'data' / 'article_notes_bal_amendments.json'
SPACE = re.compile(r'\s+')
# Zowel "artikel 4.1235" als "artikelen 4.1235 en 4.1236". De eerdere
# vorm "artikelen?" herkende abusievelijk alleen de meervoudsvorm.
ARTICLE = re.compile(r'\bartik(?:el|elen)\s+(\d+(?:\.\d+)+[a-z]?)\b', re.I)
PARAGRAPH = re.compile(r'(?:§|paragraaf)\s*(\d+(?:\.\d+)+[a-z]?)\b', re.I)


def clean(value: str) -> str:
    return SPACE.sub(' ', value).strip()


def local(element):
    return element.tag.rsplit('}', 1)[-1]


def bal_articles() -> tuple[set[str], dict[str, set[str]]]:
    numbers, by_paragraph = set(), defaultdict(set)
    # ElementTree geeft geen ouders terug; houd daarom tijdens één bronloop de
    # actuele paragraafcontext bij.
    paragraph = ''
    for element in ET.parse(SOURCE).getroot().iter():
        if local(element) == 'paragraaf':
            paragraph = element.attrib.get('label', '').replace('§ ', '').strip()
        elif local(element) == 'artikel':
            number = element.attrib.get('label', '').removeprefix('Artikel ').strip()
            if number:
                numbers.add(number)
                if paragraph:
                    by_paragraph[paragraph].add(number)
    return numbers, by_paragraph


class Sections(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.started = False
        self.heading = ''
        self.heading_parts = None
        self.parts = []
        self.sections = []
        self.context_article = ''
        self.context_paragraph = ''

    def handle_starttag(self, tag, attrs):
        if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self.flush()
            self.heading_parts = []
        elif tag in {'p', 'li'} and self.started:
            self.parts.append('\n')

    def handle_data(self, data):
        text = clean(data)
        if not text:
            return
        if self.heading_parts is not None:
            self.heading_parts.append(text)
        elif self.started:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'} and self.heading_parts is not None:
            self.heading = clean(' '.join(self.heading_parts))
            self.heading_parts = None
            lowered = self.heading.lower()
            if not self.started:
                if lowered == 'toelichting' or 'nota van toelichting' in lowered:
                    self.started = True
                    self.heading = ''
                return
            article = ARTICLE.search(self.heading)
            paragraph = PARAGRAPH.search(self.heading)
            if article:
                self.context_article = article.group(1)
                self.context_paragraph = ''
            elif paragraph:
                self.context_paragraph = paragraph.group(1)
                self.context_article = ''

    def flush(self):
        text = clean(' '.join(self.parts))
        if self.heading and text:
            self.sections.append({'heading': self.heading, 'text': text, 'article': self.context_article, 'paragraph': self.context_paragraph})
        self.heading = ''
        self.parts = []

    def result(self):
        self.flush()
        return self.sections


def source_document():
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    bal = next(item for item in catalog['regulations'] if item['id'] == 'BAL')
    return next(item for item in bal['documents'] if item.get('kind') == 'amendment' and item['file'] == 'bal-bodem-2021.html')


def main():
    document = source_document()
    path = NVT / document['file']
    if not path.exists():
        raise RuntimeError(f"Officiële wijzigingsbron ontbreekt: {path}")
    parser = Sections()
    parser.feed(path.read_text(encoding='utf-8', errors='replace'))
    article_numbers, by_paragraph = bal_articles()
    linked = defaultdict(list)
    implied_article = ''
    for section in parser.result():
        heading, text = section['heading'], section['text']
        # Koppel alleen op een juridische kop. Vermeldingen in toelichtende lopende
        # tekst zijn te breed en leveren anders fout-positieven op.
        direct = {section['article']} if section['article'] in article_numbers else set()
        paragraph_numbers = {section['paragraph']} if section['paragraph'] in by_paragraph else set()
        if direct:
            implied_article = next(iter(direct))
        elif paragraph_numbers and heading.lstrip().startswith('§'):
            # In officiële artikelsgewijze toelichtingen wordt bij het eerste
            # artikel van een paragraaf soms alleen de paragraafkop gevolgd door
            # “Eerste lid”. Dat lid hoort dan bij het eerste actuele artikel.
            implied_article = sorted(next(iter(paragraph_numbers)) and by_paragraph[next(iter(paragraph_numbers))])[0]
        elif re.match(r'^(eerste|tweede|derde|vierde|vijfde|zesde) lid\b', heading, re.I) and implied_article:
            direct = {implied_article}
            paragraph_numbers = set()
        targets = direct | set().union(*(by_paragraph[item] for item in paragraph_numbers)) if paragraph_numbers else direct
        if not targets:
            continue
        for article in sorted(targets):
            linked[article].append({
                'source': document['publication'],
                'url': document['url'],
                'text': heading + '\n' + text,
                'shared_for': sorted(targets - {article}),
                'source_kind': 'wijzigingsnota',
            })
    payload = {'schema': 1, 'regulation': 'BAL', 'sources': [document], 'articles': dict(linked)}
    OUT.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    print(f"BAL wijzigingskoppelingen: {len(linked)} artikelen uit {document['publication']}")
    if '4.1235' not in linked:
        raise RuntimeError('Verplichte proefkoppeling artikel 4.1235 ontbreekt.')


if __name__ == '__main__':
    main()
