#!/usr/bin/env python3
"""
OMGEVINGSWET ZOEKER - GENERIEKE BWB PARSER

Gebruik:
    python bwb_parser.py INPUT.xml OUTPUT.json

De parser kent geen BAL-specifieke bestandsnamen en schrijft uitsluitend naar
het door de gebruiker opgegeven uitvoerbestand.
"""
import sys, json, re
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter
from eu_references import plain_eu_refs

STRUCT = {
    "hoofdstuk":"chapter",
    "afdeling":"section",
    "paragraaf":"paragraph",
    "sub-paragraaf":"subparagraph",
    "artikel":"article",
    "lid":"member",
    "li":"item",
    "bijlage":"appendix",
}
BOUNDARY = set(STRUCT) | {"li","table"}
SKIP = {"meta-data","kop","lidnr","li.nr"}
def normalize_legal_enumeration(number, level=None):
    raw=str(number or "").strip()
    if re.fullmatch(r"[a-z]",raw,re.I):
        return {"number_raw":raw,"number_display":raw.lower()+".","enumeration_kind":"letter"}
    if re.fullmatch(r"\d+\s*[°º]",raw):
        return {"number_raw":raw,"number_display":re.sub(r"\s+","",raw).replace("º","°"),
                "enumeration_kind":"degree"}
    if re.fullmatch(r"\d+\.?",raw):
        return {"number_raw":raw,"number_display":raw.rstrip("."),
                "enumeration_kind":"numeric"}
    return {"number_raw":raw,"number_display":raw,"enumeration_kind":"other"}

def ln(tag):
    if not isinstance(tag,str): return ""
    return tag.rsplit("}",1)[-1].rsplit(":",1)[-1].lower()

def clean(s):
    return re.sub(r"\s+"," ",s or "").strip()

def text_all(e):
    return clean(" ".join(e.itertext()))

def title(e):
    for c in list(e):
        if ln(c.tag)=="kop":
            for x in list(c):
                if ln(x.tag)=="titel":
                    return text_all(x)
    return ""

def number(e,typ):
    if typ=="member":
        for c in list(e):
            if ln(c.tag)=="lidnr":
                return text_all(c)
    for c in list(e):
        if ln(c.tag)=="kop":
            for x in list(c):
                if ln(x.tag)=="nr":
                    return text_all(x)
    label=e.get("label") or ""
    m=re.search(r"(\d+(?:\.\d+)*(?:[a-z]+)?)",label,re.I)
    return m.group(1) if m else None

def li_number(e):
    for c in list(e):
        if ln(c.tag)=="li.nr":
            return text_all(c).rstrip(".")
    raw=e.get("nr") or e.get("number") or e.get("n")
    if raw:
        return str(raw).strip().rstrip(".")
    return None

def own_visible_text(e):
    out=[]
    def rec(x,isroot=False):
        tag=ln(x.tag)
        if tag=="meta-data": return
        if not isroot and tag in BOUNDARY: return
        if tag=="kop" or tag in {"lidnr","li.nr"}: return
        if x.text: out.append(x.text)
        for c in list(x):
            rec(c)
            if c.tail: out.append(c.tail)
    rec(e,True)
    return clean("".join(out))

def own_illustrations(e):
    """Illustrations that belong to this legal node, excluding nested legal nodes."""
    out=[]
    def rec(x,isroot=False):
        tag=ln(x.tag)
        if tag=="meta-data" or (not isroot and tag in BOUNDARY): return
        if tag=="illustratie" and x.get("naam"):
            out.append({"name":x.get("naam"),"alt":x.get("alt") or "",
                        "width":x.get("breedte") or "","height":x.get("hoogte") or "",
                        "display":x.get("display") or "block"})
            return
        for child in list(x): rec(child)
    rec(e,True)
    return out

def external_refs(e, visible_text=None):
    """Bewaar officiële externe XML-verwijzingen bij het zichtbare bronblok.

    De browser kan daardoor iedere <extref> als link tonen, zonder op een
    tekstpatroon te hoeven gokken. De BWB-id en documentcode blijven intact.
    """
    refs=[]
    def rec(x, isroot=False):
        tag=ln(x.tag)
        if tag=="meta-data": return
        if not isroot and tag in BOUNDARY: return
        if tag in {"kop","lidnr","li.nr"}: return
        if tag=="extref":
            add(x)
            return
        for child in list(x):
            rec(child)
    def add(x):
        anchor=clean(" ".join(x.itertext()))
        if not anchor: return
        doc=clean(str(x.get("doc") or ""))
        target={}
        for xml_key,kind in (("artikel","article"),("paragraaf","paragraph"),
                             ("afdeling","section"),("hoofdstuk","chapter"),
                             ("bijlage","appendix")):
            m=re.search(r"(?:^|&)"+xml_key+r"=([^&]+)",doc,re.I)
            if m:
                target={"type":kind,"number":m.group(1)}
                break
        refs.append({
            "anchor":anchor,
            "bwb_id":str(x.get("bwb-id") or "").upper() or None,
            "doc":doc or None,
            "target":target,
        })
    rec(e, True)
    # Niet iedere Europese verwijzing is in de officiële XML als <extref>
    # gecodeerd. Voeg de gecontroleerde, zichtbare EU-namen daarom toe als
    # virtuele externe verwijzing. Een bijlage vóór die naam blijft één link.
    existing={clean(ref["anchor"]).casefold() for ref in refs}
    for ref in plain_eu_refs(visible_text if visible_text is not None else own_visible_text(e)):
        key=clean(ref["anchor"]).casefold()
        if key not in existing:
            refs.append(ref)
            existing.add(key)
    return refs

def direct_visible_blocks(e):
    """Preserve appendix paragraphs in source order, including source alignment hints."""
    blocks=[]
    def add_block(x, depth=0):
        tag=ln(x.tag)
        if tag=="alineagroep":
            for c in list(x):
                if ln(c.tag) in {"al","alineagroep"}:
                    add_block(c, depth + (1 if ln(c.tag)=="alineagroep" else 0))
            return
        txt=text_all(x)
        if not txt: return
        attrs={}
        for key in ("align","valign","role","class","type"):
            if x.get(key) is not None: attrs[key]=x.get(key)
        blocks.append({"text":txt,"indent":depth,"attrs":attrs})
    for c in list(e):
        if ln(c.tag) in {"al","alineagroep"}: add_block(c,0)
    return blocks



