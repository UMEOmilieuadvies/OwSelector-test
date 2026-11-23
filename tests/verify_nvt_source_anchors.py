"""Gerichte regressieproef voor officiële NvT-ankers en blokgrenzen."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location('article_notes_builder', ROOT / 'tools' / 'build_article_notes_all.py')
module = module_from_spec(spec)
spec.loader.exec_module(module)

html = '''
<h2>Nota van toelichting</h2>
<h2>Artikelsgewijze toelichting</h2>
<h6><a id="d17e105234"></a>Artikel 3.26 (algemene regels)</h6>
<p>Deze toelichting hoort uitsluitend bij artikel 3.26.</p>
<h6><a id="d17e105244"></a>§ 3.2.9 Opslaan van gevaarlijke stoffen in verpakking</h6>
<h6><a id="d17e105247"></a>Artikel 3.27 (toepassingsbereik)</h6>
<p>Deze toelichting hoort bij artikel 3.27.</p>
'''
parser = module.Parser()
parser.feed(html)
notes = parser.result()

assert parser.anchors['3.26'] == 'd17e105234'
assert parser.anchors['3.27'] == 'd17e105247'
assert '§ 3.2.9' not in notes['3.26']
assert 'Artikel 3.27' not in notes['3.26']
assert 'Artikel 3.26' in notes['3.26']
assert 'Artikel 3.27' in notes['3.27']
print('NvT-bronankers en grenzen tussen artikelblokken zijn gecontroleerd.')
