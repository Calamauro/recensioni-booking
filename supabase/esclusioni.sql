-- =====================================================================
-- Recensioni escluse dal calcolo del bonus (spunta "Escludi" nell'app)
-- Da eseguire UNA VOLTA nel SQL Editor di Supabase.
-- Ognuno può escludere/riammettere le PROPRIE recensioni; l'admin quelle di tutti.
-- Si può rieseguire senza problemi.
-- =====================================================================
create table if not exists public.esclusioni (
    user_id        uuid not null references auth.users(id) on delete cascade,
    recensione_id  text not null references public.recensioni(id) on delete cascade,
    escluso_da     uuid references auth.users(id),
    creata_il      timestamptz not null default now(),
    primary key (user_id, recensione_id)
);

alter table public.esclusioni enable row level security;

drop policy if exists "leggi esclusioni"    on public.esclusioni;
drop policy if exists "admin aggiunge"      on public.esclusioni;
drop policy if exists "admin toglie"        on public.esclusioni;

create policy "leggi esclusioni" on public.esclusioni for select to authenticated
  using (public.is_admin() or user_id = auth.uid());
create policy "admin aggiunge" on public.esclusioni for insert to authenticated
  with check (public.is_admin() or user_id = auth.uid());
create policy "admin toglie" on public.esclusioni for delete to authenticated
  using (public.is_admin() or user_id = auth.uid());

grant select, insert, delete on public.esclusioni to authenticated;
grant all on public.esclusioni to service_role;
