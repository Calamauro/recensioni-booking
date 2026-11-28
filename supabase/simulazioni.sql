-- =====================================================================
-- Voti simulati (sezione "Simulatore" dell'app), salvati per chi li inserisce
-- Da eseguire UNA VOLTA nel SQL Editor di Supabase. Si può rieseguire senza problemi.
-- user_id      = chi ha inserito i voti (l'utente collegato)
-- operatore_id = di quale dashboard sono (per l'admin, che può aprire quella di ogni operatore)
-- Ognuno vede e modifica solo le proprie simulazioni.
-- =====================================================================
create table if not exists public.simulazioni (
    user_id       uuid not null default auth.uid() references auth.users(id) on delete cascade,
    operatore_id  uuid not null references auth.users(id) on delete cascade,
    ordine        integer not null check (ordine between 0 and 9),
    struttura     text not null,
    voto          numeric(3,1) not null check (voto between 1 and 10),
    creata_il     timestamptz not null default now(),
    primary key (user_id, operatore_id, ordine)
);

alter table public.simulazioni enable row level security;

drop policy if exists "leggi le mie simulazioni"    on public.simulazioni;
drop policy if exists "aggiungi le mie simulazioni" on public.simulazioni;
drop policy if exists "togli le mie simulazioni"    on public.simulazioni;

create policy "leggi le mie simulazioni" on public.simulazioni for select to authenticated
  using (user_id = auth.uid());
create policy "aggiungi le mie simulazioni" on public.simulazioni for insert to authenticated
  with check (user_id = auth.uid());
create policy "togli le mie simulazioni" on public.simulazioni for delete to authenticated
  using (user_id = auth.uid());

grant select, insert, delete on public.simulazioni to authenticated;
grant all on public.simulazioni to service_role;
