#!/usr/bin/env python3
"""
Download een geconsolideerde BWB-toestand via de officiële KOOP SRU-service.

Gebruik:
    python download_regeling.py BWBR0041330 2026-08-20 BAL.xml

Werking:
    BWB-id + peildatum
      -> SRU x-connection=BWB
      -> dcterms.identifier + overheidbwb.geldigheidsdatum
      -> overheidbwb:locatie_toestand
      -> officiële repository-XML
      -> validatie
      -> uitvoerbestand

Alleen Python standaardbibliotheek nodig.
"""
from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
def log(message, *args, **kwargs):
    print(message)
def exception(message, *args, **kwargs):
    print(message)

SRU_ENDPOINT = "https://zoekservice.overheid.nl/sru/Search"
OFFICIAL_REPOSITORY_HOST = "repository.officiele-overheidspublicaties.nl"
UA = "Omgevingswet-Zoeker"

NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "gzd": "http://standaarden.overheid.nl/sru",
    "bwb": "http://standaarden.overheid.nl/bwb/terms/",
    "dc": "http://purl.org/dc/terms/",
}

def lname(tag):
    return tag.rsplit("}", 1)[-1]

def http_get(url):
    req = Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.1",
    })
    with urlopen(req, timeout=90) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type", "")

def text_of_first(root, local_name):
    for e in root.iter():
        if lname(e.tag) == local_name and e.text and e.text.strip():
            return e.text.strip()
    return None

def all_text(root, local_name):
    out=[]
    for e in root.iter():
        if lname(e.tag)==local_name and e.text and e.text.strip():
            out.append(e.text.strip())
    return out

def parse_sru(raw, bwb_id):
    root=ET.fromstring(raw)

    # SRU diagnostics duidelijk melden.
    diagnostics=[]
    for e in root.iter():
        if lname(e.tag) in ("message","details") and e.text and e.text.strip():
            diagnostics.append(e.text.strip())
    if diagnostics and text_of_first(root,"numberOfRecords") in (None,"0"):
        raise RuntimeError("SRU-diagnostic: " + " | ".join(dict.fromkeys(diagnostics)))

    n_text=text_of_first(root,"numberOfRecords")
    try:n=int(n_text or "0")
    except:n=0
    if n==0:
        raise RuntimeError("SRU gaf 0 records terug voor BWB-id en peildatum.")

    records=[]
    for rec in [e for e in root.iter() if lname(e.tag)=="record"]:
        record_data=next((e for e in rec.iter() if lname(e.tag)=="recordData"),None)
        if record_data is None: continue

        ident=text_of_first(record_data,"identifier")
        title=text_of_first(record_data,"title")
        toestand=text_of_first(record_data,"toestand")
        loc=text_of_first(record_data,"locatie_toestand")
        start=text_of_first(record_data,"geldigheidsperiode_startdatum")
        end=text_of_first(record_data,"geldigheidsperiode_einddatum")

        if ident==bwb_id and loc:
            records.append({
                "identifier":ident,"title":title,"toestand":toestand,
                "locatie_toestand":loc,"start":start,"end":end
            })
    if not records:
        raise RuntimeError(
            f"SRU meldde {n} record(s), maar geen record met {bwb_id} en locatie_toestand werd gevonden."
        )
    return n,records

def validate_repository_url(url):
    from urllib.parse import urlparse
    p=urlparse(url)
    if p.scheme!="https" or p.hostname!=OFFICIAL_REPOSITORY_HOST:
        raise RuntimeError("SRU retourneerde geen URL op de officiële BWB-repository: "+url)

def normalize_for_validation(raw):
    """Alleen voor lokale validatie van oudere/niet-strikte BWB XML."""
    s=raw.decode("utf-8-sig","replace")
    if "xsi:" in s[:5000] and "xmlns:xsi=" not in s[:5000]:
        s=re.sub(r'<toestand\b',
                 '<toestand xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
                 s,count=1)
    attr=re.compile(r'(\s[\w:.-]+\s*=\s*)(["\'])(.*?)(\2)',re.S)
    bare_amp=re.compile(r'&(?!#\d+;|#x[0-9A-Fa-f]+;|[A-Za-z_:][\w:.-]*;)')
    def fix(m):
        return m.group(1)+m.group(2)+bare_amp.sub("&amp;",m.group(3))+m.group(4)
    return attr.sub(fix,s)

def validate_xml(raw,bwb_id):
    normalized=normalize_for_validation(raw)
    try:
        root=ET.fromstring(normalized)
    except ET.ParseError as e:
        raise RuntimeError(f"Repositorybestand kon niet als BWB XML worden gevalideerd: {e}")
    if lname(root.tag)!="toestand":
        raise RuntimeError(f"Repositorybestand heeft root <{lname(root.tag)}> in plaats van <toestand>.")
    if root.get("bwb-id")!=bwb_id:
        raise RuntimeError(f"Repositorybestand heeft BWB-id {root.get('bwb-id')!r}; verwacht {bwb_id}.")
    counts={}
    for e in root.iter():
        k=lname(e.tag); counts[k]=counts.get(k,0)+1
    return root,counts

def iso_date(s):
    if not s:return None
    try:return datetime.strptime(s[:10],"%Y-%m-%d").date()
    except:return None

