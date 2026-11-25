"""Dove vengono salvate le recensioni.

- ArchivioSupabase: database online (usato su GitHub Actions e, volendo, dal tuo PC)
- ArchivioCSV:      file recensioni.csv locale (come la versione precedente)

Lo scraper sceglie da solo: se trova le variabili d'ambiente SUPABASE_URL e
SUPABASE_KEY usa Supabase, altrimenti il CSV.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import requests

CAMPI = [
    "id", "struttura", "data_recensione", "mese_soggiorno", "notti", "punteggio",
    "titolo", "positivo", "negativo", "nome", "paese", "tipo_viaggiatore", "camera",
]


def _pulisci(r: dict) -> dict:
    """Converte i campi vuoti in None e i numeri nel tipo giusto, per il database."""
    out = {}
    for k in CAMPI:
        v = r.get(k)
        if v in ("", None):
            out[k] = None
        elif k == "notti":
            out[k] = int(float(v))
        elif k == "punteggio":
            out[k] = float(v)
        else:
            out[k] = str(v)
    return out


class ArchivioSupabase:
    nome = "Supabase"

    def __init__(self, url: str, chiave: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.h = {"apikey": chiave, "Content-Type": "application/json"}
        # Le chiavi "legacy" (JWT) vanno anche nell'header Authorization; quelle nuove (sb_...) no.
        if not chiave.startswith("sb_"):
            self.h["Authorization"] = f"Bearer {chiave}"

    def strutture(self) -> dict[str, dict]:
        """Strutture attive dal database: {nome: {"url": ..., "raccogli_dal": "AAAA-MM-GG"}}"""
        r = requests.get(f"{self.base}/strutture",
                         params={"select": "nome,url_booking,raccogli_dal", "attiva": "eq.true"},
                         headers=self.h, timeout=30)
        r.raise_for_status()
        return {x["nome"]: {"url": x["url_booking"].split("?")[0], "raccogli_dal": x["raccogli_dal"]}
                for x in r.json()}

    def carica(self) -> dict[str, dict]:
        righe, offset, passo = [], 0, 1000
        while True:
            r = requests.get(f"{self.base}/recensioni",
                             params={"select": "*", "order": "id", "limit": passo, "offset": offset},
                             headers=self.h, timeout=30)
            r.raise_for_status()
            blocco = r.json()
            righe += blocco
            if len(blocco) < passo:
                break
            offset += passo
        return {x["id"]: x for x in righe}

    def salva(self, recensioni: list[dict]) -> None:
        if not recensioni:
            return
        r = requests.post(f"{self.base}/recensioni", params={"on_conflict": "id"},
                          headers={**self.h, "Prefer": "resolution=merge-duplicates,return=minimal"},
                          json=[_pulisci(x) for x in recensioni], timeout=60)
        r.raise_for_status()

    def registra_esecuzione(self, nuove: int, esito: str, dettagli: str = "") -> None:
        try:
            requests.post(f"{self.base}/esecuzioni", headers={**self.h, "Prefer": "return=minimal"},
                          json={"nuove": nuove, "esito": esito, "dettagli": dettagli[:2000]},
                          timeout=30).raise_for_status()
        except Exception as e:                       # il log non deve mai far fallire lo scraping
            print("  (impossibile registrare l'esecuzione:", e, ")")


class ArchivioCSV:
    nome = "CSV locale"

    def __init__(self, percorso: Path, strutture: dict[str, dict] | None = None):
        self.percorso = percorso
        self._strutture = strutture or {}

    def strutture(self) -> dict[str, dict]:
        return self._strutture

    def carica(self) -> dict[str, dict]:
        if not self.percorso.exists():
            return {}
        with self.percorso.open(encoding="utf-8-sig", newline="") as f:
            return {r["id"]: r for r in csv.DictReader(f)}

    def salva(self, recensioni: list[dict]) -> None:
        tutte = self.carica()
        for r in recensioni:
            tutte[r["id"]] = r
        ordinate = sorted(tutte.values(), key=lambda r: (r["data_recensione"], r["struttura"]), reverse=True)
        with self.percorso.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CAMPI, extrasaction="ignore")
            w.writeheader()
            w.writerows(ordinate)

    def registra_esecuzione(self, nuove: int, esito: str, dettagli: str = "") -> None:
        pass


def scegli_archivio(cartella: Path, strutture_locali: dict[str, dict]):
    """Supabase se ci sono le variabili d'ambiente, altrimenti CSV con le strutture della configurazione."""
    url, chiave = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
    if url and chiave:
        return ArchivioSupabase(url, chiave)
    return ArchivioCSV(cartella / "recensioni.csv", strutture_locali)
