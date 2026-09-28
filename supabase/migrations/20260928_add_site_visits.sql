-- Anonieme bezoekstatistiek voor Omgevingswet Zoeker.
-- Slaat geen naam, IP-adres, zoekopdracht of andere inhoudelijke gegevens op.

create table if not exists public.site_visits (
  session_id uuid primary key,
  visitor_id uuid not null,
  visited_at timestamptz not null default now()
);

create index if not exists site_visits_visited_at_idx on public.site_visits (visited_at desc);
create index if not exists site_visits_visitor_id_idx on public.site_visits (visitor_id);

alter table public.site_visits enable row level security;

create or replace function public.register_site_visit(p_session_id uuid, p_visitor_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.site_visits (session_id, visitor_id)
  values (p_session_id, p_visitor_id)
  on conflict (session_id) do nothing;
end;
$$;

revoke all on public.site_visits from anon, authenticated;
revoke all on function public.register_site_visit(uuid, uuid) from public;
grant execute on function public.register_site_visit(uuid, uuid) to anon, authenticated;

create or replace view public.site_visit_weekly as
select
  date_trunc('week', visited_at at time zone 'Europe/Amsterdam')::date as periode_start,
  count(*)::integer as bezoeken,
  count(distinct visitor_id)::integer as unieke_bezoeken
from public.site_visits
group by 1
order by 1 desc;

create or replace view public.site_visit_monthly as
select
  date_trunc('month', visited_at at time zone 'Europe/Amsterdam')::date as periode_start,
  count(*)::integer as bezoeken,
  count(distinct visitor_id)::integer as unieke_bezoeken
from public.site_visits
group by 1
order by 1 desc;