def appendix_source_tree(e):
    """Preserve the official appendix XML hierarchy and source order for faithful rendering."""
    def attrs_of(x):
        out={}
        for key in ("align","valign","role","class","type","label","id","name"):
            if x.get(key) is not None: out[key]=x.get(key)
        return out
    def convert(x):
        tag=ln(x.tag)
        if tag=="meta-data": return None
        if tag=="plaatje":
            illustration=next((c for c in x.iter() if ln(c.tag)=="illustratie"),None)
            if illustration is not None:
                return {"kind":"image","tag":tag,"name":illustration.get("naam") or "",
                        "alt":illustration.get("alt") or text_all(x),
                        "width":illustration.get("breedte") or "","height":illustration.get("hoogte") or "",
                        "display":illustration.get("display") or "block","attrs":attrs_of(x)}
        if tag=="table":
            rows=table_rows(x)
            columns=table_columns(x)
            return {"kind":"table","tag":tag,"number":table_identity(x),"title":title(x),
                    "rows":rows,"columns":columns,"attrs":attrs_of(x),
                    **table_layout(rows,columns)}
        if tag=="kop":
            nr=""; ttl=""
            for c in list(x):
                if ln(c.tag)=="nr": nr=text_all(c)
                elif ln(c.tag)=="titel": ttl=text_all(c)
            return {"kind":"heading","tag":tag,"number":nr,"title":ttl,
                    "text":text_all(x),"attrs":attrs_of(x)}
        if tag in {"al","alineagroep"}:
            # Alineagroep is a container; keep nested paragraphs separate.
            nested=[convert(c) for c in list(x) if ln(c.tag) in {"al","alineagroep","table","lijst","li"}]
            nested=[v for v in nested if v]
            if tag=="alineagroep" and nested:
                return {"kind":"group","tag":tag,"attrs":attrs_of(x),"children":nested}
            return {"kind":"paragraph","tag":tag,"text":text_all(x),"attrs":attrs_of(x)}
        if tag=="li":
            kids=[convert(c) for c in list(x) if ln(c.tag) not in {"li.nr","kop"}]
            kids=[v for v in kids if v]
            return {"kind":"list_item","tag":tag,"number":li_number(x),
                    "text":own_visible_text(x),"attrs":attrs_of(x),"children":kids}
        kids=[convert(c) for c in list(x)]
        kids=[v for v in kids if v]
        own=own_visible_text(x) if tag not in SKIP else ""
        if kids or own:
            return {"kind":"container","tag":tag,"number":number(x,STRUCT.get(tag,"")) if tag in STRUCT else None,
                    "title":title(x),"text":own,"attrs":attrs_of(x),"children":kids}
        return None
    out=[]
    for c in list(e):
        v=convert(c)
        if v: out.append(v)
    return out

def table_columns(e):
    """Preserve CALS column widths/alignment from the official regulation XML."""
    cols=[]
    for x in e.iter():
        if ln(x.tag)!="colspec": continue
        d={}
        for key in ("colname","colnum","colwidth","align","char","charoff"):
            if x.get(key) is not None: d[key]=x.get(key)
        cols.append(d)
    return cols

def descendant_search_text(e):
    out=[]
    def rec(x):
        if ln(x.tag)=="meta-data": return
        if x.text: out.append(x.text)
        for c in list(x):
            rec(c)
            if c.tail: out.append(c.tail)
    rec(e)
    return clean("".join(out))

def _table_colspecs(table):
    """Return XML column-name -> zero-based index mapping."""
    names=[]
    for x in table.iter():
        if ln(x.tag)=="colspec":
            n=x.get("colname") or x.get("name") or x.get("id")
            if n:
                names.append(n)
    return {n:i for i,n in enumerate(names)}

def _cell_span(cell, colspec_map, current_col):
    """Read rowspan/colspan from common BWB/TEI table encodings."""
    rowspan=1
    colspan=1

    # HTML-like attributes.
    for key in ("rowspan","morerows"):
        val=cell.get(key)
        if val:
            try:
                n=int(val)
                rowspan=max(1, n if key=="rowspan" else n+1)
            except ValueError:
                pass

    val=cell.get("colspan")
    if val:
        try:
            colspan=max(1,int(val))
        except ValueError:
            pass

    # CALS/TEI namest/nameend encodes a horizontal span.
    namest=cell.get("namest") or cell.get("start")
    nameend=cell.get("nameend") or cell.get("end")
    if namest and nameend and namest in colspec_map and nameend in colspec_map:
        colspan=max(1,colspec_map[nameend]-colspec_map[namest]+1)
    elif namest and namest in colspec_map:
        colspan=max(1,colspec_map[namest]-current_col+1)

    return rowspan,colspan

