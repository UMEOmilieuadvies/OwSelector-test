-- Versie 0.6: status voor afgehandelde opmerkingen en een betrouwbare datum daarvoor.
-- Deze status verschijnt na tien dagen in de historie van de applicatie.
update public.statuses
set code = 'geen_actie_nodig',
    status = 'Geen actie nodig',
    description = 'De opmerking is beoordeeld; verdere actie is niet nodig.',
    color = '#64748b',
    sort_order = 60,
    updated_at = now()
where table_name = 'comments'
  and (code = 'geen_actie' or status = 'Geen actie');

insert into public.statuses (table_name, code, status, description, color, sort_order)
values ('comments', 'geen_actie_nodig', 'Geen actie nodig', 'De opmerking is beoordeeld; verdere actie is niet nodig.', '#64748b', 60)
on conflict (table_name, code) do update set
  status = excluded.status,
  description = excluded.description,
  color = excluded.color,
  sort_order = excluded.sort_order,
  updated_at = now();

alter table public.comments
  add column if not exists status_changed_at timestamptz;

update public.comments
set status_changed_at = coalesce(status_changed_at, resolved_at, created_at, now())
where status_changed_at is null;

alter table public.comments
  alter column status_changed_at set default now(),
  alter column status_changed_at set not null;

create or replace function public.set_comment_status_changed_at()
returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' or new.status_id is distinct from old.status_id then
    new.status_changed_at = now();
  end if;
  return new;
end;
$$;

drop trigger if exists comments_status_changed_at on public.comments;
create trigger comments_status_changed_at
before insert or update on public.comments
for each row execute function public.set_comment_status_changed_at();
