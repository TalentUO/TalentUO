"""Limpieza de señales de interés (parte B, tabla 5).

Entradas (no se modifican):
  data/raw/wikipedia_*.json               visitas diarias (Wikimedia REST pageviews)
  data/raw/wikipedia_sonda_dias_ausentes.json
  data/raw/oapn/*.pdf                     visitantes anuales del Parque Nacional
  data/raw/trends/*.json, trends/ancla_cabrales/*.json (+ manual/*.csv si existen)
Salidas:
  data/clean/wikipedia_diario.parquet     una fila por fecha y artículo
  data/clean/oapn_anual.csv               visitantes anuales (solo contexto)
  data/clean/trends_semanal.parquet       series fiables (ancla 'cabrales'): semana, término, geo y ancla
  data/clean/trends_semanal_no_fiable.parquet  series con ancla 'picos de europa' (no usar)
  data/clean/_qc/{wikipedia_diario,oapn_anual,trends_semanal}.json

Uso: python -X utf8 src/limpieza_B/limpia_senales.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import (CLEAN, RAW, asegurar_dirs, comprobar_continuidad, comprobar_rango,  # noqa: E402
                   comprobar_sin_duplicados, escribir_parquet, resumen_qc)

WIKI_INI, WIKI_FIN = "2022-01-01", "2026-10-14"
VENTANA_MEDIANA = 29          # días, centrada
UMBRAL_PICO = 10              # visitas > 10 × mediana móvil y ≥ 500 → pico
UMBRAL_ANOMALIA = 50          # visitas > 50 × mediana móvil y ≥ 500 → posible anomalía
MIN_VISITAS_PICO = 500


# --------------------------------------------------------------------------
# Wikipedia
# --------------------------------------------------------------------------

def comprobar_sonda() -> dict:
    """Lee la sonda y confirma el comportamiento en el que se basa la regla."""
    s = json.loads((RAW / "wikipedia_sonda_dias_ausentes.json").read_text(encoding="utf-8"))
    casos = {c["titulo"]: c for c in s["casos"]}
    ercina = casos["Lago_de_la_Ercina"]
    assert ercina["http"] == 200 and ercina["n_items"] == 296, "la sonda ya no muestra días omitidos"
    assert casos["Mirador_de_Entrelagos"]["http"] == 404
    return {"Lago_de_la_Ercina_2022": "HTTP 200 con 296 de 365 días (la API omite días)",
            "Mirador_de_Entrelagos_2022": "HTTP 404 (sin datos en todo el rango)"}


def wikipedia() -> pd.DataFrame:
    sonda = comprobar_sonda()
    dias = pd.date_range(WIKI_INI, WIKI_FIN, freq="D")
    partes = []
    for f in sorted(RAW.glob("wikipedia_*.json")):
        w = json.loads(f.read_text(encoding="utf-8"))
        if "meta" not in w:  # la sonda
            continue
        assert w["meta"]["http_status"] == 200 and w["meta"]["agent"] == "user"
        articulo = f.stem.removeprefix("wikipedia_")
        it = pd.DataFrame(w["respuesta"]["items"])
        it["fecha"] = pd.to_datetime(it["timestamp"].str[:8], format="%Y%m%d")
        assert not it["fecha"].duplicated().any(), f"{articulo}: fechas repetidas en la API"
        s = it.set_index("fecha")["views"].reindex(dias)
        g = pd.DataFrame({"fecha": dias, "articulo": articulo, "proyecto": w["meta"]["proyecto"],
                          "titulo": w["meta"]["titulo"], "visitas_api": s.values})
        g["visitas_imputado"] = g["visitas_api"].isna()
        # Regla: día omitido por la API = 0 visitas de usuario (ver diccionario).
        g["visitas"] = g["visitas_api"].fillna(0).astype("int64")
        med = g["visitas"].rolling(VENTANA_MEDIANA, center=True, min_periods=15).median().clip(lower=1)
        g["mediana_movil_29d"] = med
        g["pico"] = (g["visitas"] > UMBRAL_PICO * med) & (g["visitas"] >= MIN_VISITAS_PICO)
        g["posible_anomalia"] = (g["visitas"] > UMBRAL_ANOMALIA * med) & (g["visitas"] >= MIN_VISITAS_PICO)
        # Variable para el modelo (decisión del equipo): media de los 7 días
        # ANTERIORES (d-7..d-1), sin el propio día. NaN si la ventana no está
        # completa (primeros 7 días). Cuántos de esos 7 días son imputados:
        g["visitas_media7_ant"] = g["visitas"].shift(1).rolling(7, min_periods=7).mean()
        g["media7_ant_n_imputados"] = (g["visitas_imputado"].astype(int).shift(1)
                                       .rolling(7, min_periods=7).sum().astype("Int64"))
        partes.append(g)
    df = pd.concat(partes, ignore_index=True)
    df["visitas_api"] = df["visitas_api"].astype("Int64")
    df["fuente"] = "Wikimedia REST API pageviews per-article (agent=user, all-access)"
    df = df[["fecha", "articulo", "proyecto", "titulo", "visitas", "visitas_api", "visitas_imputado",
             "visitas_media7_ant", "media7_ant_n_imputados",
             "mediana_movil_29d", "pico", "posible_anomalia", "fuente"]]
    # la media con retraso no puede usar el propio día
    chk = df[df.articulo == "covadonga"].set_index("fecha")
    assert abs(chk.loc["2023-09-17", "visitas_media7_ant"]
               - chk.loc["2023-09-10":"2023-09-16", "visitas"].mean()) < 1e-9
    assert chk["visitas_media7_ant"].iloc[:7].isna().all() and chk["visitas_media7_ant"].iloc[7:].notna().all()

    assert df["articulo"].nunique() == 20, "se esperaban 20 artículos"
    comprobar_sin_duplicados(df, ["fecha", "articulo"], "wikipedia_diario")
    comprobar_continuidad(df, "fecha", "articulo", "wikipedia_diario", WIKI_INI, WIKI_FIN)
    comprobar_rango(df, "visitas", 0, None, "wikipedia_diario")
    # Comprobaciones conocidas por la auditoría
    imp = df.groupby("articulo")["visitas_imputado"].sum()
    assert imp["covadonga_fr"] == 630 and imp["parque_nacional_de_los_picos_de_europa"] == 1
    assert imp.drop(["covadonga_fr", "parque_nacional_de_los_picos_de_europa"]).eq(0).all()
    ceros = df[df["visitas_api"] == 0].groupby("articulo").size()
    assert ceros.get("covadonga_fr") == 405 and ceros.get("parque_nacional_de_los_picos_de_europa") == 7
    v = df.set_index(["articulo", "fecha"])["visitas"]
    assert v[("covadonga", pd.Timestamp("2023-09-17"))] == 193
    assert v[("lagos_de_covadonga", pd.Timestamp("2025-08-15"))] == 169
    assert v[("picos_de_europa", pd.Timestamp("2024-06-01"))] == 191
    anom = df[df["posible_anomalia"]]
    assert ((anom["articulo"] == "picos_de_europa") & (anom["fecha"] == "2023-09-17")).any()

    escribir_parquet(df, "wikipedia_diario.parquet")
    resumen_qc(df, "wikipedia_diario", ["fecha", "articulo"], extra={
        "articulos": int(df["articulo"].nunique()),
        "dias_imputados_por_articulo": {k: int(x) for k, x in imp[imp > 0].items()},
        "ceros_explicitos_api": {k: int(x) for k, x in ceros.items()},
        "sonda": sonda,
        "dias_pico": int(df["pico"].sum()),
        "posibles_anomalias": anom[["articulo", "fecha", "visitas"]].astype(str).to_dict("records"),
        "validaciones": ["continuidad 2022-01-01..2026-10-14 por artículo", "sin duplicados",
                         "visitas >= 0", "imputados y ceros = recuentos de la auditoría",
                         "3 valores contrastados en vivo por la auditoría (Covadonga 2023-09-17=193, "
                         "Lagos 2025-08-15=169, Picos 2024-06-01=191)"],
    })
    return df


# --------------------------------------------------------------------------
# OAPN
# --------------------------------------------------------------------------

# Cifras de referencia de notas/fuentes/senales/notas_senales.md (para contrastar lo extraído).
OAPN_REF = {2015: 1913858, 2016: 2101293, 2017: 2047956, 2018: 1958240, 2019: 1791410,
            2020: 1383338, 2021: 1620739, 2022: 1798533, 2023: 1698780, 2024: 1632805, 2025: 1565899}
OAPN_DOCS = {2022: ("oapn_visitantes_2022.pdf", 4), 2023: ("oapn_visitantes_2023.pdf", 5),
             2024: ("oapn_visitantes_2024.pdf", 5), 2025: ("oapn_visitantes_2025.pdf", 7)}
NUM = r"\d{1,3}(?:\.\d{3})+"


def _texto(pdf: str, pagina: int) -> str:
    with pymupdf.open(RAW / "oapn" / pdf) as doc:
        return doc[pagina - 1].get_text()


def oapn() -> pd.DataFrame:
    filas = []
    for anio, (pdf, pag) in OAPN_DOCS.items():
        t = re.sub(r"\s+", " ", _texto(pdf, pag))
        m = re.search(r"Picos de Europa[^0-9]{0,40}?(" + NUM + ")", t)
        valor = int(m.group(1).replace(".", "")) if m else np.nan
        filas.append((anio, valor, pdf, pag, "frase del texto del informe anual de visitantes"))
    # 2015-2021: tabla "Visitas anuales" de la memoria 2021, p. 129 (Ilustración 27)
    pdf, pag = "oapn_memoria_red_2021.pdf", 129
    t = re.sub(r"\s+", " ", _texto(pdf, pag))
    m = re.search(r"Picos de Europa ((?:" + NUM + r" ){7})", t)
    nums = [int(x.replace(".", "")) for x in m.group(1).split()] if m else [np.nan] * 7
    for anio, v in zip(range(2015, 2022), nums):
        filas.append((anio, v, pdf, pag, "tabla 'Visitas anuales' (Ilustración 27) de la memoria 2021"))

    df = pd.DataFrame(filas, columns=["anio", "visitantes", "documento", "pagina", "localizacion"])
    df["parque"] = "Picos de Europa"
    df["referencia_notas"] = df["anio"].map(OAPN_REF)
    df["verificado"] = df["visitantes"].eq(df["referencia_notas"])
    df["fuente"] = "OAPN / MITECO (Red de Parques Nacionales), data/raw/oapn/"
    df["uso"] = "solo_contexto"
    df = df.sort_values("anio")[["anio", "parque", "visitantes", "documento", "pagina", "localizacion",
                                 "referencia_notas", "verificado", "fuente", "uso"]].reset_index(drop=True)
    comprobar_sin_duplicados(df, ["anio", "parque"], "oapn_anual")
    assert df["anio"].tolist() == list(range(2015, 2026))
    comprobar_rango(df, "visitantes", 500_000, 5_000_000, "oapn_anual")
    df["visitantes"] = df["visitantes"].astype("Int64")
    df.to_csv(CLEAN / "oapn_anual.csv", index=False, encoding="utf-8")
    resumen_qc(df, "oapn_anual", ["anio", "parque"], col_fecha=None, extra={
        "anio_min": int(df["anio"].min()), "anio_max": int(df["anio"].max()),
        "verificados": int(df["verificado"].sum()),
        "no_verificados": df.loc[~df["verificado"], "anio"].tolist(),
        "validaciones": ["cifra extraída del PDF = cifra de notas/fuentes/senales/notas_senales.md"],
    })
    return df


# --------------------------------------------------------------------------
# Google Trends
# --------------------------------------------------------------------------

def _trends_json(f: Path, ancla: str) -> pd.DataFrame:
    t = json.loads(f.read_text(encoding="utf-8"))
    kw = t["meta"]["kw_list"]
    assert kw[0] == ancla, f"{f.name}: ancla {kw[0]} != {ancla}"
    termino = kw[1]
    d = pd.DataFrame(t["respuesta"]["data"])
    return pd.DataFrame({
        "semana_inicio": pd.to_datetime(d["date"]).dt.normalize(),
        "termino": termino, "geo": t["meta"]["geo"], "ancla": ancla,
        "valor": d[termino].astype("int64"), "valor_ancla": d[ancla].astype("int64"),
        "is_partial": d["isPartial"].astype(bool),
        "fichero": str(f.relative_to(RAW).as_posix()), "origen": "pytrends",
        "timeframe": t["meta"]["timeframe"], "descargado_utc": t["meta"]["descargado_utc"],
    })


def _trends_csv_manual(f: Path) -> pd.DataFrame:
    """CSV exportado a mano desde trends.google.es (formato: 2 líneas de cabecera)."""
    raw = pd.read_csv(f, skiprows=2)
    col_fecha = raw.columns[0]
    cols = list(raw.columns[1:])
    ancla_col = next(c for c in cols if c.lower().startswith("cabrales"))
    term_col = next(c for c in cols if c != ancla_col)
    geo = f.stem.rsplit("_", 1)[1]
    a_num = lambda s: pd.to_numeric(s.astype(str).str.replace("<1", "0"), errors="coerce")  # noqa: E731
    return pd.DataFrame({
        "semana_inicio": pd.to_datetime(raw[col_fecha]).dt.normalize(),
        "termino": term_col.split(":")[0].strip(), "geo": geo, "ancla": "cabrales",
        "valor": a_num(raw[term_col]).astype("Int64"), "valor_ancla": a_num(raw[ancla_col]).astype("Int64"),
        "is_partial": False, "fichero": str(f.relative_to(RAW).as_posix()), "origen": "csv_manual",
        "timeframe": np.nan, "descargado_utc": np.nan,
    })


def trends() -> pd.DataFrame:
    partes = [_trends_json(f, "picos de europa") for f in sorted((RAW / "trends").glob("*.json"))]
    partes += [_trends_json(f, "cabrales") for f in sorted((RAW / "trends" / "ancla_cabrales").glob("*.json"))]
    manual = RAW / "trends" / "ancla_cabrales" / "manual"
    if manual.exists():
        partes += [_trends_csv_manual(f) for f in sorted(manual.glob("*.csv"))]
    df = pd.concat(partes, ignore_index=True)
    df["valor"] = df["valor"].astype("Int64")
    df["valor_ancla"] = df["valor_ancla"].astype("Int64")
    df["termino_sobre_ancla"] = (df["valor"].astype("Float64") /
                                 df["valor_ancla"].astype("Float64").replace(0, pd.NA))
    df["fiable"] = df["ancla"].eq("cabrales")
    df["motivo"] = np.where(
        df["fiable"],
        "ancla 'cabrales' (estable, sin ceros); semanal; índice relativo 0-100 por consulta; "
        "muestra de Google variable entre descargas; 'cabrales' es también un queso (solo escala)",
        "ancla 'picos de europa' inservible: único 100 la semana del 2023-09-17 y mediana 3; "
        "aplasta el otro término a 0-4 (auditoría fase B)")
    df["fuente"] = "Google Trends vía pytrends (no oficial)"
    df.loc[df["origen"] == "csv_manual", "fuente"] = "Google Trends, exportación manual (trends.google.es)"

    comprobar_sin_duplicados(df, ["semana_inicio", "termino", "geo", "ancla"], "trends_semanal")
    comprobar_rango(df, "valor", 0, 100, "trends_semanal")
    comprobar_rango(df, "valor_ancla", 0, 100, "trends_semanal")
    assert (df["semana_inicio"].dt.dayofweek == 6).all(), "las semanas de Trends deberían empezar en domingo"
    for clave, g in df.groupby(["termino", "geo", "ancla"]):
        sem = g["semana_inicio"].sort_values()
        assert sem.diff().dropna().eq(pd.Timedelta(days=7)).all(), f"{clave}: semanas no contiguas"
    # Series fiables y no fiables en tablas separadas (las no fiables, solo para consulta).
    for nombre, parte in (("trends_semanal", df[df["fiable"]]), ("trends_semanal_no_fiable", df[~df["fiable"]])):
        parte = parte.reset_index(drop=True)
        escribir_parquet(parte, f"{nombre}.parquet")
        series = parte.groupby(["termino", "geo", "ancla"]).agg(
            semanas=("valor", "size"), mediana=("valor", "median"), maximo=("valor", "max"),
            semanas_cero=("valor", lambda s: int((s == 0).sum()))).reset_index()
        resumen_qc(parte, nombre, ["semana_inicio", "termino", "geo", "ancla"], col_fecha="semana_inicio",
                   extra={"series": series.astype(str).to_dict("records"), "n_series": int(len(series)),
                          "csv_manuales": int(parte.loc[parte["origen"] == "csv_manual", "fichero"].nunique()),
                          "validaciones": ["sin duplicados", "valores 0-100", "semanas contiguas de 7 días",
                                           "ancla = primer término de kw_list"]})
    return df


def main() -> None:
    asegurar_dirs()
    w = wikipedia()
    print(f"wikipedia_diario: {len(w)} filas, {w['articulo'].nunique()} artículos, "
          f"{int(w['visitas_imputado'].sum())} días imputados, {int(w['posible_anomalia'].sum())} posibles anomalías")
    o = oapn()
    print(f"oapn_anual: {len(o)} años, verificados {int(o['verificado'].sum())}/{len(o)}")
    t = trends()
    print(f"trends_semanal: {len(t)} filas, series fiables {t.groupby(['termino','geo','ancla'])['fiable'].first().sum()}"
          f" / {t.groupby(['termino','geo','ancla']).ngroups}")


if __name__ == "__main__":
    main()
