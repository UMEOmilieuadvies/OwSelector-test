#!/usr/bin/env python3
"""Download official BWB illustration files belonging to the downloaded XML."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'data'/'source'
TARGET=ROOT/'data'/'illustrations'
REGS={'omgevingswet':'ow','bal':'bal','bbl':'bbl','bkl':'bkl','ob':'ob','or':'or'}

def local(tag): return tag.rsplit('}',1)[-1].lower()
def repository_base(bwb):
    candidates=sorted(SOURCE.glob(f'{bwb}_*_sru.xml'))
    if not candidates: raise RuntimeError(f'SRU-bron ontbreekt voor {bwb}')
    root=ET.parse(candidates[-1]).getroot()
    url=next((e.text.strip() for e in root.iter() if local(e.tag)=='locatie_toestand' and e.text),None)
    if not url or '/xml/' not in url: raise RuntimeError(f'Geen officiële XML-locatie voor {bwb}')
    return url.rsplit('/',1)[0]+'/'
def download(url,dest):
    req=Request(url,headers={'User-Agent':'Omgevingswet-Zoeker','Accept':'image/png,image/*;q=0.9,*/*;q=0.1'})
    last_error=None
    for attempt in range(1,5):
        try:
            with urlopen(req,timeout=90) as r: raw=r.read(); typ=r.headers.get_content_type()
            if not raw or not typ.startswith('image/'):
                raise RuntimeError(f'onverwacht antwoord {typ}')
            dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(raw)
            return len(raw)
        except (OSError, URLError) as error:
            last_error=error
            if attempt<4: time.sleep(attempt*2)
    raise RuntimeError(f'illustratie kon na 4 pogingen niet worden opgehaald: {url}') from last_error
def main():
    jobs=[]
    for stem,reg in REGS.items():
        xml=SOURCE/(stem+'.xml')
        if not xml.exists(): raise RuntimeError(f'Bron ontbreekt: {xml}')
        root=ET.parse(xml).getroot(); bwb=root.get('bwb-id')
        base=repository_base(bwb)
        names=sorted({x.get('naam') for x in root.iter() if local(x.tag)=='illustratie' and x.get('naam')})
        print(f'[{reg.upper()}] {len(names)} illustraties')
        for name in names:
            dest=TARGET/reg/name
            if not dest.exists() or dest.stat().st_size==0: jobs.append((base+name,dest,reg,name))
    done=0
    # De officiële repository accepteert veel losse afbeeldingen betrouwbaarder
    # met een beperkt aantal gelijktijdige verbindingen.
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(download,url,dest) for url,dest,_,_ in jobs]
        for future in as_completed(futures): future.result();done+=1
    print(f'GESLAAGD: {done} officiële illustraties opgehaald; bestaande bestanden zijn hergebruikt.')
if __name__=='__main__': main()