def table_rows(e):
    """
    Preserve the table structure, not just flattened cell text.

    Each cell is stored as:
      {"text": ..., "rowspan": N, "colspan": N, "attrs": {...}}

    The legacy viewer can still read the "text" value, while viewer_zoekbalk1_15 can render
    exact row/column spans from a freshly built official XML graph.
    """
    colspec_map=_table_colspecs(e)
    rows=[]
    # CALS tables omit cells that are covered by a vertical span.  Keep an
    # occupancy map so that every source cell receives its actual column.
    # This makes the browser rendering and the validation deterministic.
    active_spans={}
    header_rows={id(r) for sec in e.iter() if ln(sec.tag)=="thead" for r in sec.iter() if ln(r.tag)=="row"}
    for row_index,row in enumerate(x for x in e.iter() if ln(x.tag)=="row"):
        is_header=id(row) in header_rows
        cells=[]
        occupied=set(active_spans)
        current_col=0
        next_spans={column:{"remaining":span["remaining"]-1,"cell":span["cell"]}
                    for column,span in active_spans.items() if span["remaining"]>1}
        for c in list(row):
            if ln(c.tag) not in {"entry","cell"}:
                continue
            text=clean(" ".join(c.itertext()))
            preferred=colspec_map.get(c.get("colname") or c.get("namest") or c.get("start"))
            if preferred is None:
                while current_col in occupied:
                    current_col += 1
                column=current_col
            else:
                column=preferred
            rowspan,colspan=_cell_span(c,colspec_map,column)
            # An explicit CALS colname starts a new visual cell. Some official
            # BWB tables use it to terminate an earlier morerows span one row
            # before its nominal end. Clamp that preceding span here instead
            # of shifting the new cell into a non-existent extra column.
            if preferred is not None:
                # A few BWB header rows contain an empty spanning cell followed
                # by an explicitly placed cell in its final column.  Clip the
                # earlier empty span to that boundary so HTML receives one
                # unambiguous cell per grid position.
                for prior in list(cells):
                    prior_start=int(prior["column"])
                    prior_end=prior_start+int(prior["colspan"])
                    if prior_start<column<prior_end:
                        prior["colspan"]=max(1,column-prior_start)
                occupied=set(active_spans)
                for prior in cells:
                    occupied.update(range(int(prior["column"]),int(prior["column"])+int(prior["colspan"])))
                conflicts={id(active_spans[col]["cell"]):active_spans[col]["cell"]
                           for col in range(column,column+colspan) if col in active_spans}
                for prior in conflicts.values():
                    prior["rowspan"]=max(1,row_index-int(prior["row"]))
                    for col,span in list(active_spans.items()):
                        if span["cell"] is prior:
                            active_spans.pop(col,None)
                            next_spans.pop(col,None)
                    occupied=set(active_spans)
            current_col=column+colspan
            attrs={}
            for key in ("align","valign","colwidth","morerows","rowspan","colspan","colname","colnum",
                        "namest","nameend","start","end"):
                if c.get(key) is not None:
                    attrs[key]=c.get(key)
            cells.append({
                "text":text,
                "row":row_index,
                "column":column,
                "rowspan":rowspan,
                "colspan":colspan,
                "attrs":attrs,
                "header":is_header
            })
            for covered in range(column,column+colspan):
                occupied.add(covered)
                if rowspan>1:
                    next_spans[covered]={"remaining":rowspan-1,"cell":cells[-1]}
        if cells:
            rows.append(cells)
        active_spans=next_spans
    return rows

def table_layout(rows, columns):
    """Return structural facts about a parsed table for rendering and checks."""
    expected=len(columns)
    width=max([expected]+[max((int(c.get("column",0))+int(c.get("colspan",1)) for c in row),default=0) for row in rows])
    issues=[]
    occupied={}
    for ri,row in enumerate(rows):
        current=set()
        for cell in row:
            start=int(cell.get("column",0)); span=max(1,int(cell.get("colspan",1)))
            for col in range(start,start+span):
                if (ri,col) in occupied or col in current:
                    issues.append(f"overlap row={ri} column={col}")
                current.add(col)
                for offset in range(max(1,int(cell.get("rowspan",1)))):
                    occupied[(ri+offset,col)]=True
        if expected and any(int(c.get("column",0))+int(c.get("colspan",1))>expected for c in row):
            issues.append(f"outside declared columns row={ri}")
    return {"grid_columns":width,"layout_issues":issues}

def table_identity(e):
    """Return a stable legal table number independent of XML id/label spelling."""
    candidates=[]
    for key in ("id", "label", "naam", "nr", "number"):
        raw=str(e.get(key) or "").strip()
        if raw: candidates.append(raw)
    # Also inspect direct child numbering/heading elements.
    for c in list(e):
        if ln(c.tag) in {"nr","naam","titel","label"}:
            raw=text_all(c)
            if raw: candidates.append(raw)
    for raw in candidates:
        m=re.search(r"(?:tabel|table)[\s_-]*([0-9]+(?:\.[0-9]+)*[a-z]?)\b",raw,re.I)
        if m:return m.group(1)
        m=re.fullmatch(r"[0-9]+(?:\.[0-9]+)*[a-z]?",raw,re.I)
        if m:return m.group(0)
    return None

def target_from_text(anchor):
    """Parse a legal reference into a type/number pair. Qualifiers are retained separately."""
    s=clean(anchor)
    patterns=[
      ("table",r"(?:tabel|table)\s*([0-9]+(?:\.[0-9]+)*[a-z]?)"),
      ("appendix",r"bijlage\s+([A-Za-z0-9IVXLCDM]+(?:\.[A-Za-z0-9]+)*)"),
      ("article",r"(?:artikel|art\.?)\s*([0-9]+(?:\.[0-9]+)*[a-z]?)"),
      ("paragraph",r"(?:paragraaf|§)\s*([0-9]+(?:\.[0-9]+)*[a-z]?)"),
      ("section",r"afdeling\s+([0-9]+(?:\.[0-9]+)*[a-z]?)"),
      ("chapter",r"hoofdstuk\s+([0-9]+(?:\.[0-9]+)*|[IVX]+)")
    ]
    for typ,pat in patterns:
        m=re.search(pat,s,re.I)
        if m:return {"type":typ,"number":m.group(1),"anchor":s}
    return {}

REF_QUAL = r"(?:\s*,\s*(?:eerste|tweede|derde|vierde|vijfde|zesde|zevende|achtste|negende|tiende)(?:\s+en\s+(?:eerste|tweede|derde|vierde|vijfde|zesde|zevende|achtste|negende|tiende))?(?:\s+lid)?(?:\s*,?\s*onderdeel\s+[a-z])?)?"

LEGAL_REF_RE = re.compile(
    r"\b(?:artikel|art\.?|paragraaf|§|afdeling|hoofdstuk|tabel|table|bijlage)\s+"
    r"(?:[0-9]+(?:\.[0-9]+)*[a-z]?|[IVXLCDM]+(?:[a-z]+)?)" + REF_QUAL, re.I)

