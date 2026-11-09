#!/usr/bin/env python3
"""Controleer de structuur van de samengestelde NVT-gegevens."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data' / 'nvt'
index = json.loads((BASE / 'integrated_index.json').read_text(encoding='utf-8'))
assert index['schema'] == 1
assert len(index['regulations']) == 7
for regulation in index['regulations']:
    data = json.loads((BASE / 'integrated' / regulation['file']).read_text(encoding='utf-8'))
    assert data['regulation']['id'] == regulation['id']
    blocks = [block for document in data['documents'] for block in document['sections']]
    assert blocks, f"Geen NVT-blokken voor {regulation['id']}"
    assert all(block['official_url'] and block['source'] and block['text'] for block in blocks)
    assert {block['kind'] for block in blocks} <= {'general', 'article'}
    assert any(block['kind'] == 'general' for block in blocks), f"Geen algemeen deel voor {regulation['id']}"
    assert any(block['kind'] == 'article' for block in blocks), f"Geen artikelsgewijs deel voor {regulation['id']}"
print(f"Geïntegreerde NVT gecontroleerd: {len(index['regulations'])} regelingen.")
