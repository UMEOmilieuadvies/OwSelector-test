-- Herstel voor het plaatsen van openbare opmerkingen.
-- De status "Ontvangen" moet beschikbaar zijn als verplichte beginstatus.
update public.statuses
set is_active = true,
    updated_at = now()
where table_name = 'comments'
  and code in ('ontvangen', 'in_onderzoek', 'geaccepteerd', 'doorgevoerd',
               'niet_geaccepteerd', 'geen_actie_nodig');

-- Deze functie wordt uitgevoerd tijdens een openbare invoer. SECURITY DEFINER
-- voorkomt dat RLS op de opzoektabel de standaardstatus onzichtbaar maakt.
create or replace function public.default_comment_status()
returns bigint
language sql
stable
security definer
set search_path = public
as $$
  select id
  from public.statuses
  where table_name = 'comments'
    and code = 'ontvangen'
    and is_active
  limit 1;
$$;

revoke all on function public.default_comment_status() from public;
grant execute on function public.default_comment_status() to anon, authenticated;

alter table public.comments
  alter column status_id set default public.default_comment_status();
-- De trigger vult de leesbare statustekst in. Ook deze draait tijdens
-- openbare invoer en moet daarom de afgeschermde opzoektabel kunnen lezen.
create or replace function public.sync_comment_status()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  select status into new.status
  from public.statuses
  where id = new.status_id and table_name = new.status_scope;

  if new.status is null then
    raise exception 'Geen geldige status voor % / %', new.status_scope, new.status_id;
  end if;

  return new;
end;
$$;
