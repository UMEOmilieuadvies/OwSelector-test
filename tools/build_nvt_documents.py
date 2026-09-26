#!/usr/bin/env python3
"""Haal de officiële oorspronkelijke NvT-documenten op voor lokale Pages-weergave."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
import json, os, time
ROOT=Path(__file__).resolve().parents[1]; CATALOG=ROOT/'nvt_catalog.json'; OUT=ROOT/'data'/'nvt'


class NoteContentsParser(HTMLParser):
    """Lees de gekoppelde NvT-inhoudsopgave uit de officiële documentnavigatie."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.note_anchor = None
        self.link_target = None
        self.link_text = []
        self.awaiting_contents = False
        self.in_contents = False
        self.contents_depth = 0
        self.items = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = set(attributes.get('class', '').split())
        if tag == 'ul' and 'toc' in classes:
            if self.awaiting_contents:
                self.in_contents = True
                self.awaiting_contents = False
                self.contents_depth = 1
            elif self.in_contents:
                self.contents_depth += 1
        if tag == 'a':
            href = attributes.get('href', '')
            self.link_target = href[1:] if href.startswith('#') and len(href) > 1 else None
            self.link_text = []
            if self.in_contents and self.link_target and not self.note_anchor:
                self.note_anchor = self.link_target

    def handle_data(self, data):
        if self.link_target is not None:
            self.link_text.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.link_target is not None:
            label = ' '.join(''.join(self.link_text).split())
            if label.upper() == 'NOTA VAN TOELICHTING':
                self.note_anchor = self.link_target
                self.awaiting_contents = True
            elif self.in_contents and label:
                self.items.append({'target': self.link_target, 'label': label, 'level': self.contents_depth})
            self.link_target = None
            self.link_text = []
        if tag == 'ul' and self.in_contents:
            self.contents_depth -= 1
            if self.contents_depth == 0:
                self.in_contents = False


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
 fallback_base=os.environ.get('NVT_FALLBACK_BASE','').rstrip('/')
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
   else:
    # Een tijdelijke blokkade van de bron mag een Pages-publicatie niet stoppen.
    # Gebruik dan de laatst gepubliceerde, lokaal beschikbare NvT als terugval.
    if fallback_base:
     try:
      fallback_url=f"{fallback_base}/{quote(doc['file'])}"
      req=Request(fallback_url,headers={'User-Agent':'Omgevingswet-Zoeker'})
      with urlopen(req,timeout=90) as r: raw=r.read()
      if not raw: raise RuntimeError('lege terugvalbron')
      target.write_bytes(raw)
      toc[doc['file']] = extract_note_contents(raw)
      print(f"[{reg['id']}] WAARSCHUWING: {target.name} hergebruikt uit de vorige publicatie na bronfout.")
      continue
     except Exception as fallback_error:
      raise RuntimeError(f"NvT niet opgehaald: {doc['url']}; terugval mislukt: {fallback_error}") from last
    raise RuntimeError(f"NvT niet opgehaald: {doc['url']}") from last
 (OUT / 'toc.json').write_text(json.dumps(toc, ensure_ascii=False), encoding='utf-8')
if __name__=='__main__': main()
