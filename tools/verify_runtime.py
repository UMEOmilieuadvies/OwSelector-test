from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent; APPROOT=ROOT.parent; GRAPH=APPROOT/'data'/'graph'
expected=['ow','bal','bbl','bkl','ob','or']; missing=[]
registry_path=APPROOT/'data'/'external_refs.json'
if not registry_path.exists():raise SystemExit('ONTBREKEND EXTERN-VERWIJZINGENREGISTER')
backref_path=APPROOT/'data'/'back_references.json'
if not backref_path.exists():raise SystemExit('ONTBREKEND TERUGVERWIJZINGENREGISTER')
registry=json.loads(registry_path.read_text(encoding='utf-8'))
backrefs=json.loads(backref_path.read_text(encoding='utf-8'))
if not isinstance(backrefs.get('references'),dict):raise SystemExit('ONGELDIG TERUGVERWIJZINGENREGISTER')
keys={str(row.get('key')) for row in registry.get('references',[])}
checked=0
for stem in expected:
 p=GRAPH/f'{stem}_legal_graph.json'
 if not p.exists():missing.append(stem);continue
 g=json.loads(p.read_text(encoding='utf-8'))
 if not isinstance(g.get('nodes'),list):raise SystemExit(f'ONGELDIGE GRAPH: {p}')
 for node in g['nodes']:
  for ref in node.get('external_refs') or []:
   key=str(ref.get('bwb_id') or ref.get('doc') or '')
   if not ref.get('anchor') or not key or key not in keys:
    raise SystemExit(f'ONGELDIGE EXTERNE VERWIJZING: {p} {ref!r}')
   checked+=1
print(f'Runtimecontrole: {len(expected)-len(missing)}/6 grafen aanwezig.')
print(f'Externe verwijzingen gecontroleerd: {checked}; registerdoelen: {len(keys)}.')
print(f'Terugverwijzingen gecontroleerd: {backrefs.get("count",0)}.')
if missing:print('Ontbrekend:',', '.join(missing))
raise SystemExit(0 if len(missing)<6 else 1)
