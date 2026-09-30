-- Testbeheer: toegang is alleen mogelijk voor een vooraf aangewezen gebruiker
-- met een Supabase-authsessie op MFA-niveau aal2 (authenticator-app / TOTP).

create table if not exists public.admin_users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  enabled boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.admin_users enable row level security;

create or replace function public.is_test_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.admin_users
    where user_id = auth.uid() and enabled = true
  ) and coalesce(auth.jwt()->>'aal', 'aal1') = 'aal2';
$$;

revoke all on function public.is_test_admin() from public;
grant execute on function public.is_test_admin() to authenticated;

-- De beheerder ziet alle bedrijfsgegevens; publieke bezoekers houden hun bestaande leesrechten.
drop policy if exists admin_manage_comments on public.comments;
create policy admin_manage_comments on public.comments for all to authenticated
  using (public.is_test_admin()) with check (public.is_test_admin());

drop policy if exists admin_manage_statuses on public.statuses;
create policy admin_manage_statuses on public.statuses for all to authenticated
  using (public.is_test_admin()) with check (public.is_test_admin());

drop policy if exists admin_manage_qna on public.qna;
create policy admin_manage_qna on public.qna for all to authenticated
  using (public.is_test_admin()) with check (public.is_test_admin());

drop policy if exists admin_read_releases on public.releases;
create policy admin_read_releases on public.releases for select to authenticated
  using (public.is_test_admin());

grant select on public.site_visit_weekly, public.site_visit_monthly to authenticated;
