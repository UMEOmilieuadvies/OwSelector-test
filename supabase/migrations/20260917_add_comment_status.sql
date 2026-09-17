alter table public.comments
  add column if not exists status text not null default 'Ontvangen';

alter table public.comments
  drop constraint if exists comments_status_check;

alter table public.comments
  add constraint comments_status_check
  check (status in ('Ontvangen', 'In onderzoek', 'Geaccepteerd', 'Doorgevoerd', 'Niet geaccepteerd'));
