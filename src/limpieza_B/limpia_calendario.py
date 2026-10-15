"""Limpieza del calendario (parte B, tabla 3).

Ejecutar desde la raíz del repositorio:
    python -X utf8 src/limpieza_B/limpia_calendario.py

Lee los PDF de `data/raw/calendario/` (no los modifica) y escribe:
  - data/clean/calendario_diario.parquet       una fila por día, 2022-01-01..2027-12-31
  - data/clean/festivos_locales.parquet        fiestas locales de todos los concejos de Asturias 2022-2027
  - data/clean/festivos_autonomicos.csv        festivos del BOE (AST/MAD/CYL) antes de expandir
  - data/clean/vacaciones_escolares_periodos.csv  periodos escolares fuente antes de expandir
  - data/clean/lagos_folleto_transcripcion.csv  transcripción del folleto de imagen (verificado=False)
  - data/clean/_qc/calendario_diario.json y _qc/festivos_locales.json

Festivos del BOE y fiestas locales del BOPA se extraen de los PDF por la
posición de las palabras (PyMuPDF). Calendarios escolares y días regulados
de los Lagos se transcribieron a mano en `calendario_datos.py`.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import (RAW, CLEAN, comprobar_continuidad, comprobar_sin_duplicados,  # noqa: E402
                   escribir_parquet, resumen_qc, asegurar_dirs)
import calendario_datos as CD  # noqa: E402

CAL = RAW / "calendario"
INI, FIN = date(2022, 1, 1), date(2027, 12, 31)
ANIOS = range(2022, 2028)
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
CCAA = {"ast": "Asturias", "mad": "Madrid", "cyl": "León"}  # palabra de cabecera en el BOE

BOE_FIESTAS = {2022: "BOE-A-2021-17113", 2023: "BOE-A-2022-16755", 2024: "BOE-A-2023-22014",
               2025: "BOE-A-2024-21316", 2026: "BOE-A-2025-21667", 2027: "BOE-A-2026-21254"}
BOPA_LOCALES = {2022: "BOPA 2021-03949", 2023: "BOPA 2022-03495", 2024: "BOPA 2023-03229",
                2025: "BOPA 2024-04382", 2026: "BOPA 2025-04744", 2027: "BOPA 2026-04656"}
# Columnas de la tabla del BOE (17 CCAA + Ceuta + Melilla), palabra de cabecera única
COLS_BOE = ["Andalucía", "Aragón", "Asturias", "Balears", "Canarias", "Cantabria", "Mancha", "León",
            "Cataluña", "Extremadura", "Galicia", "Madrid", "Murcia", "Navarra", "Vasco", "Rioja",
            "Valenciana", "Ceuta", "Melilla"]


def rango(a: date, b: date):
    return [a + timedelta(days=i) for i in range((b - a).days + 1)]


def clave(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


# ---------------------------------------------------------------------------
# 1. Festivos laborales (BOE)
# ---------------------------------------------------------------------------

def parsea_boe(anio: int) -> pd.DataFrame:
    """Filas (fecha, nombre, marca por comunidad) de la tabla del anexo del BOE.

    Cada fila de la tabla empieza con el día en la columna izquierda; las
    marcas (*, **, ***) se asignan a la fila por altura y a la comunidad por
    la posición horizontal de su cabecera.
    """
    doc = pymupdf.open(CAL / f"boe_fiestas_{anio}.pdf")
    filas, mes = [], None
    for pag in doc:
        ws = pag.get_text("words")
        heads = {}
        for w in ws:
            if w[4] in COLS_BOE and w[1] < 240 and w[0] > 100:
                heads.setdefault(w[4], (w[0] + w[2]) / 2)
        if "Asturias" not in heads:
            continue
        assert len(heads) == 19, f"BOE {anio}: {len(heads)} columnas de comunidad (esperadas 19)"
        xcol = min(heads.values()) - 15
        xd = min(w[0] for w in ws if w[4].isdigit() and w[1] > 150 and w[0] < 60)
        items = []
        for w in ws:
            if w[4].lower() in MESES and 60 < w[0] < xcol:
                items.append(("M", w[1], w[4].lower()))
            elif w[4].isdigit() and abs(w[0] - xd) < 3 and w[1] > 150:
                items.append(("F", w[1], int(w[4]), w[2]))
        items.sort(key=lambda t: t[1])
        marcas = [w for w in ws if set(w[4]) == {"*"}]
        for i, it in enumerate(items):
            if it[0] == "M":
                mes = MESES.index(it[2]) + 1
                continue
            ysig = items[i + 1][1] if i + 1 < len(items) else 1e9
            st = [s for s in marcas if it[1] - 3 <= s[1] < ysig - 3]
            nombre = " ".join(x[4] for x in ws if it[1] - 2 <= x[1] < ysig - 2 and it[3] < x[0] < xcol
                              and set(x[4]) != {"*"} and x[4].lower() not in MESES).rstrip(".")
            m = {}
            for c, x in heads.items():
                v = [s[4] for s in st if abs((s[0] + s[2]) / 2 - x) < 12]
                assert len(v) <= 1, f"BOE {anio} {mes}-{it[2]}: dos marcas en {c}"
                if v:
                    m[c] = v[0]
            assert len(m) == len(st), f"BOE {anio} {mes}-{it[2]}: marcas sin comunidad asignada"
            filas.append(dict(fecha=pd.Timestamp(anio, mes, it[2]), nombre=nombre, n_ccaa=len(m),
                              **{k: m.get(v, "") for k, v in CCAA.items()}))
    df = pd.DataFrame(filas)
    df["fuente"] = BOE_FIESTAS[anio]
    return df


def festivos_boe() -> pd.DataFrame:
    df = pd.concat([parsea_boe(a) for a in ANIOS], ignore_index=True)
    # Comprobaciones: 12-14 festivos por comunidad y año; los "lunes siguiente" caen en lunes
    for a in ANIOS:
        for c in CCAA:
            n = (df[df.fecha.dt.year == a][c] != "").sum()
            assert 12 <= n <= 14, f"BOE {a} {c}: {n} festivos"
    lun = df[df.nombre.str.lower().str.startswith("lunes")]
    assert (lun.fecha.dt.dayofweek == 0).all(), "un 'Lunes ...' del BOE no cae en lunes"
    return df


# ---------------------------------------------------------------------------
# 2. Fiestas locales (BOPA)
# ---------------------------------------------------------------------------

RE_FECHA = re.compile(r"(\d{1,2})\s*(?:de\s+)?(" + "|".join(MESES) + r")", re.I)


def _lineas(pag):
    out = []
    for b in pag.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = re.sub(r"\s+", " ", " ".join(s["text"] for s in l["spans"])).strip()
            if t:
                out.append((l["bbox"][0], l["bbox"][1], t))
    return out


def _bopa_tablas(doc):
    """Años con tabla dibujada (2023, 2025-2027): find_tables."""
    filas, conc = [], None
    for pno, pag in enumerate(doc):
        for t in pag.find_tables().tables:
            for r in t.extract():
                c, f, n = (list(r) + [None] * 3)[:3]
                if c and c.strip():
                    c = re.sub(r"\s+", " ", c).strip()
                    # concejo partido en dos celdas (p. ej. "MUROS DE" / "NALÓN")
                    conc = f"{conc} {c}" if (conc and re.search(r" (DE|DEL)$", conc.upper())) else c
                for dd, mm in RE_FECHA.findall(f or ""):
                    filas.append(dict(pagina=pno + 1, concejo=conc, dia=int(dd), mes=MESES.index(mm.lower()) + 1,
                                      nombre=re.sub(r"\s+", " ", n or "").strip()))
    # las filas anteriores a la unión llevan el nombre incompleto: se completa con el siguiente
    for i, r in enumerate(filas):
        if re.search(r" (DE|DEL)$", r["concejo"].upper()):
            r["concejo"] = next(s["concejo"] for s in filas[i + 1:] if s["concejo"] != r["concejo"])
    return filas


def _bopa_lineas(doc):
    """Años sin tabla dibujada (2022, 2024): columnas por posición del texto."""
    filas = []
    for pno, pag in enumerate(doc):
        ls = _lineas(pag)
        fechas = sorted([l for l in ls if re.fullmatch(r"\s*\d{1,2}\s*de\s+[a-záéíóú]+\s*", l[2], re.I)
                         and RE_FECHA.search(l[2])], key=lambda l: l[1])
        if not fechas:
            continue
        xf = min(l[0] for l in fechas)
        y0, y1 = fechas[0][1] - 3, fechas[-1][1] + 25
        conc = sorted([l for l in ls if 60 < l[0] < xf - 20 and y0 <= l[1] <= y1], key=lambda l: l[1])
        # une nombres de concejo partidos en dos líneas ("SAN MARTÍN DEL REY" + "AURELIO")
        unidos = []
        for l in conc:
            sola = not any(abs(l[1] - f[1]) < 3 for f in fechas)
            if unidos and sola and l[1] - unidos[-1][1] < 12:
                unidos[-1] = (unidos[-1][0], unidos[-1][1], unidos[-1][2] + " " + l[2])
            else:
                unidos.append(l)
        noms = sorted([l for l in ls if l[0] > xf + 40 and y0 <= l[1] <= y1], key=lambda l: l[1])
        for f in fechas:
            c = [l for l in unidos if l[1] <= f[1] + 2]
            n = [l[2] for l in noms if abs(l[1] - f[1]) < 3]
            m = RE_FECHA.search(f[2])
            filas.append(dict(pagina=pno + 1, concejo=c[-1][2] if c else None, dia=int(m.group(1)),
                              mes=MESES.index(m.group(2).lower()) + 1, nombre=n[0] if n else "", _y=f[1]))
        # continuación de nombres largos en la línea siguiente
        for l in noms:
            if not any(abs(l[1] - f[1]) < 3 for f in fechas):
                prev = [r for r in filas if r["pagina"] == pno + 1 and r["_y"] < l[1]]
                if prev and l[1] - max(prev, key=lambda r: r["_y"])["_y"] < 25:
                    max(prev, key=lambda r: r["_y"])["nombre"] += " " + l[2]
    for r in filas:
        r.pop("_y", None)
    return filas


def _txt(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z ,()]", " ", s).split())


def ambito_festivo(nombre, concejo: str) -> str:
    """Ámbito de una fiesta local según el texto del BOPA (decisión del equipo:
    las parciales cuentan como fiesta del concejo, pero se marcan).

    - "parcial": "excepto/salvo", "sólo/solamente/exclusivamente", "parroquia(s)"
      o "en <lugar>" (p. ej. "San Jorge en Nueva y Valle de San Jorge").
    - "concejo": sin indicación de lugar, o "en todo el concejo/municipio",
      "y (resto del) Concejo", "para todo el Término" (sin "excepto").
    - "dudoso_villa_o_concejo": "en <nombre del propio concejo>" (p. ej.
      "Festividad del Bollo en Salas"): la villa o todo el concejo.
    - "sin_nombre": el BOPA no da nombre.
    """
    if nombre is None or pd.isna(nombre):
        return "sin_nombre"
    t = _txt(str(nombre))
    if re.search(r"\b(excepto|salvo)\b", t):
        return "parcial"
    if re.search(r"todo el (concejo|municipio|termino)|resto del concejo|\by concejo\b", t):
        return "concejo"
    if re.search(r"\b(solo|solamente|exclusivamente|unicamente)\b", t) or re.search(r"\bparroquias?\b", t):
        return "parcial"
    m = re.search(r"(?:^|[\s,(])en ([a-z].*)$", t)
    if m:
        return "dudoso_villa_o_concejo" if m.group(1).startswith(_txt(concejo)) else "parcial"
    return "concejo"


def festivos_locales() -> pd.DataFrame:
    canon = None
    dfs = []
    for a in ANIOS:
        doc = pymupdf.open(CAL / f"bopa_fiestas_locales_{a}.pdf")
        tiene_tabla = any(p.find_tables().tables for p in doc)
        filas = _bopa_tablas(doc) if tiene_tabla else _bopa_lineas(doc)
        df = pd.DataFrame(filas)
        df["anio"] = a
        df["metodo_extraccion"] = "tabla_pdf" if tiene_tabla else "posicion_texto"
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    assert df.concejo.notna().all(), "fecha sin concejo en el BOPA"
    # Nombre canónico: el de 2022 (mayúsculas/minúsculas y tildes); los años en
    # mayúsculas se emparejan sin tildes ni espacios.
    canon = {clave(c): c for c in df[df.anio == 2022].concejo.unique()}
    assert len(canon) == 78, f"2022: {len(canon)} concejos (Asturias tiene 78)"
    canon[clave("Villayón")] = canon.get(clave("Villayón"), "Villayón")
    df["concejo"] = df.concejo.map(lambda c: canon.get(clave(c)))
    assert df.concejo.notna().all(), "concejo no reconocido en algún año"
    for a in ANIOS:
        n = df[df.anio == a].concejo.nunique()
        assert n == 78, f"BOPA {a}: {n} concejos"
    df["fecha"] = pd.to_datetime(dict(year=df.anio, month=df.mes, day=df.dia))
    df["nombre"] = df.nombre.str.strip().replace("", pd.NA)
    df["fuente"] = df.anio.map(BOPA_LOCALES)
    # Comprobación: si el nombre empieza por un día de la semana, ¿coincide con la fecha?
    # No se corrige nada (se publica tal cual el BOPA); la columna lo señala.
    dias_k = [clave(d) for d in DIAS]

    def coherente(r):
        if pd.isna(r.nombre):
            return pd.NA
        primera = clave(re.split(r"[\s,\-–]+", str(r.nombre).strip())[0])
        return pd.NA if primera not in dias_k else dias_k.index(primera) == r.fecha.dayofweek

    df["dia_semana_coherente"] = df.apply(coherente, axis=1).astype("boolean")
    df["ambito"] = [ambito_festivo(n, c) for n, c in zip(df.nombre, df.concejo)]
    df["festivo_parcial"] = df.ambito.map({"parcial": True, "concejo": False}).astype("boolean")
    df = (df[["fecha", "anio", "concejo", "nombre", "ambito", "festivo_parcial", "fuente", "pagina",
              "metodo_extraccion", "dia_semana_coherente"]]
          .sort_values(["fecha", "concejo"]).reset_index(drop=True))
    # una misma fecha puede repetirse en un concejo con ámbitos distintos (parroquias)
    df = df.drop_duplicates(["fecha", "concejo", "nombre"])
    return df


# ---------------------------------------------------------------------------
# 3. Semana Santa
# ---------------------------------------------------------------------------

def pascua(y: int) -> date:
    """Domingo de Resurrección (algoritmo anónimo gregoriano, Meeus/Jones/Butcher)."""
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = (h + l - 7 * m + 114) % 31 + 1
    return date(y, mes, dia)


def comprueba_semana_santa(boe: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for a in ANIOS:
        p = pascua(a)
        b = boe[boe.fecha.dt.year == a]
        js = b[b.nombre.str.contains("Jueves Santo")].fecha
        vs = b[b.nombre.str.contains("Viernes Santo")].fecha
        lp = b[b.nombre.str.fullmatch("Lunes de Pascua")].fecha
        r = dict(anio=a, domingo_pascua=p, jueves_santo_calc=p - timedelta(3), jueves_santo_boe=js.iloc[0].date(),
                 viernes_santo_calc=p - timedelta(2), viernes_santo_boe=vs.iloc[0].date(),
                 lunes_pascua_calc=p + timedelta(1), lunes_pascua_boe=lp.iloc[0].date() if len(lp) else None)
        r["coincide"] = (r["jueves_santo_calc"] == r["jueves_santo_boe"] and r["viernes_santo_calc"] == r["viernes_santo_boe"]
                         and (r["lunes_pascua_boe"] is None or r["lunes_pascua_calc"] == r["lunes_pascua_boe"]))
        assert r["coincide"], f"Semana Santa {a}: el cálculo no coincide con el BOE"
        filas.append(r)
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 4. Calendario escolar
# ---------------------------------------------------------------------------

def escolar(cal: pd.DataFrame, ccaa: str) -> pd.DataFrame:
    """periodo_escolar, vacaciones, no_lectivo, verificado y fuente por día."""
    cursos = CD.ESCOLAR[ccaa]
    festivo = dict(zip(cal.fecha.dt.date, cal[f"festivo_{ccaa}"]))
    per, ver, fue = {}, {}, {}
    for i, c in enumerate(cursos):
        # comprobaciones de la transcripción
        assert c["inicio"] < c["navidad"][0] <= c["navidad"][1] < c["semana_santa"][0] <= c["semana_santa"][1] < c["fin"]
        vs = pascua(c["semana_santa"][0].year) - timedelta(2)
        assert c["semana_santa"][0] <= vs <= c["semana_santa"][1], f"{ccaa} {c['curso']}: vacaciones de primavera sin Viernes Santo"
        for d in c["no_lectivos"]:
            assert d.weekday() < 5, f"{ccaa} {c['curso']}: no lectivo {d} en fin de semana"
            assert c["inicio"] <= d <= c["fin"], f"{ccaa} {c['curso']}: no lectivo {d} fuera del curso"
        nl = set(c["no_lectivos"])
        for d in rango(c["inicio"], c["fin"]):
            if c["navidad"][0] <= d <= c["navidad"][1]:
                p = "vacaciones_navidad"
            elif c["semana_santa"][0] <= d <= c["semana_santa"][1]:
                p = "vacaciones_semana_santa"
            elif d.weekday() >= 5:
                p = "fin_de_semana"
            elif festivo.get(d, False):
                p = "festivo"
            elif d in nl:
                p = "no_lectivo_puntual"
            else:
                p = "lectivo"
            per[d], ver[d], fue[d] = p, c["verificado"], c["fuente"]
        # verano: del día siguiente al fin de clases al día anterior al inicio del curso siguiente
        if i + 1 < len(cursos):
            fin_v, v, f = cursos[i + 1]["inicio"] - timedelta(1), c["verificado"] and cursos[i + 1]["verificado"], \
                c["fuente"] + " / " + cursos[i + 1]["fuente"]
        else:
            fin_v, v, f = CD.FIN_CONOCIDO_VERANO_2027, False, c["fuente"] + " (fin del verano 2027 no publicado; se asume >= 1-sep-2027)"
        for d in rango(c["fin"] + timedelta(1), fin_v):
            per[d], ver[d], fue[d] = "verano", v, f
    s = cal.fecha.dt.date
    out = pd.DataFrame({"fecha": cal.fecha})
    out[f"periodo_escolar_{ccaa}"] = s.map(per).astype("string")
    p = out[f"periodo_escolar_{ccaa}"]
    out[f"vacaciones_escolares_{ccaa}"] = p.isin(["vacaciones_navidad", "vacaciones_semana_santa", "verano"]).astype("boolean").mask(p.isna())
    out[f"no_lectivo_{ccaa}"] = (p != "lectivo").astype("boolean").mask(p.isna())
    out[f"escolar_verificado_{ccaa}"] = s.map(ver).astype("boolean")
    out[f"escolar_fuente_{ccaa}"] = s.map(fue).astype("string")
    return out


def periodos_escolares() -> pd.DataFrame:
    filas = []
    for ccaa, cursos in CD.ESCOLAR.items():
        for c in cursos:
            base = dict(ccaa=ccaa, curso=c["curso"], fuente=c["fuente"], verificado=c["verificado"])
            filas.append({**base, "periodo": "lectivo_inicio_fin", "inicio": c["inicio"], "fin": c["fin"]})
            filas.append({**base, "periodo": "vacaciones_navidad", "inicio": c["navidad"][0], "fin": c["navidad"][1]})
            filas.append({**base, "periodo": "vacaciones_semana_santa", "inicio": c["semana_santa"][0], "fin": c["semana_santa"][1]})
            for d in c["no_lectivos"]:
                filas.append({**base, "periodo": "no_lectivo_puntual", "inicio": d, "fin": d})
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 5. Lagos de Covadonga
# ---------------------------------------------------------------------------

def lagos(cal: pd.DataFrame) -> pd.DataFrame:
    reg, fue, hor = {}, {}, {}
    for a, L in CD.LAGOS.items():
        dias = set()
        for i0, i1 in L["rangos"]:
            assert i0.year == a and i1.year == a and i0 <= i1
            dias.update(rango(i0, i1))
        for m in L["findes"]:
            dias.update(d for d in rango(date(a, m, 1), (date(a, m + 1, 1) - timedelta(1))) if d.weekday() >= 5)
        dias -= set(L["excepto"])
        for d in rango(date(a, 1, 1), date(a, 12, 31)):
            reg[d] = d in dias
            fue[d] = f"oficial: {L['boe']} (DGT, CO-04)"
            if d in dias:
                h = [t for i0, i1, t in L["horario"] if i0 <= d <= i1]
                assert len(h) == 1, f"Lagos {d}: sin horario"
                hor[d] = h[0] + (" salvo la tarde (excepción del BOE)" if d in L["tarde_libre"] else "")
    s = cal.fecha.dt.date
    out = pd.DataFrame({"fecha": cal.fecha})
    out["lagos_regulado"] = s.map(reg).astype("boolean")
    out["lagos_regulado_fuente"] = s.map(fue).astype("string")
    out["lagos_horario"] = s.map(hor).astype("string")
    inc, ifue = {}, {}
    for e in CD.LAGOS_INCIDENCIAS:
        for d in rango(e["inicio"], e["fin"]):
            inc[d], ifue[d] = e["tipo"], e["fuente"] + " | " + e["nota"]
    out["lagos_incidencia"] = s.map(inc).astype("string")
    out["lagos_incidencia_fuente"] = s.map(ifue).astype("string")
    out["lagos_incidencia_verificado"] = out.lagos_incidencia.notna().map({True: False}).astype("boolean")
    return out


# ---------------------------------------------------------------------------
# 6. Puentes y fines de semana largos
# ---------------------------------------------------------------------------

def puentes(cal: pd.DataFrame, ccaa: str) -> pd.DataFrame:
    """puente: día laborable (lun-vie, no festivo) con un día no laborable a cada lado.
    finde_largo: tramo de >= 3 días no laborables seguidos (fines de semana + festivos).
    finde_largo_con_puente: tramo de >= 3 días seguidos no laborables o de puente."""
    nolab = (cal.es_fin_de_semana | cal[f"festivo_{ccaa}"]).to_numpy()
    n = len(nolab)
    # fuera del rango solo se conocen los fines de semana
    ant = (cal.fecha.iloc[0] - pd.Timedelta(days=1)).dayofweek >= 5
    sig = (cal.fecha.iloc[-1] + pd.Timedelta(days=1)).dayofweek >= 5
    prev = [ant] + list(nolab[:-1])
    nxt = list(nolab[1:]) + [sig]
    puente = [(not nolab[i]) and prev[i] and nxt[i] for i in range(n)]

    def tramos(mask):
        out = [False] * n
        i = 0
        while i < n:
            if mask[i]:
                j = i
                while j + 1 < n and mask[j + 1]:
                    j += 1
                if j - i + 1 >= 3:
                    for k in range(i, j + 1):
                        out[k] = True
                i = j + 1
            else:
                i += 1
        return out

    out = pd.DataFrame({"fecha": cal.fecha})
    out[f"puente_{ccaa}"] = puente
    out[f"finde_largo_{ccaa}"] = tramos(list(nolab))
    out[f"finde_largo_con_puente_{ccaa}"] = tramos([a or b for a, b in zip(nolab, puente)])
    return out


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------

def main():
    asegurar_dirs()
    boe = festivos_boe()
    ss = comprueba_semana_santa(boe)

    cal = pd.DataFrame({"fecha": pd.date_range(INI, FIN, freq="D")})
    cal["anio"] = cal.fecha.dt.year
    cal["mes"] = cal.fecha.dt.month
    cal["dia_semana"] = cal.fecha.dt.dayofweek
    cal["nombre_dia"] = cal.dia_semana.map(dict(enumerate(DIAS)))
    cal["es_fin_de_semana"] = cal.dia_semana >= 5

    nac = boe[boe.n_ccaa == 19].groupby("fecha").nombre.first()
    cal["festivo_nacional"] = cal.fecha.isin(nac.index)
    cal["nombre_festivo_nacional"] = cal.fecha.map(nac).astype("string")
    for c in CCAA:
        f = boe[boe[c] != ""].groupby("fecha").nombre.agg(" / ".join)
        cal[f"festivo_{c}"] = cal.fecha.isin(f.index)
        cal[f"nombre_festivo_{c}"] = cal.fecha.map(f).astype("string")
        tipo = boe[boe[c] != ""].groupby("fecha")[c].first().map({"*": "nacional_no_sustituible", "**": "nacional_no_sustituida",
                                                                  "***": "autonomica"})
        cal[f"tipo_festivo_{c}"] = cal.fecha.map(tipo).astype("string")
    cal["festivos_fuente"] = cal.anio.map(BOE_FIESTAS)

    for c in CCAA:
        cal = cal.merge(puentes(cal, c), on="fecha")

    pas = {a: pascua(a) for a in ANIOS}
    d = cal.fecha.dt.date
    cal["semana_santa"] = d.map(lambda x: pas[x.year] - timedelta(3) <= x <= pas[x.year])
    cal["semana_santa_ampliada"] = d.map(lambda x: pas[x.year] - timedelta(7) <= x <= pas[x.year] + timedelta(1))
    cal["domingo_pascua"] = d.map(lambda x: x == pas[x.year])

    for c in CCAA:
        cal = cal.merge(escolar(cal, c), on="fecha")
    cal = cal.merge(lagos(cal), on="fecha")

    loc = festivos_locales()
    # número de concejos asturianos con fiesta local ese día (contexto regional)
    cal["n_concejos_fiesta_local"] = cal.fecha.map(loc.groupby("fecha").concejo.nunique()).fillna(0).astype(int)

    # ---- comprobaciones ----
    comprobar_sin_duplicados(cal, ["fecha"], "calendario_diario")
    comprobar_continuidad(cal, "fecha", None, "calendario_diario", INI, FIN)
    assert len(cal) == (FIN - INI).days + 1
    assert cal.dia_semana.between(0, 6).all()
    for c in CCAA:
        assert not (cal[f"puente_{c}"] & (cal.es_fin_de_semana | cal[f"festivo_{c}"])).any()
        assert cal[f"periodo_escolar_{c}"].loc[cal.fecha <= "2027-08-31"].notna().all(), f"{c}: huecos escolares"
        assert cal[f"periodo_escolar_{c}"].loc[cal.fecha >= "2027-09-01"].isna().all()
    assert cal.lagos_regulado[cal.anio <= 2026].notna().all() and cal.lagos_regulado[cal.anio == 2027].isna().all()
    n_lagos = cal[cal.anio <= 2026].groupby("anio").lagos_regulado.sum()
    assert n_lagos.between(150, 200).all(), n_lagos
    assert cal.semana_santa.sum() == 4 * len(ANIOS)
    comprobar_sin_duplicados(loc, ["fecha", "concejo", "nombre"], "festivos_locales")

    # ---- escritura ----
    escribir_parquet(cal, "calendario_diario.parquet")
    escribir_parquet(loc, "festivos_locales.parquet")
    boe_out = boe[(boe.ast != "") | (boe.mad != "") | (boe.cyl != "")].copy()
    boe_out.to_csv(CLEAN / "festivos_autonomicos.csv", index=False)
    periodos_escolares().to_csv(CLEAN / "vacaciones_escolares_periodos.csv", index=False)
    pd.DataFrame([dict(apartado=a, texto=t, fuente="turismocangasdeonis_folleto_acceso_lagos.pdf p. 2 (imagen; transcripción manual)",
                       anio_inferido=2024, verificado=False) for a, t in CD.FOLLETO_LAGOS]) \
        .to_csv(CLEAN / "lagos_folleto_transcripcion.csv", index=False)
    ss.to_csv(CLEAN / "_qc" / "semana_santa_comprobacion.csv", index=False)

    resumen_qc(cal, "calendario_diario", ["fecha"], extra=dict(
        festivos_por_anio={c: cal.groupby("anio")[f"festivo_{c}"].sum().to_dict() for c in CCAA},
        puentes_por_anio={c: cal.groupby("anio")[f"puente_{c}"].sum().to_dict() for c in CCAA},
        lagos_regulado_por_anio=n_lagos.to_dict(),
        semana_santa_ok=bool(ss.coincide.all()),
    ))
    resumen_qc(loc, "festivos_locales", ["fecha", "concejo", "nombre"], extra=dict(
        filas_por_anio=loc.groupby("anio").size().to_dict(),
        concejos_por_anio=loc.groupby("anio").concejo.nunique().to_dict(),
    ))
    print(f"calendario_diario: {len(cal)} filas, {cal.shape[1]} columnas")
    print(f"festivos_locales: {len(loc)} filas, {loc.concejo.nunique()} concejos")
    print(ss[["anio", "domingo_pascua", "jueves_santo_boe", "viernes_santo_boe", "coincide"]].to_string(index=False))


if __name__ == "__main__":
    main()
