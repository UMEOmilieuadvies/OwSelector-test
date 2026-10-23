-- Testomgeving: anonieme online favorieten, uitsluitend toegankelijk met herstelcode.
create extension if not exists pgcrypto;

create table if not exists public.favorite_sets (
  id uuid primary key default gen_random_uuid(),
  recovery_hash text not null unique,
  favorites jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  last_used_at timestamptz not null default now(),
  constraint favorite_sets_favorites_array check (jsonb_typeof(favorites) = 'array')
);
alter table public.favorite_sets enable row level security;

create or replace function public.favorites_create(p_code text, p_favorites jsonb default '[]'::jsonb)
returns jsonb language plpgsql security definer set search_path=public as $$
declare h text; begin
  if length(p_code) < 32 or jsonb_typeof(p_favorites) <> 'array' then raise exception 'Ongeldige favorietenaanvraag'; end if;
  h := encode(digest(p_code,'sha256'),'hex');
  insert into favorite_sets(recovery_hash,favorites) values(h,p_favorites)
  on conflict(recovery_hash) do update set favorites=excluded.favorites,last_used_at=now();
  return p_favorites;
end $$;
create or replace function public.favorites_load(p_code text)
returns jsonb language plpgsql security definer set search_path=public as $$
declare h text; result jsonb; begin
  h:=encode(digest(p_code,'sha256'),'hex');
  update favorite_sets set last_used_at=now() where recovery_hash=h returning favorites into result;
  return coalesce(result,'[]'::jsonb);
end $$;
create or replace function public.favorites_save(p_code text, p_favorites jsonb)
returns jsonb language plpgsql security definer set search_path=public as $$
declare h text; begin
  if jsonb_typeof(p_favorites) <> 'array' then raise exception 'Ongeldige favorieten'; end if;
  h:=encode(digest(p_code,'sha256'),'hex');
  update favorite_sets set favorites=p_favorites,last_used_at=now() where recovery_hash=h;
  if not found then raise exception 'Herstelcode niet gevonden'; end if;
  return p_favorites;
end $$;
create or replace function public.favorites_clear(p_code text)
returns jsonb language plpgsql security definer set search_path=public as $$
declare h text; begin
  h:=encode(digest(p_code,'sha256'),'hex');
  update favorite_sets set favorites='[]'::jsonb,last_used_at=now() where recovery_hash=h;
  if not found then raise exception 'Herstelcode niet gevonden'; end if;
  return '[]'::jsonb;
end $$;
revoke all on public.favorite_sets from anon, authenticated;
grant execute on function public.favorites_create(text,jsonb), public.favorites_load(text), public.favorites_save(text,jsonb), public.favorites_clear(text) to anon;

-- Dagelijkse opschoning: aanroepen door een beheerproces.
create or replace function public.favorites_cleanup_expired()
returns integer language plpgsql security definer set search_path=public as $$
declare removed integer; begin delete from favorite_sets where last_used_at < now() - interval '365 days'; get diagnostics removed = row_count; return removed; end $$;
