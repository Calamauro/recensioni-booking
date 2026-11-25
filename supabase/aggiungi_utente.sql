-- =====================================================================
-- Configurare una persona DOPO averla creata in Authentication -> Users -> Add user
-- Sostituisci i valori tra <...> e lancia nel SQL Editor.
-- =====================================================================

-- 1) (facoltativo) Nome visualizzato e ruolo. Ruolo 'admin' = vede tutte le strutture e tutte le persone.
update public.profili
set nome = '<Nome Cognome>', ruolo = 'operatore'          -- oppure 'admin'
where user_id = (select id from auth.users where email = '<email@esempio.it>');

-- 2) Strutture seguite e data da cui contano le recensioni
insert into public.assegnazioni (user_id, struttura_id, conta_dal)
select u.id, s.id, date '<AAAA-MM-GG>'
from auth.users u, public.strutture s
where u.email = '<email@esempio.it>'
  and s.nome in ('Magenta Luxury Purificazione', 'Magenta Casa Barberini')
on conflict (user_id, struttura_id) do update set conta_dal = excluded.conta_dal;

-- 3) Scaglioni bonus personali: (media minima, bonus inverno 1 nov-31 mar, bonus estate 1 apr-31 ott)
insert into public.scaglioni (user_id, soglia, bonus_inverno, bonus_estate)
select u.id, v.soglia, v.inv, v.est
from auth.users u,
     (values (8.70, 0.00, 0.00), (8.80, 0.05, 0.05), (8.90, 0.10, 0.10), (9.00, 0.15, 0.15),
             (9.10, 0.20, 0.25), (9.20, 0.25, 0.35), (9.30, 0.30, 0.45), (9.40, 0.35, 0.55),
             (9.50, 0.40, 0.65), (9.60, 0.45, 0.75), (9.70, 0.50, 0.85), (9.80, 0.55, 0.95),
             (9.90, 0.60, 0.95), (10.00, 0.65, 0.95)) as v(soglia, inv, est)
where u.email = '<email@esempio.it>'
on conflict (user_id, soglia) do update set bonus_inverno = excluded.bonus_inverno, bonus_estate = excluded.bonus_estate;


-- =====================================================================
-- ESEMPIO COMPILATO PER TE (Davide): cambia solo l'email
-- =====================================================================
-- update public.profili set nome = 'Davide Buccino', ruolo = 'admin'
-- where user_id = (select id from auth.users where email = 'LA_TUA_EMAIL');
--
-- insert into public.assegnazioni (user_id, struttura_id, conta_dal)
-- select u.id, s.id, date '2026-11-05'
-- from auth.users u, public.strutture s
-- where u.email = 'LA_TUA_EMAIL'
--   and s.nome in ('Magenta Luxury Purificazione', 'Magenta Casa Barberini')
-- on conflict (user_id, struttura_id) do update set conta_dal = excluded.conta_dal;
--
-- insert into public.scaglioni (user_id, soglia, bonus_inverno, bonus_estate)
-- select u.id, v.soglia, v.inv, v.est
-- from auth.users u,
--      (values (8.70, 0.00, 0.00), (8.80, 0.05, 0.05), (8.90, 0.10, 0.10), (9.00, 0.15, 0.15),
--              (9.10, 0.20, 0.25), (9.20, 0.25, 0.35), (9.30, 0.30, 0.45), (9.40, 0.35, 0.55),
--              (9.50, 0.40, 0.65), (9.60, 0.45, 0.75), (9.70, 0.50, 0.85), (9.80, 0.55, 0.95),
--              (9.90, 0.60, 0.95), (10.00, 0.65, 0.95)) as v(soglia, inv, est)
-- where u.email = 'LA_TUA_EMAIL'
-- on conflict (user_id, soglia) do update set bonus_inverno = excluded.bonus_inverno, bonus_estate = excluded.bonus_estate;


-- =====================================================================
-- AGGIUNGERE UNA NUOVA STRUTTURA (lo scraper la prenderà dal giro successivo)
-- Usa l'indirizzo della versione italiana della pagina (.it.html), senza parametri dopo il "?"
-- =====================================================================
-- insert into public.strutture (nome, url_booking, raccogli_dal)
-- values ('<Nome struttura>', 'https://www.booking.com/hotel/it/<nome>.it.html', date '<AAAA-MM-GG>');
