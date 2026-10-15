"""Limpieza de AEMET OpenData (climatologías diarias) -> data/clean/aemet_diario.parquet.

Entrada (no se modifica): data/raw/aemet_diario_<indicativo>.json y
data/raw/aemet_inventario.json.

Salidas:
- data/clean/aemet_diario.parquet  (una fila por fecha y estación; calendario
  completo 2022-01-01..última fecha de la estación; los días que la API no
  devuelve son filas con NaN y `fila_ausente_en_fuente=True`).
- data/clean/estaciones_aemet.csv
- data/clean/_qc/aemet_diario.json
- notas/huecos_aemet.md

Tratamiento (ver notas/diccionario_B.md):
- Coma decimal -> punto; texto vacío/ausente -> NaN (nunca 0).
- `prec` = "Ip" (inapreciable, < 0,1 mm) -> 0.0 y `prec_inapreciable=True` (regla 2).
- Horas "HH:MM" se conservan como texto; "Varias" -> NaN y `<hora>_varias=True`.
- `dir` (decenas de grado) -> grados (x10). Códigos 99 y 88 no son direcciones:
  -> NaN y el código se guarda en `dir_racha_codigo`.
- `pintMax` negativo (-0,3, solo valor negativo que aparece) no es un valor
  físico: -> NaN y `prec_max_intervalo_negativo_en_fuente=True`.

Ejecución: python -X utf8 src/limpieza_B/limpia_aemet.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import (NOTAS, RAW, CLEAN, comprobar_continuidad, comprobar_rango,  # noqa: E402
                   comprobar_sin_duplicados, escribir_parquet, resumen_qc, asegurar_dirs)

INICIO = pd.Timestamp("2022-01-01")
FUENTE = "AEMET OpenData climatologías diarias"

# columna bruta -> (columna limpia, rango válido)
NUMERICAS = {
    "tmed": ("tmed_c", (-30, 50)),
    "tmin": ("tmin_c", (-30, 50)),
    "tmax": ("tmax_c", (-30, 50)),
    "prec": ("prec_mm", (0, 500)),
    "velmedia": ("viento_medio_ms", (0, 70)),
    "racha": ("racha_max_ms", (0, 90)),
    "sol": ("sol_h", (0, 16)),
    "presMax": ("pres_max_hpa", (700, 1100)),
    "presMin": ("pres_min_hpa", (700, 1100)),
    "hrMedia": ("hr_media_pct", (0, 100)),
    "hrMax": ("hr_max_pct", (0, 100)),
    "hrMin": ("hr_min_pct", (0, 100)),
    "pintMax": ("prec_max_intervalo_mm", (0, 500)),
}
HORAS = {
    "horatmin": "hora_tmin",
    "horatmax": "hora_tmax",
    "horaracha": "hora_racha",
    "horaPresMax": "hora_pres_max",
    "horaPresMin": "hora_pres_min",
    "horaHrMax": "hora_hr_max",
    "horaHrMin": "hora_hr_min",
    "horaPIntMax": "hora_prec_max_intervalo",
}
# variables cuyo hueco se informa (las de interés para el modelo)
VARS_HUECOS = ["tmed_c", "tmin_c", "tmax_c", "prec_mm", "viento_medio_ms", "racha_max_ms",
               "sol_h", "hr_media_pct", "pres_max_hpa"]

# zona/uso según notas/estaciones_aemet.md
USO = {
    "1186P": ("picos_de_europa", "principal Cangas de Onís / Covadonga / Lagos"),
    "1179B": ("picos_de_europa", "alternativa (Lagos, lado este)"),
    "1178R": ("picos_de_europa", "contraste alta montaña; hueco 2022-01-16..2023-07-06"),
    "1199X": ("picos_de_europa", "alternativa interior"),
    "1203D": ("costa_oriental", "Colunga; termina 2026-06-04, no sirve para el presente"),
    "1212E": ("asturias_centro", "Asturias Aeropuerto; serie completa con sol"),
    "1249X": ("oviedo", "Oviedo"),
    "1183X": ("llanes", "Llanes; con sol"),
    "1207U": ("gijon", "Gijón Campus"),
    "1210X": ("gijon", "Cabo Peñas; huecos largos"),
    "3195": ("madrid", "Madrid Retiro (origen)"),
    "5783": ("sevilla", "Sevilla Aeropuerto (origen)"),
}


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype("string").str.strip().str.replace(",", ".", regex=False),
                         errors="coerce").astype("float64")


def dms_a_decimal(txt: str) -> float:
    """'431620N' / '050716W' -> grados decimales."""
    m = re.fullmatch(r"(\d{2,3})(\d{2})(\d{2})([NSEW])", txt)
    assert m, f"coordenada no reconocida: {txt}"
    g, mi, s, h = int(m[1]), int(m[2]), int(m[3]), m[4]
    v = g + mi / 60 + s / 3600
    return round(-v if h in "SW" else v, 5)


def cargar_bruto() -> pd.DataFrame:
    filas = []
    for f in sorted(RAW.glob("aemet_diario_*.json")):
        filas += json.loads(f.read_text(encoding="utf-8"))
    return pd.DataFrame(filas)


def limpiar(raw: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({"fecha": pd.to_datetime(raw["fecha"], format="%Y-%m-%d"),
                       "estacion": raw["indicativo"].astype("string")})
    # precipitación: Ip -> 0.0 + indicador
    prec_txt = raw["prec"].astype("string").str.strip()
    df["prec_inapreciable"] = (prec_txt == "Ip").fillna(False).astype(bool)
    for c, (nuevo, _) in NUMERICAS.items():
        col = raw[c] if c in raw else pd.Series(np.nan, index=raw.index)
        if c == "prec":
            col = col.where(prec_txt != "Ip", "0,0")
        df[nuevo] = num(col)
    # textos no numéricos inesperados (distintos de vacío e Ip) -> error
    for c in NUMERICAS:
        if c in raw:
            t = raw[c].dropna().astype(str).str.strip()
            t = t[(t != "") & (t != "Ip")]
            malos = t[pd.to_numeric(t.str.replace(",", ".", regex=False), errors="coerce").isna()]
            assert malos.empty, f"{c}: valores no numéricos inesperados {malos.unique()[:5]}"
    # pintMax negativo
    neg = df["prec_max_intervalo_mm"] < 0
    df["prec_max_intervalo_negativo_en_fuente"] = neg.fillna(False).astype(bool)
    df.loc[neg, "prec_max_intervalo_mm"] = np.nan
    # dirección de la racha
    d = num(raw["dir"])
    especial = d.isin([88, 99])
    df["dir_racha_grados"] = (d.where(~especial) * 10).astype("float64")
    df["dir_racha_codigo"] = d.where(especial).astype("Int64")
    # horas
    for c, nuevo in HORAS.items():
        h = raw[c].astype("string").str.strip() if c in raw else pd.Series(pd.NA, index=raw.index, dtype="string")
        varias = h == "Varias"
        df[nuevo] = h.where(~varias.fillna(False))
        if varias.fillna(False).any():
            df[f"{nuevo}_varias"] = varias.fillna(False).astype(bool)
        # la presión llega a veces solo con la hora ("21"): se admite "HH" tal cual
        patron = r"([01]\d|2[0-4])(:[0-5]\d)?" if c.startswith("horaPres") else r"([01]\d|2[0-4]):[0-5]\d"
        validas = df[nuevo].str.fullmatch(patron)
        invalidas = df[nuevo].notna() & ~validas.fillna(False)
        if c == "horaracha":
            # 5 casos con horas imposibles ("72:30"): -> NaN + indicador
            df[f"{nuevo}_invalida_en_fuente"] = invalidas.astype(bool)
            df.loc[invalidas, nuevo] = pd.NA
        else:
            assert not invalidas.any(), f"{c}: horas con formato inesperado {df.loc[invalidas, nuevo].unique()[:5]}"
    return df


def reindexar(df: pd.DataFrame) -> pd.DataFrame:
    partes = []
    for est, g in df.groupby("estacion"):
        fin = g["fecha"].max()
        idx = pd.date_range(INICIO, fin, freq="D")
        g2 = g.set_index("fecha").reindex(idx)
        g2.index.name = "fecha"
        g2["fila_ausente_en_fuente"] = g2["estacion"].isna()
        g2["estacion"] = est
        partes.append(g2.reset_index())
    out = pd.concat(partes, ignore_index=True)
    for c in out.columns:
        if (c.endswith(("_varias", "_en_fuente")) or c == "prec_inapreciable") and c != "fila_ausente_en_fuente":
            # en filas ausentes no se sabe: NaN (boolean con nulos)
            out[c] = out[c].astype("boolean")
    out["fuente"] = FUENTE
    return out.sort_values(["estacion", "fecha"]).reset_index(drop=True)


def huecos(df: pd.DataFrame) -> dict:
    """Por estación y variable: días sin dato, % y tramos de >=5 días."""
    res = {}
    for est, g in df.groupby("estacion"):
        g = g.sort_values("fecha")
        r = {"rango": [g.fecha.min().strftime("%Y-%m-%d"), g.fecha.max().strftime("%Y-%m-%d")],
             "dias": int(len(g)), "filas_ausentes": int(g.fila_ausente_en_fuente.sum()), "vars": {}}
        for v in VARS_HUECOS:
            nulo = g[v].isna().to_numpy()
            tramos, i = [], 0
            while i < len(nulo):
                if nulo[i]:
                    j = i
                    while j + 1 < len(nulo) and nulo[j + 1]:
                        j += 1
                    if j - i + 1 >= 5:
                        tramos.append([g.fecha.iloc[i].strftime("%Y-%m-%d"),
                                       g.fecha.iloc[j].strftime("%Y-%m-%d"), int(j - i + 1)])
                    i = j + 1
                else:
                    i += 1
            r["vars"][v] = {"nan": int(nulo.sum()), "pct": round(100 * nulo.mean(), 1), "tramos_ge5": tramos}
        res[est] = r
    return res


def escribir_huecos_md(h: dict, est_nombres: dict) -> None:
    cab = "| Estación | Rango | Filas ausentes | " + " | ".join(VARS_HUECOS) + " |"
    sep = "|" + "---|" * (3 + len(VARS_HUECOS))
    lineas = [
        "# Huecos de AEMET por estación y variable",
        "",
        "Generado por `src/limpieza_B/limpia_aemet.py` desde `data/clean/aemet_diario.parquet`. "
        "Celda = % de días sin dato (NaN) en el rango de la estación (2022-01-01 → último día "
        "devuelto). «Filas ausentes» = días que la API no devolvió (fila entera vacía). "
        "Un 100 % indica que la estación no mide esa variable.",
        "",
        cab, sep,
    ]
    for est, r in h.items():
        celdas = [f"{r['vars'][v]['pct']}" for v in VARS_HUECOS]
        lineas.append(f"| {est} {est_nombres.get(est, '')} | {r['rango'][0]} → {r['rango'][1]} | "
                      f"{r['filas_ausentes']} | " + " | ".join(celdas) + " |")
    lineas += ["", "## Tramos sin dato de 5 días o más (temperatura media y precipitación)", ""]
    for est, r in h.items():
        t = r["vars"]["tmed_c"]["tramos_ge5"]
        p = r["vars"]["prec_mm"]["tramos_ge5"]
        if t or p:
            lineas.append(f"- **{est}**: tmed {', '.join(f'{a}→{b} ({n})' for a, b, n in t) or '—'}; "
                          f"prec {', '.join(f'{a}→{b} ({n})' for a, b, n in p) or '—'}")
    lineas += ["", "No se imputa ningún hueco. Si el modelo necesita una serie sin huecos, elegir otra "
               "estación de respaldo (ver `notas/estaciones_aemet.md`) o usar Open-Meteo.", ""]
    (NOTAS / "huecos_aemet.md").write_text("\n".join(lineas), encoding="utf-8")


def estaciones(raw: pd.DataFrame) -> pd.DataFrame:
    inv = pd.DataFrame(json.loads((RAW / "aemet_inventario.json").read_text(encoding="utf-8")))
    inv = inv.set_index("indicativo")
    base = raw.groupby("indicativo")[["nombre", "altitud", "provincia"]].first()
    filas = []
    for ind, r in base.iterrows():
        i = inv.loc[ind]
        zona, uso = USO[ind]
        filas.append({"indicativo": ind, "nombre": r["nombre"], "altitud_m": int(r["altitud"]),
                      "provincia": r["provincia"], "lat": dms_a_decimal(i["latitud"]),
                      "lon": dms_a_decimal(i["longitud"]), "indsinop": i.get("indsinop") or pd.NA,
                      "zona": zona, "uso": uso,
                      "fuente": "AEMET OpenData: inventario de estaciones (data/raw/aemet_inventario.json)"})
    return pd.DataFrame(filas)


def main() -> None:
    asegurar_dirs()
    raw = cargar_bruto()
    assert set(raw["indicativo"]) == set(USO), f"estaciones inesperadas: {set(raw['indicativo']) ^ set(USO)}"
    comprobar_sin_duplicados(raw, ["fecha", "indicativo"], "aemet_bruto")
    df = reindexar(limpiar(raw))

    # comprobaciones
    comprobar_sin_duplicados(df, ["fecha", "estacion"], "aemet_diario")
    ausentes = comprobar_continuidad(df, "fecha", "estacion", "aemet_diario")  # tras reindexar: 0
    for c, (nuevo, (lo, hi)) in NUMERICAS.items():
        comprobar_rango(df, nuevo, lo, hi, "aemet_diario")
    comprobar_rango(df, "dir_racha_grados", 0, 360, "aemet_diario")
    assert (df.loc[df.prec_inapreciable.fillna(False), "prec_mm"] == 0).all()
    assert (df.tmin_c <= df.tmax_c + 1e-9).where(df.tmin_c.notna() & df.tmax_c.notna(), True).all(), \
        "tmin > tmax en alguna fila"
    # el número de filas presentes coincide con el bruto
    assert (~df.fila_ausente_en_fuente).sum() == len(raw)

    escribir_parquet(df, "aemet_diario.parquet")
    est = estaciones(raw)
    est.to_csv(CLEAN / "estaciones_aemet.csv", index=False, encoding="utf-8")

    h = huecos(df)
    escribir_huecos_md(h, dict(zip(est.indicativo, est.nombre)))
    resumen_qc(df, "aemet_diario", ["fecha", "estacion"], extra={
        "fuente": FUENTE,
        "estaciones": sorted(df.estacion.unique()),
        "filas_presentes_en_fuente": int((~df.fila_ausente_en_fuente).sum()),
        "filas_ausentes_en_fuente": int(df.fila_ausente_en_fuente.sum()),
        "prec_inapreciable_dias": int(df.prec_inapreciable.fillna(False).sum()),
        "prec_max_intervalo_negativo_dias": int(df.prec_max_intervalo_negativo_en_fuente.fillna(False).sum()),
        "dir_racha_codigo_99": int((df.dir_racha_codigo == 99).sum()),
        "dir_racha_codigo_88": int((df.dir_racha_codigo == 88).sum()),
        "fechas_ausentes_tras_reindexar": ausentes,
        "huecos_por_estacion_variable": h,
        "comprobaciones": ["sin duplicados (fecha, estacion) en bruto y limpio",
                           "calendario continuo por estación tras reindexar",
                           "rangos válidos de todas las variables numéricas",
                           "prec=0 en días Ip", "tmin<=tmax", "filas presentes = registros brutos"],
    })
    print(f"aemet_diario: {len(df)} filas, {df.estacion.nunique()} estaciones, "
          f"{int(df.fila_ausente_en_fuente.sum())} filas ausentes en la fuente")
    print(f"estaciones_aemet.csv: {len(est)} filas")


if __name__ == "__main__":
    main()
