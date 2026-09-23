#!/usr/bin/env python3
"""Haal de officiële oorspronkelijke NvT-documenten op voor lokale Pages-weergave."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import json, time
ROOT=Path(__file__).resolve().parents[1]; CATALOG=ROOT/'nvt_catalog.json'; OUT=ROOT/'data'/'nvt'


class NoteContentsParser(HTMLParser):
    """Lees alleen de officiële inhoudsopgave direct na NOTA VAN TOELICHTING."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.note_depth = None
        self.note_heading = False
        self.note_anchor = None
        self.table_depth = None
        self.row_depth = None
        self.row_text = []
        self.row_targets = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = set(attributes.get('class', '').split())
        if tag == 'div' and 'nota-toelichting' in classes and self.note_depth is None:
            self.note_depth = self.depth
        if self.note_depth is not None and tag == 'h2' and 'nota-toelichting_kop' in classes:
            self.note_heading = True
        if self.note_heading and tag == 'a' and attributes.get('id') and not self.note_anchor:
            self.note_anchor = attributes['id']
        if self.note_heading and self.table_depth is None and tag == 'table':
            self.table_depth = self.depth
        if self.table_depth is not None and self.table_depth >= 0 and tag == 'tr':
            self.row_depth = self.depth
            self.row_text = []
            self.row_targets = []
        if self.row_depth is not None and tag == 'a':
            href = attributes.get('href', '')
            if href.startswith('#') and len(href) > 1:
                self.row_targets.append(href[1:])
        self.depth += 1

    def handle_data(self, data):
        if self.row_depth is not None:
            self.row_text.append(data)

    def handle_endtag(self, tag):
        self.depth -= 1
        if tag == 'tr' and self.row_depth is not None and self.depth == self.row_depth:
            label = ' '.join(' '.join(self.row_text).split())
            if label and self.row_targets:
                self.items.append({'target': self.row_targets[0], 'label': label})
            self.row_depth = None
            self.row_text = []
            self.row_targets = []
        if self.table_depth is not None and self.table_depth >= 0 and self.depth == self.table_depth and tag == 'table':
            self.table_depth = -1


def extract_note_contents(raw: bytes) -> dict:
    parser = NoteContentsParser()
    parser.feed(raw.decode('utf-8', errors='replace'))
    seen = set()
    items = []
    for item in parser.items:
        key = (item['target'], item['label'])
        if key not in seen:
            seen.add(key)
            items.append(item)
    return {'note_anchor': parser.note_anchor, 'items': items}
def main():
 data=json.loads(CATALOG.read_text(encoding='utf8')); OUT.mkdir(parents=True,exist_ok=True)
 toc = {}
 for reg in data['regulations']:
  for doc in reg['documents']:
   target=OUT/doc['file']; last=None
   for attempt in range(3):
    try:
     req=Request(doc['url'],headers={'User-Agent':'Omgevingswet-Zoeker'})
     with urlopen(req,timeout=90) as r: raw=r.read()
     if not raw: raise RuntimeError('lege bron')
     target.write_bytes(raw)
     toc[doc['file']] = extract_note_contents(raw)
     print(f"[{reg['id']}] {target.name}: {len(raw)} bytes; {len(toc[doc['file']]['items'])} inhoudsregels")
     break
    except Exception as exc:
     last=exc; time.sleep(attempt+1)
   else: raise RuntimeError(f"NvT niet opgehaald: {doc['url']}") from last
 (OUT / 'toc.json').write_text(json.dumps(toc, ensure_ascii=False), encoding='utf-8')
if __name__=='__main__': main()