def scan_refs(root, nodes, by_id):
    refs=[]
    known_external=re.compile(
      r"\b(BWBR\d{7,}|Omgevingswet|Besluit activiteiten leefomgeving|"
      r"Besluit bouwwerken leefomgeving|Besluit kwaliteit leefomgeving|"
      r"Omgevingsbesluit|Omgevingsregeling|Vuurwerkbesluit)\b",re.I)

    for node in nodes:
        raw=node.get("text","")
        if not raw: continue
        anchors=[]
        for m in LEGAL_REF_RE.finditer(raw):
            anchors.append((m.group(0),"internal",target_from_text(m.group(0))))
        # § references are included in LEGAL_REF_RE; external names are kept.
        for m in known_external.finditer(raw):
            anchors.append((m.group(1),"external",{}))
        seen=set()
        for anchor,kind,target in anchors:
            key=(node["id"],anchor,kind,target.get("type"),target.get("number"))
            if key in seen: continue
            seen.add(key)
            refs.append({
              "id":f"ref-{len(refs)+1}",
              "source":node["id"],
              "source_bwb":None,
              "anchor":anchor,
              "kind":kind,
              "target":target,
              "target_bwb":None,
            })
    return refs



def glossary_key(bwb_id, appendix_number, section, term):
    """Stabiele functionele sleutel; nooit afhankelijk van n123-nodevolgorde."""
    norm=lambda v: clean(str(v or "")).casefold()
    return "|".join([str(bwb_id or "UNKNOWN").upper(), norm(appendix_number), norm(section), norm(term)])


