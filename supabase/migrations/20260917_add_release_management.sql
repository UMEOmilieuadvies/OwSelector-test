alter table public.comments
  add column if not exists resolved_in_version text,
  add column if not exists resolved_at timestamptz,
  add column if not exists admin_note text;

create table if not exists public.releases (
  version text primary key,
  release_kind text not null check (release_kind in ('groot', 'klein')),
  published_at timestamptz not null default now(),
  notes jsonb not null default '[]'::jsonb,
  commit_sha text,
  pages_url text
);

alter table public.releases enable row level security;

drop policy if exists "Releases zijn openbaar leesbaar" on public.releases;
create policy "Releases zijn openbaar leesbaar"
  on public.releases for select using (true);
