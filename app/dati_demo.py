"""Modalità DEMO: dati completamente fittizi, generati in memoria.

Si attiva da sola quando l'app non trova i segreti di Supabase (SUPABASE_URL...).
Nessun dato reale, nessun database: ogni visitatore ha la sua copia in memoria,
quindi può escludere recensioni o simulare voti senza toccare nulla di condiviso.

Imita l'interfaccia di supa.Supa (login, leggi, inserisci, elimina) così l'app
funziona identica in produzione e in demo.
"""

from __future__ import annotations

import random
import time
import uuid
from datetime import date, datetime, timedelta, timezone

import streamlit as st

# ------------------------------------------------------------------ configurazione demo
STRUTTURE = ["Casa Aurora Trevi", "Loft Pantheon", "Suite Navona"]

UTENTI = {
    "op_giulia": {"nome": "Giulia (operatrice demo)", "ruolo": "operatore", "metodo_media": "tutte_recensioni"},
    "op_marco": {"nome": "Marco (operatore demo)", "ruolo": "operatore", "metodo_media": "tutte_recensioni"},
    "admin_demo": {"nome": "Amministratore demo", "ruolo": "admin", "metodo_media": "tutte_recensioni"},
}

ASSEGNAZIONI = [
    ("op_giulia", "Casa Aurora Trevi", "2026-10-01"),
    ("op_giulia", "Loft Pantheon", "2026-10-01"),
    ("op_marco", "Suite Navona", "2026-10-15"),
]

# (media minima, bonus inverno 1 nov-31 mar, bonus estate 1 apr-31 ott)
SCAGLIONI = [
    (8.7, 0.00, 0.00), (8.8, 0.05, 0.05), (8.9, 0.10, 0.10), (9.0, 0.15, 0.15),
    (9.1, 0.20, 0.25), (9.2, 0.25, 0.35), (9.3, 0.30, 0.45), (9.4, 0.35, 0.55),
    (9.5, 0.40, 0.65), (9.6, 0.45, 0.75), (9.7, 0.50, 0.85), (9.8, 0.55, 0.95),
    (9.9, 0.60, 0.95), (10.0, 0.65, 0.95),
]

NOMI = ["Anna", "Lukas", "Sophie", "Mateo", "Emma", "Oliver", "Chloé", "Hiroshi", "Lucía", "Noah", "Ingrid",
        "Pedro", "Amelia", "Jonas", "Marta", "Ethan", "Léa", "Kenji", "Sara", "Tomás", "Isabel", "Finn",
        "Nora", "Daniel", "Elif", "Aisha", "Pablo", "Mia", "Lars", "Giorgia", "Hannah", "Ravi"]
PAESI = ["Germania", "Francia", "Spagna", "Regno Unito", "Stati Uniti", "Paesi Bassi", "Giappone", "Brasile",
         "Svezia", "Italia", "Australia", "Canada", "Turchia", "Polonia", "Portogallo", "Irlanda"]
TIPI = ["Coppia", "Famiglia", "Gruppo", "Viaggiatore singolo", "Viaggiatore per affari"]
CAMERE = {
    "Casa Aurora Trevi": ["Camera Matrimoniale", "Camera Tripla Classic", "Camera Familiare"],
    "Loft Pantheon": ["Appartamento con 2 Camere da Letto"],
    "Suite Navona": ["Suite Deluxe", "Camera Doppia Superior"],
}
TITOLI = {
    10: ["Eccezionale", "Perfetto in tutto", "Posizione imbattibile!", "Torneremo sicuramente", "Wonderful stay"],
    9: ["Eccellente", "Molto consigliato", "Great location", "Ottimo soggiorno"],
    8: ["Molto buono", "Buona esperienza", "Good value"],
    7: ["Buono", "Nel complesso ok"],
    6: ["Discreto", "Poteva andare meglio"],
    5: ["Non all'altezza delle aspettative"],
}
POSITIVI = ["Posizione centralissima, tutto raggiungibile a piedi.", "Camera pulita e spaziosa.",
            "Staff gentilissimo e disponibile.", "Letto comodissimo, si dorme benissimo.",
            "Check-in veloce e senza problemi.", "Ottimo rapporto qualità-prezzo.", ""]