def extract_glossary(root, nodes, bwb_id=None):
    """Bouw de begrippenindex uit de officiële begrippenbijlage.

    V320 behandelt ieder BAL-begrip als één bronblok: vanaf de alinea waarin
    het begrip begint tot vlak vóór het volgende begrip op hetzelfde niveau.
    Onderliggende lijsten/inspringingen blijven onderdeel van dezelfde
    definitie en worden niet als zelfstandige begrippen geïnterpreteerd.
    """
    by_id={n["id"]:n for n in nodes}
    appendix_ids=set(); appendix_numbers={}
    for n in nodes:
        if n.get("type")!="appendix": continue
        no=clean(str(n.get("number") or ""))
        hay=clean(" ".join([no,str(n.get("title") or ""),str(n.get("text") or "")])).casefold()
        # De Omgevingswet noemt in de titel uitsluitend "bij artikel 1.1";
        # de aanduiding "Begrippen" staat daaronder in divisie A.
        if ("begrip" in hay or "artikel 1.1" in hay
                or (str(bwb_id or "").upper()=="BWBR0041330" and no.upper() in {"I","1"})):
            appendix_ids.add(n["id"]); appendix_numbers[n["id"]]=no or "I"

    found=[]; seen=set()
    def add(term, definition, source_node, aid, section="A", extraction="structured"):
        term=clean(term).rstrip(" :;")
        # Definitie bewust NIET met clean() platmaken: regeleinden en
        # inspringingen uit de officiële bron moeten zichtbaar blijven.
        definition=str(definition or "").replace("\r\n","\n").replace("\r","\n")
        definition="\n".join(line.rstrip() for line in definition.split("\n")).strip().rstrip(";")
        if not term or not definition or len(term)>160:return
        if len(term.split())>16 or term.endswith(('.',':',';')):return
        appno=appendix_numbers.get(aid,"I")
        key=glossary_key(bwb_id,appno,section,term)
        nk=clean(term).casefold()
        if nk in seen:return
        seen.add(nk)
        found.append({
          "key":key,"term":term,"term_normalized":nk,
          "definition":definition,
          "definition_text":clean(definition),
          "bwb_id":str(bwb_id or "").upper() or None,"appendix":appno,
          "section":section,"source_node":source_node,"appendix_id":aid,
          "extraction":extraction
        })

    # BAL: officiële BWB-structuur Bijlage I -> Divisie A.
    if str(bwb_id or "").upper()=="BWBR0041330":
        xml_appendix=None
        for e in root.iter():
            if ln(e.tag)!="bijlage": continue
            label=clean(e.get("label") or "")
            path=e.get("bwb-ng-variabel-deel") or ""
            kop=next((c for c in list(e) if ln(c.tag)=="kop"),None)
            koptxt=text_all(kop) if kop is not None else ""
            if label.casefold()=="bijlage i" or path.endswith("/BijlageI") or "bijlage i" in koptxt.casefold():
                xml_appendix=e; break

        aid=next((x for x in appendix_ids if appendix_numbers.get(x,"I").upper() in {"I","1"}),None)
        if aid is None and appendix_ids: aid=next(iter(appendix_ids))

        division_a=None
        if xml_appendix is not None:
            for c in list(xml_appendix):
                if ln(c.tag)!="divisie": continue
                kop=next((x for x in list(c) if ln(x.tag)=="kop"),None)
                if kop is None: continue
                nr=""; titel=""
                for x in list(kop):
                    if ln(x.tag)=="nr": nr=text_all(x)
                    elif ln(x.tag)=="titel": titel=text_all(x)
                if clean(nr).upper()=="A" or clean(nr+" "+titel).casefold().startswith("a begrippen"):
                    division_a=c; break

        def entry_start(e):
            if ln(e.tag)!="al": return None
            s=text_all(e)
            emph=[x for x in list(e) if ln(x.tag)=="nadruk" and (x.get("type") or "").casefold()=="cur"]
            if emph:
                term=clean(text_all(emph[0])).rstrip(" :;")
                if term and ":" in s[:len(term)+10]: return term
            m=re.match(r"^(.{1,160}?)\s*:\s*(.*)$",s)
            if m and not m.group(1).casefold().startswith("voor de toepassing"):
                return clean(m.group(1)).rstrip(" :;")
            return None

        def block_lines(e, depth=0):
            """Zet één XML-bronblok om in leesbare tekst met inspringing."""
            tag=ln(e.tag); indent="    "*depth
            if tag in {"meta-data","kop"}: return []
            if tag=="al":
                txt=text_all(e)
                return [indent+txt] if txt else []
            if tag=="lijst":
                out=[]
                for li in [x for x in list(e) if ln(x.tag)=="li"]:
                    nr=next((text_all(x) for x in list(li) if ln(x.tag)=="li.nr"),"")
                    direct_als=[x for x in list(li) if ln(x.tag)=="al"]
                    first=text_all(direct_als[0]) if direct_als else ""
                    prefix=(nr+" ") if nr else ""
                    if first or prefix: out.append(indent+prefix+first)
                    for extra_al in direct_als[1:]:
                        t=text_all(extra_al)
                        if t: out.append(indent+"    "+t)
                    for child in list(li):
                        if ln(child.tag)=="lijst": out.extend(block_lines(child,depth+1))
                return out
            txt=text_all(e)
            return [indent+txt] if txt else []

        if division_a is not None and aid is not None:
            current_term=None; current_lines=[]
            for c in list(division_a):
                term=entry_start(c)
                if term:
                    if current_term:
                        add(current_term,"\n".join(current_lines),aid,aid,"A","bwb_division_a_block")
                    current_term=term
                    full=text_all(c); pos=full.find(":")
                    first=clean(full[pos+1:]) if pos>=0 else ""
                    current_lines=[first] if first else []
                elif current_term and ln(c.tag) not in {"kop","meta-data"}:
                    current_lines.extend(block_lines(c,0))
            if current_term:
                add(current_term,"\n".join(current_lines),aid,aid,"A","bwb_division_a_block")

        found.sort(key=lambda x:(-len(x["term"]),x["term_normalized"]))
        by_key={x["key"]:x for x in found}
        by_term={x["term_normalized"]:x["key"] for x in found}
        controls={t:bool(t in by_term) for t in [
          "aaneengesloten bodemvoorziening","bodembeschermende voorziening","lekbak","seveso-inrichting"
        ]}
        complete=bool(division_a is not None and len(found)>=100 and all(controls.values()))
        return found,{"by_key":by_key,"by_term":by_term},{
          "appendix_found":bool(xml_appendix is not None),"appendix_ids":sorted(appendix_ids),
          "section_a_found":bool(division_a is not None),"count":len(found),
          "control_terms":controls,"complete":complete,"method":"bwb_division_a_block"
        }

    # V332: bronblokextractie voor de overige regelingen.
    # De officiële BWB-bijlage is leidend: ieder <al> dat met een cursief
    # begrip plus dubbele punt begint, start een nieuw begrip. Alles tot het
    # volgende begrip blijft bij dezelfde definitie horen.
    def source_entry_start(e):
        if ln(e.tag)!="al": return None
        s=text_all(e)
        emph=[x for x in list(e) if ln(x.tag)=="nadruk" and (x.get("type") or "").casefold()=="cur"]
        if emph:
            term=clean(text_all(emph[0])).rstrip(" :;")
            if term and ":" in s[:len(term)+12]: return term
        m=re.match(r"^(.{1,160}?)\s*:\s*(.*)$",s)
        if m and not m.group(1).casefold().startswith("voor de toepassing"):
            return clean(m.group(1)).rstrip(" :;")
        return None

    def source_block_lines(e, depth=0):
        tag=ln(e.tag); indent="    "*depth
        if tag in {"meta-data","kop"}: return []
        if tag=="al":
            txt=text_all(e); return [indent+txt] if txt else []
        if tag=="lijst":
            out=[]
            for li in [x for x in list(e) if ln(x.tag)=="li"]:
                nr=next((text_all(x) for x in list(li) if ln(x.tag)=="li.nr"),"")
                als=[x for x in list(li) if ln(x.tag)=="al"]
                first=text_all(als[0]) if als else ""
                if nr or first: out.append(indent+((nr+" ") if nr else "")+first)
                for extra in als[1:]:
                    t=text_all(extra)
                    if t: out.append(indent+"    "+t)
                for child in list(li):
                    if ln(child.tag)=="lijst": out.extend(source_block_lines(child,depth+1))
            return out
        txt=text_all(e); return [indent+txt] if txt else []

    xml_candidates=[]
    for e in root.iter():
        if ln(e.tag)!="bijlage": continue
        kop=next((c for c in list(e) if ln(c.tag)=="kop"),None)
        koptxt=clean(text_all(kop) if kop is not None else "")
        # De Omgevingswet noemt in de bijlagekop alleen het artikelnummer;
        # "Begrippen" staat pas in divisie A. De overige regelingen noemen
        # Begrippen al in de bijlagekop.
        is_ow_glossary="artikel 1.1" in koptxt.casefold()
        if "begrip" in koptxt.casefold() or is_ow_glossary:
            xml_candidates.append(e)
    for xml_app in xml_candidates:
        kop=next((c for c in list(xml_app) if ln(c.tag)=="kop"),None)
        appno=""
        if kop is not None:
            appno=next((clean(text_all(x)) for x in list(kop) if ln(x.tag)=="nr"),"")
        aid=next((x for x in appendix_ids if clean(appendix_numbers.get(x,"" )).casefold()==clean(appno).casefold()),None)
        if aid is None and len(appendix_ids)==1: aid=next(iter(appendix_ids))
        if aid is None: continue
        containers=[]
        for c in list(xml_app):
            if ln(c.tag)=="divisie":
                ck=next((x for x in list(c) if ln(x.tag)=="kop"),None)
                ckt=clean(text_all(ck) if ck is not None else "")
                if "begrip" in ckt.casefold() or ckt.casefold().startswith("a "): containers.append((c,"A"))
        if not containers: containers=[(xml_app,"A")]
        for container,section in containers:
            current_term=None; current_lines=[]
            for c in list(container):
                term=source_entry_start(c)
                if term:
                    if current_term: add(current_term,"\n".join(current_lines),aid,aid,section,"bwb_glossary_block")
                    current_term=term
                    full=text_all(c); pos=full.find(":")
                    first=clean(full[pos+1:]) if pos>=0 else ""
                    current_lines=[first] if first else []
                elif current_term and ln(c.tag) not in {"kop","meta-data"}:
                    current_lines.extend(source_block_lines(c,0))
            if current_term: add(current_term,"\n".join(current_lines),aid,aid,section,"bwb_glossary_block")

    if found:
        found.sort(key=lambda x:(-len(x["term"]),x["term_normalized"]))
        by_key={x["key"]:x for x in found}; by_term={x["term_normalized"]:x["key"] for x in found}
        return found,{"by_key":by_key,"by_term":by_term},{
          "appendix_found":bool(appendix_ids),"appendix_ids":sorted(appendix_ids),"section_a_found":True,
          "count":len(found),"control_terms":{},"complete":True,"method":"bwb_glossary_block"
        }

    # Generieke fallback alleen wanneer de officiële bronblokstructuur niet is aangetroffen.
    def ancestry(n):
        out=[]; cur=n; seen_ids=set()
        while cur and cur.get("id") not in seen_ids:
            seen_ids.add(cur.get("id")); out.append(cur); cur=by_id.get(cur.get("parent"))
        return out
    def glossary_context(n):
        chain=ancestry(n)
        aid=next((x.get("id") for x in chain if x.get("id") in appendix_ids),None)
        if not aid:return None,None
        section="A"
        for x in reversed(chain):
            no=clean(str(x.get("number_raw") or x.get("number") or ""))
            if re.fullmatch(r"[A-Z]",no): section=no.upper()
        return aid,section
    for n in nodes:
        aid,section=glossary_context(n)
        if not aid or n.get("id")==aid or n.get("type") in {"table","appendix"}:continue
        term=clean(str(n.get("title") or "")); definition=clean(str(n.get("text") or ""))
        if term and definition:add(term,definition,n.get("id"),aid,section,"graph_title_text")
        elif definition:
            m=re.match(r"^(.{2,160}?)\s*(?::|[–—])\s+(.{3,})$",definition)
            if m:add(m.group(1),m.group(2),n.get("id"),aid,section,"graph_pair")
    found.sort(key=lambda x:(-len(x["term"]),x["term_normalized"]))
    by_key={x["key"]:x for x in found}; by_term={x["term_normalized"]:x["key"] for x in found}
    return found,{"by_key":by_key,"by_term":by_term},{
      "appendix_found":bool(appendix_ids),"appendix_ids":sorted(appendix_ids),"count":len(found),
      "control_terms":{},"complete":False,"method":"generic"
    }

