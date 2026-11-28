"""Recensioni & Bonus Monitor - app (Streamlit).

Senza segreti Supabase parte in MODALITÀ DEMO con dati fittizi (vedi dati_demo.py).

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
from testi import LINGUE, MESI, MESI_BREVI, t as _t
from supa import ErroreLogin, SessioneScaduta, Supa, filtro_in

# Produzione se ci sono i segreti di Supabase, altrimenti demo con dati fittizi
try:
    _URL, _CHIAVE = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_PUBLISHABLE_KEY"]
    DEMO = False
except Exception:
    DEMO = True
TITOLO = "Recensioni & Bonus Monitor" if DEMO else "Recensioni Booking"


def corto(nome: str) -> str:
    """Nome breve della struttura per titoli, grafici e tabelle (toglie il prefisso del marchio)."""
    return nome.replace("Magenta ", "")

try:
    from pathlib import Path
    from PIL import Image
    _ICONA = Image.open(Path(__file__).parent / "icona.png")
except Exception:
    _ICONA = "⭐"
st.set_page_config(page_title=TITOLO, page_icon=_ICONA, layout="centered")

BLU = "#1F3B57"          # colore principale
ORO = "#C9A227"          # bonus / media che conta
GRIGIO = "#6B7A89"
TINTE = ["#7F9BB8", "#B4C6D8", "#4F7396", "#D5DFE9", "#2F5577"]   # strutture nei grafici

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stButton button, .stRadio, .stCaption, input, textarea {
    font-family: 'Inter', sans-serif !important;
}
/* barra in alto di Streamlit (Fork, GitHub, menu) e piè di pagina */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, footer { display: none !important; }
.block-container { padding-top: 1.2rem !important; padding-bottom: 3rem !important; max-width: 760px; }
h1, h2, h3 { color: #1F3B57; letter-spacing: -0.01em; }
h3 { font-size: 1.15rem !important; margin-top: 0.6rem !important; }
/* intestazione */
.bm-head { display:flex; align-items:center; gap:12px; margin-bottom:2px; }
.bm-logo { width:42px; height:42px; border-radius:11px; background:#1F3B57; display:flex;
           align-items:center; justify-content:center; font-size:22px; flex-shrink:0; }
.bm-title { font-size:1.35rem; font-weight:700; color:#1F3B57; line-height:1.15; }
.bm-sub { font-size:0.82rem; color:#6B7A89; margin-top:2px; }
.bm-badge { display:inline-block; background:#FBF3DC; color:#7A5F0E; border-radius:999px;
            padding:2px 10px; font-size:0.72rem; font-weight:600; margin-left:6px; vertical-align:middle; }
/* card dei numeri chiave */
.bm-kpi { display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin: 6px 0 4px 0; }
.bm-card { background:#F4F7FA; border:1px solid #E1E8EF; border-radius:14px; padding:12px 14px; }
.bm-card.bm-full { grid-column: 1 / -1; display:flex; justify-content:space-between; align-items:center; }
.bm-card.bm-bonus { background:#1F3B57; border-color:#1F3B57; }
.bm-lab { font-size:0.74rem; color:#6B7A89; text-transform:uppercase; letter-spacing:0.04em; font-weight:600; }
.bm-val { font-size:1.9rem; font-weight:700; color:#1F3B57; line-height:1.15; margin-top:2px; }
.bm-bonus .bm-lab { color:#B9C7D6; }
.bm-bonus .bm-val { color:#E3C35A; }
.bm-note { font-size:0.8rem; color:#6B7A89; margin-top:2px; }
.bm-pill { background:#FBF3DC; color:#7A5F0E; border-radius:999px; padding:3px 10px; font-size:0.78rem;
           font-weight:600; white-space:nowrap; }
.bm-avviso { background:#FBF3DC; color:#5E4A0B; border:1px solid #EAD9A0; border-radius:10px;
              padding:8px 12px; font-size:0.85rem; margin: 2px 0 8px 0; }
.bm-periodo { font-size:0.82rem; color:#6B7A89; background:#F4F7FA; border-radius:10px; padding:7px 12px;
              margin: 4px 0 8px 0; }
/* expander e tabelle più morbidi */
[data-testid="stExpander"] details { border-radius:12px !important; border-color:#E1E8EF !important; }
[data-testid="stExpander"] summary:hover { color:#1F3B57; }
.stButton button, .stFormSubmitButton button, .stDownloadButton button { border-radius:10px !important; font-weight:600; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border-radius:10px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)
# ---- lingua dell'interfaccia (it / en / ru): scelta dall'utente e salvata nella tabella preferenze
if "lingua" not in st.session_state:
    st.session_state["lingua"] = "it"
LANG = st.session_state["lingua"]


def tr(chiave: str, **valori) -> str:
    return _t(chiave, LANG, **valori)


def num(x, dec: int = 2) -> str:
    s_ = L.num(x, dec)
    return s_.replace(",", ".") if LANG == "en" else s_


def euro(x: float) -> str:
    """1.234,56 € (it) · €1,234.56 (en) · 1 234,56 € (ru)"""
    base = f"{x:,.2f}"
    if LANG == "en":
        return f"€{base}"
    sep_migliaia = "\u00a0" if LANG == "ru" else "."
    return base.replace(",", "X").replace(".", ",").replace("X", sep_migliaia) + " €"


SEPARATORI = ".," if LANG == "en" else (", " if LANG == "ru" else ",.")   # decimali e migliaia nei grafici


def scegli_lingua(chiave: str) -> None:
    """Selettore della lingua; se cambia la salva (dopo il login) e ricarica la pagina."""
    nuova = st.selectbox(tr("lingua"), list(LINGUE), format_func=LINGUE.get, index=list(LINGUE).index(LANG),
                         key=chiave, label_visibility="collapsed")
    if nuova != LANG:
        st.session_state["lingua"] = nuova
        if "sessione" in st.session_state and not DEMO:
            try:
                db.elimina(token(), "preferenze", {"user_id": f"eq.{st.session_state['sessione']['user_id']}"})
                db.inserisci(token(), "preferenze", [{"user_id": st.session_state["sessione"]["user_id"],
                                                      "lingua": nuova}])
            except Exception:
                pass                     # tabella non ancora creata: la lingua vale solo per questa sessione
        st.rerun()


def sfumatura(n: int) -> list[str]:
    """n tinte di blu, dalla più chiara alla più scura (uno spicchio per scaglione)."""
    tappe = [(0xEE, 0xF2, 0xF6), (0xC9, 0xD6, 0xE3), (0x8F, 0xA9, 0xC3)]
    out = []
    for i in range(n):
        t = i / max(n - 1, 1) * (len(tappe) - 1)
        k = min(int(t), len(tappe) - 2)
        r = t - k
        out.append("#" + "".join(f"{round(a + (b - a) * r):02X}" for a, b in zip(tappe[k], tappe[k + 1])))
    return out


def nome_mese(d: date) -> str:
    return f"{MESI[LANG][d.month - 1].capitalize()} {d.year}"


def stag_txt(stag: str) -> str:
    """Nome della stagione nella lingua scelta (internamente resta 'Inverno' / 'Estate')."""
    return tr(f"s_{stag}")


def titolo_app() -> str:
    if DEMO:
        return TITOLO
    return {"it": "Recensioni Booking", "en": "Booking Reviews", "ru": "Отзывы Booking"}[LANG]


def intestazione(sottotitolo: str = "", badge: str = "") -> None:
    b = f'<span class="bm-badge">{badge}</span>' if badge else ""
    sub = f'<div class="bm-sub">{sottotitolo}</div>' if sottotitolo else ""
    st.markdown(f'<div class="bm-head"><div class="bm-logo">⭐</div><div>'
                f'<div class="bm-title">{titolo_app()}{b}</div>{sub}</div></div>', unsafe_allow_html=True)

if DEMO:
    from dati_demo import DemoDB
    db = DemoDB()
else:
    db = Supa(_URL, _CHIAVE)


# =================================================================== sessione / login
def esci():
    if "sessione" in st.session_state:
        db.logout(st.session_state["sessione"])
    lingua = st.session_state.get("lingua", "it")
    st.session_state.clear()
    st.session_state["lingua"] = lingua
    st.cache_data.clear()


def token() -> str:
    s = st.session_state["sessione"]
    if time.time() > s["scade"]:
        st.session_state["sessione"] = s = db.rinnova(s)
    return s["access_token"]


def schermata_demo():
    intestazione(tr("demo_sotto"), "DEMO")
    scegli_lingua("lingua_demo")
    st.markdown(tr("demo_testo"))
    st.info(tr("demo_info"), icon="🧪")
    c1, c2 = st.columns(2)
    if c1.button(tr("entra_operatrice"), type="primary", use_container_width=True):
        st.session_state["sessione"] = db.login_demo("op_giulia")
        st.rerun()
    if c2.button(tr("entra_admin"), use_container_width=True):
        st.session_state["sessione"] = db.login_demo("admin_demo")
        st.rerun()
    st.caption(tr("demo_ruoli"))


def schermata_login():
    if DEMO:
        return schermata_demo()
    intestazione(tr("login_sotto"))
    scegli_lingua("lingua_login")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input(tr("password"), type="password")
        entra = st.form_submit_button(tr("accedi"), type="primary")
    if entra:
        try:
            st.session_state["sessione"] = db.login(email, password)
            st.rerun()
        except ErroreLogin:
            st.error(tr("login_errato"))
        except Exception:
            st.error(tr("servizio_ko"))


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
    if not DEMO and "lingua_caricata" not in st.session_state:      # primo giro dopo il login
        st.session_state["lingua_caricata"] = True
        try:
            pref = db.leggi(token(), "preferenze", {"select": "lingua", "user_id": f"eq.{io}"})
        except SessioneScaduta:
            raise
        except Exception:
            pref = []
        if pref and pref[0].get("lingua") in LINGUE and pref[0]["lingua"] != LANG:
            st.session_state["lingua"] = pref[0]["lingua"]
            st.rerun()
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
                utente = st.selectbox(tr("dashboard_di"), list(nomi), format_func=nomi.get,
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
    esclusi = {e["recensione_id"] for e in q("esclusioni", select="recensione_id", user_id=f"eq.{utente}")}
    ultima_esec = q("esecuzioni", select="eseguita_il,nuove,esito,dettagli", order="eseguita_il.desc", limit=1)
except SessioneScaduta:
    esci()
    st.warning(tr("sessione_scaduta"))
    st.stop()

# =================================================================== intestazione
c1, c2, c3 = st.columns([4, 1.4, 1], vertical_alignment="center")
with c1:
    intestazione(f"{prof_utente['nome']} · {', '.join(corto(s) for s in strutture) or tr('nessuna_struttura')}",
                 tr("demo_badge") if DEMO else "")
with c2:
    scegli_lingua("lingua_app")
if c3.button(tr("esci")):
    esci()
    st.rerun()

if not strutture:
    st.info(tr("no_strutture"))
    st.stop()
if not scaglioni:
    st.warning(tr("no_scaglioni"))

# =================================================================== filtri
oggi = datetime.now(ZoneInfo("Europe/Rome")).date()   # il server è in UTC
inizio = min(a["conta_dal"] for a in assegnazioni.values())
with st.expander(tr("filtri"), expanded=False):
    scelta = st.radio(tr("periodo"), ["Dall'inizio", "Mese corrente", "Mese a scelta", "Intervallo personalizzato"],
                      horizontal=True, format_func=lambda x: tr(f"p_{x}"))
    mese = dal_s = al_s = None
    if scelta == "Mese a scelta":
        mesi = pd.date_range(inizio.replace(day=1), oggi, freq="MS")[::-1]
        mese = st.selectbox(tr("mese"), [m.date() for m in mesi], format_func=nome_mese)
    elif scelta == "Intervallo personalizzato":
        cc1, cc2 = st.columns(2)
        dal_s = cc1.date_input(tr("dal"), inizio, format="DD/MM/YYYY")
        al_s = cc2.date_input(tr("al"), oggi, format="DD/MM/YYYY")
    crit_label = st.radio(tr("calcolato_su"), list(L.CRITERI), horizontal=True,
                          format_func=lambda x: tr(f"c_{x}"),
                          help=tr("calcolato_help", piattaforme=tr("piattaforme_demo") if DEMO else "Booking"))
    metodi_inv = {v: k for k, v in L.METODI.items()}
    metodo_label = st.radio(tr("media_bonus_label"), list(L.METODI), horizontal=True,
                            format_func=lambda x: tr(f"m_{x}"),
                            index=list(L.METODI).index(metodi_inv.get(prof_utente["metodo_media"],
                                                                      "Media delle strutture")),
                            help=tr("metodo_help"))
    stag_label = st.radio(tr("scaglioni"), ["Automatica", "Inverno", "Estate"], horizontal=True,
                          format_func=lambda x: tr(f"s_{x}"), help=tr("stag_help"))

criterio, metodo = L.CRITERI[crit_label], L.METODI[metodo_label]
dal, al = L.periodo(scelta, oggi, inizio, mese, dal_s, al_s)
df["escluso"] = df["id"].isin(esclusi) if not df.empty else pd.Series(dtype=bool)
df_calc = df[~df["escluso"]] if not df.empty else df          # le escluse non contano nei calcoli
dff = L.filtra(df_calc, assegnazioni, dal, al, criterio)
n_escl = int(L.filtra(df, assegnazioni, dal, al, criterio)["escluso"].sum()) if not df.empty else 0
st.markdown(f'<div class="bm-periodo">📅 <b>{dal:%d/%m/%Y} – {al:%d/%m/%Y}</b> · {tr("c_" + crit_label).lower()} · '
            + tr("recensioni_n", n=len(dff)) + (" · " + tr("escluse_n", n=n_escl) if n_escl else "") + "</div>",
            unsafe_allow_html=True)

# =================================================================== bonus
stag = L.stagione(al) if stag_label == "Automatica" else stag_label
media = L.media_bonus(dff, strutture, metodo)
bonus = L.bonus_per(media, scaglioni, stag)
prossimo = L.prossimo_scaglione(media, scaglioni, stag)

STIPENDIO = "stip"
SEZIONI = ["pan", "mesi", "sim", "rec"] + ([] if DEMO else [STIPENDIO])     # codici interni
if st.session_state.get("sezione") not in SEZIONI + [None]:   # valore di una versione precedente
    st.session_state.pop("sezione", None)
try:
    sezione = st.segmented_control("Sezione", SEZIONI, default=SEZIONI[0], key="sezione",
                                   format_func=lambda x: tr(f"sez_{x}"), label_visibility="collapsed")
except AttributeError:                                   # versioni vecchie di Streamlit
    sezione = st.radio("Sezione", SEZIONI, horizontal=True, key="sezione",
                       format_func=lambda x: tr(f"sez_{x}"), label_visibility="collapsed")
sezione = sezione or SEZIONI[0]


def card_numeri(media_, bonus_, prossimo_, stag_, titolo_media=None, titolo_bonus=None,
                nota_media="", nota_bonus="") -> None:
    titolo_media = titolo_media or tr("media_bonus_label")
    if prossimo_ and media_ is not None:
        pross = (f'<div><div class="bm-lab">{tr("prossimo")}</div><div class="bm-val" style="font-size:1.35rem">'
                 f'{num(prossimo_[0], 1)} → {L.perc(prossimo_[1])}</div></div>'
                 f'<span class="bm-pill">{tr("mancano", x=num(prossimo_[0] - media_))}</span>')
    elif prossimo_:
        pross = (f'<div><div class="bm-lab">{tr("prossimo")}</div><div class="bm-val" style="font-size:1.35rem">'
                 f'{num(prossimo_[0], 1)} → {L.perc(prossimo_[1])}</div></div>')
    else:
        pross = (f'<div><div class="bm-lab">{tr("prossimo")}</div><div class="bm-val" style="font-size:1.35rem">'
                 f'{tr("massimo")}</div></div>')
    nm = f'<div class="bm-note">{nota_media}</div>' if nota_media else ""
    nb = f'<div class="bm-note" style="color:#B9C7D6">{nota_bonus}</div>' if nota_bonus else ""
    st.markdown(
        f'<div class="bm-kpi">'
        f'<div class="bm-card"><div class="bm-lab">{titolo_media}</div><div class="bm-val">{num(media_)}</div>{nm}</div>'
        f'<div class="bm-card bm-bonus"><div class="bm-lab">{titolo_bonus or tr("bonus_stag", stag=stag_txt(stag_).lower())}</div>'
        f'<div class="bm-val">{L.perc(bonus_)}</div>{nb}</div>'
        f'<div class="bm-card bm-full">{pross}</div></div>', unsafe_allow_html=True)


# --- simulazione: voti ipotetici, salvati nel database (tabella simulazioni) per chi li ha inseriti
ALTRA = "Altra struttura"               # valore salvato nel database (non tradotto)
ALTRA_TXT = tr("altra_struttura")       # come appare nel menu


def _a_schermo(v: str) -> str:
    return ALTRA_TXT if v == ALTRA else v


def _da_schermo(v: str) -> str:
    return ALTRA if v == ALTRA_TXT else v


def _pulisci_sim(d: pd.DataFrame) -> pd.DataFrame:
    d = d.dropna(subset=["Struttura", "Voto"]).head(10).reset_index(drop=True)
    return pd.DataFrame({"Struttura": d["Struttura"].astype(str), "Voto": d["Voto"].astype(float)})


def _sim_firma(d: pd.DataFrame) -> list:
    return [(r.Struttura, float(r.Voto)) for r in d.itertuples()]


def carica_sim() -> pd.DataFrame:
    try:
        righe = db.leggi(token(), "simulazioni",
                         {"select": "struttura,voto,ordine", "user_id": f"eq.{io}",
                          "operatore_id": f"eq.{utente}", "order": "ordine"})
    except SessioneScaduta:
        raise
    except Exception:
        righe = []                       # tabella non ancora creata: simulatore senza salvataggio
        st.session_state["sim_no_db"] = True
    validi = set(strutture + [ALTRA])
    righe = [r for r in righe if r["struttura"] in validi]
    return pd.DataFrame({"Struttura": pd.Series([r["struttura"] for r in righe], dtype="object"),
                         "Voto": pd.Series([float(r["voto"]) for r in righe], dtype="float")})


def salva_sim(d: pd.DataFrame) -> bool:
    try:
        db.elimina(token(), "simulazioni", {"user_id": f"eq.{io}", "operatore_id": f"eq.{utente}"})
        if len(d):
            db.inserisci(token(), "simulazioni",
                         [{"user_id": io, "operatore_id": utente, "ordine": i, "struttura": r.Struttura,
                           "voto": float(r.Voto)} for i, r in enumerate(d.itertuples())])
        return True
    except SessioneScaduta:
        esci()
        st.rerun()
    except Exception as e:
        dettaglio = getattr(getattr(e, "response", None), "text", "") or str(e)
        st.warning(f"{tr('sim_non_salvata')} ({dettaglio[:150]})")
        return False


chiave_sim = f"sim_base_{utente}"
if chiave_sim not in st.session_state:           # primo accesso della sessione: riprende i voti salvati
    st.session_state[chiave_sim] = carica_sim()
    st.session_state[f"sim_ver_{utente}"] = 0
sim = st.session_state[chiave_sim]
n_sim = len(sim)
if n_sim:
    finti = pd.DataFrame({"struttura": sim["Struttura"].values, "punteggio": sim["Voto"].astype(float).values,
                          "data_riferimento": al, "id": [f"sim{i}" for i in range(n_sim)]})
    dff_sim = pd.concat([dff, finti], ignore_index=True)
    media_vis = L.media_bonus(dff_sim, strutture + [ALTRA], metodo)
    bonus_vis = L.bonus_per(media_vis, scaglioni, stag)
    prossimo_vis = L.prossimo_scaglione(media_vis, scaglioni, stag)
else:
    dff_sim, media_vis, bonus_vis, prossimo_vis = dff, media, bonus, prossimo

# --- contagiri: uno spicchio per scaglione, tinte di blu; la barra oro è la media attuale
soglie = [x[0] for x in sorted(scaglioni)]
inizio_scala = max(0.0, (min(soglie) - 0.2) // 0.5 * 0.5) if soglie else 8.5
bordi = [inizio_scala] + [x for x in soglie if inizio_scala < x < 10] + [10.0]
colori = sfumatura(len(bordi) - 1)
passi = [{"range": [bordi[i], bordi[i + 1]], "color": colori[i]} for i in range(len(bordi) - 1)]
gauge = go.Figure(go.Indicator(
    mode="gauge+number" if media_vis is not None else "gauge",
    value=media_vis if media_vis is not None else inizio_scala,
    number={"valueformat": ".2f", "font": {"size": 46, "color": BLU, "family": "Inter, sans-serif"}},
    gauge={"axis": {"range": [inizio_scala, 10], "tickvals": [x for x in bordi if round(x * 10) % 2 == 0 or x == bordi[0]],
                    "tickformat": ".1f", "tickcolor": "#B4C6D8", "tickfont": {"color": GRIGIO, "size": 11}},
           "bar": {"color": ORO, "thickness": 0.32},
           "bgcolor": "white", "borderwidth": 0,
           "steps": passi,
           "threshold": {"line": {"color": BLU, "width": 4}, "thickness": 0.95,
                         "value": prossimo_vis[0] if prossimo_vis else 10}},
))
gauge.update_layout(height=240, margin=dict(l=28, r=28, t=24, b=0), separators=SEPARATORI,
                    paper_bgcolor="rgba(0,0,0,0)", font={"family": "Inter, sans-serif"})

if sezione == SEZIONI[0]:
    if n_sim:
        st.markdown(f'<div class="bm-avviso">{tr("sim_avviso", n=n_sim, m=num(media), b=L.perc(bonus))}</div>',
                    unsafe_allow_html=True)
        card_numeri(media_vis, bonus_vis, prossimo_vis, stag, titolo_media=tr("media_con_sim"),
                    titolo_bonus=tr("bonus_con_sim", stag=stag_txt(stag).lower()))
    else:
        card_numeri(media, bonus, prossimo, stag)
    st.plotly_chart(gauge, config={"displayModeBar": False})
    if prossimo_vis:
        st.caption(tr("gauge_nota", quale=tr("quale_simulata" if n_sim else "quale_attuale"))
                   + (tr("gauge_nota_sim") if n_sim else ""))

if sezione == SEZIONI[2]:
    st.subheader(tr("sim_titolo"))
    salva_txt = tr("sim_salvati") if not st.session_state.get("sim_no_db") else tr("sim_non_salvati")
    st.caption(tr("sim_testo", altra=ALTRA_TXT, salva=salva_txt))
    sim_vista = sim.assign(Struttura=sim["Struttura"].map(_a_schermo))
    with st.form(f"form_sim_{utente}", border=False):
        modificata = st.data_editor(
            sim_vista, num_rows="dynamic", hide_index=True, use_container_width=True,
            key=f"simulazione_{utente}_{st.session_state[f'sim_ver_{utente}']}",
            column_config={
                "Struttura": st.column_config.SelectboxColumn(tr("struttura"), options=strutture + [ALTRA_TXT],
                                                              required=True,
                                                              default=strutture[0] if strutture else ALTRA_TXT),
                "Voto": st.column_config.NumberColumn(tr("voto"), min_value=1, max_value=10, step=1, default=10,
                                                      required=True),
            })
        salva = st.form_submit_button(tr("salva_simula"), type="primary", use_container_width=True)
    if salva:
        nuova = _pulisci_sim(modificata)
        nuova["Struttura"] = nuova["Struttura"].map(_da_schermo)
        if _sim_firma(nuova) == _sim_firma(sim):
            st.toast(tr("nessuna_modifica"))
        elif st.session_state.get("sim_no_db") or salva_sim(nuova):
            st.session_state[chiave_sim] = nuova
            st.session_state[f"sim_ver_{utente}"] += 1      # l'editor riparte dai voti appena salvati
            st.rerun()
    if n_sim and st.button(tr("azzera_sim"), use_container_width=True):
        if st.session_state.get("sim_no_db") or salva_sim(sim.iloc[0:0]):
            st.session_state[chiave_sim] = sim.iloc[0:0]
            st.session_state[f"sim_ver_{utente}"] += 1
            st.rerun()
    if n_sim:
        d_media = "" if media is None else f"{media_vis - media:+.2f}"
        d_media = d_media if LANG == "en" else d_media.replace(".", ",")
        d_bonus = (tr("invariato") if bonus_vis == bonus
                   else tr("punti_perc", x=f"{(bonus_vis - bonus) * 100:+.0f}"))
        card_numeri(media_vis, bonus_vis, prossimo_vis, stag, titolo_media=tr("media_simulata"),
                    titolo_bonus=tr("bonus_simulato"),
                    nota_media=tr("rispetto_oggi", d=d_media, n=len(dff_sim), k=n_sim), nota_bonus=d_bonus)
        if n_sim == 10:
            st.caption(tr("max_sim"))
    else:
        card_numeri(media, bonus, prossimo, stag, titolo_media=tr("media_attuale"), titolo_bonus=tr("bonus_attuale"),
                    nota_media=tr("sim_vuoto"))

if sezione == SEZIONI[0]:
    with st.expander(tr("tab_scaglioni", stag=stag_txt(stag).lower())):
        col_b = 1 if stag == "Inverno" else 2
        tab_s = pd.DataFrame([{tr("media_da"): num(x[0], 1), tr("bonus"): L.perc(x[col_b]),
                               "": tr("attuale_freccia") if media is not None and L.bonus_per(media, scaglioni, stag) == x[col_b]
                               and media >= x[0] and (prossimo is None or x[0] < prossimo[0]) else ""}
                              for x in sorted(scaglioni)])
        st.dataframe(tab_s, hide_index=True, use_container_width=True)

    # =============================================================== per struttura
    st.subheader(tr("per_struttura"))
    riep = L.riepilogo(dff, strutture)
    riep["Struttura"] = riep["Struttura"].map(corto)
    riep["Bonus"] = riep["Media"].apply(lambda m: L.perc(L.bonus_per(m, scaglioni, stag)) if pd.notna(m) else "-")
    riep["% voti ≥ 9"] = riep["% voti ≥ 9"] * 100
    st.dataframe(
        riep, hide_index=True, use_container_width=True,
        column_config={"Struttura": tr("struttura"), "Recensioni": tr("recensioni"),
                       "Media": st.column_config.NumberColumn(tr("media"), format="%.2f"),
                       "% voti ≥ 9": st.column_config.ProgressColumn(tr("voti_9"), format="%.0f%%",
                                                                     min_value=0, max_value=100),
                       "Voti < 7": tr("voti_7"), "Bonus": tr("bonus")},
    )

# =================================================================== andamento mensile (12 mesi fissi)
mesi12 = L.mesi_fissi(inizio)
fine12 = (pd.Timestamp(mesi12[-1]) + pd.offsets.MonthEnd(0)).date()
df12_tutte = L.filtra(df, assegnazioni, inizio, fine12, criterio)       # per l'elenco (anche le escluse)
df12 = L.filtra(df_calc, assegnazioni, inizio, fine12, criterio)       # per i calcoli
mens = L.mensile(df12, strutture, mesi12, scaglioni, metodo)
if sezione == SEZIONI[1]:
    st.subheader(tr("andamento", da=nome_mese(mesi12[0]), a=nome_mese(mesi12[-1])))
    fig = go.Figure()
    etich = [f"{MESI_BREVI[LANG][m.month - 1]} {str(m.year)[2:]}" for m in mens["Mese"]]
    for i_, s_ in enumerate(strutture):
        fig.add_bar(x=etich, y=mens[f"Media {s_}"], name=corto(s_), marker_color=TINTE[i_ % len(TINTE)])
    fig.add_bar(x=etich, y=mens["Media per bonus"],
                name=tr("media_per_bonus_leg"), marker_color=ORO)      # oro: la media che conta per il bonus
    fig.update_layout(height=300, barmode="group", bargap=0.25, yaxis_range=[7, 10],
                      margin=dict(l=10, r=10, t=10, b=10), separators=SEPARATORI,
                      legend=dict(orientation="h", y=-0.22, font={"size": 11}),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font={"family": "Inter, sans-serif", "color": GRIGIO})
    fig.update_yaxes(gridcolor="#E9EEF3", zeroline=False, tickformat=".1f")
    fig.update_xaxes(showgrid=False)
    st.plotly_chart(fig, config={"displayModeBar": False})
    st.caption(tr("mesi_nota"))
    # riepilogo: un mese per riga, solo i mesi con recensioni
    n_mese = mens[[f"N° {s_}" for s_ in strutture]].sum(axis=1)
    tab_m = pd.DataFrame({
        "Mese": [nome_mese(m) for m in mens["Mese"]],
        "Recensioni": n_mese.astype(int),
        "Media": mens["Media per bonus"],
        "Bonus": [L.perc(b) if b is not None and pd.notna(b) else "-" for b in mens["Bonus del mese"]],
        "Stagione": [stag_txt(x) for x in mens["Stagione"]],
    })[n_mese > 0]
    if tab_m.empty:
        st.caption(tr("nessuna_rec_mesi"))
    else:
        st.dataframe(tab_m, hide_index=True, use_container_width=True,
                     column_config={"Mese": tr("mese"), "Recensioni": tr("recensioni"),
                                    "Media": st.column_config.NumberColumn(tr("media"), format="%.2f"),
                                    "Bonus": tr("bonus"), "Stagione": tr("stagione")})


def mese_anno(d) -> str:
    return "" if d is None or pd.isna(d) else f"{MESI_BREVI[LANG][d.month - 1]} {d.year}"


def salva_esclusioni(prima: pd.DataFrame, dopo: pd.DataFrame, mese_key: str):
    # il mese resta aperto dopo il ricalcolo
    st.session_state["mese_aperto"] = mese_key
    cambi = dopo[dopo["Escludi"] != prima["Escludi"]]
    if cambi.empty:
        st.toast(tr("nessuna_modifica"))
        return
    da_aggiungere = [{"user_id": utente, "recensione_id": i, "escluso_da": io}
                     for i in cambi.loc[cambi["Escludi"], "id"]]
    da_togliere = list(cambi.loc[~cambi["Escludi"], "id"])
    try:
        if da_aggiungere:
            db.inserisci(token(), "esclusioni", da_aggiungere)
        if da_togliere:
            db.elimina(token(), "esclusioni", {"user_id": f"eq.{utente}", "recensione_id": filtro_in(da_togliere)})
    except SessioneScaduta:
        esci()
        st.rerun()
    except Exception as e:
        dettaglio = getattr(getattr(e, "response", None), "text", "") or str(e)
        st.error(tr("escl_errore", d=dettaglio[:300]))
        return
    # nuova "versione" della tabella: l'editor riparte pulito dai dati salvati
    st.session_state["ver_escl"] = st.session_state.get("ver_escl", 0) + 1
    st.session_state["msg_escl"] = tr("escl_salvate", a=len(da_aggiungere), b=len(da_togliere))
    st.cache_data.clear()
    st.rerun()


if sezione == SEZIONI[3]:
    st.subheader(tr("mese_per_mese"))
    st.caption(tr("mese_per_mese_nota"))
    for _, r in mens.iterrows():
        m = r["Mese"]
        parti = []
        for s_ in strutture:
            if r[f"N° {s_}"]:
                parti.append(f"{s_.split()[-1]} {num(r[f'Media {s_}'])} ({r[f'N° {s_}']})")
        if df12_tutte.empty:
            dm = df12_tutte
        else:
            rif = pd.to_datetime(df12_tutte["data_riferimento"])
            dm = df12_tutte[(rif.dt.year == m.year) & (rif.dt.month == m.month)].sort_values("data_recensione")
        n_escl_m = int(dm["escluso"].sum()) if not dm.empty else 0
        escl_txt = (" · " + tr("esclusa_n" if n_escl_m == 1 else "escluse_n_breve", n=n_escl_m)) if n_escl_m else ""
        stag_m = stag_txt(r["Stagione"]).lower()
        if parti:
            etichetta = tr("mese_riga", mese=nome_mese(m), parti=" · ".join(parti), m=num(r["Media per bonus"]),
                           b=L.perc(r["Bonus del mese"]), stag=stag_m, escl=escl_txt)
        elif not dm.empty:
            etichetta = tr("tutte_escluse", mese=nome_mese(m), stag=stag_m)
        else:
            etichetta = tr("nessuna_rec_mese", mese=nome_mese(m), stag=stag_m)
        mese_key = f"{m:%Y%m}"
        with st.expander(etichetta, expanded=st.session_state.get("mese_aperto") == mese_key):
            if dm.empty:
                st.caption(tr("nessuna_rec_ancora"))
                continue
            vista = pd.DataFrame({
                "Escludi": dm["escluso"].astype(bool).values,
                "Data": pd.to_datetime(dm["data_recensione"]).dt.strftime("%d/%m").values,
                "Soggiorno": [mese_anno(d) for d in dm["mese_soggiorno"]],
                "Struttura": dm["struttura"].map(corto).values,
                "Voto": dm["punteggio"].values,
                "Ospite": dm["nome"].fillna("").values,
                "Paese": dm["paese"].fillna("").values,
                "Titolo": dm["titolo"].fillna("").values,
                "👎": dm["negativo"].fillna("").values,
                "id": dm["id"].values,
            })
            config = {
                "Escludi": st.column_config.CheckboxColumn(tr("escludi"), help=tr("escludi_help")),
                "Data": tr("data"), "Soggiorno": tr("soggiorno"), "Struttura": tr("struttura"),
                "Voto": st.column_config.NumberColumn(tr("voto"), format="%.1f"),
                "Ospite": tr("ospite"), "Paese": tr("paese"), "Titolo": tr("titolo"),
                "id": None,                                   # nascosta
            }
            if st.session_state.get("mese_aperto") == mese_key and st.session_state.get("msg_escl"):
                st.success(st.session_state.pop("msg_escl"))
            # form: si possono spuntare più caselle e poi confermare una volta sola
            with st.form(f"form_{mese_key}", border=False):
                modificata = st.data_editor(
                    vista, hide_index=True, column_config=config,
                    key=f"mese_{mese_key}_{st.session_state.get('ver_escl', 0)}",
                    disabled=[c for c in vista.columns if c != "Escludi"])
                if st.form_submit_button(tr("applica"), type="primary"):
                    salva_esclusioni(vista, modificata, mese_key)

# =================================================================== elenco recensioni
dff_tutte = L.filtra(df, assegnazioni, dal, al, criterio)
if sezione == SEZIONI[3]:
    st.subheader(tr("tutte_periodo", n=len(dff_tutte)))
    st.caption(tr("periodo_filtri"))
    if dff_tutte.empty:
        st.caption(tr("nessuna_rec_periodo"))
    else:
        elenco = dff_tutte.sort_values("data_recensione", ascending=False)[
            ["escluso", "data_recensione", "struttura", "punteggio", "titolo", "positivo", "negativo",
             "nome", "paese", "tipo_viaggiatore", "mese_soggiorno"]].copy()
        for c in ("titolo", "positivo", "negativo", "nome", "paese", "tipo_viaggiatore"):
            elenco[c] = elenco[c].fillna("")
        elenco["struttura"] = elenco["struttura"].map(corto)
        st.dataframe(elenco, hide_index=True, use_container_width=True, column_config={
            "data_recensione": st.column_config.DateColumn(tr("data"), format="DD/MM/YYYY"),
            "struttura": tr("struttura"), "punteggio": st.column_config.NumberColumn(tr("voto"), format="%.1f"),
            "titolo": tr("titolo"), "positivo": "👍", "negativo": "👎", "nome": tr("ospite"), "paese": tr("paese"),
            "tipo_viaggiatore": tr("tipo"),
            "mese_soggiorno": st.column_config.DateColumn(tr("soggiorno"), format="MM/YYYY"),
            "escluso": st.column_config.CheckboxColumn(tr("esclusa")),
        })
        st.download_button(tr("scarica_csv"), elenco.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"recensioni_{dal:%Y%m%d}_{al:%Y%m%d}.csv", mime="text/csv")

# =================================================================== calcolatore stipendio
STIP_DEFAULT = {
    "fissi": pd.DataFrame({"Voce": ["Fisso"], "Importo €": [600.0], "Con bonus": [True]}),
    "checkin": 0, "tariffa": 5.5, "bonus": None, "bonus_auto": True,
    "coeff": 67.0, "imposta": 5.0, "inps": 27.0,
}


def stip_da_db() -> dict:
    """Ultimi valori salvati del calcolatore (tabella stipendio), oppure quelli predefiniti."""
    stp = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in STIP_DEFAULT.items()}
    try:
        righe = db.leggi(token(), "stipendio", {"select": "dati", "user_id": f"eq.{io}",
                                                "operatore_id": f"eq.{utente}"})
    except SessioneScaduta:
        raise
    except Exception:
        st.session_state["stip_no_db"] = True          # tabella non ancora creata
        return stp
    if righe and isinstance(righe[0].get("dati"), dict):
        d = righe[0]["dati"]
        if d.get("fissi"):
            stp["fissi"] = pd.DataFrame({"Voce": [x.get("voce", "Fisso") for x in d["fissi"]],
                                         "Importo €": [float(x.get("importo", 0)) for x in d["fissi"]],
                                         "Con bonus": [bool(x.get("con_bonus", False)) for x in d["fissi"]]})
        for k in ("checkin", "tariffa", "bonus", "bonus_auto", "coeff", "imposta", "inps"):
            if d.get(k) is not None:
                stp[k] = d[k]
    return stp


def stip_salva(stp: dict) -> None:
    if st.session_state.get("stip_no_db"):
        return
    dati = {"fissi": [{"voce": str(r["Voce"]), "importo": float(r["Importo €"]), "con_bonus": bool(r["Con bonus"])}
                      for _, r in stp["fissi"].iterrows()],
            **{k: stp.get(k) for k in ("checkin", "tariffa", "bonus", "bonus_auto", "coeff", "imposta", "inps")}}
    try:
        db.elimina(token(), "stipendio", {"user_id": f"eq.{io}", "operatore_id": f"eq.{utente}"})
        db.inserisci(token(), "stipendio", [{"user_id": io, "operatore_id": utente, "dati": dati}])
    except SessioneScaduta:
        esci()
        st.rerun()
    except Exception as e:
        dettaglio = getattr(getattr(e, "response", None), "text", "") or str(e)
        st.warning(f"{tr('stip_non_salvato')} ({dettaglio[:150]})")


if st.session_state.get("stip_utente") != utente:   # primo accesso (o cambio operatore per l'admin)
    st.session_state["stip"] = stip_da_db() if not DEMO else {
        k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in STIP_DEFAULT.items()}
    st.session_state["stip_utente"] = utente
    st.session_state["stip_ver"] = st.session_state.get("stip_ver", 0) + 1

if sezione == STIPENDIO:
    stp = st.session_state["stip"]
    if "Con bonus" not in stp["fissi"]:                 # sessioni aperte prima di questa colonna
        stp["fissi"]["Con bonus"] = [i == 0 for i in range(len(stp["fissi"]))]
    bonus_app = bonus_vis if bonus_vis is not None else 0.0
    st.subheader(tr("stip_titolo"))
    st.caption(tr("stip_testo", salva=tr("stip_salvati") if not st.session_state.get("stip_no_db") else "."))
    with st.form("form_stipendio", border=False):
        st.markdown(tr("fissi_titolo"))
        fissi = st.data_editor(
            stp["fissi"], num_rows="dynamic", hide_index=True, use_container_width=True,
            key=f"stip_fissi_{st.session_state['stip_ver']}",
            column_config={
                "Voce": st.column_config.TextColumn(tr("voce"), default=tr("fisso")),
                "Importo €": st.column_config.NumberColumn(tr("importo"), min_value=0.0, step=10.0, default=600.0,
                                                           format="%.2f €", required=True),
                "Con bonus": st.column_config.CheckboxColumn(tr("con_bonus"), default=False),
            })
        c1, c2 = st.columns(2)
        n_checkin = c1.number_input(tr("checkin_mese"), min_value=0, step=1, value=int(stp["checkin"]))
        tariffa = c2.number_input(tr("euro_checkin"), min_value=0.0, step=0.5, value=float(stp["tariffa"]),
                                  format="%.2f")
        auto = st.checkbox(
            tr("usa_bonus_app", b=L.perc(bonus_app), sim=tr("con_simulazione") if n_sim else ""),
            value=bool(stp.get("bonus_auto", True)), help=tr("usa_bonus_help"))
        bonus_pct = st.number_input(
            tr("bonus_mano"), min_value=0.0, max_value=200.0, step=5.0,
            value=float(stp["bonus"] if stp["bonus"] is not None else round(bonus_app * 100)))
        with st.expander(tr("param_fiscali")):
            f1, f2, f3 = st.columns(3)
            coeff = f1.number_input(tr("coeff"), 0.0, 100.0, float(stp["coeff"]), 1.0, help=tr("coeff_help"))
            aliq = f2.number_input(tr("imposta"), 0.0, 100.0, float(stp["imposta"]), 1.0, help=tr("imposta_help"))
            inps = f3.number_input(tr("inps"), 0.0, 100.0, float(stp["inps"]), 0.5, help=tr("inps_help"))
        calcola = st.form_submit_button(tr("calcola"), type="primary", use_container_width=True)
    if calcola:
        f = fissi.dropna(subset=["Importo €"]).reset_index(drop=True)
        f["Voce"] = f["Voce"].fillna(tr("fisso"))
        f["Con bonus"] = f["Con bonus"].fillna(False).astype(bool)
        st.session_state["stip"] = {"fissi": f, "checkin": n_checkin, "tariffa": tariffa, "bonus": bonus_pct,
                                    "bonus_auto": auto,
                                    "coeff": coeff, "imposta": aliq, "inps": inps}
        stip_salva(st.session_state["stip"])
        st.session_state["stip_ver"] += 1
        st.rerun()

    # ---- risultati (con i valori salvati)
    stp = st.session_state["stip"]
    b = (bonus_app if stp.get("bonus_auto", True) or stp["bonus"] is None else stp["bonus"] / 100)
    tot_fissi = float(stp["fissi"]["Importo €"].sum()) if len(stp["fissi"]) else 0.0
    fissi_bonus = (float(stp["fissi"].loc[stp["fissi"]["Con bonus"].astype(bool), "Importo €"].sum())
                   if len(stp["fissi"]) else 0.0)
    tot_ci = stp["checkin"] * stp["tariffa"]
    base = tot_fissi + tot_ci

    def netto(lordo: float) -> dict:
        imponibile = lordo * stp["coeff"] / 100
        contributi = imponibile * stp["inps"] / 100
        imposta = max(imponibile - contributi, 0) * stp["imposta"] / 100   # i contributi si deducono
        return {"imponibile": imponibile, "inps": contributi, "imposta": imposta,
                "netto": lordo - contributi - imposta}

    # scenario 1: bonus sui fissi spuntati + check-in; scenario 2: bonus solo sui check-in
    scen = {"Bonus su tutto": base + (fissi_bonus + tot_ci) * b, "Bonus solo sui check-in": base + tot_ci * b}
    calc = {k: netto(v) for k, v in scen.items()}

    st.markdown(f"#### {tr('lordo_mese')}")
    st.caption(tr("lordo_nota", f=euro(fissi_bonus), c=euro(tot_ci)))
    righe = [(tr("compensi_fissi"), tot_fissi, tot_fissi),
             (tr("checkin_riga", n=stp["checkin"], t=euro(stp["tariffa"])), tot_ci, tot_ci),
             (tr("prima_bonus"), base, base),
             (tr("bonus_riga", p=f"{b * 100:.0f}"), (fissi_bonus + tot_ci) * b, tot_ci * b),
             (tr("totale_lordo"), scen["Bonus su tutto"], scen["Bonus solo sui check-in"])]
    tab = pd.DataFrame({tr("voce"): [r[0] for r in righe],
                        tr("col_fisso_ci"): [euro(r[1]) for r in righe],
                        tr("col_solo_ci"): [euro(r[2]) for r in righe]})
    st.dataframe(tab, hide_index=True, use_container_width=True)

    st.markdown(f"#### {tr('dopo_tasse')}")
    tab2 = pd.DataFrame({
        tr("voce"): [tr("imponibile_riga", p=f"{stp['coeff']:.0f}"), tr("inps_riga", p=f"{stp['inps']:g}"),
                     tr("imposta_riga", p=f"{stp['imposta']:g}"), tr("netto_stimato")],
        tr("col_fisso_ci"): [euro(calc["Bonus su tutto"][k]) for k in ("imponibile", "inps", "imposta", "netto")],
        tr("col_solo_ci"): [euro(calc["Bonus solo sui check-in"][k])
                            for k in ("imponibile", "inps", "imposta", "netto")]})
    st.dataframe(tab2, hide_index=True, use_container_width=True)

    n1, n2 = calc["Bonus su tutto"]["netto"], calc["Bonus solo sui check-in"]["netto"]
    st.markdown(
        f'<div class="bm-kpi">'
        f'<div class="bm-card bm-bonus"><div class="bm-lab">{tr("netto_fisso_ci")}</div>'
        f'<div class="bm-val" style="font-size:1.5rem">{euro(n1)}</div>'
        f'<div class="bm-note" style="color:#B9C7D6">{tr("lordo_x", x=euro(scen["Bonus su tutto"]))}</div></div>'
        f'<div class="bm-card"><div class="bm-lab">{tr("netto_solo_ci")}</div>'
        f'<div class="bm-val" style="font-size:1.5rem">{euro(n2)}</div>'
        f'<div class="bm-note">{tr("lordo_x", x=euro(scen["Bonus solo sui check-in"]))}</div></div></div>',
        unsafe_allow_html=True)
    st.caption(tr("stip_nota"))

# =================================================================== piè di pagina
st.divider()
if ultima_esec:
    e = ultima_esec[0]
    quando = pd.to_datetime(e["eseguita_il"]).tz_convert("Europe/Rome").strftime("%d/%m/%Y %H:%M")
    icona = {"ok": "🟢", "parziale": "🟠", "errore": "🔴"}.get(e["esito"], "⚪")
    st.caption(f"{icona} " + tr("ultimo_agg", quando=quando, n=e["nuove"])
               + (f" · {e['dettagli']}" if e["esito"] != "ok" and e["dettagli"] else ""))
st.caption(tr("nota_media", p=tr("le_piattaforme") if DEMO else "Booking"))
