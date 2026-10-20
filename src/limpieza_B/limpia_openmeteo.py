"""Limpieza de Open-Meteo -> tablas diarias por zona meteorológica.

Entradas (no se modifican), para cada zona de config/zonas_meteo.csv:
- data/raw/openmeteo_<zona>.json           Historical Forecast, diario (serie de entrenamiento)
- data/raw/openmeteo_previous_<zona>.json  Previous Runs, horario (previsión hecha 1, 2 y 3 días antes)
- data/raw/openmeteo_archive_<zona>.json   ERA5, diario (solo referencia)
- data/raw/openmeteo_prevision_ejemplo.json  previsión en vivo (7 días, una zona)

Salidas:
- data/clean/openmeteo_diario.parquet         fecha × zona_meteo; Historical Forecast + columnas *_prev1/2/3
- data/clean/openmeteo_era5_diario.parquet    fecha × zona_meteo; ERA5, `uso`=solo_referencia_no_entrenar
- data/clean/openmeteo_prevision_ejemplo.parquet  mismo esquema exacto que openmeteo_diario
- data/clean/_qc/openmeteo_*.json

Decisiones (ver notas/diccionario_B.md y notas/fuentes/openmeteo/openmeteo_tramo_2022.md):
- `es_reanalisis` = fecha < corte de la zona (Asturias 2022-11-09; Madrid y Sevilla 2022-11-16).
  Esos días NO deben usarse para evaluar; se conservan para el análisis de sensibilidad.
- Previous Runs (horario, hora local Europe/Madrid) -> diario por día natural local:
  tmax/tmin = máx/mín de temperature_2m; prec = suma; prec_horas = nº de horas con
  precipitación >= 0,1 mm; viento/racha = máximo; sol = suma (s); weather_code = máximo
  horario (aproximación a "código más severo" del diario de Open-Meteo).
  Un valor diario prevN solo existe si las 24 horas del día tienen dato; además se
  fuerza NaN antes de 2024-01-22 (primer día con day1..day3 completos).
- El último día de cada serie (día de la descarga) puede estar incompleto:
  `dia_posiblemente_incompleto=True`.

Ejecución: python -X utf8 src/limpieza_B/limpia_openmeteo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import (CONFIG, RAW, asegurar_dirs, comprobar_continuidad, comprobar_rango,  # noqa: E402
                   comprobar_sin_duplicados, escribir_parquet, resumen_qc)

CORTE = {"madrid": "2022-11-16", "sevilla": "2022-11-16"}  # resto (Asturias): 2022-11-09
CORTE_ASTURIAS = "2022-11-09"
INICIO_PREVIOUS = pd.Timestamp("2024-01-22")

# nombre Open-Meteo diario -> nombre limpio
DIARIAS = {
    "temperature_2m_max": "tmax_c",
    "temperature_2m_min": "tmin_c",
    "precipitation_sum": "prec_mm",
    "precipitation_hours": "prec_horas",
    "sunshine_duration": "sol_s",
    "wind_speed_10m_max": "viento_max_kmh",
    "wind_gusts_10m_max": "racha_max_kmh",
    "weather_code": "weather_code",
}
VARS = list(DIARIAS.values())
RANGOS = {"tmax_c": (-30, 50), "tmin_c": (-30, 50), "prec_mm": (0, 500), "prec_horas": (0, 24),
          "sol_s": (0, 86400), "viento_max_kmh": (0, 250), "racha_max_kmh": (0, 300),
          "weather_code": (0, 99)}
FUENTE_HIST = "Open-Meteo Historical Forecast API (best_match), diario"
FUENTE_ERA5 = "Open-Meteo Archive API (ERA5), diario"
FUENTE_PREV = "Open-Meteo Forecast API (previsión en vivo), diario"
NEGATIVOS_ANULADOS: dict = {}  # zona -> {variable horaria: [horas anuladas]}


def zonas() -> list[str]:
    return pd.read_csv(CONFIG / "zonas_meteo.csv")["zona"].tolist()


def leer(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def diario(d: dict, zona: str) -> pd.DataFrame:
    df = pd.DataFrame(d["daily"]).rename(columns=DIARIAS)
    df.insert(0, "fecha", pd.to_datetime(df.pop("time"), format="%Y-%m-%d"))
    df.insert(1, "zona_meteo", zona)
    for v in VARS:
        df[v] = df[v].astype("float64")
    return df[["fecha", "zona_meteo"] + VARS]


def agrega_horario(h: pd.DataFrame, suf: str) -> pd.DataFrame:
    """Horario -> diario para una serie (suf='' es el día 0; '_previous_dayN' las previsiones)."""
    t = h[f"temperature_2m{suf}"]
    p = h[f"precipitation{suf}"]
    g = h["dia"]
    out = pd.DataFrame({
        "tmax_c": t.groupby(g).max(),
        "tmin_c": t.groupby(g).min(),
        "prec_mm": p.groupby(g).sum(min_count=1).round(2),
        "prec_horas": (p >= 0.1).where(p.notna()).groupby(g).sum(min_count=1),
        "sol_s": h[f"sunshine_duration{suf}"].groupby(g).sum(min_count=1),
        "viento_max_kmh": h[f"wind_speed_10m{suf}"].groupby(g).max(),
        "racha_max_kmh": h[f"wind_gusts_10m{suf}"].groupby(g).max(),
        "weather_code": h[f"weather_code{suf}"].groupby(g).max(),
    })
    # día completo = 24 horas con todas las variables presentes
    cols = [f"{b}{suf}" for b in ("temperature_2m", "precipitation", "sunshine_duration",
                                  "wind_speed_10m", "wind_gusts_10m", "weather_code")]
    completo = h[cols].notna().all(axis=1).groupby(g).sum() == 24
    n_horas = g.value_counts().reindex(out.index)
    out.loc[~(completo & (n_horas == 24)), :] = np.nan
    out.index.name = "fecha"
    return out.astype("float64")


def previous(d: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (columnas *_prev1..3 por fecha, agregado del día 0 para el sanity check)."""
    h = pd.DataFrame(d["hourly"])
    ts = pd.to_datetime(h["time"], format="%Y-%m-%dT%H:%M")
    h["dia"] = ts.dt.normalize()
    assert not ts.duplicated().any(), "horas duplicadas en Previous Runs"
    # valores físicamente imposibles (p. ej. precipitación -0,9 mm el 2025-06-15 12:00 en
    # day1 de 3 zonas) -> NaN; el día afectado queda incompleto y su prevN es NaN.
    negativos = {}
    for c in h.columns:
        if c.startswith(("precipitation", "sunshine_duration", "wind_speed", "wind_gusts", "weather_code")):
            m = h[c] < 0
            if m.any():
                negativos[c] = h.loc[m, "time"].tolist()
                h.loc[m, c] = np.nan
    NEGATIVOS_ANULADOS[d["_descarga"]["zona"]] = negativos
    partes = []
    for n in (1, 2, 3):
        a = agrega_horario(h, f"_previous_day{n}")
        a.loc[a.index < INICIO_PREVIOUS, :] = np.nan
        partes.append(a.add_suffix(f"_prev{n}"))
    dia0 = agrega_horario(h, "")
    return pd.concat(partes, axis=1), dia0


