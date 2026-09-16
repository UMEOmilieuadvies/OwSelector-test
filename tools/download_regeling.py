#!/usr/bin/env python3
from __future__ import annotations
import re, shutil, sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

SRU_ENDPOINT="https://zoekservice.overheid.nl/sru/Search"
OFFICIAL_REPOSITORY_HOST="repository.officiele-overheidspublicaties.nl"
UA="Omgevingswet-Zoeker"

def log(message,*args,**kwargs): print(message)
def lname(tag): return tag.rsplit("}",1)[-1]
def http_get(url):
    req=Request(url,headers={"User-Agent":UA,"Accept":"application/xml,text/xml;q=0.9,*/*;q=0.1"})
    with urlopen(req,timeout=90) as r:return r.read(),r.geturl(),r.headers.get("Content-Type","")
def text_of_first(root,local_name):
    for e in root.iter():
        if lname(e.tag)==local_name and e.text and e.text.strip():return e.text.strip()
    return None
def parse_sru(raw,bwb_id):
    root=ET.fromstring(raw); n_text=text_of_first(root,"numberOfRecords")
    try:n=int(n_text or "0")
    except:n=0
    if n==0:raise RuntimeError("SRU gaf 0 records terug voor BWB-id en peildatum.")
    records=[]
    for rec in [e for e in root.iter() if lname(e.tag)=="record"]:
        rd=next((e for e in rec.iter() if lname(e.tag)=="recordData"),None)
        if rd is None:continue
        ident=text_of_first(rd,"identifier"); loc=text_of_first(rd,"locatie_toestand")
        if ident==bwb_id and loc:records.append({"identifier":ident,"title":text_of_first(rd,"title"),"toestand":text_of_first(rd,"toestand"),"locatie_toestand":loc,"start":text_of_first(rd,"geldigheidsperiode_startdatum"),"end":text_of_first(rd,"geldigheidsperiode_einddatum")})
    if not records:raise RuntimeError(f"SRU meldde {n} record(s), maar geen record met {bwb_id} en locatie_toestand werd gevonden.")
    return n,records
def validate_repository_url(url):
    p=urlparse(url)
    if p.scheme!="https" or p.hostname!=OFFICIAL_REPOSITORY_HOST:raise RuntimeError("SRU retourneerde geen URL op de officiële BWB-repository: "+url)
def normalize_for_validation(raw):
    s=raw.decode("utf-8-sig","replace")
    if "xsi:" in s[:5000] and "xmlns:xsi=" not in s[:5000]:s=re.sub(r'<toestand\b','<toestand xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',s,count=1)
    attr=re.compile(r'(\s[\w:.-]+\s*=\s*)(["\'])(.*?)(\2)',re.S); bare_amp=re.compile(r'&(?!#\d+;|#x[0-9A-Fa-f]+;|[A-Za-z_:][\w:.-]*;)')
    def fix(m):return m.group(1)+m.group(2)+bare_amp.sub("&amp;",m.group(3))+m.group(4)
    return attr.sub(fix,s)
def validate_xml(raw,bwb_id):
    root=ET.fromstring(normalize_for_validation(raw))
    if lname(root.tag)!="toestand":raise RuntimeError(f"Repositorybestand heeft root <{lname(root.tag)}> in plaats van <toestand>.")
    if root.get("bwb-id")!=bwb_id:raise RuntimeError(f"Repositorybestand heeft BWB-id {root.get('bwb-id')!r}; verwacht {bwb_id}.")
    counts={}
    for e in root.iter():k=lname(e.tag);counts[k]=counts.get(k,0)+1
    return root,counts
def iso_date(s):
    if not s:return None
    try:return datetime.strptime(s[:10],"%Y-%m-%d").date()
    except:return None
def choose_record(records,on_date):
    fitting=[]
    for r in records:
        a,b=iso_date(r["start"]),iso_date(r["end"])
        if (a is None or a<=on_date) and (b is None or on_date<=b):fitting.append(r)
    if len(fitting)==1:return fitting[0]
    if len(fitting)>1:
        fitting.sort(key=lambda r:iso_date(r["start"]) or datetime.min.date(),reverse=True);return fitting[0]
    if len(records)==1:return records[0]
    raise RuntimeError("Meerdere SRU-records gevonden, maar geen geldigheidsperiode omvat de peildatum.")
def main():
    if len(sys.argv)!=4:raise SystemExit("Gebruik: python download_regeling.py BWBR0041330 2026-08-20 BAL.xml")
    bwb_id=sys.argv[1].upper()
    if not re.fullmatch(r"BWBR\d{7}",bwb_id):raise SystemExit("Ongeldige BWB-id")
    on_date=datetime.strptime(sys.argv[2],"%Y-%m-%d").date();output=Path(sys.argv[3])
    if not output.is_absolute():output=(Path(__file__).resolve().parent.parent/"data"/"source"/output.name).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    query=f'dcterms.identifier=={bwb_id} and overheidbwb.geldigheidsdatum={on_date.isoformat()}'
    sru_url=SRU_ENDPOINT+"?"+urlencode({"operation":"searchRetrieve","version":"1.2","x-connection":"BWB","query":query,"maximumRecords":"10"})
    raw,_,_=http_get(sru_url);n,records=parse_sru(raw,bwb_id);rec=choose_record(records,on_date)
    validate_repository_url(rec["locatie_toestand"]);xml_raw,final_xml,_=http_get(rec["locatie_toestand"]);root,counts=validate_xml(xml_raw,bwb_id)
    print("Titel:",rec["title"] or "(onbekend)","Artikelen:",counts.get("artikel",0),"Bron:",final_xml)
    if output.exists():shutil.copy2(output,output.with_suffix(output.suffix+".bak"))
    tmp=output.with_suffix(output.suffix+".tmp");tmp.write_bytes(xml_raw);tmp.replace(output)
    print("GESLAAGD",output.resolve())
if __name__=="__main__":
    try:main()
    except Exception as e:print("STOP:",e);raise SystemExit(1)
