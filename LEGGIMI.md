# Recensioni Booking – app con login (tutto gratuito)

```
Booking ──► scraper (GitHub Actions, ogni mattina) ──► Supabase (database + login) ──► App Streamlit (telefono/PC)
```

| Pezzo | Servizio gratuito | Cartella |
|---|---|---|
| Database + utenti | Supabase (piano Free) | `supabase/` |
| Scraping automatico | GitHub Actions (repo privato: 2.000 minuti/mese, ne usi ~100) | `scraper/`, `.github/workflows/` |
| App | Streamlit Community Cloud | `app/` |

Ti servono 3 account gratuiti: **GitHub**, **Supabase** (puoi entrare con GitHub), **Streamlit Community Cloud** (entri con GitHub).
Tempo stimato: 1–2 ore la prima volta.

---

## Fase 1 – Database (Supabase)

1. Su supabase.com → **New project**. Nome a piacere, **Region: Europe (Frankfurt)**, scegli una password del database e salvala.
2. Menu a sinistra **SQL Editor** → **New query** → incolla tutto `supabase/schema.sql` → **Run**.
   Crea le tabelle, inserisce le tue 2 strutture e attiva la sicurezza.
3. **Project Settings → API Keys**: copia e conserva
   - **Project URL** (`https://xxxx.supabase.co`)
   - **Publishable key** (`sb_publishable_...`) → va all'app
   - **Secret key** (`sb_secret_...`) → va SOLO allo scraper. Non metterla mai nell'app né su GitHub in chiaro.
   *(Se il tuo progetto mostra le chiavi "legacy", usa `anon` al posto della publishable e `service_role` al posto della secret: funzionano uguale.)*
4. **Authentication → impostazioni dei provider/Sign In**: disattiva **"Allow new users to sign up"**.
   Così nessuno può registrarsi da solo: gli account li crei solo tu.

## Fase 2 – Il tuo utente

1. **Authentication → Users → Add user → Create new user**: la tua email e una password, spunta **Auto Confirm User**.
2. **SQL Editor**: apri `supabase/aggiungi_utente.sql`, usa l'**esempio compilato per te** in fondo
   (togli i `--` all'inizio delle righe e metti la tua email) → **Run**.
   Ti rende **admin**, ti assegna le 2 strutture con conteggio dal **05/11/2026** e gli scaglioni stagionali (inverno 1 nov–31 mar, estate 1 apr–31 ott).
   *Se avevi già eseguito la versione precedente di `schema.sql`*, prima lancia `supabase/aggiorna_scaglioni_stagionali.sql`.

## Fase 3 – Caricare le recensioni che hai già

Dal **Prompt di Anaconda**, nella cartella `scraper`:
```
pip install requests
set SUPABASE_URL=https://xxxx.supabase.co
set SUPABASE_KEY=sb_secret_xxxx
python importa_csv.py C:\percorso\del\tuo\recensioni.csv
```
Controllo: su Supabase, **Table Editor → recensioni** deve mostrare le righe.

## Fase 4 – Scraping automatico (GitHub)

1. Su github.com → **New repository** → nome es. `recensioni-booking` → **Private** → Create.
2. **Add file → Upload files**: trascina il contenuto di questa cartella (`app`, `scraper`, `supabase`, `.github`, `.gitignore`, `LEGGIMI.md`) → **Commit**.
   *Se la cartella `.github` non viene caricata* (su Windows a volte succede): tab **Actions → set up a workflow yourself**,
   chiama il file `scraping.yml`, incolla il contenuto di `.github/workflows/scraping.yml` → Commit.
3. **Settings → Secrets and variables → Actions → New repository secret**, due volte:
   - `SUPABASE_URL` = Project URL
   - `SUPABASE_SECRET_KEY` = Secret key
4. Tab **Actions → Scraping recensioni Booking → Run workflow** per la prima prova.
   Apri l'esecuzione e guarda il passo "Raccogli recensioni nuove": deve dire `pagina 1: ... lette`.
   Da quel momento parte da sola ogni mattina. Se fallisce, GitHub ti manda un'email.

## Fase 5 – L'app (Streamlit)

1. share.streamlit.io → entra con GitHub → **Create app → Deploy a public app from GitHub** *(il codice resta privato, l'app è comunque protetta dal login)*.
2. Repository `recensioni-booking`, branch `main`, **Main file path: `app/streamlit_app.py`**.
3. **Advanced settings → Secrets**, incolla (con i tuoi valori):
   ```
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_PUBLISHABLE_KEY = "sb_publishable_xxxx"
   ```
4. **Deploy**. Dopo un paio di minuti hai un indirizzo tipo `https://recensioni-booking.streamlit.app`: entra con email e password della Fase 2.

> Se l'app non viene aperta per un po', Streamlit la mette in pausa: alla visita successiva basta premere il pulsante per riattivarla (qualche secondo).

## Fase 6 – Sul telefono come un'app

- **iPhone (Safari)**: apri l'indirizzo → Condividi → **Aggiungi alla schermata Home**
- **Android (Chrome)**: apri l'indirizzo → menu ⋮ → **Aggiungi a schermata Home**

---

## Aggiungere persone e strutture (senza toccare il codice)

Tutto da Supabase, con `supabase/aggiungi_utente.sql`:

- **Nuova struttura**: ultimo blocco del file (nome, indirizzo Booking **in versione italiana `.it.html`**, data da cui raccogliere). Lo scraper la prende dal giro successivo.
- **Nuova persona**: crea l'utente in Authentication (Fase 2, punto 1), poi blocchi 1–3 del file con la sua email, le sue strutture, la sua data di inizio e i suoi scaglioni.
- **Cosa vede chi**: un operatore vede solo le sue strutture e i suoi bonus (lo impone il database, non l'app). Un **admin** vede tutto e in alto può scegliere la dashboard di chi visualizzare.
- **Cambiare scaglioni o date**: Table Editor → `scaglioni` (colonne `bonus_inverno` / `bonus_estate`) o `assegnazioni` → modifica la cella.
- **Fine di un incarico**: in `assegnazioni` compila `conta_fino`.

## Piano B – se Booking blocca lo scraping da GitHub

I server di GitHub sono in datacenter e Booking potrebbe mostrare verifiche anti-bot.
Se l'esecuzione fallisce di continuo (pallino 🔴 in fondo all'app), fai girare lo scraper **dal tuo PC**: scrive comunque su Supabase e l'app funziona uguale.

1. Copia `scraper/aggiorna.bat.esempio` come `scraper/aggiorna.bat` e inserisci URL e Secret key.
2. Windows → **Utilità di pianificazione → Crea attività di base** → ogni giorno → *Avvia programma* → scegli `aggiorna.bat`.
3. Disattiva lo scraping su GitHub: tab Actions → workflow → **⋯ → Disable workflow**.

## Uso locale senza cloud (come prima)

Senza le variabili `SUPABASE_URL`/`SUPABASE_KEY`, `scraper/booking_reviews.py` funziona come la versione precedente: `recensioni.csv` + Excel.

## Note

- Lo scraping è incrementale: ogni giorno legge di solito 1 pagina per struttura.
- Le condizioni d'uso di Booking non permettono lo scraping automatico: tienilo a 1 volta al giorno e non usarlo su larga scala.
- Nell'app ci sono nomi e paesi degli ospiti: è per questo che è protetta da login e che non ci sono iscrizioni libere.