def sanity_dia0(hist: pd.DataFrame, dia0: pd.DataFrame, zona: str) -> dict:
    """Compara el agregado diario del día 0 horario con el diario de Historical Forecast."""
    a = hist.set_index("fecha").loc[dia0.index.intersection(hist.fecha)]
    b = dia0.loc[a.index]
    r = {}
    for v in VARS:
        dif = (a[v] - b[v]).abs()
        tol = 0.05 if v in ("prec_mm", "tmax_c", "tmin_c") else 0.5
        r[v] = {"mae": round(float(dif.mean()), 3), "pct_iguales_tol": round(float((dif <= tol).mean() * 100), 1),
                "corr": round(float(a[v].corr(b[v])), 4) if a[v].std() > 0 and b[v].std() > 0 else None}
    return r


def corte(zona: str) -> pd.Timestamp:
    return pd.Timestamp(CORTE.get(zona, CORTE_ASTURIAS))


def construir() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    tablas, era5s, sanity, meta = [], [], {}, {}
    for z in zonas():
        dh = leer(RAW / f"openmeteo_{z}.json")
        hist = diario(dh, z)
        prev, dia0 = previous(leer(RAW / f"openmeteo_previous_{z}.json"))
        sanity[z] = sanity_dia0(hist, dia0, z)
        t = hist.merge(prev, left_on="fecha", right_index=True, how="left")
        t["es_reanalisis"] = t["fecha"] < corte(z)
        f_desc = pd.Timestamp(dh["_descarga"]["fecha_descarga_ultimo_tramo"]).normalize()
        t["dia_posiblemente_incompleto"] = t["fecha"] >= f_desc
        t["fuente"] = FUENTE_HIST
        tablas.append(t)
        meta[z] = {"lat_respuesta": dh["latitude"], "lon_respuesta": dh["longitude"],
                   "elevacion": dh["elevation"], "fecha_descarga": f_desc.strftime("%Y-%m-%d"),
                   "corte_reanalisis": corte(z).strftime("%Y-%m-%d")}
        e = diario(leer(RAW / f"openmeteo_archive_{z}.json"), z)
        e["uso"] = "solo_referencia_no_entrenar"
        e["fuente"] = FUENTE_ERA5
        era5s.append(e)
    om = pd.concat(tablas, ignore_index=True).sort_values(["zona_meteo", "fecha"]).reset_index(drop=True)
    era5 = pd.concat(era5s, ignore_index=True).sort_values(["zona_meteo", "fecha"]).reset_index(drop=True)
    return om, era5, sanity, meta


