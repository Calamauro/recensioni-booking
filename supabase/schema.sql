-- =====================================================================
-- Schema database "Recensioni Booking" (multi-utente)
-- Da eseguire UNA VOLTA in Supabase: SQL Editor -> New query -> incolla tutto -> Run
--
-- Concetti:
--   strutture     = le strutture su Booking da monitorare (lo scraper legge da qui)
--   profili       = una riga per ogni persona che accede all'app (creata in automatico)
--   assegnazioni  = chi segue quale struttura e DA QUANDO contano le recensioni per lui
--   scaglioni     = soglie e % di bonus (inverno / estate), diverse per ogni persona
--   recensioni    = dati raccolti dallo scraper
--   esecuzioni    = registro delle esecuzioni dello scraper
-- =====================================================================

-- ---------------------------------------------------------------- tabelle
create table if not exists public.strutture (
    id            bigint generated always as identity primary key,
    nome          text not null unique,
    url_booking   text not null,              -- versione italiana: .../nome.it.html
    raccogli_dal  date not null,              -- lo scraper non legge recensioni più vecchie
    attiva        boolean not null default true
);

create table if not exists public.recensioni (
    id                text primary key,
    struttura         text not null references public.strutture(nome) on update cascade,
    data_recensione   date not null,
    mese_soggiorno    date,
    notti             integer,
    punteggio         numeric(3,1),
    titolo            text,
    positivo          text,
    negativo          text,
    nome              text,
    paese             text,
    tipo_viaggiatore  text,
    camera            text,
    inserita_il       timestamptz not null default now()
);
create index if not exists recensioni_struttura_data on public.recensioni (struttura, data_recensione desc);

create table if not exists public.profili (
    user_id      uuid primary key references auth.users(id) on delete cascade,
    nome         text not null,
    ruolo        text not null default 'operatore' check (ruolo in ('operatore', 'admin')),
    metodo_media text not null default 'media_strutture'
                 check (metodo_media in ('media_strutture', 'tutte_recensioni'))
);

create table if not exists public.assegnazioni (
    id            bigint generated always as identity primary key,
    user_id       uuid not null references auth.users(id) on delete cascade,
    struttura_id  bigint not null references public.strutture(id) on delete cascade,
    conta_dal     date not null,             -- da questa data le recensioni contano per il bonus
    conta_fino    date,                      -- vuoto = ancora in corso
    unique (user_id, struttura_id)
);

create table if not exists public.scaglioni (
    id             bigint generated always as identity primary key,
    user_id        uuid not null references auth.users(id) on delete cascade,
    soglia         numeric(4,2) not null,     -- media minima
    bonus_inverno  numeric(5,4) not null,     -- 1 nov - 31 mar   (0.05 = 5%)
    bonus_estate   numeric(5,4) not null,     -- 1 apr - 31 ott
    unique (user_id, soglia)
);

create table if not exists public.esecuzioni (
    id          bigint generated always as identity primary key,
    eseguita_il timestamptz not null default now(),
    nuove       integer not null default 0,
    esito       text not null,               -- 'ok' | 'parziale' | 'errore'
    dettagli    text
);

-- ---------------------------------------------------------------- dati iniziali
insert into public.strutture (nome, url_booking, raccogli_dal) values
  ('Magenta Luxury Purificazione', 'https://www.booking.com/hotel/it/house-purificazione-holiday.it.html', '2026-10-28'),
  ('Magenta Casa Barberini',       'https://www.booking.com/hotel/it/casa-barberini.it.html',            '2026-10-28')
on conflict (nome) do nothing;

-- ---------------------------------------------------------------- profilo automatico
-- Quando crei un utente in Authentication, gli viene creato il profilo da solo.
create or replace function public.nuovo_utente()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profili (user_id, nome)
  values (new.id, coalesce(new.raw_user_meta_data->>'nome', split_part(new.email, '@', 1)))
  on conflict (user_id) do nothing;
  return new;
end $$;

drop trigger if exists al_nuovo_utente on auth.users;
create trigger al_nuovo_utente after insert on auth.users
  for each row execute procedure public.nuovo_utente();

-- ---------------------------------------------------------------- funzioni di supporto per la sicurezza
create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.profili where user_id = auth.uid() and ruolo = 'admin')
$$;

create or replace function public.mie_strutture()
returns setof text language sql stable security definer set search_path = public as $$
  select s.nome from public.strutture s
  join public.assegnazioni a on a.struttura_id = s.id
  where a.user_id = auth.uid()
$$;

-- ---------------------------------------------------------------- Permessi API
-- Nei progetti Supabase recenti le tabelle create da SQL non ricevono i permessi in automatico.
grant usage on schema public to anon, authenticated, service_role;
grant all on all tables in schema public to service_role;
grant usage, select on all sequences in schema public to service_role;
grant select on all tables in schema public to authenticated;
grant execute on function public.is_admin(), public.mie_strutture() to authenticated;

-- ---------------------------------------------------------------- Row Level Security
-- Ogni utente loggato vede SOLO le proprie strutture, recensioni, scaglioni e assegnazioni.
-- Chi ha ruolo 'admin' vede tutto. Nessuno può scrivere dall'app:
-- scrive solo lo scraper (chiave secret) o tu dal pannello di Supabase.
alter table public.strutture    enable row level security;
alter table public.recensioni   enable row level security;
alter table public.profili      enable row level security;
alter table public.assegnazioni enable row level security;
alter table public.scaglioni    enable row level security;
alter table public.esecuzioni   enable row level security;

drop policy if exists "leggi strutture"    on public.strutture;
drop policy if exists "leggi recensioni"   on public.recensioni;
drop policy if exists "leggi profili"      on public.profili;
drop policy if exists "leggi assegnazioni" on public.assegnazioni;
drop policy if exists "leggi scaglioni"    on public.scaglioni;
drop policy if exists "leggi esecuzioni"   on public.esecuzioni;

create policy "leggi strutture" on public.strutture for select to authenticated
  using (public.is_admin() or nome in (select public.mie_strutture()));
create policy "leggi recensioni" on public.recensioni for select to authenticated
  using (public.is_admin() or struttura in (select public.mie_strutture()));
create policy "leggi profili" on public.profili for select to authenticated
  using (public.is_admin() or user_id = auth.uid());
create policy "leggi assegnazioni" on public.assegnazioni for select to authenticated
  using (public.is_admin() or user_id = auth.uid());
create policy "leggi scaglioni" on public.scaglioni for select to authenticated
  using (public.is_admin() or user_id = auth.uid());
create policy "leggi esecuzioni" on public.esecuzioni for select to authenticated
  using (true);
