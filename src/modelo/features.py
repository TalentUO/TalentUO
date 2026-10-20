"""Variables del modelo por fecha, zona y horizonte (sin fuga de información).

Dos tablas:
- largo (h >= 8): una fila por (fecha, zona). Solo calendario, eventos y
  partidos, que se conocen con meses de antelación.
- corto (h = 1..7): una fila por (fecha, zona, horizonte). Lo mismo + tiempo
  (previsión archivada) + interés en internet, calculados con lo que se
  conocía en d - h.

Regla de disponibilidad (la comprueba tests/test_antifuga.py):
- Tiempo: `openmeteo_diario.<var>_prev{k}` es la previsión emitida en d - k.
  Para el horizonte h se usa `_prev{h}` (h <= 3). La serie base (plazo ~0) no
  se usa en modo estricto. Nunca AEMET (observación) ni ERA5.
- Wikipedia: media de log(1 + visitas) de los 7 días que terminan en d - h.
- Trends: valor de la última semana completa (domingo a sábado) que termina
  antes de d - h.
- Nunca valores del propio objetivo (el MITMA no se publica en tiempo real).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from util import CLEAN, cfg, importar_limpieza_B, norm_texto

FECHA_FIN_CALENDARIO = "2027-12-31"
VARS_TIEMPO = {"tmax": "tmax_c", "prec": "prec_mm", "sol_h": "sol_s", "viento": "viento_max_kmh"}
EVENTOS_EXCLUIDOS = {"crucero_gijon", "partido_futbol"}  # cruceros: solo previsión; partidos: futbol_*


def cargar_tablas() -> dict[str, pd.DataFrame]:
    nombres = ["calendario_diario", "festivos_locales", "eventos_diario", "partidos_diario",
               "openmeteo_diario", "aemet_diario", "wikipedia_diario", "trends_semanal"]
    t = {n: pd.read_parquet(CLEAN / f"{n}.parquet") for n in nombres}
    for n in nombres:
        if "fecha" in t[n].columns:
            t[n]["fecha"] = pd.to_datetime(t[n]["fecha"]).dt.normalize()
    return t


def _bool_float(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype("boolean").astype("Float64"), errors="coerce").astype(float)


# --------------------------------------------------------------------------
# Base (fecha, zona): calendario, eventos y partidos
# --------------------------------------------------------------------------

def tabla_base(mapeo: pd.DataFrame, tablas: dict, solo_eventos_verificados: bool = False,
               fecha_fin: str = FECHA_FIN_CALENDARIO) -> pd.DataFrame:
    importar_limpieza_B()
    from unir_B import unir_B  # noqa: E402

    ev = tablas["eventos_diario"]
    ev = ev[~ev["tipo"].isin(EVENTOS_EXCLUIDOS)]
    if solo_eventos_verificados:
        ev = ev[ev["estado"] == "verificado"]
    t = dict(tablas)
    t["eventos_diario"] = ev
    u = unir_B(mapeo, tablas=t, fecha_ini="2022-01-01", fecha_fin=fecha_fin, salida=None)
    u = u.sort_values(["zona_mitma_id", "fecha"]).reset_index(drop=True)

    b = u[["fecha", "zona_mitma_id"]].copy()
    b["cal_dia_semana"] = u["dia_semana"].astype(int)
    b["cal_mes"] = u["mes"].astype(int)
    doy = u["fecha"].dt.dayofyear
    b["cal_doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    b["cal_doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    b["cal_fin_de_semana"] = u["es_fin_de_semana"].astype(float)
    for c in ["festivo_nacional", "festivo_ast", "festivo_local", "festivo_mad", "festivo_cyl",
              "puente_ast", "puente_mad", "puente_cyl",
              "finde_largo_con_puente_ast", "finde_largo_con_puente_mad", "finde_largo_con_puente_cyl",
              "semana_santa", "semana_santa_ampliada"]:
        b[f"cal_{c}"] = _bool_float(u[c])
    b["cal_festivo_local_parcial"] = _bool_float(u["festivo_local_parcial"])

    # Víspera y distancia a festivos: el calendario se conoce de antemano.
    laborable = (~u["es_fin_de_semana"].astype(bool))
    fest_ast = (u["festivo_ast"].astype(bool) | u["festivo_local"].astype(bool))
    fest_mad = u["festivo_mad"].astype(bool)
    sig_ast = fest_ast.groupby(u["zona_mitma_id"]).shift(-1).astype("boolean").fillna(False).astype(bool)
    sig_mad = fest_mad.groupby(u["zona_mitma_id"]).shift(-1).astype("boolean").fillna(False).astype(bool)
    b["cal_vispera_festivo_ast"] = (sig_ast & laborable & ~fest_ast).astype(float)
    b["cal_vispera_festivo_mad"] = (sig_mad & laborable & ~fest_mad).astype(float)
    ff = u["fecha"].where(fest_ast)
    prox = ff.groupby(u["zona_mitma_id"]).bfill()
    ult = ff.groupby(u["zona_mitma_id"]).ffill()
    b["cal_dias_hasta_festivo"] = (prox - u["fecha"]).dt.days.clip(upper=30).astype(float)
    b["cal_dias_desde_festivo"] = (u["fecha"] - ult).dt.days.clip(upper=30).astype(float)

    for c in ["ast", "mad", "cyl"]:
        b[f"cal_vacaciones_{c}"] = _bool_float(u[f"vacaciones_escolares_{c}"])
    b["cal_lagos_regulado"] = _bool_float(u["lagos_regulado"])

    # Eventos en el concejo (sin cruceros ni partidos) y partidos en casa.
    b["ev_n"] = u["ev_n"].astype(float) if "ev_n" in u else 0.0
    for tipo in ["fiesta", "festival", "romeria", "deportivo", "feria"]:
        col = f"ev_{tipo}"
        b[col] = u[col].astype(float) if col in u.columns else 0.0
    for c in ["partido_oviedo", "partido_sporting", "derbi_asturiano"]:
        b[f"futbol_{c}"] = _bool_float(u[f"futbol_{c}"])

    # Calendario aún no publicado (2027: curso escolar desde septiembre y
    # regulación de los Lagos): se supone igual que 364 días antes (mismo día
    # de la semana) y se marca. Solo afecta a las previsiones de 2027.
    b["calendario_supuesto"] = False
    for c in ["cal_vacaciones_ast", "cal_vacaciones_mad", "cal_vacaciones_cyl", "cal_lagos_regulado"]:
        falta = b[c].isna() & (b["fecha"] >= "2027-01-01")
        if falta.any():
            ant = b[["fecha", "zona_mitma_id", c]].copy()
            ant["fecha"] = ant["fecha"] + pd.Timedelta(days=364)
            rel = b[["fecha", "zona_mitma_id"]].merge(ant, on=["fecha", "zona_mitma_id"], how="left")[c]
            b.loc[falta, c] = rel[falta].to_numpy()
            b.loc[falta, "calendario_supuesto"] = True
    return b


# --------------------------------------------------------------------------
# Tiempo (previsión archivada) por horizonte
# --------------------------------------------------------------------------

def tiempo(om: pd.DataFrame, mapeo: pd.DataFrame, h: int, modo: str | None = None,
           desde_reanalisis: bool = False) -> pd.DataFrame:
    """(fecha, zona_mitma_id) -> tv_* (valle) y tm_* (montaña) para el horizonte h."""
    modo = modo or cfg()["tiempo"]["modo"]
    max_lead = int(cfg()["tiempo"]["max_lead_archivado"])
    corte = pd.Timestamp(cfg()["corte_reanalisis"])
    out = []
    for z, zm, zmm in zip(mapeo["zona_mitma_id"], mapeo["zona_meteo"], mapeo.get("zona_meteo_montana", [None] * len(mapeo))):
        piezas = {}
        for pref, punto in (("tv", zm), ("tm", zmm)):
            if punto is None or (isinstance(punto, float) and np.isnan(punto)):
                continue
            s = om[om["zona_meteo"] == punto].set_index("fecha").sort_index()
            for nombre, var in VARS_TIEMPO.items():
                if h <= max_lead and f"{var}_prev{h}" in s.columns:
                    v = s[f"{var}_prev{h}"].astype(float)
                else:
                    v = pd.Series(np.nan, index=s.index)
                if modo == "aproximado":
                    base = s[var].astype(float)
                    if not desde_reanalisis:
                        base = base.where(base.index >= corte)
                    v = v.fillna(base)
                if var == "sol_s":
                    v = v / 3600.0
                piezas[f"{pref}_{nombre}"] = v
        df = pd.DataFrame(piezas)
        df.index.name = "fecha"
        df = df.reset_index()
        df["zona_mitma_id"] = z
        out.append(df)
    res = pd.concat(out, ignore_index=True)
    for pref in ("tv", "tm"):
        for nombre in VARS_TIEMPO:
            if f"{pref}_{nombre}" not in res.columns:
                res[f"{pref}_{nombre}"] = np.nan
    return res


# --------------------------------------------------------------------------
# Interés en internet por horizonte
# --------------------------------------------------------------------------

def articulos_zona(mapeo: pd.DataFrame, articulos: set[str]) -> dict[str, list[str]]:
    res = {}
    for z, ce in zip(mapeo["zona_mitma_id"], mapeo["concejo_eventos"]):
        cands = [norm_texto(c) for c in str(ce or "").split(";") if c.strip()]
        res[z] = [a for a in cands if a in articulos]
    return res


def interes(wiki: pd.DataFrame, trends: pd.DataFrame, mapeo: pd.DataFrame, h: int,
            fechas: pd.DatetimeIndex) -> pd.DataFrame:
    """(fecha, zona) -> int_* con la información disponible en fecha - h."""
    ventana = int(cfg()["interes"]["ventana_wiki_dias"])
    piv = wiki.pivot_table(index="fecha", columns="articulo", values="visitas", aggfunc="sum")
    piv = piv.reindex(pd.date_range(piv.index.min(), max(piv.index.max(), fechas.max()), freq="D"))

    def media_log(cols):
        cols = [c for c in cols if c in piv.columns]
        if not cols:
            return pd.Series(np.nan, index=piv.index)
        s = np.log1p(piv[cols].sum(axis=1, min_count=len(cols)))
        return s.rolling(ventana, min_periods=ventana).mean()

    disp = fechas - pd.Timedelta(days=h)            # fecha de disponibilidad d - h
    picos = media_log(cfg()["interes"]["wiki_picos"]).reindex(disp).to_numpy()
    por_zona = articulos_zona(mapeo, set(piv.columns))

    # Trends: semana (domingo..sábado) completa que termina antes de d - h:
    # domingo S más reciente con S <= d - h - 7.
    tr = trends[trends["fiable"] & ~trends["is_partial"].astype(bool)].copy()
    tr["semana_inicio"] = pd.to_datetime(tr["semana_inicio"]).dt.normalize()
    tr["col"] = "int_trends_" + tr["termino"].map(norm_texto) + "_" + tr["geo"].str.lower().str.replace("-", "_")
    trp = tr.pivot_table(index="semana_inicio", columns="col", values="valor", aggfunc="first")
    lim = disp - pd.Timedelta(days=7)
    domingo = lim - pd.to_timedelta((lim.dayofweek + 1) % 7, unit="D")
    trv = trp.reindex(domingo)

    out = []
    for z in mapeo["zona_mitma_id"]:
        df = pd.DataFrame({"fecha": fechas, "zona_mitma_id": z})
        df["int_wiki_zona"] = media_log(por_zona.get(z, [])).reindex(disp).to_numpy()
        df["int_wiki_picos"] = picos
        for c in trp.columns:
            df[c] = trv[c].to_numpy(dtype=float)
        out.append(df)
    return pd.concat(out, ignore_index=True)


# --------------------------------------------------------------------------
# Tablas completas
# --------------------------------------------------------------------------

def columnas_modelo(df: pd.DataFrame, tipo: str) -> list[str]:
    pref = ("cal_", "ev_", "futbol_") if tipo == "largo" else ("cal_", "ev_", "futbol_", "tv_", "tm_", "int_")
    cols = [c for c in df.columns if c.startswith(pref)]
    cols.append("zona")
    if tipo == "corto":
        cols.append("horizonte")
    return cols


def zona_categorica(df: pd.DataFrame, zonas: list[str]) -> pd.DataFrame:
    df["zona"] = pd.Categorical(df["zona_mitma_id"], categories=sorted(zonas))
    return df


def tabla_largo(base: pd.DataFrame, zonas: list[str]) -> pd.DataFrame:
    df = base.copy()
    df["horizonte"] = int(cfg()["horizonte_largo"])
    return zona_categorica(df, zonas)


def tabla_corto(base: pd.DataFrame, mapeo: pd.DataFrame, tablas: dict, fechas: pd.DatetimeIndex,
                modo_tiempo: str | None = None, desde_reanalisis: bool = False,
                horizontes: list[int] | None = None) -> pd.DataFrame:
    horizontes = horizontes or cfg()["horizontes_corto"]
    b = base[base["fecha"].isin(fechas)]
    partes = []
    for h in horizontes:
        t = tiempo(tablas["openmeteo_diario"], mapeo, h, modo_tiempo, desde_reanalisis)
        i = interes(tablas["wikipedia_diario"], tablas["trends_semanal"], mapeo, h, fechas)
        df = (b.merge(t, on=["fecha", "zona_mitma_id"], how="left", validate="one_to_one")
              .merge(i, on=["fecha", "zona_mitma_id"], how="left", validate="one_to_one"))
        df["horizonte"] = h
        partes.append(df)
    return zona_categorica(pd.concat(partes, ignore_index=True), list(mapeo["zona_mitma_id"]))
