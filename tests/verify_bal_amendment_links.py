#!/usr/bin/env python3
"""Regressiecontrole voor de eerste automatische BAL-wijzigingsbron."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data'/'article_notes.json').read_text(encoding='utf-8'))['regulations']['BAL']
notes=data['4.1235']['notes']
assert any(note.get('source')=='Staatsblad 2021, 98' for note in notes), 'Artikel 4.1235 mist Stb. 2021, 98.'
assert any('Saneren van de bodem' in note.get('text','') for note in notes), 'De bodemtoelichting is niet gekoppeld.'
assert any('Dit artikel bepaalt de reikwijdte van paragraaf 4.121.' in note.get('text','') for note in notes), 'De eigen toelichting van artikel 4.1235 ontbreekt.'
assert not any('Artikel 4.1236 (melding)' in note.get('text','') for note in notes), 'Tekst van artikel 4.1236 is foutief aan artikel 4.1235 gekoppeld.'
print('BAL wijzigingsnota gecontroleerd: artikel 4.1235 bevat Stb. 2021, 98.')
