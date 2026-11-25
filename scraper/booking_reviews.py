"""
Booking.com - raccolta recensioni per Magenta Luxury Purificazione e Magenta Casa Barberini
==========================================================================================

Cosa fa
-------
1. Apre la pagina di ogni struttura su Booking (browser vero, visibile, via Playwright),
   apre "Leggi tutte le recensioni", ordina per "Più recenti" e scorre le pagine
   finché le recensioni non diventano più vecchie della data di inizio (o dell'ultima già salvata).
2. Estrae: struttura, data recensione, mese di soggiorno, notti, punteggio, titolo,
   testo positivo/negativo, nome ospite, paese, tipo di viaggiatore, camera.
3. Salva le recensioni nuove nell'archivio:
   - Supabase (database online) se sono impostate le variabili SUPABASE_URL e SUPABASE_KEY;
   - altrimenti recensioni.csv locale, e in quel caso rigenera anche l'Excel.

Installazione (una volta sola)
------------------------------
    pip install playwright beautifulsoup4 lxml openpyxl
    python -m playwright install chromium

Uso
---
    python booking_reviews.py                      # scraping + Excel
    python booking_reviews.py --from-html a.html b.html --struttura "Casa Barberini" "Purificazione"
                                                   # fallback: HTML salvato a mano dal browser
    python booking_reviews.py --solo-excel         # rigenera solo l'Excel dal CSV
    python booking_reviews.py --completo           # rilegge tutto ignorando lo storico (raramente utile)

Scraping incrementale: se recensioni.csv esiste già, per ogni struttura lo script
riparte dall'ultima recensione salvata (meno MARGINE_GIORNI) e si ferma alla prima
pagina che non contiene nulla di nuovo. Di solito basta 1 pagina per struttura.

Se compare un CAPTCHA o una verifica, risolvila tu nella finestra del browser:
lo script aspetta.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import random
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from bs4 import BeautifulSoup

from archivio import CAMPI, ArchivioCSV, scegli_archivio

# ----------------------------------------------------------------------------
# CONFIGURAZIONE
# ----------------------------------------------------------------------------
DATA_INIZIO_LAVORO = date(2026, 10, 28)     # da qui lo script raccoglie le recensioni (inizio del tuo lavoro)
DATA_INIZIO_CONTEGGIO = date(2026, 11, 5)   # data "Dal" predefinita nella Dashboard (prima recensione tua)

# Scaglioni bonus stagionali: (media minima, bonus INVERNO 1 nov-31 mar, bonus ESTATE 1 apr-31 ott)
SCAGLIONI = [
    (8.7, 0.00, 0.00), (8.8, 0.05, 0.05), (8.9, 0.10, 0.10), (9.0, 0.15, 0.15),
    (9.1, 0.20, 0.25), (9.2, 0.25, 0.35), (9.3, 0.30, 0.45), (9.4, 0.35, 0.55),
    (9.5, 0.40, 0.65), (9.6, 0.45, 0.75), (9.7, 0.50, 0.85), (9.8, 0.55, 0.95),
    (9.9, 0.60, 0.95), (10.0, 0.65, 0.95),
]
INIZIO_SCALA_GRAFICI = 8.5                  # da dove parte il contagiri

# Scraping incrementale: si riparte dall'ultima recensione salvata meno questi giorni
# (Booking a volte pubblica le recensioni con qualche giorno di ritardo).
MARGINE_GIORNI = 7

# Usate solo in modalità locale (CSV). Con Supabase le strutture si leggono dalla tabella "strutture".
STRUTTURE = {
    "Magenta Luxury Purificazione": "https://www.booking.com/hotel/it/house-purificazione-holiday.it.html",
    "Magenta Casa Barberini": "https://www.booking.com/hotel/it/casa-barberini.it.html",
}

try:
    CARTELLA = Path(__file__).resolve().parent
except NameError:                       # eseguito dentro Jupyter: usa la cartella del notebook
    CARTELLA = Path.cwd()
FILE_CSV = CARTELLA / "recensioni.csv"
FILE_XLSX = CARTELLA / "recensioni_booking.xlsx"
PROFILO_BROWSER = CARTELLA / ".browser_profile"   # conserva cookie/consenso tra un'esecuzione e l'altra
MAX_PAGINE = 40                                    # limite di sicurezza per struttura

MESI = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
    "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}


NO_COMMENTO = "L'ospite non ha lasciato un commento"


# ----------------------------------------------------------------------------
# PARSING (indipendente dal browser: funziona sia sul DOM live che su HTML salvato)
# ----------------------------------------------------------------------------
def _txt(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def _data_it(testo: str) -> date | None:
    """'Data della recensione: 5 novembre 2026' -> date(2026, 11, 5)"""
    m = re.search(r"(\d{1,2})\s+([a-zà]+)\s+(\d{4})", testo.lower())
    if not m or m.group(2) not in MESI:
        return None
    return date(int(m.group(3)), MESI[m.group(2)], int(m.group(1)))


def _mese_it(testo: str) -> date | None:
    """'novembre 2026' -> date(2026, 11, 1)"""
    m = re.search(r"([a-zà]+)\s+(\d{4})", testo.lower())
    if not m or m.group(1) not in MESI:
        return None
    return date(int(m.group(2)), MESI[m.group(1)], 1)


def parse_recensioni(html: str, struttura: str) -> list[dict]:
    """Estrae tutte le schede recensione presenti in un frammento HTML di Booking.

    Usa solo gli attributi data-testid (stabili): le classi CSS di Booking
    sono generate e cambiano spesso.
    """
    soup = BeautifulSoup(html, "lxml")
    risultati = []
    for card in soup.select('[data-testid="review-card"]'):
        data_rec = _data_it(_txt(card.select_one('[data-testid="review-date"]')))
        if data_rec is None:
            continue

        punteggio_el = card.select_one('[data-testid="review-score"] [aria-hidden="true"]')
        punteggio = float(_txt(punteggio_el).replace(",", ".")) if punteggio_el else None

        notti_txt = _txt(card.select_one('[data-testid="review-num-nights"]'))
        notti_m = re.search(r"\d+", notti_txt)

        nome_el = card.select_one('[data-testid="review-avatar"] h4')
        paese_el = card.select_one('[data-testid="review-avatar"] img[alt=""] + span')

        positivo = _txt(card.select_one('[data-testid="review-positive-text"] span:not([aria-hidden])'))
        negativo = _txt(card.select_one('[data-testid="review-negative-text"] span:not([aria-hidden])'))

        soggiorno = _mese_it(_txt(card.select_one('[data-testid="review-stay-date"]')))

        rec = {
            "struttura": struttura,
            "data_recensione": data_rec.isoformat(),
            "mese_soggiorno": soggiorno.isoformat() if soggiorno else "",
            "notti": int(notti_m.group()) if notti_m else "",
            "punteggio": punteggio,
            "titolo": _txt(card.select_one('[data-testid="review-title"]')),
            "positivo": positivo,
            "negativo": negativo,
            "nome": _txt(nome_el),
            "paese": _txt(paese_el),
            "tipo_viaggiatore": _txt(card.select_one('[data-testid="review-traveler-type"]')),
            "camera": _txt(card.select_one('[data-testid="review-room-name"]')),
        }
        # ID stabile per de-duplicare tra un'esecuzione e l'altra
        chiave = "|".join(str(rec[k]) for k in ("struttura", "data_recensione", "nome", "paese", "punteggio", "titolo"))
        rec["id"] = hashlib.md5(chiave.encode("utf-8")).hexdigest()[:12]
        risultati.append(rec)
    return risultati


# ----------------------------------------------------------------------------
# SCRAPING (Playwright)
# ----------------------------------------------------------------------------
def _pausa(a=1.2, b=2.8):
    time.sleep(random.uniform(a, b))


def scrape_struttura(page, nome: str, url: str, data_inizio: date, gia_salvati: set[str]) -> list[dict]:
    print(f"\n=== {nome} ===")
    print(f"  leggo le recensioni dal {data_inizio:%d/%m/%Y} in poi")
    page.goto(url, wait_until="domcontentloaded")
    _pausa(2, 4)

    # Banner cookie: rifiuta i non necessari, se presente
    for sel in ("#onetrust-reject-all-handler", 'button:has-text("Rifiuta")'):
        try:
            page.locator(sel).first.click(timeout=2500)
            break
        except Exception:
            pass

    # Apri il pannello "Leggi tutte le recensioni"
    try:
        page.get_by_role("button", name=re.compile("Leggi tutte le recensioni", re.I)).first.click(timeout=8000)
    except Exception:
        page.locator('text="Leggi tutte le recensioni"').first.click(timeout=8000)

    # Attende le schede (se c'è un CAPTCHA, l'utente ha 3 minuti per risolverlo)
    page.wait_for_selector('[data-testid="review-card"]', timeout=180_000)
    _pausa()

    # Ordina per più recenti
    try:
        page.select_option('[data-testid="reviews-sorter-component"]', "NEWEST_FIRST")
        _pausa(2, 3.5)
    except Exception as e:
        print("  ! impossibile ordinare per data:", e)

    raccolte: dict[str, dict] = {}
    for n_pag in range(1, MAX_PAGINE + 1):
        contenitore = page.locator('[data-testid="review-list-container"]').first
        html = contenitore.inner_html()
        recensioni = parse_recensioni(html, nome)
        nel_periodo = [r for r in recensioni if date.fromisoformat(r["data_recensione"]) >= data_inizio]
        mai_viste = [r for r in nel_periodo if r["id"] not in gia_salvati]
        for r in nel_periodo:
            raccolte[r["id"]] = r
        print(f"  pagina {n_pag}: {len(recensioni)} lette, {len(mai_viste)} nuove")

        # Le recensioni sono ordinate dalla più recente: ci fermiamo appena
        # - troviamo recensioni più vecchie della soglia, oppure
        # - l'intera pagina è già nel nostro file (niente di nuovo più indietro)
        if not recensioni or len(nel_periodo) < len(recensioni) or not mai_viste:
            break

        avanti = page.locator('button[aria-label="pagina successiva"]').first
        if avanti.count() == 0 or avanti.is_disabled():
            break
        primo_id_prima = recensioni[0]["id"]
        avanti.click()
        # Aspetta che la lista cambi davvero
        for _ in range(30):
            time.sleep(0.5)
            nuove_card = parse_recensioni(page.locator('[data-testid="review-list-container"]').first.inner_html(), nome)
            if nuove_card and nuove_card[0]["id"] != primo_id_prima:
                break
        _pausa()

    return list(raccolte.values())


def scrape_tutto(urls: dict[str, str], soglie: dict[str, date], gia_salvati: set[str]) -> tuple[list[dict], list[str]]:
    """Avvia lo scraping. Dentro Jupyter (dove gira già un event loop asyncio)
    l'API sincrona di Playwright non è ammessa: in quel caso la esegue in un thread separato."""
    import asyncio
    try:
        asyncio.get_running_loop()
        dentro_jupyter = True
    except RuntimeError:
        dentro_jupyter = False

    if dentro_jupyter:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(_scrape_sync, urls, soglie, gia_salvati).result()
    return _scrape_sync(urls, soglie, gia_salvati)


