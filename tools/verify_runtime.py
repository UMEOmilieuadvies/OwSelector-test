from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent; APPROOT=ROOT.parent; GRAPH=APPROOT/'data'/'graph'
expected=['ow','bal','bbl','bkl','ob','or']; missing=[]
for stem in expected:
 p=GRAPH/f'{stem}_legal_graph.json'
 if not p.exists():missing.append(stem);continue
 g=json.loads(p.read_text(encoding='utf-8'))
 if not isinstance(g.get('nodes'),list):raise SystemExit(f'ONGELDIGE GRAPH: {p}')
print(f'Runtimecontrole: {len(expected)-len(missing)}/6 grafen aanwezig.')
if missing:print('Ontbrekend:',', '.join(missing))
raise SystemExit(0 if len(missing)<6 else 1)