def prevision_ejemplo(om: pd.DataFrame, meta: dict) -> tuple[pd.DataFrame, str]:
    d = leer(RAW / "openmeteo_prevision_ejemplo.json")
    # la previsión no lleva nombre de zona: se identifica por las coordenadas de la respuesta
    cand = [z for z, m in meta.items()
            if abs(m["lat_respuesta"] - d["latitude"]) < 1e-6 and abs(m["lon_respuesta"] - d["longitude"]) < 1e-6]
    assert len(cand) == 1, f"no se identifica la zona de la previsión de ejemplo: {cand}"
    z = cand[0]
    p = diario(d, z)
    for c in om.columns:
        if c not in p.columns:
            p[c] = np.nan
    p["es_reanalisis"] = False
    p["dia_posiblemente_incompleto"] = False
    p["fuente"] = FUENTE_PREV
    p = p[om.columns].astype(om.dtypes.to_dict())
    return p, z


def comprobar_esquema(a: pd.DataFrame, b: pd.DataFrame) -> None:
    assert list(a.columns) == list(b.columns), "la previsión y el entrenamiento no tienen las mismas columnas"
    dif = {c: (str(a[c].dtype), str(b[c].dtype)) for c in a.columns if a[c].dtype != b[c].dtype}
    assert not dif, f"dtypes distintos entre entrenamiento y previsión: {dif}"


def comprobar(df: pd.DataFrame, tabla: str) -> dict:
    comprobar_sin_duplicados(df, ["fecha", "zona_meteo"], tabla)
    aus = comprobar_continuidad(df, "fecha", "zona_meteo", tabla)
    for c in df.columns:
        base = c.rsplit("_prev", 1)[0]
        if base in RANGOS:
            comprobar_rango(df, c, *RANGOS[base], tabla=tabla)
    for s in ["", "_prev1", "_prev2", "_prev3"]:
        if f"tmin_c{s}" in df:
            m = df[f"tmin_c{s}"].notna() & df[f"tmax_c{s}"].notna()
            assert (df.loc[m, f"tmin_c{s}"] <= df.loc[m, f"tmax_c{s}"] + 1e-9).all(), f"[{tabla}] tmin>tmax{s}"
    return aus


