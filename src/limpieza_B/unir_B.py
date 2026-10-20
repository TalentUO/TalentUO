"""Une las tablas limpias de la parte B en una tabla diaria por zona MITMA.

Uso:
    python -X utf8 src/limpieza_B/unir_B.py --mapeo config/mapeo_zonas.csv
    python -X utf8 src/limpieza_B/unir_B.py --mapeo config/mapeo_zonas_ejemplo.csv --salida data/clean/_prueba/factores_B_ejemplo.parquet

Entrada: un `mapeo_zonas.csv` completo (una fila por `zona_mitma_id`):
    zona_mitma_id, nombre, concejos_ine, zona_meteo, [zona_meteo_montana],
    estacion_aemet, concejo_eventos
`concejos_ine` y `concejo_eventos` admiten varios valores separados por ";"
(zonas MITMA que agrupan concejos). `zona_meteo_montana`, `estacion_aemet` y
`concejo_eventos` pueden quedar vacíos (las columnas correspondientes salen
NaN o False).

Salida: `data/clean/factores_B_diario.parquet`, una fila por `fecha` y
`zona_mitma_id`. Qué entra y qué no:
- calendario_diario: todas las columnas (por fecha).
- festivos_locales: `festivo_local` (algún concejo de la zona; las fiestas
  parciales cuentan), `festivo_local_parcial` y el nombre.
- openmeteo_diario: columnas de entrenamiento con prefijo `om_` (incluye
  `om_es_reanalisis` y las `*_prevN`) y, si hay `zona_meteo_montana`, las
  mismas con prefijo `om_montana_`.
- aemet_diario: variables con prefijo `aemet_` (observación: NO está
  disponible en producción para el día a predecir; usar solo con retardo).
- eventos_diario: agregados por zona (`ev_n`, `ev_n_verificado`, un
  indicador por tipo y cruceros en previsión); partidos_diario: `futbol_*`.
- wikipedia_diario: media de los 7 días anteriores por artículo
  (`wiki_<articulo>_media7_ant`, comunes a todas las zonas).
- trends_semanal (solo fiables): valor de la semana anterior completa
  (`trends_<termino>_<geo>_sem_ant`).
- NO entran: ERA5 (solo referencia), previsión de ejemplo, OAPN anual (total
  anual: fuga si se usa a diario), Trends no fiable.

Comprobaciones: el resultado tiene exactamente n_fechas × n_zonas filas,
sin duplicados de (fecha, zona_mitma_id) y sin fechas perdidas.
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import CLEAN, RAIZ, comprobar_continuidad, comprobar_sin_duplicados  # noqa: E402

COLS_MAPEO = ["zona_mitma_id", "nombre", "concejos_ine", "zona_meteo", "estacion_aemet", "concejo_eventos"]
# Columnas descriptivas que no se arrastran a la tabla unida.
NO_ARRASTRAR = {"fuente", "uso", "nombre", "provincia", "altitud", "indicativo", "fichero"}


# --------------------------------------------------------------------------
# utilidades
# --------------------------------------------------------------------------

def norm_concejo(s) -> str | None:
    """Clave de unión para concejos: sin tildes, minúsculas, solo la parte
    castellana de los nombres bilingües ("Gijón/Xixón" -> "gijon")."""
    if s is None or (isinstance(s, float) and pd.isna(s)) or str(s).strip() == "":
        return None
    s = str(s).split("/")[0].strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(s.lower().replace("-", " ").split())


def lista(valor) -> list[str]:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return []
    return [v.strip() for v in str(valor).split(";") if v.strip()]


def leer_mapeo(ruta: Path) -> pd.DataFrame:
    m = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    faltan = [c for c in COLS_MAPEO if c not in m.columns]
    if faltan:
        raise ValueError(f"mapeo sin columnas {faltan}")
    m = m.replace({"": None})
    if m["zona_mitma_id"].isna().any():
        raise ValueError("mapeo incompleto: hay filas sin zona_mitma_id "
                         "(revisa la columna zona_mitma_id de config/mapeo_zonas.csv)")
    if m["zona_mitma_id"].duplicated().any():
        raise ValueError("zona_mitma_id duplicado en el mapeo")
    if m["zona_meteo"].isna().any():
        raise ValueError("todas las zonas necesitan zona_meteo")
    return m


def columnas_valor(df: pd.DataFrame, claves: list[str]) -> list[str]:
    return [c for c in df.columns if c not in claves and c not in NO_ARRASTRAR]


def cargar(nombre: str, tablas: dict | None) -> pd.DataFrame:
    if tablas is not None and nombre in tablas:
        return tablas[nombre].copy()
    return pd.read_parquet(CLEAN / f"{nombre}.parquet")


# --------------------------------------------------------------------------
# bloques
# --------------------------------------------------------------------------

def bloque_eventos(ev: pd.DataFrame, zonas_concejo: pd.DataFrame) -> pd.DataFrame:
    """Agrega eventos por (fecha, zona_mitma_id)."""
    ev = ev.copy()
    ev["concejo_n"] = ev["concejo"].map(norm_concejo)
    x = zonas_concejo.merge(ev, on="concejo_n", how="inner")
    if x.empty:
        return pd.DataFrame(columns=["fecha", "zona_mitma_id"])
    # un mismo evento podría llegar por dos concejos de la zona: contar una vez
    x = x.drop_duplicates(subset=["fecha", "zona_mitma_id", "evento"])
    g = x.groupby(["fecha", "zona_mitma_id"])
    out = g.size().rename("ev_n").to_frame()
    out["ev_n_verificado"] = g["estado"].apply(lambda s: int((s == "verificado").sum()))
    for tipo in sorted(x["tipo"].dropna().unique()):
        out[f"ev_{tipo}"] = g["tipo"].apply(lambda s, t=tipo: bool((s == t).any()))
    if "es_prevision" in x.columns:
        pas = next((c for c in ("pasajeros_capacidad", "aforo_o_pasajeros") if c in x.columns), None)
        cr = x[x["tipo"] == "crucero_gijon"]
        if pas and not cr.empty:
            # Cruceros: solo previsiones 2025-2026. NO usar para entrenar.
            out["crucero_pasajeros_prevision"] = (
                cr.groupby(["fecha", "zona_mitma_id"])[pas]
                .apply(lambda s: pd.to_numeric(s, errors="coerce").sum(min_count=1)))
    return out.reset_index()


def bloque_festivos_locales(fl: pd.DataFrame, zonas_concejo: pd.DataFrame) -> pd.DataFrame:
    fl = fl.copy()
    fl["concejo_n"] = fl["concejo"].map(norm_concejo)
    x = zonas_concejo.merge(fl, on="concejo_n", how="inner")
    if x.empty:
        return pd.DataFrame(columns=["fecha", "zona_mitma_id", "festivo_local"])
    col_nombre = "nombre" if "nombre" in x.columns else None
    g = x.groupby(["fecha", "zona_mitma_id"])
    out = g.size().gt(0).rename("festivo_local").to_frame()
    if "festivo_parcial" in x.columns:
        # Parcial = todas las fiestas de ese día en la zona son de una parte del
        # concejo. Si alguna es de todo el concejo -> False; si solo hay de ámbito
        # dudoso o sin nombre -> NA.
        def _parcial(s):
            s = s.astype("boolean")
            if (s == False).any():  # noqa: E712
                return False
            return True if (s == True).any() else pd.NA  # noqa: E712
        out["festivo_local_parcial"] = g["festivo_parcial"].apply(_parcial).astype("boolean")
    if col_nombre:
        out["festivo_local_nombre"] = g[col_nombre].apply(
            lambda s: "; ".join(sorted({str(v) for v in s.dropna()})) or None)
    return out.reset_index()


# --------------------------------------------------------------------------
# función principal
# --------------------------------------------------------------------------

def unir_B(mapeo: pd.DataFrame | str | Path, tablas: dict | None = None,
           fecha_ini: str | None = None, fecha_fin: str | None = None,
           salida: str | Path | None = CLEAN / "factores_B_diario.parquet") -> pd.DataFrame:
    """Devuelve (y si `salida` no es None, escribe) la tabla fecha × zona.

    `tablas` permite pasar DataFrames en memoria (para pruebas) con las claves
    calendario_diario, festivos_locales, openmeteo_diario, aemet_diario,
    eventos_diario y wikipedia_diario; las que falten se leen de data/clean/.
    Rango por defecto: del 2022-01-01 al último día de openmeteo_diario.
    """
    m = leer_mapeo(Path(mapeo)) if not isinstance(mapeo, pd.DataFrame) else mapeo.copy()
    cal = cargar("calendario_diario", tablas)
    om = cargar("openmeteo_diario", tablas)
    ae = cargar("aemet_diario", tablas)
    fl = cargar("festivos_locales", tablas)
    ev = cargar("eventos_diario", tablas)
    wk = cargar("wikipedia_diario", tablas)
    pa = cargar("partidos_diario", tablas)
    tr = cargar("trends_semanal", tablas)

    for nombre, df in [("calendario_diario", cal), ("openmeteo_diario", om), ("aemet_diario", ae),
                       ("festivos_locales", fl), ("eventos_diario", ev), ("wikipedia_diario", wk),
                       ("partidos_diario", pa)]:
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.normalize()

    if "zona_meteo_montana" not in m.columns:
        m["zona_meteo_montana"] = None
    desconocidas = (set(m["zona_meteo"]) | set(m["zona_meteo_montana"].dropna())) - set(om["zona_meteo"])
    if desconocidas:
        raise ValueError(f"zona_meteo sin datos en openmeteo_diario: {sorted(desconocidas)}")
    est = set(m["estacion_aemet"].dropna()) - set(ae["estacion"])
    if est:
        raise ValueError(f"estacion_aemet sin datos en aemet_diario: {sorted(est)}")

    ini = pd.Timestamp(fecha_ini or "2022-01-01")
    fin = pd.Timestamp(fecha_fin) if fecha_fin else om["fecha"].max()
    fechas = pd.date_range(ini, fin, freq="D")
    base = (pd.MultiIndex.from_product([fechas, m["zona_mitma_id"]], names=["fecha", "zona_mitma_id"])
            .to_frame(index=False)
            .merge(m[["zona_mitma_id", "zona_meteo", "zona_meteo_montana", "estacion_aemet"]],
                   on="zona_mitma_id", how="left"))
    n_esperado = len(fechas) * len(m)

    # calendario (por fecha)
    cal_cols = columnas_valor(cal, ["fecha"])
    out = base.merge(cal[["fecha"] + cal_cols], on="fecha", how="left", validate="many_to_one")

    # Open-Meteo (por fecha y zona_meteo)
    om_cols = columnas_valor(om, ["fecha", "zona_meteo"])
    om_r = om[["fecha", "zona_meteo"] + om_cols].rename(columns={c: f"om_{c}" for c in om_cols})
    out = out.merge(om_r, on=["fecha", "zona_meteo"], how="left", validate="many_to_one")
    # Segundo punto (montaña), opcional: decisión del equipo para Cangas de Onís
    # (valle = zona_meteo, montaña = zona_meteo_montana = lagos_enol).
    om_m = (om[["fecha", "zona_meteo"] + om_cols]
            .rename(columns={c: f"om_montana_{c}" for c in om_cols})
            .rename(columns={"zona_meteo": "zona_meteo_montana"}))
    out = out.merge(om_m, on=["fecha", "zona_meteo_montana"], how="left", validate="many_to_one")

    # AEMET (por fecha y estación)
    # sin las horas de cada extremo ni los códigos crudos (se consultan en aemet_diario)
    ae_cols = [c for c in columnas_valor(ae, ["fecha", "estacion"])
               if not c.startswith("hora_") and c != "dir_racha_codigo"]
    ae_r = (ae[["fecha", "estacion"] + ae_cols]
            .rename(columns={c: f"aemet_{c}" for c in ae_cols})
            .rename(columns={"estacion": "estacion_aemet"}))
    out = out.merge(ae_r, on=["fecha", "estacion_aemet"], how="left", validate="many_to_one")

    # concejos de cada zona (para festivos locales y eventos)
    zc = [(z, norm_concejo(c)) for z, cs in zip(m["zona_mitma_id"], m["concejo_eventos"]) for c in lista(cs)]
    zonas_concejo = pd.DataFrame(zc, columns=["zona_mitma_id", "concejo_n"]).drop_duplicates()

    flb = bloque_festivos_locales(fl, zonas_concejo)
    out = out.merge(flb, on=["fecha", "zona_mitma_id"], how="left", validate="one_to_one")
    out["festivo_local"] = out["festivo_local"].astype("boolean").fillna(False).astype(bool)
    if "festivo_local_parcial" in out.columns:
        # sin fiesta local ese día -> False (no aplica); NA solo si el ámbito es dudoso
        out.loc[~out["festivo_local"], "festivo_local_parcial"] = False

    evb = bloque_eventos(ev, zonas_concejo)
    out = out.merge(evb, on=["fecha", "zona_mitma_id"], how="left", validate="one_to_one")
    # sin fila de evento = no hay evento registrado (no es un dato ausente)
    for c in [c for c in evb.columns if c.startswith("ev_")]:
        if c in ("ev_n", "ev_n_verificado"):
            out[c] = out[c].fillna(0).astype(int)
        else:
            out[c] = out[c].astype("boolean").fillna(False).astype(bool)

    # Partidos en casa de Oviedo y Sporting (por fecha, comunes a todas las zonas:
    # atraen público de toda Asturias). Fuera del rango de partidos_diario -> NaN.
    pa_cols = ["partido_oviedo", "partido_sporting", "derbi_asturiano",
               "hora_partido_oviedo", "hora_partido_sporting",
               "categoria_temporada_oviedo", "categoria_temporada_sporting",
               "calendario_confirmado_oviedo", "calendario_confirmado_sporting"]
    pa_cols = [c for c in pa_cols if c in pa.columns]
    out = out.merge(pa[["fecha"] + pa_cols].rename(columns={c: f"futbol_{c}" for c in pa_cols}),
                    on="fecha", how="left", validate="many_to_one")

    # Wikipedia (por fecha, ancho)
    # Decisión del equipo: media de los 7 días anteriores, sin el propio día.
    # Las visitas del mismo día no entran (no se conocen al predecir); están en
    # wikipedia_diario para análisis.
    wk_p = wk.pivot(index="fecha", columns="articulo", values="visitas_media7_ant")
    wk_p.columns = [f"wiki_{c}_media7_ant" for c in wk_p.columns]
    out = out.merge(wk_p.reset_index(), on="fecha", how="left", validate="many_to_one")

    # Trends (decisión del equipo): variable SEMANAL con retraso de una semana,
    # sin pasar a diario. Las semanas de Trends empiezan en domingo; a cada día
    # se le asigna el valor de la semana completa anterior a la suya (conocida
    # el sábado previo). Solo series fiables y semanas no parciales.
    tr = tr[tr["fiable"] & ~tr["is_partial"].astype(bool)].copy()
    tr["semana_inicio"] = pd.to_datetime(tr["semana_inicio"]).dt.normalize()
    assert (tr["semana_inicio"].dt.dayofweek == 6).all(), "las semanas de Trends deberían empezar en domingo"
    tr["col"] = ("trends_" + tr["termino"].map(lambda t: norm_concejo(t).replace(" ", "_"))
                 + "_" + tr["geo"].str.replace("-", "_") + "_sem_ant")
    tr_p = tr.pivot(index="semana_inicio", columns="col", values="valor")
    tr_p.columns.name = None
    dom = out["fecha"] - pd.to_timedelta((out["fecha"].dt.dayofweek + 1) % 7, unit="D")
    out["_semana_ant"] = dom - pd.Timedelta(days=7)
    out = (out.merge(tr_p.reset_index().rename(columns={"semana_inicio": "_semana_ant"}),
                     on="_semana_ant", how="left", validate="many_to_one")
           .drop(columns="_semana_ant"))

    out = out.sort_values(["zona_mitma_id", "fecha"]).reset_index(drop=True)

    # comprobaciones
    assert len(out) == n_esperado, f"filas {len(out)} != {n_esperado} (fechas × zonas)"
    comprobar_sin_duplicados(out, ["fecha", "zona_mitma_id"], "factores_B_diario")
    comprobar_continuidad(out, "fecha", "zona_mitma_id", "factores_B_diario", ini=ini, fin=fin)

    if salida is not None:
        salida = Path(salida)
        salida.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(salida, index=False)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mapeo", default=str(RAIZ / "config" / "mapeo_zonas.csv"))
    ap.add_argument("--desde")
    ap.add_argument("--hasta")
    ap.add_argument("--salida", default=str(CLEAN / "factores_B_diario.parquet"))
    a = ap.parse_args()
    df = unir_B(a.mapeo, fecha_ini=a.desde, fecha_fin=a.hasta, salida=a.salida)
    print(f"{a.salida}: {len(df)} filas, {df['zona_mitma_id'].nunique()} zonas, "
          f"{df['fecha'].min().date()} .. {df['fecha'].max().date()}, {df.shape[1]} columnas")


if __name__ == "__main__":
    main()