def choose_record(records,on_date):
    # geldigheidsdatum hoort normaal één toestand per regeling te geven.
    # Mocht SRU meerdere records teruggeven: kies degene waarvan de periode de datum omvat.
    fitting=[]
    for r in records:
        a,b=iso_date(r["start"]),iso_date(r["end"])
        if (a is None or a<=on_date) and (b is None or on_date<=b):
            fitting.append(r)
    if len(fitting)==1:return fitting[0]
    if len(fitting)>1:
        fitting.sort(key=lambda r: iso_date(r["start"]) or datetime.min.date(), reverse=True)
        return fitting[0]
    if len(records)==1:return records[0]
    raise RuntimeError("Meerdere SRU-records gevonden, maar geen geldigheidsperiode omvat de peildatum.")

def main():
    if len(sys.argv)!=4:
        print("Gebruik:")
        print("  python download_regeling.py BWBR0041330 2026-08-20 BAL.xml")
        raise SystemExit(2)

    bwb_id=sys.argv[1].upper()
    log("DOWNLOAD_ARGS",bwb=bwb_id,peildatum=sys.argv[2],output=sys.argv[3])
    if not re.fullmatch(r"BWBR\d{7}",bwb_id):
        raise SystemExit("Ongeldige BWB-id; voorbeeld: BWBR0041330.")
    try:
        on_date=datetime.strptime(sys.argv[2],"%Y-%m-%d").date()
    except ValueError:
        raise SystemExit("Peildatum moet JJJJ-MM-DD zijn.")
    output=Path(sys.argv[3])
    if not output.is_absolute():
        output = (Path(__file__).resolve().parents[2] / "data" / "source" / output.name).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    # Officiële SRU-documentatie ondersteunt '=' en '==' voor identifier/geldigheidsdatum.
    query=f'dcterms.identifier=={bwb_id} and overheidbwb.geldigheidsdatum={on_date.isoformat()}'
    params={
        "operation":"searchRetrieve",
        "version":"1.2",
        "x-connection":"BWB",
        "query":query,
        "maximumRecords":"10",
    }
    sru_url=SRU_ENDPOINT+"?"+urlencode(params)

    print("BWB-id:       ",bwb_id)
    print("Peildatum:    ",on_date.isoformat())
    print("SRU-query:    ",query)
    print("SRU endpoint: ",SRU_ENDPOINT)

    log("SRU_REQUEST_START",bwb=bwb_id,url=sru_url)
    raw,final_sru,_=http_get(sru_url)
    log("SRU_REQUEST_FINISH",bwb=bwb_id,url=final_sru,bytes=len(raw))
    debug=output.parent / f"{bwb_id}_{on_date.isoformat()}_sru.xml"
    debug.write_bytes(raw)
    print("SRU-response: ",debug.resolve())

    n,records=parse_sru(raw,bwb_id)
    log("SRU_PARSE_FINISH",bwb=bwb_id,records=n,candidates=len(records))
    print("SRU records:  ",n)
    rec=choose_record(records,on_date)
    log("TOESTAND_SELECTED",bwb=bwb_id,toestand=rec.get("toestand"),start=rec.get("start"),end=rec.get("end"),url=rec.get("locatie_toestand"))

    print("Titel:        ",rec["title"] or "(onbekend)")
    print("Toestand-ID:  ",rec["toestand"] or "(onbekend)")
    print("Geldig vanaf: ",rec["start"] or "(onbekend)")
    print("Geldig t/m:   ",rec["end"] or "(onbekend)")
    print("XML-locatie:  ",rec["locatie_toestand"])

    validate_repository_url(rec["locatie_toestand"])
    log("XML_REQUEST_START",bwb=bwb_id,url=rec["locatie_toestand"])
    xml_raw,final_xml,_=http_get(rec["locatie_toestand"])
    log("XML_REQUEST_FINISH",bwb=bwb_id,url=final_xml,bytes=len(xml_raw))
    root,counts=validate_xml(xml_raw,bwb_id)
    log("XML_VALIDATE_FINISH",bwb=bwb_id,counts=counts)

    print("\nValidatie repositorybestand")
    print("BWB-id:       ",root.get("bwb-id"))
    print("Inwerking:    ",root.get("inwerkingtreding","(niet op root)"))
    print("Artikelen:    ",counts.get("artikel",0))
    print("intref:       ",counts.get("intref",0))
    print("extref:       ",counts.get("extref",0))

    # Niet langer hard afwijzen op 0 artikelen: sommige BWB XML-vormen kunnen anders structureren.
    # Wel expliciet waarschuwen.
    if counts.get("artikel",0)==0:
        print("WAARSCHUWING: 0 <artikel>-elementen. XML is wel de door SRU aangewezen officiële toestand.")

    if output.exists():
        backup=output.with_suffix(output.suffix+".bak")
        shutil.copy2(output,backup)
        print("Backup:       ",backup.resolve())

    tmp=output.with_suffix(output.suffix+".tmp")
    tmp.write_bytes(xml_raw)
    tmp.replace(output)
    log("XML_SAVED",bwb=bwb_id,file=str(output),bytes=output.stat().st_size)

    print("\nGESLAAGD")
    print("Bron XML:     ",final_xml)
    print("Opgeslagen:   ",output.resolve())
    print("\nVolgende stap:")
    print(f"  python bwb_parser.py {output} bal_graph.json")

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("\nSTOP:",e)
        print("Het uitvoerbestand is niet overschreven.")
        raise SystemExit(1)
