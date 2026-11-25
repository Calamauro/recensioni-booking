"""Genera recensioni_booking.xlsx.

Fogli:
- Dashboard   : filtri, riepilogo per struttura, bonus stagionale, contagiri,
                andamento mensile (12 mesi fissi, ogni mese apribile con le sue recensioni).
- Scaglioni   : tabella bonus inverno / estate (modificabile).
- Recensioni  : elenco completo (tabella Excel filtrabile).
- Calcoli     : celle tecniche per grafici e filtri (nascosto).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, DoughnutChart, Reference
from openpyxl.chart.series import DataPoint
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import Outline
from openpyxl.worksheet.table import Table, TableStyleInfo

FONT = "Arial"
BLU = "1F3B57"
GIALLO = PatternFill("solid", start_color="FFF2CC")
GRIGIO = PatternFill("solid", start_color="F2F2F2")
MESE_FILL = PatternFill("solid", start_color="DCE6F0")
TESTATA = PatternFill("solid", start_color=BLU)
BORDO = Border(bottom=Side(style="thin", color="D9D9D9"))

TIPI_BASE = ["Famiglia", "Coppia", "Gruppo", "Viaggiatore singolo", "Viaggiatore per affari"]
MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
           "agosto", "settembre", "ottobre", "novembre", "dicembre"]

# (media minima, bonus inverno 1 nov–31 mar, bonus estate 1 apr–31 ott)
SCAGLIONI_DEFAULT = [
    (8.7, 0.00, 0.00), (8.8, 0.05, 0.05), (8.9, 0.10, 0.10), (9.0, 0.15, 0.15),
    (9.1, 0.20, 0.25), (9.2, 0.25, 0.35), (9.3, 0.30, 0.45), (9.4, 0.35, 0.55),
    (9.5, 0.40, 0.65), (9.6, 0.45, 0.75), (9.7, 0.50, 0.85), (9.8, 0.55, 0.95),
    (9.9, 0.60, 0.95), (10.0, 0.65, 0.95),
]
INIZIO_SCALA_DEFAULT = 8.5

METODO_DUE = "Media delle 2 strutture"
METODO_TUTTE = "Tutte le recensioni insieme"


def f(bold=False, size=10, color="000000", italic=False):
    return Font(name=FONT, bold=bold, size=size, color=color, italic=italic)


def _testata(ws, riga, col_inizio, testi):
    for i, t in enumerate(testi):
        c = ws.cell(row=riga, column=col_inizio + i, value=t)
        c.font = f(bold=True, color="FFFFFF")
        c.fill = TESTATA
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _sfumatura(n: int) -> list[str]:
    """n colori dal rosso al verde passando per il giallo."""
    tappe = [(0xD9, 0x53, 0x4F), (0xF0, 0xAD, 0x4E), (0xE8, 0xD8, 0x4A), (0x8C, 0xC0, 0x5A), (0x1E, 0x7B, 0x45)]
    out = []
    for i in range(n):
        t = i / max(n - 1, 1) * (len(tappe) - 1)
        k = min(int(t), len(tappe) - 2)
        r = t - k
        c = [round(a + (b - a) * r) for a, b in zip(tappe[k], tappe[k + 1])]
        out.append("".join(f"{x:02X}" for x in c))
    return out


def _colora_punto(serie, idx, colore=None):
    pt = DataPoint(idx=idx)
    if colore:
        pt.graphicalProperties.solidFill = colore
        pt.graphicalProperties.line.solidFill = "FFFFFF"
    else:
        pt.graphicalProperties.noFill = True
        pt.graphicalProperties.line.noFill = True
    serie.dPt.append(pt)


def _stagione(d) -> str:
    return "Inverno" if d.month >= 11 or d.month <= 3 else "Estate"


def crea_excel(righe: list[dict], percorso: Path, data_inizio: date, strutture: list[str],
               scaglioni: list[tuple[float, float, float]] | None = None,
               inizio_scala: float = INIZIO_SCALA_DEFAULT):
    scaglioni = sorted(scaglioni or SCAGLIONI_DEFAULT)
    wb = Workbook()
    dash = wb.active
    dash.title = "Dashboard"
    sca = wb.create_sheet("Scaglioni")
    rec = wb.create_sheet("Recensioni")
    calc = wb.create_sheet("Calcoli")

    # =================================================================== Recensioni
    intest = ["Struttura", "Data recensione", "Mese soggiorno", "Notti", "Punteggio", "Titolo",
              "Commento positivo", "Commento negativo", "Ospite", "Paese", "Tipo viaggiatore",
              "Camera", "Data riferimento", "Nel periodo", "ID"]
    larghezze = [28, 14, 14, 7, 10, 34, 50, 50, 14, 14, 20, 34, 15, 11, 14]
    rec.append(intest)
    for i, w in enumerate(larghezze, 1):
        rec.column_dimensions[get_column_letter(i)].width = w
    for n, r in enumerate(righe, start=2):
        punteggio = float(r["punteggio"]) if str(r["punteggio"]).strip() not in ("", "None") else None
        rec.append([
            r["struttura"],
            date.fromisoformat(str(r["data_recensione"])),
            date.fromisoformat(str(r["mese_soggiorno"])) if r["mese_soggiorno"] else None,
            int(float(r["notti"])) if str(r["notti"]).strip() not in ("", "None") else None,
            punteggio,
            r["titolo"], r["positivo"], r["negativo"], r["nome"], r["paese"],
            r["tipo_viaggiatore"] or "N/D", r["camera"],
            f'=IF(Dashboard!$C$7="Mese soggiorno",IF(C{n}="",B{n},C{n}),B{n})',
            f'=IF(AND(M{n}>=Calcoli!$B$3,M{n}<=Dashboard!$C$5),"Sì","No")',
            r["id"],
        ])
    ultima = max(len(righe) + 1, 2)
    for row in rec.iter_rows(min_row=2, max_row=ultima):
        for c in row:
            c.font = f()
            c.alignment = Alignment(vertical="top", wrap_text=c.column in (6, 7, 8))
        row[1].number_format = "dd/mm/yyyy"
        row[2].number_format = "mmm yyyy"
        row[4].number_format = "0.0"
        row[12].number_format = "dd/mm/yyyy"
    for c in rec[1]:
        c.font = f(bold=True, color="FFFFFF")
    rec.freeze_panes = "B2"
    tab = Table(displayName="Recensioni", ref=f"A1:{get_column_letter(len(intest))}{ultima}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    rec.add_table(tab)
    rec.conditional_formatting.add(f"E2:E{ultima}", CellIsRule(operator="greaterThanOrEqual", formula=["9"],
                                   fill=PatternFill("solid", start_color="C6EFCE")))
    rec.conditional_formatting.add(f"E2:E{ultima}", CellIsRule(operator="lessThan", formula=["7"],
                                   fill=PatternFill("solid", start_color="FFC7CE")))
    rec.conditional_formatting.add(f"A2:O{ultima}", FormulaRule(formula=['$N2="No"'],
                                   font=Font(name=FONT, color="A6A6A6")))

    R = lambda col: f"Recensioni!${col}$2:${col}${ultima}"
    STR, PUN, TIPO, PER, RIF = R("A"), R("E"), R("K"), R("N"), R("M")

    # =================================================================== Scaglioni
    sca.sheet_view.showGridLines = False
    for col, w in zip("ABCDE", [14, 26, 26, 4, 60]):
        sca.column_dimensions[col].width = w
    _testata(sca, 1, 1, ["Media da", "Bonus inverno\n(1 nov – 31 mar)", "Bonus estate\n(1 apr – 31 ott)"])
    sca.row_dimensions[1].height = 32
    sca.append([0, 0, 0])
    for c in sca[2]:
        c.fill, c.font = GRIGIO, f(color="808080")
    for s, inv, est in scaglioni:
        sca.append([s, inv, est])
    n_sca = len(scaglioni)
    ultima_s = 2 + n_sca
    for row in sca.iter_rows(min_row=2, max_row=ultima_s, max_col=3):
        for c in row:
            c.alignment = Alignment(horizontal="center")
            if c.row > 2:
                c.fill, c.font = GIALLO, f(color="0000FF")
        row[0].number_format = "0.00"
        row[1].number_format = row[2].number_format = "0%"
    sca.conditional_formatting.add(f"B3:C{ultima_s}", CellIsRule(operator="greaterThan", formula=["0"],
                                   font=Font(name=FONT, color="006100", bold=True)))
    note_s = ["Come si legge", "Se la media è almeno il valore di 'Media da', si ottiene il bonus della riga.",
              "La riga grigia (0) è la base: sotto il primo scaglione il bonus è 0%. Non cancellarla.",
              "Le celle gialle si possono modificare; aggiungendo righe, aggiungile anche in booking_reviews.py.",
              "Stagione: inverno = recensioni di novembre–marzo, estate = aprile–ottobre."]
    for i, t in enumerate(note_s):
        sca.cell(row=1 + i, column=5, value=t).font = f(bold=(i == 0), size=9, color="595959")
    SOG = f"Scaglioni!$A$2:$A${ultima_s}"
    INV = f"Scaglioni!$B$2:$B${ultima_s}"
    EST = f"Scaglioni!$C$2:$C${ultima_s}"

    def bonus_f(media: str, stagione: str) -> str:
        return (f'IF(ISNUMBER({media}),IF({stagione}="Inverno",INDEX({INV},MATCH({media},{SOG},1)),'
                f'INDEX({EST},MATCH({media},{SOG},1))),"-")')

    # =================================================================== Dashboard
    dash.sheet_view.showGridLines = False
    dash.sheet_properties.outlinePr = Outline(summaryBelow=False, summaryRight=True)
    for col, w in zip("ABCDEFGHI", [2, 34, 24, 14, 16, 14, 16, 14, 46]):
        dash.column_dimensions[col].width = w

    dash["B1"] = "Recensioni Booking – monitoraggio punteggio e bonus"
    dash["B1"].font = f(bold=True, size=16, color=BLU)
    dash["B2"] = "Modifica solo le celle gialle. Gli scaglioni si cambiano nel foglio 'Scaglioni'."
    dash["B2"].font = f(italic=True, color="595959")

    filtri = [
        (4, "Dal", data_inizio, "dd/mm/yyyy", "inizio del conteggio"),
        (5, "Al", "=TODAY()", "dd/mm/yyyy", "di default: oggi"),
        (6, "Struttura", "Tutte", None, ""),
        (7, "Periodo calcolato su", "Data recensione", None, "vedi Note in fondo"),
        (8, "Tipo viaggiatore", "Tutti", None, ""),
        (9, "Media bonus calcolata su", METODO_DUE, None, ""),
        (10, "Stagione scaglioni", "Automatica", None, "Automatica = stagione della data 'Al'"),
    ]
    for riga, etichetta, valore, fmt, nota in filtri:
        dash[f"B{riga}"] = etichetta
        dash[f"B{riga}"].font = f(bold=True)
        c = dash[f"C{riga}"]
        c.value, c.fill, c.font = valore, GIALLO, f(color="0000FF")
        c.alignment = Alignment(horizontal="center", shrink_to_fit=True)
        if fmt:
            c.number_format = fmt
        if nota:
            dash[f"D{riga}"] = "← " + nota
            dash[f"D{riga}"].font = f(italic=True, size=9, color="808080")
    tipi = TIPI_BASE + sorted({r["tipo_viaggiatore"] for r in righe if r["tipo_viaggiatore"]} - set(TIPI_BASE))
    for cella, opzioni in (("C6", ["Tutte"] + strutture), ("C7", ["Data recensione", "Mese soggiorno"]),
                           ("C8", ["Tutti"] + tipi), ("C9", [METODO_DUE, METODO_TUTTE]),
                           ("C10", ["Automatica", "Inverno", "Estate"])):
        dv = DataValidation(type="list", formula1='"' + ",".join(opzioni) + '"', allow_blank=False)
        dash.add_data_validation(dv)
        dv.add(dash[cella])

    # --- celle tecniche
    calc["A1"] = "Celle tecniche usate da filtri e grafici: non modificare."
    calc["A3"], calc["B3"] = "Inizio periodo effettivo", \
        '=IF(Dashboard!$C$7="Mese soggiorno",DATE(YEAR(Dashboard!$C$4),MONTH(Dashboard!$C$4),1),Dashboard!$C$4)'
    calc["B3"].number_format = "dd/mm/yyyy"
    calc["A4"], calc["B4"] = "Criterio struttura", '=IF(Dashboard!$C$6="Tutte","*",Dashboard!$C$6)'
    calc["A5"], calc["B5"] = "Criterio tipo", '=IF(Dashboard!$C$8="Tutti","*",Dashboard!$C$8)'
    calc["A6"], calc["B6"] = "Stagione in uso", \
        ('=IF(Dashboard!$C$10="Automatica",IF(OR(MONTH(Dashboard!$C$5)>=11,MONTH(Dashboard!$C$5)<=3),'
         '"Inverno","Estate"),Dashboard!$C$10)')
    CRIT_STR, CRIT_TIPO, STAG = "Calcoli!$B$4", "Calcoli!$B$5", "Calcoli!$B$6"

    # --- riepilogo per struttura
    dash["B12"] = "Riepilogo nel periodo selezionato"
    dash["B12"].font = f(bold=True, size=12, color=BLU)
    _testata(dash, 13, 2, ["Struttura", "N° recensioni", "Media", "% voti ≥ 9", "N° voti < 7", "Bonus raggiunto"])
    righe_riep = strutture + ["Selezione corrente (filtro struttura)"]
    for k, nome in enumerate(righe_riep):
        r_ = 14 + k
        ultima_riga = k == len(strutture)
        crit = CRIT_STR if ultima_riga else f"$B${r_}"
        base = f'{STR},{crit},{PER},"Sì",{TIPO},{CRIT_TIPO}'
        dash[f"B{r_}"] = nome
        dash[f"C{r_}"] = f"=COUNTIFS({base})"
        dash[f"D{r_}"] = f'=IFERROR(AVERAGEIFS({PUN},{base}),"-")'
        dash[f"E{r_}"] = f'=IFERROR(COUNTIFS({base},{PUN},">=9")/C{r_},"-")'
        dash[f"F{r_}"] = f'=COUNTIFS({base},{PUN},"<7")'
        dash[f"G{r_}"] = "=" + bonus_f(f"D{r_}", STAG)
        for col in "BCDEFG":
            c = dash[f"{col}{r_}"]
            c.font, c.border = f(bold=ultima_riga), BORDO
            if col != "B":
                c.alignment = Alignment(horizontal="center")
            if ultima_riga:
                c.fill = GRIGIO
        dash[f"D{r_}"].number_format = "0.00"
        dash[f"E{r_}"].number_format = "0%"
        dash[f"G{r_}"].number_format = "0%"
    riep_fine = 14 + len(righe_riep) - 1
    riep_strutt = f"D14:D{13 + len(strutture)}"

    # --- box bonus
    b0 = riep_fine + 2
    dash[f"B{b0}"] = "Bonus"
    dash[f"B{b0}"].font = f(bold=True, size=12, color=BLU)
    MEDIA = f"$C${b0 + 2}"
    BON = f"$C${b0 + 3}"
    PROX = f"$C${b0 + 4}"
    tutte = f'{STR},"*",{PER},"Sì",{TIPO},{CRIT_TIPO}'
    prossimo = (f'IF({STAG}="Inverno",_xlfn.MINIFS({SOG},{SOG},">"&{MEDIA},{INV},">"&{BON}),'
                f'_xlfn.MINIFS({SOG},{SOG},">"&{MEDIA},{EST},">"&{BON}))')
    box = [
        ("Stagione scaglioni in uso", f"={STAG}", "@"),
        ("Media valida per il bonus",
         f'=IFERROR(IF($C$9="{METODO_TUTTE}",AVERAGEIFS({PUN},{tutte}),AVERAGE({riep_strutt})),"-")', "0.00"),
        ("Bonus raggiunto", f'=IF(ISNUMBER({MEDIA}),{bonus_f(MEDIA, STAG)},0)', "0%"),
        ("Prossimo scaglione (media)",
         f'=IF(ISNUMBER({MEDIA}),IF({prossimo}=0,"Massimo raggiunto",{prossimo}),INDEX({SOG},2))', "0.00"),
        ("Bonus al prossimo scaglione",
         f'=IF(ISNUMBER({PROX}),IF({STAG}="Inverno",INDEX({INV},MATCH({PROX},{SOG},0)),'
         f'INDEX({EST},MATCH({PROX},{SOG},0))),"-")', "0%"),
        ("Punti di media mancanti",
         f'=IF(AND(ISNUMBER({MEDIA}),ISNUMBER({PROX})),{PROX}-{MEDIA},0)', "0.00"),
    ]
    for i, (etichetta, formula, fmt) in enumerate(box):
        r_ = b0 + 1 + i
        dash[f"B{r_}"] = etichetta
        dash[f"B{r_}"].font = f(bold=True)
        c = dash[f"C{r_}"]
        c.value, c.number_format = formula, fmt
        c.alignment = Alignment(horizontal="center")
        c.font = f(bold=True, size=12 if i in (1, 2) else 10, color=BLU if i in (1, 2) else "000000")
        for col in "BC":
            dash[f"{col}{r_}"].border = BORDO
    dash[f"C{b0 + 3}"].fill = PatternFill("solid", start_color="E2EFDA")

    # --- contagiri (accanto al box)
    calc["A12"] = "Contagiri"
    calc["A13"], calc["B13"], calc["C13"] = "Fascia", "Fasce colorate", "Lancetta"
    MED_C, MIN_C = f"Dashboard!{MEDIA}", "Calcoli!$B$8"
    calc["A8"], calc["B8"] = "Inizio scala contagiri", inizio_scala
    soglie_c = [f"Scaglioni!$A${3 + i}" for i in range(n_sca)]
    fasce = [("Sotto il 1° scaglione", f"=MAX(0,{soglie_c[0]}-{MIN_C})")]
    for i in range(n_sca - 1):
        fasce.append((f"Da {scaglioni[i][0]:.1f}", f"=MAX(0,{soglie_c[i + 1]}-MAX({soglie_c[i]},{MIN_C}))"))
    fasce.append(("Oltre l'ultimo", f"=MAX(0,10-MAX({soglie_c[-1]},{MIN_C}))"))
    fasce.append(("Metà inferiore (invisibile)", f"=10-{MIN_C}"))
    larg = f"(10-{MIN_C})*0.02"
    pos = f"MAX(0,MIN(IF(ISNUMBER({MED_C}),{MED_C},{MIN_C}),10)-{MIN_C}-{larg}/2)"
    lancetta = [f"={pos}", f"={larg}", f"=MAX(0,10-{MIN_C}-{pos}-{larg})"]
    lancetta += ["=0"] * (len(fasce) - 4) + [f"=10-{MIN_C}"]
    for i, ((nome, formula), lan) in enumerate(zip(fasce, lancetta)):
        r_ = 14 + i
        calc[f"A{r_}"], calc[f"B{r_}"], calc[f"C{r_}"] = nome, formula, lan
    ultima_fascia = 13 + len(fasce)

    gauge = DoughnutChart(holeSize=55, firstSliceAng=270)
    gauge.title = "Contagiri bonus"
    gauge.add_data(Reference(calc, min_col=2, min_row=13, max_row=ultima_fascia), titles_from_data=True)
    gauge.add_data(Reference(calc, min_col=3, min_row=13, max_row=ultima_fascia), titles_from_data=True)
    colori = _sfumatura(len(fasce) - 1)
    for i, col in enumerate(colori):
        _colora_punto(gauge.series[0], i, col)
    _colora_punto(gauge.series[0], len(fasce) - 1, None)
    for i in range(len(fasce)):
        _colora_punto(gauge.series[1], i, BLU if i == 1 else None)
    gauge.legend = None
    gauge.height, gauge.width = 7.5, 10
    gauge.roundedCorners = False
    gauge.title.overlay = False
    dash.add_chart(gauge, f"E{b0}")
    dash[f"B{b0 + 8}"] = ("Contagiri: ogni spicchio è uno scaglione, dal rosso (nessun bonus) al verde scuro "
                          "(bonus massimo). La lancetta blu è la media attuale.")
    dash[f"B{b0 + 8}"].font = f(italic=True, size=9, color="808080")

    # =================================================================== Andamento mensile (12 mesi fissi)
    m0 = b0 + 16
    mesi = []
    a, m = data_inizio.year, data_inizio.month
    for _ in range(12):
        mesi.append(date(a, m, 1))
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)

    dash[f"B{m0}"] = (f"Andamento mensile ({MESI_IT[mesi[0].month - 1]} {mesi[0].year} – "
                      f"{MESI_IT[mesi[-1].month - 1]} {mesi[-1].year})")
    dash[f"B{m0}"].font = f(bold=True, size=12, color=BLU)
    dash[f"B{m0 + 1}"] = "Premi il + a sinistra del numero di riga per aprire un mese e vedere le sue recensioni."
    dash[f"B{m0 + 1}"].font = f(italic=True, size=9, color="808080")
    brevi = [s.replace("Magenta ", "") for s in strutture]
    testate_m = ["Mese"]
    for b in brevi:
        testate_m += [f"Media {b}", f"N° {b}"]
    testate_m += ["Media delle 2 strutture", "Bonus del mese", "Dettaglio recensione"]
    _testata(dash, m0 + 2, 2, testate_m)
    dash.row_dimensions[m0 + 2].height = 30
    col_comb = get_column_letter(3 + 2 * len(strutture))
    col_bon = get_column_letter(4 + 2 * len(strutture))
    col_det = get_column_letter(5 + 2 * len(strutture))
    ultima_col = 5 + 2 * len(strutture)

    # dati per il grafico mensile (Calcoli E:..)
    calc["E1"] = "Mese"
    for j, b in enumerate(brevi):
        calc.cell(row=1, column=6 + j, value=f"Media {b}")
    calc.cell(row=1, column=6 + len(brevi), value="Media delle 2 strutture")
    col_mbon = get_column_letter(7 + len(brevi))
    calc[f"{col_mbon}1"] = "Media per bonus del mese"

    per_mese = {}
    for r in righe:
        d = date.fromisoformat(str(r["data_recensione"]))
        if d >= data_inizio:
            per_mese.setdefault((d.year, d.month), []).append(r)

    riga = m0 + 3
    righe_mese = []
    for i, mese in enumerate(mesi):
        rm = riga
        righe_mese.append(rm)
        dash[f"B{rm}"] = mese
        dash[f"B{rm}"].number_format = "mmmm yyyy"
        col_medie = []
        for j, s in enumerate(strutture):
            cm, cn = get_column_letter(3 + 2 * j), get_column_letter(4 + 2 * j)
            col_medie.append(f"{cm}{rm}")
            crit_m = (f'{STR},"{s}",{RIF},">="&$B{rm},{RIF},"<"&EDATE($B{rm},1),'
                      f'{RIF},">="&Calcoli!$B$3,{RIF},"<="&$C$5,{TIPO},{CRIT_TIPO}')
            dash[f"{cm}{rm}"] = f'=IFERROR(AVERAGEIFS({PUN},{crit_m}),"-")'
            dash[f"{cn}{rm}"] = f"=COUNTIFS({crit_m})"
            dash[f"{cm}{rm}"].number_format = "0.00"
        dash[f"{col_comb}{rm}"] = f'=IFERROR(AVERAGE({",".join(col_medie)}),"-")'
        dash[f"{col_comb}{rm}"].number_format = "0.00"
        # media usata per il bonus del mese (metodo scelto in C9) e bonus con la stagione del mese
        crit_tutte = (f'{RIF},">="&Dashboard!$B{rm},{RIF},"<"&EDATE(Dashboard!$B{rm},1),'
                      f'{RIF},">="&Calcoli!$B$3,{RIF},"<="&Dashboard!$C$5,{TIPO},{CRIT_TIPO}')
        cr = 2 + i
        calc[f"E{cr}"] = f"=Dashboard!B{rm}"
        calc[f"E{cr}"].number_format = "mmm yy"
        for j in range(len(strutture)):
            calc.cell(row=cr, column=6 + j, value=f'=IF(ISNUMBER(Dashboard!{col_medie[j]}),Dashboard!{col_medie[j]},0)')
        calc.cell(row=cr, column=6 + len(brevi),
                  value=f'=IF(ISNUMBER(Dashboard!{col_comb}{rm}),Dashboard!{col_comb}{rm},0)')
        calc[f"{col_mbon}{cr}"] = (f'=IF(Dashboard!$C$9="{METODO_TUTTE}",IFERROR(AVERAGEIFS({PUN},{crit_tutte}),"-"),'
                                   f'Dashboard!{col_comb}{rm})')
        stag_mese = f'IF(OR(MONTH($B{rm})>=11,MONTH($B{rm})<=3),"Inverno","Estate")'
        dash[f"{col_bon}{rm}"] = "=" + bonus_f(f"Calcoli!{col_mbon}{cr}", stag_mese)
        dash[f"{col_bon}{rm}"].number_format = "0%"
        n_rec = len(per_mese.get((mese.year, mese.month), []))
        dash[f"{col_det}{rm}"] = (f"{_stagione(mese)} · {n_rec} recensioni" if n_rec
                                  else f"{_stagione(mese)} · nessuna recensione")
        for col in range(2, ultima_col + 1):
            c = dash.cell(row=rm, column=col)
            c.font = f(bold=True, color=BLU if col == ultima_col else "000000",
                       italic=col == ultima_col, size=9 if col == ultima_col else 10)
            c.fill, c.border = MESE_FILL, BORDO
            c.alignment = Alignment(horizontal="left" if col in (2, ultima_col) else "center")
        riga += 1

        # righe di dettaglio del mese (raggruppate e chiuse)
        dettagli = sorted(per_mese.get((mese.year, mese.month), []),
                          key=lambda r: (str(r["data_recensione"]), r["struttura"]))
        if dettagli:
            primo = riga
            for r in dettagli:
                d = date.fromisoformat(str(r["data_recensione"]))
                ospite = " · ".join(x for x in (r["nome"], r["paese"]) if x)
                dash[f"B{riga}"] = f"   {d:%d/%m}  {ospite}"
                if r["struttura"] in strutture:
                    j = strutture.index(r["struttura"])
                    cm = get_column_letter(3 + 2 * j)
                    v = r["punteggio"]
                    dash[f"{cm}{riga}"] = float(v) if str(v).strip() not in ("", "None") else None
                    dash[f"{cm}{riga}"].number_format = "0.0"
                testo = r["titolo"] or ""
                if r.get("negativo"):
                    testo += f"  (👎 {r['negativo']})"
                dash[f"{col_det}{riga}"] = testo
                for col in range(2, ultima_col + 1):
                    c = dash.cell(row=riga, column=col)
                    c.font = f(size=9, color="404040")
                    c.alignment = Alignment(horizontal="left" if col in (2, ultima_col) else "center",
                                            shrink_to_fit=col == 2)
                riga += 1
            dash.row_dimensions.group(primo, riga - 1, outline_level=1, hidden=True)
    m_fine = riga - 1

    # colori sui punteggi (mesi e dettagli)
    for j in range(len(strutture)):
        cm = get_column_letter(3 + 2 * j)
        area = f"{cm}{m0 + 3}:{cm}{m_fine}"
        dash.conditional_formatting.add(area, CellIsRule(operator="lessThan", formula=["7"],
                                        font=Font(name=FONT, color="9C0006", bold=True)))
    dash.conditional_formatting.add(f"{col_bon}{m0 + 3}:{col_bon}{m_fine}",
                                    CellIsRule(operator="greaterThan", formula=["0"],
                                               font=Font(name=FONT, color="006100", bold=True)))

    # grafico mensile
    chart = BarChart()
    chart.type = "col"
    chart.gapWidth = 60
    chart.title = "Media punteggio per mese"
    chart.y_axis.title = "Punteggio"
    chart.y_axis.scaling.min = 7
    chart.y_axis.scaling.max = 10
    chart.height, chart.width = 7.5, 20
    for j in range(len(brevi) + 1):
        chart.add_data(Reference(calc, min_col=6 + j, min_row=1, max_row=13), titles_from_data=True)
    chart.set_categories(Reference(calc, min_col=5, min_row=2, max_row=13))
    chart.x_axis.number_format = "mmm yy"
    chart.roundedCorners = False
    chart.legend.position = "b"
    chart.legend.overlay = False
    chart.title.overlay = False
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    dash.add_chart(chart, f"B{m_fine + 2}")

    # --- note
    n0 = m_fine + 19
    note = [
        "Note",
        "• Periodo calcolato su: 'Data recensione' = giorno in cui l'ospite ha scritto; "
        "'Mese soggiorno' = mese in cui ha dormito (Booking mostra solo mese/anno, quindi conta tutto il mese della data 'Dal').",
        "• Media bonus calcolata su: 'Media delle 2 strutture' = (media Purificazione + media Barberini) / 2; "
        "'Tutte le recensioni insieme' = media di tutti i voti.",
        "• Bonus del mese: usa la stagione del mese (inverno = nov–mar, estate = apr–ott) e il metodo di media scelto sopra.",
        "• Le recensioni dentro ogni mese seguono la data della recensione dal giorno 'Dal' iniziale: "
        "se cambi i filtri, si aggiornano i totali ma l'elenco resta quello generato dallo script.",
        "• Il punteggio che Booking mostra in pagina NON è una media semplice (usa le recensioni degli ultimi 36 mesi).",
        "• Il file viene rigenerato a ogni esecuzione dello script: per rendere permanenti date e scaglioni "
        "modificali in booking_reviews.py (sezione CONFIGURAZIONE).",
    ]
    for i, t in enumerate(note):
        c = dash[f"B{n0 + i}"]
        c.value = t
        c.font = f(bold=(i == 0), size=9 if i else 10, color="595959")

    for row in calc.iter_rows():
        for c in row:
            c.font = f()
    calc.column_dimensions["A"].width = 28
    calc.sheet_state = "hidden"

    dash.page_setup.orientation = "landscape"
    dash.page_setup.fitToWidth = 1
    dash.page_setup.fitToHeight = 0
    dash.sheet_properties.pageSetUpPr.fitToPage = True
    wb.save(percorso)


if __name__ == "__main__":
    import csv
    try:
        cartella = Path(__file__).resolve().parent
    except NameError:
        cartella = Path.cwd()
    src = cartella / "recensioni.csv"
    if not src.exists():
        print(f"Nessun recensioni.csv in {cartella}: lancia prima booking_reviews.py")
    else:
        with src.open(encoding="utf-8-sig") as fh:
            crea_excel(list(csv.DictReader(fh)), cartella / "recensioni_booking.xlsx",
                       date(2026, 11, 5), ["Magenta Luxury Purificazione", "Magenta Casa Barberini"])
        print("Excel creato:", cartella / "recensioni_booking.xlsx")
