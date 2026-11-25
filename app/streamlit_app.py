"""Recensioni Booking - app (Streamlit).

Avvio in locale:   streamlit run app/streamlit_app.py
Online:            Streamlit Community Cloud, file principale app/streamlit_app.py

Segreti richiesti (.streamlit/secrets.toml in locale, oppure "Secrets" su Streamlit Cloud):
    SUPABASE_URL = "https://xxxx.supabase.co"
    SUPABASE_PUBLISHABLE_KEY = "sb_publishable_xxxx"
"""

from __future__ import annotations

import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import logica as L
from supa import ErroreLogin, SessioneScaduta, Supa, filtro_in

st.set_page_config(page_title="Recensioni Booking", page_icon="⭐", layout="centered")

BLU = "#1F3B57"
MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
           "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def sfumatura(n: int) -> list[str]:
    """n colori dal rosso al verde scuro passando per il giallo (uno per scaglione)."""
    tappe = [(0xD9, 0x53, 0x4F), (0xF0, 0xAD, 0x4E), (0xE8, 0xD8, 0x4A), (0x8C, 0xC0, 0x5A), (0x1E, 0x7B, 0x45)]
    out = []
    for i in range(n):
        t = i / max(n - 1, 1) * (len(tappe) - 1)
        k = min(int(t), len(tappe) - 2)
        r = t - k
        out.append("#" + "".join(f"{round(a + (b - a) * r):02X}" for a, b in zip(tappe[k], tappe[k + 1])))
    return out


def nome_mese(d: date) -> str:
    return f"{MESI_IT[d.month - 1].capitalize()} {d.year}"

