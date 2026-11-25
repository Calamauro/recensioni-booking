"""Carica su Supabase le recensioni che hai già nel tuo recensioni.csv (da fare UNA volta).

Uso (dal Prompt dei comandi di Anaconda, nella cartella scraper):
    set SUPABASE_URL=https://xxxx.supabase.co
    set SUPABASE_KEY=sb_secret_xxxx
    python importa_csv.py percorso\\del\\tuo\\recensioni.csv

Su Mac/Linux usa "export" al posto di "set".
"""
import os
import sys
from pathlib import Path

from archivio import ArchivioCSV, ArchivioSupabase

if len(sys.argv) != 2:
    sys.exit("Uso: python importa_csv.py percorso/recensioni.csv")
url, chiave = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
if not (url and chiave):
    sys.exit("Imposta prima le variabili SUPABASE_URL e SUPABASE_KEY (vedi istruzioni in cima al file)")

righe = list(ArchivioCSV(Path(sys.argv[1])).carica().values())
print(f"Trovate {len(righe)} recensioni nel CSV")
db = ArchivioSupabase(url, chiave)
db.salva(righe)
print(f"Fatto: ora su Supabase ci sono {len(db.carica())} recensioni")
