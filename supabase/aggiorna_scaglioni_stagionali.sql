-- =====================================================================
-- DA USARE SOLO SE avevi già eseguito la versione precedente di schema.sql
-- (quella con gli scaglioni 8,5 / 9 / 9,5 senza stagioni).
-- Sostituisce la tabella scaglioni con quella stagionale. Poi riesegui il blocco 3
-- di aggiungi_utente.sql per inserire i tuoi scaglioni.
-- =====================================================================
drop table if exists public.scaglioni;

create table public.scaglioni (
    id             bigint generated always as identity primary key,
    user_id        uuid not null references auth.users(id) on delete cascade,
    soglia         numeric(4,2) not null,
    bonus_inverno  numeric(5,4) not null,
    bonus_estate   numeric(5,4) not null,
    unique (user_id, soglia)
);
alter table public.scaglioni enable row level security;
create policy "leggi scaglioni" on public.scaglioni for select to authenticated
  using (public.is_admin() or user_id = auth.uid());
grant all on public.scaglioni to service_role;
grant select on public.scaglioni to authenticated;