def _scrape_sync(urls: dict[str, str], soglie: dict[str, date], gia_salvati: set[str]) -> tuple[list[dict], list[str]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright non installato: pip install playwright && python -m playwright install chromium")

    # HEADLESS=1 (impostato su GitHub Actions): browser senza finestra, perché sul server non c'è uno schermo
    headless = os.environ.get("HEADLESS", "0") == "1"
    tutte, errori = [], []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILO_BROWSER), headless=headless, locale="it-IT",
            viewport={"width": 1366, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for nome, url in urls.items():
            try:
                tutte += scrape_struttura(page, nome, url, soglie[nome], gia_salvati)
            except Exception as e:
                msg = f"{nome}: {str(e).splitlines()[0][:300]}"
                print("  !!", msg)
                errori.append(msg)
            _pausa(3, 6)
        ctx.close()
    return tutte, errori


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-html", nargs="+", help="file HTML salvati a mano (uno per struttura)")
    ap.add_argument("--struttura", nargs="+", help="nome struttura per ciascun file --from-html")
    ap.add_argument("--solo-excel", action="store_true", help="non raccoglie nulla, rigenera solo l'Excel (solo modalità CSV)")
    ap.add_argument("--data-inizio", help="sovrascrive DATA_INIZIO_LAVORO (formato AAAA-MM-GG)")
    ap.add_argument("--completo", action="store_true",
                    help="ignora lo storico e rilegge tutto dalla data di inizio (di solito non serve)")
    args, _ = ap.parse_known_args()   # ignora gli argomenti extra di Jupyter

    data_inizio = date.fromisoformat(args.data_inizio) if args.data_inizio else DATA_INIZIO_LAVORO
    locali = {n: {"url": u, "raccogli_dal": data_inizio.isoformat()} for n, u in STRUTTURE.items()}
    archivio = scegli_archivio(CARTELLA, locali)
    strutture = archivio.strutture()
    print(f"Archivio: {archivio.nome} - strutture: {', '.join(strutture)}")
    storico = archivio.carica()
    print(f"Recensioni già salvate: {len(storico)}")

    errori: list[str] = []
    if args.from_html:
        if not args.struttura or len(args.struttura) != len(args.from_html):
            sys.exit("Indica una --struttura per ogni file --from-html")
        nuove = []
        for file, nome in zip(args.from_html, args.struttura):
            nuove += parse_recensioni(Path(file).read_text(encoding="utf-8"), nome)
    elif args.solo_excel:
        nuove = []
    else:
        soglie = {}
        for nome, cfg in strutture.items():
            inizio = date.fromisoformat(str(cfg["raccogli_dal"]))
            if args.data_inizio:
                inizio = data_inizio
            date_salvate = [str(r["data_recensione"]) for r in storico.values() if r["struttura"] == nome]
            if date_salvate and not args.completo:
                ultima = date.fromisoformat(max(date_salvate))
                soglie[nome] = max(inizio, ultima - timedelta(days=MARGINE_GIORNI))
                print(f"{nome}: ultima recensione salvata {ultima:%d/%m/%Y} -> riparto dal {soglie[nome]:%d/%m/%Y}")
            else:
                soglie[nome] = inizio
                print(f"{nome}: nessuno storico -> leggo tutto dal {inizio:%d/%m/%Y}")
        nuove, errori = scrape_tutto({n: c["url"] for n, c in strutture.items()}, soglie, set(storico))

    davvero_nuove = [r for r in nuove if r["id"] not in storico]
    archivio.salva(nuove)
    print(f"\nSalvate {len(davvero_nuove)} recensioni nuove su {archivio.nome}")

    if not (args.from_html or args.solo_excel):
        esito = "ok" if not errori else ("errore" if len(errori) == len(strutture) else "parziale")
        archivio.registra_esecuzione(len(davvero_nuove), esito, " | ".join(errori))

    # Excel: solo in modalità locale (CSV). Nel cloud il "foglio" è l'app.
    if isinstance(archivio, ArchivioCSV):
        from crea_excel import crea_excel
        crea_excel(sorted(archivio.carica().values(), key=lambda r: (r["data_recensione"], r["struttura"]), reverse=True),
                   FILE_XLSX, DATA_INIZIO_CONTEGGIO, list(strutture),
                   scaglioni=SCAGLIONI, inizio_scala=INIZIO_SCALA_GRAFICI)
        print(f"Excel aggiornato -> {FILE_XLSX.name}")

    # Se TUTTE le strutture sono fallite, codice d'uscita 1: GitHub ti avvisa via email.
    if errori and len(errori) == len(strutture):
        sys.exit(1)


if __name__ == "__main__":
    main()