NEGATIVI = {8: ["Wi-Fi un po' lento.", "Doccia piccola."],
            7: ["Rumore dalla strada la sera.", "Pulizia del bagno migliorabile."],
            6: ["Aria condizionata non funzionante.", "Letto scomodo."],
            5: ["Camera diversa dalle foto.", "Problemi con il riscaldamento."]}

# quante recensioni per struttura e periodo (ottobre "più difficile", novembre in crescita)
PIANO = {
    "Casa Aurora Trevi": [("2026-09-20", "2026-09-30", 3, "medio"), ("2026-10-01", "2026-10-31", 14, "ottobre"),
                          ("2026-11-01", "2026-11-25", 15, "novembre")],
    "Loft Pantheon": [("2026-10-01", "2026-10-31", 5, "ottobre"), ("2026-11-01", "2026-11-25", 6, "novembre")],
    "Suite Navona": [("2026-10-01", "2026-10-31", 9, "medio"), ("2026-11-01", "2026-11-25", 10, "novembre")],
}
PESI = {  # distribuzione dei voti 10/9/8/7/6/5
    "ottobre": [0.48, 0.30, 0.12, 0.05, 0.03, 0.02],
    "novembre": [0.62, 0.28, 0.06, 0.03, 0.01, 0.00],
    "medio": [0.55, 0.28, 0.10, 0.04, 0.02, 0.01],
}


def _genera_recensioni() -> list[dict]:
    rnd = random.Random(2026)          # seme fisso: dati sempre uguali, demo ripetibile
    out, n = [], 0
    for struttura, blocchi in PIANO.items():
        for inizio, fine, quante, profilo in blocchi:
            d0, d1 = date.fromisoformat(inizio), date.fromisoformat(fine)
            giorni = (d1 - d0).days
            for _ in range(quante):
                n += 1
                d = d0 + timedelta(days=rnd.randint(0, giorni))
                voto = rnd.choices([10, 9, 8, 7, 6, 5], weights=PESI[profilo])[0]
                notti = rnd.choice([1, 2, 2, 3, 3, 4, 5, 6])
                # il soggiorno è finito prima della recensione: a volte il mese prima
                soggiorno = d - timedelta(days=rnd.randint(0, 9) + notti)
                out.append({
                    "id": f"demo{n:03d}",
                    "struttura": struttura,
                    "data_recensione": d.isoformat(),
                    "mese_soggiorno": soggiorno.replace(day=1).isoformat(),
                    "notti": notti,
                    "punteggio": float(voto),
                    "titolo": rnd.choice(TITOLI[voto]),
                    "positivo": rnd.choice(POSITIVI) if voto >= 7 else "Posizione comoda.",
                    "negativo": rnd.choice(NEGATIVI[voto]) if voto <= 8 and rnd.random() < 0.8 else "",
                    "nome": rnd.choice(NOMI),
                    "paese": rnd.choice(PAESI),
                    "tipo_viaggiatore": rnd.choice(TIPI),
                    "camera": rnd.choice(CAMERE[struttura]),
                })
    # un caso "da escludere" ben visibile per il video: soggiorno di settembre recensito a ottobre
    out.append({"id": "demo999", "struttura": "Casa Aurora Trevi", "data_recensione": "2026-10-03",
                "mese_soggiorno": "2026-09-01", "notti": 3, "punteggio": 6.0, "titolo": "Poteva andare meglio",
                "positivo": "Posizione comoda.", "negativo": "Rumore notturno (soggiorno prima del cambio gestione).",
                "nome": "Viktor", "paese": "Austria", "tipo_viaggiatore": "Coppia", "camera": "Camera Matrimoniale"})
    return sorted(out, key=lambda r: r["data_recensione"], reverse=True)


