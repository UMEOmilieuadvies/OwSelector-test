#!/usr/bin/env python3
"""Blokkeer publicatie van wijzigings-NvT zonder alle vier poorten."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT / 'nvt_catalog.json').read_text(encoding='utf-8'))
for regulation in catalog['regulations']:
    for document in regulation.get('documents', []):
        if document.get('kind') != 'amendment':
            continue
        check = document.get('verification', {})
        assert check.get('status') == 'verified', f"{document['file']}: bron is niet geverifieerd."
        assert regulation['id'] in check.get('applies_to', []), f"{document['file']}: regeling ontbreekt in broncontrole."
        assert document['url'].startswith('https://zoek.officielebekendmakingen.nl/'), f"{document['file']}: geen officiële bron-URL."
        data_file = ROOT / 'data' / f"article_notes_{regulation['id'].lower()}_amendments.json"
        assert data_file.exists(), f"{document['file']}: gekoppelde artikelgegevens ontbreken."
        notes = json.loads(data_file.read_text(encoding='utf-8'))['articles'].get(check['article'], [])
        matching = [note for note in notes if note.get('url') == document['url']]
        assert matching, f"{document['file']}: verplichte koppeling naar artikel {check['article']} ontbreekt."
        assert any(check['contains'] in note.get('text', '') for note in matching), f"{document['file']}: verplichte herkenningstekst ontbreekt."
print('Alle gepubliceerde wijzigings-NvT-bronnen doorlopen bron-, regeling-, koppelings- en regressiecontrole.')
