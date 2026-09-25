#!/usr/bin/env python3
"""Validate the structural grid of every official table in the legal graphs."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent.parent
GRAPH=ROOT/'data'/'graph'
STEMS=('ow','bal','bbl','bkl','ob','or')

def tables_in_source(tree):
    for item in tree or []:
        if item.get('kind')=='table':
            yield item
        yield from tables_in_source(item.get('children'))

def validate(table, location):
    rows=table.get('rows') or []
    declared=int(table.get('grid_columns') or len(table.get('columns') or []))
    errors=list(table.get('layout_issues') or [])
    occupied=set()
    for ri,row in enumerate(rows):
        for cell in row:
            column=cell.get('column')
            if column is None:
                errors.append(f'cell without column at row {ri}')
                continue
            column=int(column); colspan=max(1,int(cell.get('colspan') or 1)); rowspan=max(1,int(cell.get('rowspan') or 1))
            if declared and column+colspan>declared:
                errors.append(f'cell outside grid at row {ri}, column {column}')
            for rr in range(ri,ri+rowspan):
                for cc in range(column,column+colspan):
                    if (rr,cc) in occupied:
                        errors.append(f'overlap at row {rr}, column {cc}')
                    occupied.add((rr,cc))
    if errors:
        raise ValueError(f'{location}: ' + '; '.join(sorted(set(errors))))

def main():
    count=0
    for stem in STEMS:
        path=GRAPH/f'{stem}_legal_graph.json'
        graph=json.loads(path.read_text(encoding='utf-8'))
        for node in graph.get('nodes') or []:
            if node.get('type')=='table':
                validate(node,f'{stem}:{node.get("id")}')
                count+=1
            if node.get('type')=='appendix':
                for index,table in enumerate(tables_in_source(node.get('source_tree'))):
                    validate(table,f'{stem}:{node.get("id")}:source:{index}')
                    count+=1
    print(f'Tabelstructuur gecontroleerd: {count} tabellen in 6 regelingen.')

if __name__=='__main__':
    main()