def _tabelle_iniziali() -> dict:
    strutture = [{"id": i + 1, "nome": s} for i, s in enumerate(STRUTTURE)]
    sid = {s["nome"]: s["id"] for s in strutture}
    adesso = datetime.now(timezone.utc).replace(hour=5, minute=17, second=0, microsecond=0)
    return {
        "profili": [{"user_id": u, **p} for u, p in UTENTI.items()],
        "strutture": strutture,
        "assegnazioni": [{"user_id": u, "struttura_id": sid[s], "conta_dal": dal, "conta_fino": None,
                          "strutture": {"nome": s}} for u, s, dal in ASSEGNAZIONI],
        "scaglioni": [{"user_id": u, "soglia": a, "bonus_inverno": b, "bonus_estate": c}
                      for u in ("op_giulia", "op_marco") for a, b, c in SCAGLIONI],
        "recensioni": _genera_recensioni(),
        "esclusioni": [],
        "simulazioni": [],
        "esecuzioni": [{"eseguita_il": adesso.isoformat(), "nuove": 2, "esito": "ok", "dettagli": ""}],
    }


class DemoDB:
    """Stessa interfaccia di supa.Supa, ma lavora su tabelle in memoria (per sessione)."""

    def _db(self) -> dict:
        if "demo_db" not in st.session_state:
            st.session_state["demo_db"] = _tabelle_iniziali()
        return st.session_state["demo_db"]

    # --- accesso
    def login_demo(self, user_id: str) -> dict:
        return {"access_token": f"demo-{user_id}-{uuid.uuid4().hex}", "refresh_token": "",
                "scade": time.time() + 10 * 365 * 86400, "user_id": user_id, "email": f"{user_id}@demo"}

    def login(self, email: str, password: str) -> dict:
        from supa import ErroreLogin
        raise ErroreLogin("In modalità demo usa i pulsanti qui sotto.")

    def rinnova(self, sessione: dict) -> dict:
        return sessione

    def logout(self, sessione: dict) -> None:
        st.session_state.pop("demo_db", None)          # all'uscita la demo riparte pulita

    # --- letture (filtri minimi in stile PostgREST, come li usa l'app)
    def leggi(self, token: str, tabella: str, params: dict) -> list[dict]:
        righe = list(self._db().get(tabella, []))
        for campo, filtro in params.items():
            if campo in ("select", "order", "limit", "offset"):
                continue
            if filtro.startswith("eq."):
                righe = [r for r in righe if str(r.get(campo)) == filtro[3:]]
            elif filtro.startswith("in.("):
                valori = [v.strip().strip('"') for v in filtro[4:-1].split(",")]
                righe = [r for r in righe if str(r.get(campo)) in valori]
        if "limit" in params:
            righe = righe[: int(params["limit"])]
        return righe

    # --- scritture (esclusioni e simulazioni), stessa logica dei filtri di lettura
    _CHIAVI = {"esclusioni": ("user_id", "recensione_id"), "simulazioni": ("user_id", "operatore_id", "ordine")}

    def inserisci(self, token: str, tabella: str, righe: list[dict]) -> None:
        tab = self._db().setdefault(tabella, [])
        campi = self._CHIAVI.get(tabella)
        presenti = {tuple(r.get(c) for c in campi) for r in tab} if campi else set()
        for r in righe:
            if not campi or tuple(r.get(c) for c in campi) not in presenti:
                tab.append(dict(r))

    def elimina(self, token: str, tabella: str, filtri: dict) -> None:
        def corrisponde(r: dict) -> bool:
            for campo, filtro in filtri.items():
                if filtro.startswith("eq.") and str(r.get(campo)) != filtro[3:]:
                    return False
                if filtro.startswith("in.("):
                    valori = {v.strip().strip('"') for v in filtro[4:-1].split(",")}
                    if str(r.get(campo)) not in valori:
                        return False
            return True
        self._db()[tabella] = [r for r in self._db().get(tabella, []) if not corrisponde(r)]