def main() -> None:
    asegurar_dirs()
    om, era5, sanity, meta = construir()
    aus = comprobar(om, "openmeteo_diario")
    comprobar(era5, "openmeteo_era5_diario")
    assert om[VARS].notna().all().all(), "Historical Forecast con nulos (no esperado)"
    prev_cols = [c for c in om.columns if "_prev" in c]
    assert om.loc[om.fecha < INICIO_PREVIOUS, prev_cols].isna().all().all()
    # desde 2024-01-22 las prevN deben estar completas salvo días incompletos
    # desde 2024-01-22 las prevN solo pueden faltar en los días con valores anulados
    dias_anulados = {(z, pd.Timestamp(t[:10])) for z, d in NEGATIVOS_ANULADOS.items()
                     for horas in d.values() for t in horas}
    for n in (1, 2, 3):
        cols_n = [c for c in prev_cols if c.endswith(f"_prev{n}")]
        f = om[(om.fecha >= INICIO_PREVIOUS) & om[cols_n].isna().any(axis=1)]
        inesperados = set(zip(f.zona_meteo, f.fecha)) - dias_anulados
        assert not inesperados, f"prev{n} con nulos inesperados desde 2024-01-22: {sorted(inesperados)[:5]}"
    for z in om.zona_meteo.unique():
        g = om[om.zona_meteo == z]
        assert g.loc[g.fecha < corte(z), "es_reanalisis"].all() and not g.loc[g.fecha >= corte(z), "es_reanalisis"].any()

    prev_ej, zona_ej = prevision_ejemplo(om, meta)
    comprobar_esquema(om, prev_ej)
    comprobar(prev_ej, "openmeteo_prevision_ejemplo")

    escribir_parquet(om, "openmeteo_diario.parquet")
    escribir_parquet(era5, "openmeteo_era5_diario.parquet")
    escribir_parquet(prev_ej, "openmeteo_prevision_ejemplo.parquet")

    # comparación Historical Forecast vs ERA5 tras el corte (contexto, no entrenamiento)
    m = om.merge(era5, on=["fecha", "zona_meteo"], suffixes=("", "_era5"))
    m = m[~m.es_reanalisis]
    sesgo = {z: {v: round(float((g[v] - g[f"{v}_era5"]).mean()), 3) for v in ("tmax_c", "tmin_c", "prec_mm")}
             for z, g in m.groupby("zona_meteo")}

    resumen_qc(om, "openmeteo_diario", ["fecha", "zona_meteo"], extra={
        "zonas": sorted(om.zona_meteo.unique()),
        "fechas_ausentes_por_zona": aus,
        "dias_es_reanalisis_por_zona": om.groupby("zona_meteo").es_reanalisis.sum().astype(int).to_dict(),
        "dias_posiblemente_incompletos": om[om.dia_posiblemente_incompleto].fecha.dt.strftime("%Y-%m-%d").unique().tolist(),
        "primer_dia_prev": om.loc[om.tmax_c_prev1.notna(), "fecha"].min().strftime("%Y-%m-%d"),
        "meta_por_zona": meta,
        "previous_valores_horarios_negativos_anulados": NEGATIVOS_ANULADOS,
        "sanity_dia0_previous_vs_historical": sanity,
        "comprobaciones": ["sin duplicados (fecha, zona_meteo)", "calendario continuo por zona",
                           "rangos válidos", "tmin<=tmax (también prevN)", "Historical Forecast sin nulos",
                           "prevN NaN antes de 2024-01-22 y completas después",
                           "es_reanalisis coherente con el corte por zona"],
    })
    resumen_qc(era5, "openmeteo_era5_diario", ["fecha", "zona_meteo"], extra={
        "uso": "solo_referencia_no_entrenar",
        "sesgo_medio_historical_menos_era5_tras_corte": sesgo})
    resumen_qc(prev_ej, "openmeteo_prevision_ejemplo", ["fecha", "zona_meteo"], extra={
        "zona_identificada_por_coordenadas": zona_ej,
        "esquema_igual_a_openmeteo_diario": True})
    print(f"openmeteo_diario: {len(om)} filas, {om.zona_meteo.nunique()} zonas, "
          f"{om.fecha.min().date()}..{om.fecha.max().date()}")
    print(f"openmeteo_era5_diario: {len(era5)} filas")
    print(f"openmeteo_prevision_ejemplo: {len(prev_ej)} filas (zona {zona_ej}); esquema idéntico: OK")
    print("sanity día 0 (covadonga):", json.dumps(sanity["covadonga"], ensure_ascii=False))


if __name__ == "__main__":
    main()
