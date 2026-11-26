"""Calcoli della dashboard (solo pandas, nessuna dipendenza da Streamlit: si può testare da solo)."""

from __future__ import annotations

import calendar
from datetime import date

import pandas as pd

CRITERI = {"Data recensione": "recensione", "Mese soggiorno": "soggiorno"}
METODI = {"Media delle strutture": "media_strutture", "Tutte le recensioni insieme": "tutte_recensioni"}


# ------------------------------------------------------------------ preparazione
def prepara(righe: list[dict]) -> pd.DataFrame:
    cols = ["id", "struttura", "data_recensione", "mese_soggiorno", "notti", "punteggio", "titolo",
            "positivo", "negativo", "nome", "paese", "tipo_viaggiatore", "camera"]
    df = pd.DataFrame(righe, columns=cols) if righe else pd.DataFrame(columns=cols)
    df["data_recensione"] = pd.to_datetime(df["data_recensione"]).dt.date
    df["mese_soggiorno"] = pd.to_datetime(df["mese_soggiorno"]).dt.date
    df["punteggio"] = pd.to_numeric(df["punteggio"])
    return df


def _primo_del_mese(d: date) -> date:
    return d.replace(day=1)


def data_riferimento(df: pd.DataFrame, criterio: str) -> pd.Series:
    if criterio == "soggiorno":
        return df["mese_soggiorno"].where(df["mese_soggiorno"].notna(), df["data_recensione"])
    return df["data_recensione"]


# ------------------------------------------------------------------ periodo
def periodo(scelta: str, oggi: date, inizio: date, mese: date | None = None,
            dal: date | None = None, al: date | None = None) -> tuple[date, date]:
    if scelta == "Mese corrente":
        return _primo_del_mese(oggi), oggi
    if scelta == "Mese a scelta" and mese:
        ultimo = calendar.monthrange(mese.year, mese.month)[1]
        return _primo_del_mese(mese), mese.replace(day=ultimo)
    if scelta == "Intervallo personalizzato" and dal and al:
        return dal, al
    return inizio, oggi                                     # "Dall'inizio"


def filtra(df: pd.DataFrame, assegnazioni: dict[str, dict], dal: date, al: date, criterio: str) -> pd.DataFrame:
    """Tiene le recensioni delle strutture assegnate, nel periodo, rispettando la data
    da cui ogni struttura conta per l'utente (conta_dal / conta_fino)."""
    if df.empty:
        return df
    rif = data_riferimento(df, criterio)
    tieni = pd.Series(False, index=df.index)
    for nome, a in assegnazioni.items():
        inizio = max(dal, a["conta_dal"])
        fine = min(al, a["conta_fino"]) if a.get("conta_fino") else al
        if criterio == "soggiorno":           # Booking dà solo mese/anno del soggiorno
            inizio = _primo_del_mese(inizio)
        tieni |= (df["struttura"] == nome) & (rif >= inizio) & (rif <= fine)
    out = df[tieni].copy()
    out["data_riferimento"] = rif[tieni]
    return out


# ------------------------------------------------------------------ indicatori
def riepilogo(df_f: pd.DataFrame, strutture: list[str]) -> pd.DataFrame:
    righe = []
    for s in strutture:
        p = df_f.loc[df_f["struttura"] == s, "punteggio"].dropna()
        righe.append({
            "Struttura": s,
            "Recensioni": len(p),
            "Media": p.mean() if len(p) else None,
            "% voti ≥ 9": (p >= 9).mean() if len(p) else None,
            "Voti < 7": int((p < 7).sum()),
        })
    return pd.DataFrame(righe)


def media_bonus(df_f: pd.DataFrame, strutture: list[str], metodo: str) -> float | None:
    if df_f.empty:
        return None
    if metodo == "tutte_recensioni":
        m = df_f["punteggio"].mean()
    else:
        medie = df_f[df_f["struttura"].isin(strutture)].groupby("struttura")["punteggio"].mean()
        m = medie.mean() if len(medie) else None
    return None if m is None or pd.isna(m) else float(m)


# Scaglioni: lista di (soglia, bonus_inverno, bonus_estate)
def stagione(d: date) -> str:
    return "Inverno" if d.month >= 11 or d.month <= 3 else "Estate"


def _col(stag: str) -> int:
    return 1 if stag == "Inverno" else 2


def bonus_per(media: float | None, scaglioni: list[tuple], stag: str) -> float:
    if media is None or pd.isna(media):
        return 0.0
    raggiunti = [s[_col(stag)] for s in sorted(scaglioni) if media >= s[0]]
    return raggiunti[-1] if raggiunti else 0.0


def prossimo_scaglione(media: float | None, scaglioni: list[tuple], stag: str) -> tuple[float, float] | None:
    """Prima soglia sopra la media che dà un bonus MAGGIORE di quello attuale."""
    attuale = bonus_per(media, scaglioni, stag)
    for s in sorted(scaglioni):
        if (media is None or media < s[0]) and s[_col(stag)] > attuale:
            return s[0], s[_col(stag)]
    return None


def mesi_fissi(inizio: date, n: int = 12) -> list[date]:
    out, a, m = [], inizio.year, inizio.month
    for _ in range(n):
        out.append(date(a, m, 1))
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return out


def mensile(df_f: pd.DataFrame, strutture: list[str], mesi: list[date],
            scaglioni: list[tuple], metodo: str) -> pd.DataFrame:
    """Una riga per ognuno dei mesi fissi: media e n° per struttura, media delle strutture,
    stagione e bonus del mese (con la stagione di quel mese)."""
    righe = []
    for m in mesi:
        if df_f.empty:
            dm = df_f
        else:
            rif = pd.to_datetime(df_f["data_riferimento"])
            dm = df_f[(rif.dt.year == m.year) & (rif.dt.month == m.month)]
        r = {"Mese": m}
        medie = []
        for s in strutture:
            p = dm.loc[dm["struttura"] == s, "punteggio"].dropna() if not dm.empty else pd.Series(dtype=float)
            r[f"Media {s}"] = p.mean() if len(p) else None
            r[f"N° {s}"] = len(p)
            if len(p):
                medie.append(p.mean())
        r["Media delle strutture"] = sum(medie) / len(medie) if medie else None
        mb = media_bonus(dm, strutture, metodo) if not dm.empty else None
        r["Media per bonus"] = mb                     # col metodo scelto (es. tutte le recensioni insieme)
        r["Stagione"] = stagione(m)
        r["Bonus del mese"] = bonus_per(mb, scaglioni, stagione(m)) if mb is not None else None
        righe.append(r)
    return pd.DataFrame(righe)


def num(x: float | None, dec: int = 2) -> str:
    """Formato italiano: 9,47"""
    return "-" if x is None or pd.isna(x) else f"{x:.{dec}f}".replace(".", ",")


def perc(x: float | None) -> str:
    return "-" if x is None or pd.isna(x) else f"{x * 100:.0f}%"
