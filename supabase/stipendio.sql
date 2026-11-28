-- =====================================================================
-- Dati del calcolatore stipendio (sezione "Stipendio" dell'app), salvati per chi li inserisce
-- Da eseguire UNA VOLTA nel SQL Editor di Supabase. Si può rieseguire senza problemi.
-- user_id      = chi ha inserito i dati (l'utente collegato)
-- operatore_id = di quale dashboard sono (per l'admin, che può aprire quella di ogni operatore)
-- dati         = fissi, check-in, tariffa, bonus e parametri fiscali (formato JSON)
-- Ognuno vede e modifica solo i propri dati.
-- =====================================================================
create table if not exists public.stipendio (
    user_id        uuid not null default auth.uid() references auth.users(id) on delete cascade,
    operatore_id   uuid not null references auth.users(id) on delete cascade,
    dati           jsonb not null,
    aggiornato_il  timestamptz not null default now(),
    primary key (user_id, operatore_id)
);

alter table public.stipendio enable row level security;

drop policy if exists "leggi il mio stipendio"    on public.stipendio;
drop policy if exists "salva il mio stipendio"    on public.stipendio;
drop policy if exists "togli il mio stipendio"    on public.stipendio;

create policy "leggi il mio stipendio" on public.stipendio for select to authenticated
  using (user_id = auth.uid());
create policy "salva il mio stipendio" on public.stipendio for insert to authenticated
  with check (user_id = auth.uid());
create policy "togli il mio stipendio" on public.stipendio for delete to authenticated
  using (user_id = auth.uid());

grant select, insert, delete on public.stipendio to authenticated;
grant all on public.stipendio to service_role;
