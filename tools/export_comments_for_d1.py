"""Eenmalige, lokale export van openbare testopmerkingen voor D1."""
from __future__ import annotations
import argparse, json, os, urllib.parse, urllib.request
from pathlib import Path

def quote(value: object) -> str:
    if value is None: return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--url', default=os.getenv('LEGACY_SUPABASE_URL'))
    parser.add_argument('--key', default=os.getenv('LEGACY_SUPABASE_ANON_KEY'))
    parser.add_argument('--output', default='cloudflare/comments-import.sql')
    args=parser.parse_args()
    if not args.url or not args.key: raise SystemExit('Geef LEGACY_SUPABASE_URL en LEGACY_SUPABASE_ANON_KEY op.')
    endpoint=args.url.rstrip('/')+'/rest/v1/comments?'+urllib.parse.urlencode({'select':'message,app_version,status,reactie,admin_note,resolved_in_version,resolved_at,status_changed_at,created_at','order':'created_at.asc'})
    request=urllib.request.Request(endpoint,headers={'apikey':args.key,'Authorization':'Bearer '+args.key})
    with urllib.request.urlopen(request,timeout=30) as response: rows=json.load(response)
    lines=['BEGIN;']
    for row in rows:
        values=[row.get(k) for k in ('message','app_version','status','reactie','admin_note','resolved_in_version','resolved_at','status_changed_at','created_at')]
        lines.append('INSERT INTO comments (message,app_version,status,reactie,admin_note,resolved_in_version,resolved_at,status_changed_at,created_at,rate_bucket) VALUES ('+','.join(map(quote,values))+",'migratie');")
    lines+=['COMMIT;','']
    Path(args.output).write_text('\n'.join(lines),encoding='utf-8')
    print(f'{len(rows)} opmerkingen geëxporteerd naar {args.output}.')
if __name__=='__main__': main()
