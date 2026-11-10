#!/usr/bin/env python3
"""Controleer dat een tijdelijke bronfout een aanwezige NvT-cache hergebruikt."""
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('build_nvt_documents', ROOT / 'tools' / 'build_nvt_documents.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

with tempfile.TemporaryDirectory() as temporary:
    temp = Path(temporary)
    catalog = temp / 'catalog.json'
    output = temp / 'nvt'
    output.mkdir()
    cached = output / 'cached.html'
    cached.write_text('<html><body>Gecachte officiële toelichting</body></html>', encoding='utf-8')
    catalog.write_text(json.dumps({'regulations': [{'id': 'TEST', 'documents': [{
        'url': 'http://127.0.0.1:9/onbereikbaar', 'file': 'cached.html'
    }]}]}), encoding='utf-8')
    MODULE.CATALOG = catalog
    MODULE.OUT = output
    MODULE.main()
    toc = json.loads((output / 'toc.json').read_text(encoding='utf-8'))
    assert 'cached.html' in toc, 'De gecachte NvT is niet verwerkt in de inhoudsopgave.'

print('NvT-broncache wordt veilig gebruikt bij een tijdelijke bronfout.')