def parse(input_path,output_path):
    src=Path(input_path); dst=Path(output_path)
    if not src.exists(): raise FileNotFoundError(f"XML niet gevonden: {src}")

    parser=ET.XMLParser()
    root=ET.parse(src,parser).getroot()

    nodes=[]
    stack=[]
    parent_by_id={}
    def walk(e,parent=None):
        tag=ln(e.tag)
        typ=STRUCT.get(tag)
        current=parent
        if typ:
            nid=f"n{len(nodes)+1}"
            n={
              "id":nid,"type":typ,"number":number(e,typ),
              "title":title(e),"parent":parent["id"] if parent else None,
              "text":own_visible_text(e),
              "illustrations":own_illustrations(e),
              "external_refs":external_refs(e),
              "blocks":direct_visible_blocks(e) if typ=="appendix" else [],
              "source_tree":appendix_source_tree(e) if typ=="appendix" else [],
              "search_text_exact":"",
              "_full_search_text":descendant_search_text(e) if typ=="article" else "",
              "children":[],"_xml_order":len(nodes),
              "_ancestors":[{k:v for k,v in x.items() if not k.startswith("_") and k not in {"external_refs"}}
                            for x in stack]
            }
            if typ=="member" and not n["number"]: n["number"]=number(e,typ)
            if tag=="li":
                n["type"]="item"; n["number"]=li_number(e)
            enum=normalize_legal_enumeration(n.get("number"),n.get("type"))
            if enum.get("number_raw"):
                n.update(enum)
            nodes.append(n)
            parent_by_id[nid]=parent["id"] if parent else None
            if parent: parent["children"].append(nid)
            current=n
            stack.append(n)
        # Tables can occur under articles and are deliberately retained.
        if tag=="table":
            nid=f"n{len(nodes)+1}"
            rows=table_rows(e)
            columns=table_columns(e)
            n={"id":nid,"type":"table","number":table_identity(e),
               "title":title(e),"parent":parent["id"] if parent else None,
               "text":clean(" ".join(" | ".join(str(c.get("text","")) if isinstance(c,dict) else str(c) for c in r) for r in rows)),
               "external_refs":external_refs(e, clean(" ".join(" | ".join(str(c.get("text","")) if isinstance(c,dict) else str(c) for c in r) for r in rows))),
               "search_text_exact":clean(" ".join(" | ".join(str(c.get("text","")) if isinstance(c,dict) else str(c) for c in r) for r in rows)),
               "rows":rows,"columns":columns,"table_layout_version":4,"children":[],"_xml_order":len(nodes),
               **table_layout(rows,columns),
               "_ancestors":[{k:v for k,v in x.items() if not k.startswith("_") and k not in {"external_refs"}} for x in stack]}
            nodes.append(n)
            if parent: parent["children"].append(nid)
            # table is a boundary; do not recurse as legal descendants
            return
        for c in list(e):
            walk(c,current)
        if typ: stack.pop()

    walk(root)

    # v1.27: artikelen indexeren met hun volledige eigen inhoud, inclusief leden en tabellen.
    # Andere juridische elementen houden hun eigen inhoud. Hierdoor is de zoekactie
    # een gewone substringzoekactie, terwijl een artikel ook matcht als de zoekterm
    # uitsluitend in een lid of tabel van dat artikel voorkomt.
    by_id={n["id"]:n for n in nodes}
    for n in nodes:
        pieces=[]
        if n.get("number"): pieces.append(str(n["number"]))
        if n.get("title"): pieces.append(str(n["title"]))
        if n.get("type")=="article":
            # Gebruik de volledige XML-inhoud van dit artikel, inclusief intref
            # tekst die geen apart legal-graph-node vormt.
            if n.get("_full_search_text"): pieces.append(str(n["_full_search_text"]))
            elif n.get("text"): pieces.append(str(n["text"]))
        elif n.get("text"):
            pieces.append(str(n["text"]))
        n["search_text_exact"]=clean(" ".join(pieces))
        n.pop("_full_search_text",None)

    # V204: maak de structurele relatie artikel -> lid -> tabel/bijlage
    # expliciet. Een artikel kan uit precies één, onaangeduid lid bestaan.
    # In dat geval hoeft er in de tekst geen "tabel ..."-verwijzing te staan,
    # terwijl de tabel wel onderdeel is van dat artikel.
    by_id={n["id"]:n for n in nodes}
    children_by_parent={}
    for n in nodes:
        parent_id=n.get("parent")
        if parent_id:
            children_by_parent.setdefault(str(parent_id),[]).append(n)

    def ancestor_article(n):
        cur=n
        seen=set()
        while cur and str(cur.get("id")) not in seen:
            seen.add(str(cur.get("id")))
            if cur.get("type")=="article":
                return cur
            cur=by_id.get(str(cur.get("parent"))) if cur.get("parent") else None
        return None

    # Eerst bepalen welke leden daadwerkelijk onder ieder artikel vallen.
    # Een enkel lid zonder lidnummer blijft bewust onaangeduid.
    for ar in [n for n in nodes if n.get("type")=="article"]:
        direct_members=[x for x in children_by_parent.get(ar["id"],[])
                        if x.get("type") in {"member","paragraph_member"}]
        # In oudere/afwijkende BWB-structuren kunnen leden nog via een wrapper
        # lopen; verzamel daarom ook directe lid-afstammelingen tot het eerste
        # artikelgrenspunt.
        if not direct_members:
            stack=list(children_by_parent.get(ar["id"],[]))
            seen=set()
            while stack:
                x=stack.pop()
                if not x or x["id"] in seen: continue
                seen.add(x["id"])
                if x.get("type") in {"article","chapter","section","paragraph","subparagraph"}:
                    continue
                if x.get("type") in {"member","paragraph_member"}:
                    direct_members.append(x)
                    continue
                stack.extend(children_by_parent.get(x["id"],[]))
        ar["member_count"]=len(direct_members)
        ar["single_unnumbered_member"]=bool(len(direct_members)==1 and not str(direct_members[0].get("number") or "").strip())
        ar["single_member_id"]=direct_members[0]["id"] if len(direct_members)==1 else None
        ar["article_attachments"]=[]

    # Koppel iedere tabel/bijlage die structureel onder een artikel valt aan
    # het dichtstbijzijnde artikel. Dit is de primaire bron voor kolom 3; een
    # expliciete tekstverwijzing blijft daarnaast gewoon een geldige route.
    for n in nodes:
        if n.get("type") not in {"table","appendix"}:
            continue
        ar=ancestor_article(n)
        if not ar:
            continue
        n["article_id"]=ar["id"]
        n["article_number"]=ar.get("number")
        # Bewaar het directe lid waaronder de tabel staat, als dat er is.
        cur=n
        member=None
        seen=set()
        while cur and cur.get("id") not in seen:
            seen.add(cur.get("id"))
            if cur.get("type") in {"member","paragraph_member"}:
                member=cur
                break
            cur=by_id.get(str(cur.get("parent"))) if cur.get("parent") else None
        n["article_member_id"]=member.get("id") if member else None
        n["article_member_number"]=member.get("number") if member else None
        # V550-regel: een tabel die werkelijk onder het ENIGE lid
        # van het artikel staat, wordt automatisch inline in kolom 2 getoond.
        # Een artikel waarvoor geen lid-node is gevonden (member_count == 0)
        # wordt nadrukkelijk NIET als deze situatie geïnterpreteerd.
        n["display_mode"] = (
            "inline"
            if n.get("type") == "table"
            and ar.get("member_count") == 1
            and member is not None
            and member.get("id") == ar.get("single_member_id")
            else "linked"
        )
        ar["article_attachments"].append(n["id"])

    # Sorteer structurele bijlagen in bronvolgorde en markeer tabellen die via
    # het enige onaangeduide lid zijn bereikt.
    for ar in [n for n in nodes if n.get("type")=="article"]:
        ar["article_attachments"]=list(dict.fromkeys(ar.get("article_attachments",[])))
        if ar.get("member_count") == 1:
            ar["attachment_route"]="single_member"
        elif ar.get("article_attachments"):
            ar["attachment_route"]="article_subtree"
        else:
            ar["attachment_route"]="none"

    # Remove private ancestry before output.
    for n in nodes:
        n.pop("_ancestors",None)

    # References are based on actual node text and are never invented from
    # parent/child relationships.
    refs=scan_refs(root,nodes,{n["id"]:n for n in nodes})

    # V311: een tabel kan in de BWB-XML als zelfstandige tabelstructuur naast
    # het artikel staan, terwijl de artikeltekst zelf rechtstreeks naar die
    # tabel verwijst. Dit is geen lid-relatie. Wanneer een artikel rechtstreeks
    # verwijst naar een bestaande tabel met exact hetzelfde juridische nummer
    # (bijv. artikel 4.34 -> tabel 4.34), is dat een betrouwbare artikel-tabel-
    # relatie. De tabel wordt dan inline bij dat artikel weergegeven.
    def ref_norm(v):
        return re.sub(r"\s+", "", str(v or "").strip().lower()).rstrip(".)")

    table_by_number={}
    for t in [x for x in nodes if x.get("type")=="table"]:
        candidates=[t.get("number"), t.get("title")]
        tno=None
        for candidate in candidates:
            if not candidate:
                continue
            m=re.search(r"(?:tabel|table)?\s*([0-9]+(?:\.[0-9]+)*[a-z]?)", str(candidate), re.I)
            if m:
                tno=ref_norm(m.group(1)); break
        if tno:
            table_by_number.setdefault(tno,[]).append(t)

    for ref in refs:
        target=ref.get("target") or {}
        if target.get("type")!="table":
            continue
        ref_source=by_id.get(str(ref.get("source")))
        if not ref_source:
            continue
        # De verwijzing kan op de article-node zelf staan, of in het enige
        # lid van dat artikel. Beide zijn dezelfde juridische
        # artikelcontext; er wordt geen lidnummer verzonnen.
        if ref_source.get("type")=="article":
            source=ref_source
        elif ref_source.get("type") in {"member","paragraph_member"}:
            source=ancestor_article(ref_source)
            if not source or source.get("member_count") != 1 or source.get("single_member_id")!=ref_source.get("id"):
                continue
        else:
            continue
        article_no=ref_norm(source.get("number"))
        target_no=ref_norm(target.get("number"))
        if not article_no or target_no!=article_no:
            continue
        candidates=table_by_number.get(target_no,[])
        relation="direct_article_table"
        # V311: sommige officiële BWB-tabellen hebben geen bruikbaar nummer op
        # de fysieke <table>-node. In dat geval mag een rechtstreekse verwijzing
        # artikel X -> tabel X uitsluitend worden gekoppeld aan de ENIGE
        # ongenummerde tabel die in bronvolgorde direct na dit artikel staat en
        # vóór het volgende artikel begint. Zo gebruiken we documentstructuur en
        # bronvolgorde, niet een globale gok op alleen het tabelnummer.
        if len(candidates)!=1:
            source_order=int(source.get("_xml_order",-1))
            later_articles=[x for x in nodes if x.get("type")=="article" and int(x.get("_xml_order",-1))>source_order]
            next_article_order=min((int(x.get("_xml_order")) for x in later_articles), default=10**12)
            unnamed=[x for x in nodes if x.get("type")=="table"
                     and not ref_norm(x.get("number"))
                     and source_order < int(x.get("_xml_order",-1)) < next_article_order
                     and (not x.get("article_id") or x.get("article_id")==source.get("id"))]
            if len(unnamed)!=1:
                continue
            table=unnamed[0]
            relation="direct_article_table_by_source_order"
        else:
            table=candidates[0]
        # Een reeds structureel aan een ander artikel gekoppelde tabel wordt
        # nooit verplaatst op basis van alleen tekst.
        if table.get("article_id") and table.get("article_id")!=source.get("id"):
            continue
        table["article_id"]=source["id"]
        table["article_number"]=source.get("number")
        table["article_member_id"]=None
        table["article_member_number"]=None
        table["display_mode"]="inline"
        table["attachment_relation"]=relation
        table["direct_article_reference"]=ref.get("anchor")
        source.setdefault("article_attachments",[])
        if table["id"] not in source["article_attachments"]:
            source["article_attachments"].append(table["id"])
        source["attachment_route"]=relation

    # Mark source BWB from XML metadata when available.
    bwb=None
    for e in root.iter():
        for k,v in e.attrib.items():
            if "bwb" in k.lower() and str(v).upper().startswith("BWBR"):
                bwb=str(v).upper()
        if not bwb and e.text and "BWBR" in e.text:
            m=re.search(r"BWBR\d{7,}",e.text)
            if m:bwb=m.group(0)
    for r in refs:r["source_bwb"]=bwb

    glossary,glossary_index,glossary_stats=extract_glossary(root,nodes,bwb)

    # V321: bouw de koppelingen tussen gewone regelingtekst en de begrippenlijst
    # tijdens het bouwen van de graph. De viewer hoeft daardoor niet te gokken
    # welke begrippen bij een tekstblok horen. Langste begrippen eerst.
    glossary_patterns=[]
    for entry in sorted(glossary,key=lambda x: len(str(x.get("term") or "")),reverse=True):
        term=str(entry.get("term") or "").strip()
        key=str(entry.get("key") or "").strip()
        if not term or not key: continue
        glossary_patterns.append((key,re.compile(r"(?<![\w])"+re.escape(term)+r"(?![\w])",re.I)))
    linked_nodes=0; linked_occurrences=0
    for n in nodes:
        text=str(n.get("text") or "")
        refs_for_node=[]
        if text:
            for key,pat in glossary_patterns:
                matches=list(pat.finditer(text))
                if matches:
                    refs_for_node.append(key)
                    linked_occurrences += len(matches)
        if refs_for_node:
            n["glossary_refs"]=refs_for_node
            linked_nodes += 1
    glossary_stats["linked_nodes"]=linked_nodes
    glossary_stats["linked_occurrences"]=linked_occurrences

    for n in nodes:
        n.pop("_xml_order",None)

    # Clean children for compact graph.
    stats=Counter(n["type"] for n in nodes)
    print("Juridische niveaus:", dict(stats), flush=True)
    graph={
      "schema_version":"14.1-generic-v550",
      "parser":"bwb_parser.py",
      "bwb_id":bwb,
      "source_xml":str(src),
      "nodes":nodes,
      "references":refs,
      "glossary":glossary,
      "glossary_index":glossary_index,
      "glossary_stats":glossary_stats,
      "stats":{"nodes":len(nodes),"references":len(refs),"by_type":dict(stats)}
    }
    dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_suffix(dst.suffix+".tmp")
    tmp.write_text(json.dumps(graph,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    tmp.replace(dst)
    if not dst.exists() or dst.stat().st_size==0: raise RuntimeError("Graph is niet aangemaakt")
    print("GESLAAGD")
    print("Bron XML:",src)
    print("Graph:",dst)
    print("Nodes:",len(nodes))
    print("References:",len(refs))
    print("Begrippen:",len(glossary))
    print("Begrippenbijlage gevonden:", "JA" if glossary_stats.get("appendix_found") else "NEE")
    print("Begrippen onderdeel A gevonden:", "JA" if glossary_stats.get("section_a_found") else "NEE")
    print("Begrippenextractie:", glossary_stats.get("method","onbekend"))
    print("Begrippenlijst compleet:", "JA" if glossary_stats.get("complete") else "NEE")
    for term,ok in glossary_stats.get("control_terms",{}).items():
        print("Begrippencontrole:",term,"=", "OK" if ok else "NIET GEVONDEN")
    print("Types:",dict(stats))
    return 0

def main():
    if len(sys.argv)!=3:
        print("Gebruik:")
        print("  python bwb_parser.py INPUT.xml OUTPUT.json")
        return 2
    try:return parse(sys.argv[1],sys.argv[2])
    except Exception as e:
        print("FOUT:",type(e).__name__,str(e))
        return 1

if __name__=="__main__":
    raise SystemExit(main())
