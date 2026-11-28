-- =====================================================================
-- Preferenze dell'utente (per ora: lingua dell'app it / en / ru)
-- Da eseguire UNA VOLTA nel SQL Editor di Supabase. Si può rieseguire senza problemi.
-- Ognuno legge e modifica solo le proprie preferenze.
-- =====================================================================
create table if not exists public.preferenze (
    user_id        uuid primary key default auth.uid() references auth.users(id) on delete cascade,
    lingua         text not null default 'it' check (lingua in ('it', 'en', 'ru')),
    aggiornato_il  timestamptz not null default now()
);

alter table public.preferenze enable row level security;

drop policy if exists "leggi le mie preferenze" on public.preferenze;
drop policy if exists "salva le mie preferenze" on public.preferenze;
drop policy if exists "togli le mie preferenze" on public.preferenze;

create policy "leggi le mie preferenze" on public.preferenze for select to authenticated
  using (user_id = auth.uid());
create policy "salva le mie preferenze" on public.preferenze for insert to authenticated
  with check (user_id = auth.uid());
create policy "togli le mie preferenze" on public.preferenze for delete to authenticated
  using (user_id = auth.uid());

grant select, insert, delete on public.preferenze to authenticated;
grant all on public.preferenze to service_role;