db = Supa(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_PUBLISHABLE_KEY"])


# =================================================================== sessione / login
def esci():
    if "sessione" in st.session_state:
        db.logout(st.session_state["sessione"])
    st.session_state.clear()
    st.cache_data.clear()


def token() -> str:
    s = st.session_state["sessione"]
    if time.time() > s["scade"]:
        st.session_state["sessione"] = s = db.rinnova(s)
    return s["access_token"]


def schermata_login():
    st.title("⭐ Recensioni Booking")
    st.caption("Accedi con le credenziali che ti sono state fornite.")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        entra = st.form_submit_button("Accedi", type="primary")
    if entra:
        try:
            st.session_state["sessione"] = db.login(email, password)
            st.rerun()
        except ErroreLogin as e:
            st.error(str(e))
        except Exception:
            st.error("Servizio non raggiungibile, riprova tra poco.")


if "sessione" not in st.session_state:
    schermata_login()
    st.stop()


# =================================================================== letture (con cache di 5 minuti)
@st.cache_data(ttl=300, show_spinner=False)
def leggi(tok: str, tabella: str, params: tuple) -> list[dict]:
    return db.leggi(tok, tabella, dict(params))


def q(tabella: str, **params) -> list[dict]:
    return leggi(token(), tabella, tuple(sorted(params.items())))


try:
    io = st.session_state["sessione"]["user_id"]
    profilo = (q("profili", select="*", user_id=f"eq.{io}") or [{"nome": "", "ruolo": "operatore",
                                                                   "metodo_media": "media_strutture"}])[0]
    admin = profilo["ruolo"] == "admin"

    # --- chi sto guardando (un admin può vedere la dashboard di chiunque)
    utente = io
    if admin:
        persone = q("profili", select="user_id,nome", order="nome")
        con_strutture = {a["user_id"] for a in q("assegnazioni", select="user_id")}
        # l'admin vede in elenco solo chi ha strutture assegnate (più sé stesso se ne ha)
        nomi = {p["user_id"]: p["nome"] for p in persone if p["user_id"] in con_strutture}
        if nomi:
            if len(nomi) > 1 or io not in nomi:
                utente = st.selectbox("👤 Dashboard di", list(nomi), format_func=nomi.get,
                                      index=list(nomi).index(io) if io in nomi else 0)
            else:
                utente = io
    prof_utente = profilo if utente == io else q("profili", select="*", user_id=f"eq.{utente}")[0]

    assegn_raw = q("assegnazioni", select="conta_dal,conta_fino,strutture(nome)", user_id=f"eq.{utente}")
    scaglioni = [(float(x["soglia"]), float(x["bonus_inverno"]), float(x["bonus_estate"]))
                 for x in q("scaglioni", select="soglia,bonus_inverno,bonus_estate",
                            user_id=f"eq.{utente}", order="soglia")]
    assegnazioni = {
        a["strutture"]["nome"]: {"conta_dal": date.fromisoformat(a["conta_dal"]),
                                 "conta_fino": date.fromisoformat(a["conta_fino"]) if a["conta_fino"] else None}
        for a in assegn_raw if a.get("strutture")
    }
    strutture = list(assegnazioni)
    df = L.prepara(q("recensioni", select="*", struttura=filtro_in(strutture), order="data_recensione.desc")
                   if strutture else [])
    ultima_esec = q("esecuzioni", select="eseguita_il,nuove,esito,dettagli", order="eseguita_il.desc", limit=1)
except SessioneScaduta:
    esci()
    st.warning("Sessione scaduta: accedi di nuovo.")
    st.stop()

# =================================================================== intestazione
c1, c2 = st.columns([4, 1])
c1.title("⭐ Recensioni Booking")
c1.caption(f"{prof_utente['nome']} · {', '.join(s.replace('Magenta ', '') for s in strutture) or 'nessuna struttura'}")
if c2.button("Esci"):
    esci()
    st.rerun()

if not strutture:
    st.info("Nessuna struttura assegnata a questo utente. Aggiungila nella tabella 'assegnazioni' su Supabase.")
    st.stop()
if not scaglioni:
    st.warning("Nessuno scaglione bonus configurato per questo utente (tabella 'scaglioni').")

# =================================================================== filtri
oggi = datetime.now(ZoneInfo("Europe/Rome")).date()   # il server è in UTC
inizio = min(a["conta_dal"] for a in assegnazioni.values())
with st.expander("⚙️ Filtri", expanded=False):
    scelta = st.radio("Periodo", ["Dall'inizio", "Mese corrente", "Mese a scelta", "Intervallo personalizzato"],
                      horizontal=True)
    mese = dal_s = al_s = None
    if scelta == "Mese a scelta":
        mesi = pd.date_range(inizio.replace(day=1), oggi, freq="MS")[::-1]
        mese = st.selectbox("Mese", [m.date() for m in mesi], format_func=nome_mese)
    elif scelta == "Intervallo personalizzato":
        cc1, cc2 = st.columns(2)
        dal_s = cc1.date_input("Dal", inizio, format="DD/MM/YYYY")
        al_s = cc2.date_input("Al", oggi, format="DD/MM/YYYY")
    crit_label = st.radio("Periodo calcolato su", list(L.CRITERI), horizontal=True,
                          help="Data recensione = giorno in cui l'ospite ha scritto. "
                               "Mese soggiorno = mese in cui ha dormito (Booking mostra solo mese/anno).")
    metodi_inv = {v: k for k, v in L.METODI.items()}
    metodo_label = st.radio("Media per il bonus", list(L.METODI), horizontal=True,
                            index=list(L.METODI).index(metodi_inv.get(prof_utente["metodo_media"],
                                                                      "Media delle strutture")),
                            help="Media delle strutture = media delle medie di ogni struttura. "
                                 "Tutte le recensioni insieme = media di tutti i voti.")
    stag_label = st.radio("Scaglioni", ["Automatica", "Inverno", "Estate"], horizontal=True,
                          help="Automatica = stagione della fine del periodo. "
                               "Inverno = 1 nov – 31 mar, Estate = 1 apr – 31 ott.")

criterio, metodo = L.CRITERI[crit_label], L.METODI[metodo_label]
dal, al = L.periodo(scelta, oggi, inizio, mese, dal_s, al_s)
dff = L.filtra(df, assegnazioni, dal, al, criterio)
st.caption(f"Periodo: **{dal:%d/%m/%Y} – {al:%d/%m/%Y}** · {crit_label.lower()} · {len(dff)} recensioni")

# =================================================================== bonus
stag = L.stagione(al) if stag_label == "Automatica" else stag_label
media = L.media_bonus(dff, strutture, metodo)
bonus = L.bonus_per(media, scaglioni, stag)
prossimo = L.prossimo_scaglione(media, scaglioni, stag)

k1, k2, k3 = st.columns(3)
k1.metric("Media per il bonus", L.num(media))
k2.metric(f"Bonus ({stag.lower()})", L.perc(bonus))
if prossimo and media is not None:
    k3.metric("Prossimo scaglione", f"{L.num(prossimo[0], 1)} → {L.perc(prossimo[1])}",
              f"mancano {L.num(prossimo[0] - media)}", delta_color="off")
elif prossimo:
    k3.metric("Prossimo scaglione", f"{L.num(prossimo[0], 1)} → {L.perc(prossimo[1])}")
else:
    k3.metric("Prossimo scaglione", "Massimo ✓")

# --- contagiri: uno spicchio per scaglione, sfumato dal rosso al verde
soglie = [x[0] for x in sorted(scaglioni)]
inizio_scala = max(0.0, (min(soglie) - 0.2) // 0.5 * 0.5) if soglie else 8.5
bordi = [inizio_scala] + [x for x in soglie if inizio_scala < x < 10] + [10.0]
colori = sfumatura(len(bordi) - 1)
passi = [{"range": [bordi[i], bordi[i + 1]], "color": colori[i]} for i in range(len(bordi) - 1)]
gauge = go.Figure(go.Indicator(
    mode="gauge+number" if media is not None else "gauge",
    value=media if media is not None else inizio_scala,
    number={"valueformat": ".2f", "font": {"size": 44, "color": BLU}},
    gauge={"axis": {"range": [inizio_scala, 10], "tickvals": [x for x in bordi if round(x * 10) % 2 == 0 or x == bordi[0]],
                    "tickformat": ".1f"},
           "bar": {"color": BLU, "thickness": 0.2},
           "steps": passi,
           "threshold": {"line": {"color": BLU, "width": 3}, "thickness": 0.9,
                         "value": prossimo[0] if prossimo else 10}},
))
gauge.update_layout(height=260, margin=dict(l=25, r=25, t=30, b=0), separators=",.")
st.plotly_chart(gauge, config={"displayModeBar": False})

with st.expander(f"📊 Tabella scaglioni ({stag.lower()})"):
    col_b = 1 if stag == "Inverno" else 2
    tab_s = pd.DataFrame([{"Media da": L.num(x[0], 1), "Bonus": L.perc(x[col_b]),
                           "": "◀ attuale" if media is not None and L.bonus_per(media, scaglioni, stag) == x[col_b]
                           and media >= x[0] and (prossimo is None or x[0] < prossimo[0]) else ""}
                          for x in sorted(scaglioni)])
    st.dataframe(tab_s, hide_index=True)

# =================================================================== per struttura
st.subheader("Per struttura")
riep = L.riepilogo(dff, strutture)
riep["Bonus"] = riep["Media"].apply(lambda m: L.perc(L.bonus_per(m, scaglioni, stag)) if pd.notna(m) else "-")
riep["% voti ≥ 9"] = riep["% voti ≥ 9"] * 100
st.dataframe(
    riep, hide_index=True,
    column_config={"Media": st.column_config.NumberColumn(format="%.2f"),
                   "% voti ≥ 9": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100)},
)

# =================================================================== andamento mensile (12 mesi fissi)
mesi12 = L.mesi_fissi(inizio)
fine12 = (pd.Timestamp(mesi12[-1]) + pd.offsets.MonthEnd(0)).date()
df12 = L.filtra(df, assegnazioni, inizio, fine12, criterio)
mens = L.mensile(df12, strutture, mesi12, scaglioni, metodo)
st.subheader(f"Andamento mensile ({nome_mese(mesi12[0]).lower()} – {nome_mese(mesi12[-1]).lower()})")

fig = go.Figure()
etich = [f"{MESI_IT[m.month - 1][:3]} {str(m.year)[2:]}" for m in mens["Mese"]]
for s_ in strutture:
    fig.add_bar(x=etich, y=mens[f"Media {s_}"], name=s_.replace("Magenta ", ""))
fig.add_scatter(x=etich, y=mens["Media delle strutture"], name="Media strutture",
                mode="lines+markers", line={"color": BLU, "width": 3}, connectgaps=False)
fig.update_layout(height=300, barmode="group", yaxis_range=[7, 10], margin=dict(l=10, r=10, t=10, b=10),
                  legend=dict(orientation="h", y=-0.25), separators=",.")
st.plotly_chart(fig, config={"displayModeBar": False})

st.caption("Tocca un mese per vedere le sue recensioni.")
for _, r in mens.iterrows():
    m = r["Mese"]
    parti = []
    for s_ in strutture:
        if r[f"N° {s_}"]:
            parti.append(f"{s_.replace('Magenta ', '').split()[-1]} {L.num(r[f'Media {s_}'])} ({r[f'N° {s_}']})")
    n_tot = sum(int(r[f"N° {s_}"]) for s_ in strutture)
    if n_tot:
        etichetta = (f"**{nome_mese(m)}** · {' · '.join(parti)} · media **{L.num(r['Media delle strutture'])}** "
                     f"· bonus **{L.perc(r['Bonus del mese'])}** ({r['Stagione'].lower()})")
    else:
        etichetta = f"{nome_mese(m)} · nessuna recensione ({r['Stagione'].lower()})"
    with st.expander(etichetta):
        if n_tot:
            rif = pd.to_datetime(df12["data_riferimento"])
            dm = df12[(rif.dt.year == m.year) & (rif.dt.month == m.month)].sort_values("data_recensione")
            vista = dm[["data_recensione", "struttura", "punteggio", "nome", "paese", "titolo", "negativo"]].copy()
            vista["struttura"] = vista["struttura"].str.replace("Magenta ", "")
            st.dataframe(vista, hide_index=True, column_config={
                "data_recensione": st.column_config.DateColumn("Data", format="DD/MM"),
                "struttura": "Struttura", "punteggio": st.column_config.NumberColumn("Voto", format="%.1f"),
                "nome": "Ospite", "paese": "Paese", "titolo": "Titolo", "negativo": "👎",
            })
        else:
            st.caption("Ancora nessuna recensione in questo mese.")

# =================================================================== elenco recensioni
with st.expander(f"📝 Recensioni del periodo ({len(dff)})"):
    if not dff.empty:
        elenco = dff.sort_values("data_recensione", ascending=False)[
            ["data_recensione", "struttura", "punteggio", "titolo", "positivo", "negativo",
             "nome", "paese", "tipo_viaggiatore", "mese_soggiorno"]].copy()
        elenco["struttura"] = elenco["struttura"].str.replace("Magenta ", "")
        st.dataframe(elenco, hide_index=True, column_config={
            "data_recensione": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "struttura": "Struttura", "punteggio": st.column_config.NumberColumn("Voto", format="%.1f"),
            "titolo": "Titolo", "positivo": "👍", "negativo": "👎", "nome": "Ospite", "paese": "Paese",
            "tipo_viaggiatore": "Tipo", "mese_soggiorno": st.column_config.DateColumn("Soggiorno", format="MM/YYYY"),
        })
        st.download_button("Scarica CSV", elenco.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"recensioni_{dal:%Y%m%d}_{al:%Y%m%d}.csv", mime="text/csv")

# =================================================================== piè di pagina
if ultima_esec:
    e = ultima_esec[0]
    quando = pd.to_datetime(e["eseguita_il"]).tz_convert("Europe/Rome").strftime("%d/%m/%Y %H:%M")
    icona = {"ok": "🟢", "parziale": "🟠", "errore": "🔴"}.get(e["esito"], "⚪")
    st.caption(f"{icona} Ultimo aggiornamento dati: {quando} · {e['nuove']} recensioni nuove"
               + (f" · {e['dettagli']}" if e["esito"] != "ok" and e["dettagli"] else ""))
st.caption("La media qui è la media semplice delle recensioni nel periodo: il punteggio mostrato da Booking "
           "usa un calcolo diverso (ultimi 36 mesi).")
