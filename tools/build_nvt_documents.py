#!/usr/bin/env python3
"""Haal de officiële oorspronkelijke NvT-documenten op voor lokale Pages-weergave."""
from pathlib import Path
from urllib.request import Request, urlopen
import json, time
ROOT=Path(__file__).resolve().parents[1]; CATALOG=ROOT/'nvt_catalog.json'; OUT=ROOT/'data'/'nvt'
def main():
 data=json.loads(CATALOG.read_text(encoding='utf8')); OUT.mkdir(parents=True,exist_ok=True)
 for reg in data['regulations']:
  for doc in reg['documents']:
   target=OUT/doc['file']; last=None
   for attempt in range(3):
    try:
     req=Request(doc['url'],headers={'User-Agent':'Omgevingswet-Zoeker'})
     with urlopen(req,timeout=90) as r: raw=r.read()
     if not raw: raise RuntimeError('lege bron')
     target.write_bytes(raw); print(f"[{reg['id']}] {target.name}: {len(raw)} bytes"); break
    except Exception as exc:
     last=exc; time.sleep(attempt+1)
   else: raise RuntimeError(f"NvT niet opgehaald: {doc['url']}") from last
if __name__=='__main__': main()