#!/usr/bin/env python3
"""Bouw artikelgewijze toelichtingen uit de oorspronkelijke officiële NvT's."""
from __future__ import annotations
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
import json,re,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]; SOURCE=ROOT/'data'/'source'; OUT=ROOT/'data'/'article_notes.json'
REGS={'OW':('omgevingswet.xml','ow-original.html'),'BAL':('bal.xml','bal-original.html'),'BBL':('bbl.xml','bbl-original.html'),'BKL':('bkl.xml','bkl-original.html'),'OB':('ob.xml','ob-original.html'),'OR':('or.xml','or-original.html'),'IWO':('invoeringswet_omgevingswet.xml','iwo-original.html')}
ARTICLE=re.compile(r'^Artikel\s+([0-9]+(?:\.[0-9]+)*[a-z]?)\b',re.I)
def local(e):return e.tag.rsplit('}',1)[-1]
def text(e):return ' '.join(''.join(e.itertext()).split())
class Parser(HTMLParser):
 def __init__(self,whole_document=False):super().__init__(convert_charrefs=True);self.tag=None;self.buf=[];self.note=whole_document;self.current=None;self.parts=defaultdict(list)
 def handle_starttag(self,t,a):
  if re.fullmatch(r'h[1-6]',t) or (t=='p' and 'tussenkop' in dict(a).get('class','')):self.tag=t;self.buf=[]
  elif self.current and t in {'p','li','br'}:self.parts[self.current].append('\n')
 def handle_data(self,d):
  if not self.note and re.search(r'artikelsgewijs(?:e)?(?:\s+toelichting)?',d,re.I):
   self.note=True;return
  if self.tag:self.buf.append(d)
  elif self.current:self.parts[self.current].append(d)
 def handle_endtag(self,t):
  if t==self.tag:
   h=' '.join(''.join(self.buf).split());self.tag=None
   if not self.note and 'nota van toelichting' in h.lower():self.note=True;return
   if self.note:
    m=ARTICLE.match(h)
    if m:self.current=m.group(1);self.parts[self.current].append(h+'\n')
    elif self.current and h:self.parts[self.current].append(h+'\n')
  elif self.current and t in {'p','li'}:self.parts[self.current].append('\n')
 def result(self):
  out={}
  for k,v in self.parts.items():
   lines=[]
   for x in ''.join(v).splitlines():
    x=' '.join(x.split())
    if x and (not lines or lines[-1]!=x):lines.append(x)
   if len(lines)>1:out[k]='\n'.join(lines)
  return out
def articles(xml):
 root=ET.parse(xml).getroot();out=[];paragraph=''
 for e in root.iter():
  if local(e)=='paragraaf':paragraph=e.attrib.get('label','')
  if local(e)!='artikel':continue
  label=e.attrib.get('label','');n=label.removeprefix('Artikel ')
  if n:out.append((n,label,paragraph))
 return out
def main():
 all_data={}
 for reg,(xml,name) in REGS.items():
  p=Parser(reg in {'OW','OR'});p.feed((ROOT/'data'/'nvt'/name).read_text(encoding='utf8',errors='replace'));notes=p.result()
  all_data[reg]={n:{'label':label,'paragraph':paragraph,'source':'Oorspronkelijke nota van toelichting','notes':([{'source':'Oorspronkelijke nota van toelichting','url':'','text':notes[n],'shared_for':[]} ] if n in notes else [])} for n,label,paragraph in articles(SOURCE/xml)}
 # BAL hoofdstuk 4 is afzonderlijk gecontroleerd en bevat ook relevante wijzigingsbronnen.
 overlay=json.loads((ROOT/'data'/'article_notes_bal_chapter4.json').read_text(encoding='utf8'))['articles']
 all_data['BAL'].update(overlay)
 OUT.write_text(json.dumps({'regulations':all_data},ensure_ascii=False),encoding='utf8')
 print('Geschreven:',OUT);print(', '.join(f'{k}: {len(v)}' for k,v in all_data.items()))
if __name__=='__main__':main()
