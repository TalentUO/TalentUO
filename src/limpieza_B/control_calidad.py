"""Genera notas/control_calidad_B.md y las gráficas de revisión visual.

    python -X utf8 src/limpieza_B/control_calidad.py

Lee los resúmenes `data/clean/_qc/*.json` (que escribe cada script de
limpieza) y las tablas de `data/clean/`. Recalcula filas, duplicados y NaN
directamente desde los ficheros para no fiarse solo del resumen. Las
gráficas van a `notas/figuras_qc/`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import CLEAN, NOTAS, QC, fechas_ausentes  # noqa: E402

FIG = NOTAS / "figuras_qc"
FIG.mkdir(parents=True, exist_ok=True)

# tabla -> (fichero, claves, columna de fecha, agrupación para fechas ausentes)
TABLAS = {
    "aemet_diario": ("aemet_diario.parquet", ["fecha", "estacion"], "fecha", "estacion"),
    "openmeteo_diario": ("openmeteo_diario.parquet", ["fecha", "zona_meteo"], "fecha", "zona_meteo"),
    "openmeteo_era5_diario": ("openmeteo_era5_diario.parquet", ["fecha", "zona_meteo"], "fecha", "zona_meteo"),
    "openmeteo_prevision_ejemplo": ("openmeteo_prevision_ejemplo.parquet", ["fecha", "zona_meteo"], "fecha", "zona_meteo"),
    "calendario_diario": ("calendario_diario.parquet", ["fecha"], "fecha", None),
    "festivos_locales": ("festivos_locales.parquet", ["fecha", "concejo"], "fecha", "no_continua"),
    "eventos_diario": ("eventos_diario.parquet", ["fecha", "concejo", "evento"], "fecha", "no_continua"),
    "partidos_diario": ("partidos_diario.parquet", ["fecha"], "fecha", None),
    "wikipedia_diario": ("wikipedia_diario.parquet", ["fecha", "articulo"], "fecha", "articulo"),
    "oapn_anual": ("oapn_anual.csv", ["anio"], None, None),
    "trends_semanal": ("trends_semanal.parquet", ["semana_inicio", "termino", "geo"], "semana_inicio", "no_continua"),
    "trends_semanal_no_fiable": ("trends_semanal_no_fiable.parquet", ["semana_inicio", "termino", "geo"], "semana_inicio", "no_continua"),
    "factores_B_ejemplo (prueba unir_B)": ("_prueba/factores_B_ejemplo.parquet", ["fecha", "zona_mitma_id"], "fecha", "zona_mitma_id"),
}


def leer(fichero: str) -> pd.DataFrame:
    p = CLEAN / fichero
    return pd.read_csv(p) if p.suffix == ".csv" else pd.read_parquet(p)


def guardar(fig, nombre: str) -> str:
    fig.tight_layout()
    fig.savefig(FIG / nombre, dpi=110)
    plt.close(fig)
    return f"figuras_qc/{nombre}"


# --------------------------------------------------------------------------
# gráficas por tabla
# --------------------------------------------------------------------------

def graf_aemet(df):
    d = df[df.estacion == "1186P"].set_index("fecha")
    fig, ax = plt.subplots(2, 1, figsize=(11, 5), sharex=True)
    ax[0].plot(d.index, d.tmax_c, lw=.6, label="tmax", color="#c0392b")
    ax[0].plot(d.index, d.tmin_c, lw=.6, label="tmin", color="#2e6fb7")
    ax[0].set_ylabel("°C"); ax[0].legend(loc="upper left", fontsize=8)
    ax[0].set_title("AEMET 1186P Amieva-Panizales (puerta de Picos)")
    ax[1].bar(d.index, d.prec_mm, width=1, color="#2e6fb7")
    aus = d.index[d.fila_ausente_en_fuente]
    ax[1].plot(aus, [0] * len(aus), "x", color="red", ms=4, label="día ausente en la fuente")
    ax[1].set_ylabel("mm/día"); ax[1].legend(loc="upper left", fontsize=8)
    out = [guardar(fig, "aemet_1186P.png")]
    # cobertura por estación y año
    cov = (df.assign(anio=df.fecha.dt.year, ok=~df.tmax_c.isna())
           .pivot_table(index="estacion", columns="anio", values="ok", aggfunc="mean") * 100)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    im = ax.imshow(cov.values, aspect="auto", cmap="viridis", vmin=0, vmax=100)
    ax.set_yticks(range(len(cov)), cov.index); ax.set_xticks(range(len(cov.columns)), cov.columns)
    for i in range(cov.shape[0]):
        for j in range(cov.shape[1]):
            v = cov.values[i, j]
            if pd.notna(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                        color="white" if v < 60 else "black")
    ax.set_title("AEMET: % de días con tmax por estación y año")
    fig.colorbar(im, ax=ax)
    out.append(guardar(fig, "aemet_cobertura_tmax.png"))
    return out


def graf_openmeteo(df):
    d = df[df.zona_meteo == "covadonga"].set_index("fecha")
    era = leer("openmeteo_era5_diario.parquet")
    era = era[era.zona_meteo == "covadonga"].set_index("fecha")
    fig, ax = plt.subplots(2, 1, figsize=(11, 5), sharex=True)
    corte = d.index[~d.es_reanalisis].min()
    for a in ax:
        a.axvspan(d.index.min(), corte, color="0.85", label="es_reanalisis")
    ax[0].plot(d.index, d.tmax_c, lw=.6, color="#c0392b", label="tmax")
    ax[0].plot(d.index, d.tmin_c, lw=.6, color="#2e6fb7", label="tmin")
    ax[0].set_ylabel("°C"); ax[0].legend(loc="upper left", fontsize=8)
    ax[0].set_title("Open-Meteo Historical Forecast, Covadonga (gris = tramo de reanálisis)")
    ax[1].bar(d.index, d.prec_mm, width=1, color="#2e6fb7", label="prec")
    ax[1].set_ylabel("mm/día"); ax[1].legend(loc="upper left", fontsize=8)
    out = [guardar(fig, "openmeteo_covadonga.png")]
    # previsión a 1 día frente a la serie base (desde 2024-01-22)
    p = d.dropna(subset=["prec_mm_prev1"])
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].scatter(p.tmax_c, p.tmax_c_prev1, s=3, alpha=.4)
    ax[0].set_xlabel("tmax Historical Forecast"); ax[0].set_ylabel("tmax_prev1"); ax[0].set_title("Covadonga, tmax")
    ax[1].scatter(d.prec_mm, era.prec_mm.reindex(d.index), s=3, alpha=.4, color="#7d3c98")
    ax[1].set_xlabel("prec Historical Forecast"); ax[1].set_ylabel("prec ERA5 (referencia)")
    ax[1].set_title("Covadonga, precipitación vs ERA5")
    out.append(guardar(fig, "openmeteo_prev1_era5.png"))
    return out


def graf_calendario(df):
    out = []
    m = df.assign(mes=df.fecha.dt.to_period("M"))
    cols = [c for c in ("festivo_ast", "festivo_mad", "festivo_cyl") if c in df.columns]
    if cols:
        fm = m.groupby("mes")[cols].apply(lambda g: g.fillna(False).astype(bool).sum())
        fig, ax = plt.subplots(figsize=(12, 3.8))
        fm.index = fm.index.to_timestamp()
        for i, c in enumerate(cols):
            ax.bar(fm.index + pd.Timedelta(days=8 * i), fm[c], width=8, label=c)
        ax.set_title("Festivos (nacional + autonómico) por mes y comunidad"); ax.legend(fontsize=8)
        out.append(guardar(fig, "calendario_festivos_mes.png"))
    vcols = [c for c in ("vacaciones_escolares_ast", "vacaciones_escolares_mad", "vacaciones_escolares_cyl")
             if c in df.columns]
    lcol = "lagos_regulado" if "lagos_regulado" in df.columns else None
    if vcols or lcol:
        fig, ax = plt.subplots(figsize=(12, 3.8))
        y = 0
        etiquetas = []
        for c in vcols + ([lcol] if lcol else []):
            s = df.set_index("fecha")[c]
            on = s[s.astype("boolean").fillna(False).astype(bool)].index
            nan = s[s.isna()].index
            ax.plot(on, [y] * len(on), "|", ms=10, color="#1e8449")
            ax.plot(nan, [y] * len(nan), "|", ms=10, color="0.8")
            etiquetas.append(c)
            y += 1
        ax.set_yticks(range(len(etiquetas)), etiquetas)
        ax.set_title("Vacaciones escolares y acceso regulado a Lagos (verde = sí, gris = sin dato)")
        out.append(guardar(fig, "calendario_vacaciones_lagos.png"))
    return out


def graf_eventos(df):
    m = (df.assign(mes=df.fecha.dt.to_period("M").dt.to_timestamp())
         .pivot_table(index="mes", columns="tipo", values="evento", aggfunc="count", fill_value=0))
    fig, ax = plt.subplots(figsize=(12, 4))
    m.plot(kind="bar", stacked=True, ax=ax, width=.9)
    ax.set_xticklabels([d.strftime("%Y-%m") if d.month in (1, 7) else "" for d in m.index], rotation=0, fontsize=7)
    ax.set_title("Días-evento por mes y tipo (cruceros 2025-26 = previsión)"); ax.legend(fontsize=7, ncol=4)
    out = [guardar(fig, "eventos_mes_tipo.png")]
    e = df.drop_duplicates(["evento", "fecha_ini"])
    t = e.pivot_table(index=e.fecha.dt.year, columns="estado", values="evento", aggfunc="count", fill_value=0)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    t.plot(kind="bar", stacked=True, ax=ax, color={"verificado": "#1e8449", "probable": "#d4ac0d",
                                                     "no_encontrado": "#c0392b"})
    ax.set_title("Eventos (ediciones) por año y estado"); ax.set_xlabel("")
    out.append(guardar(fig, "eventos_estado_anio.png"))
    return out


def graf_wikipedia(df):
    arts = [a for a in ("lagos_de_covadonga", "covadonga", "cangas_de_onis", "picos_de_europa")
            if a in set(df.articulo)]
    fig, ax = plt.subplots(figsize=(11, 4))
    for a in arts:
        d = df[df.articulo == a].set_index("fecha").visitas
        ax.plot(d.index, d.rolling(7, min_periods=1).mean(), lw=.8, label=a)
    an = df[df.posible_anomalia]
    ax.plot(an.fecha, an.visitas, "rv", ms=6, label="posible_anomalia")
    ax.set_yscale("log"); ax.legend(fontsize=8)
    ax.set_title("Wikipedia (es): visitas diarias, media móvil 7 días (escala log)")
    return [guardar(fig, "wikipedia_series.png")]


def graf_trends(df):
    fig, ax = plt.subplots(figsize=(11, 3.8))
    for (t, g), d in df.groupby(["termino", "geo"]):
        ax.plot(d.semana_inicio, d.valor, lw=.8, label=f"{t} ({g})")
    d0 = df.drop_duplicates("semana_inicio")
    ax.plot(d0.semana_inicio, d0.valor_ancla, lw=.8, ls="--", color="k", label="ancla cabrales")
    ax.legend(fontsize=8); ax.set_title("Google Trends semanal (series fiables, ancla 'cabrales')")
    return [guardar(fig, "trends_fiables.png")]


GRAFICAS = {"aemet_diario": graf_aemet, "openmeteo_diario": graf_openmeteo,
            "calendario_diario": graf_calendario, "eventos_diario": graf_eventos,
            "wikipedia_diario": graf_wikipedia, "trends_semanal": graf_trends}


# --------------------------------------------------------------------------
# informe
# --------------------------------------------------------------------------

def _recortar(txt: str, n: int = 3000) -> str:
    return txt if len(txt) <= n else txt[:n] + "\n… (recortado; completo en el JSON)"


def bloque_tabla(nombre, fichero, claves, col_fecha, grupo) -> list[str]:
    ruta = CLEAN / fichero
    L = [f"## {nombre}", ""]
    if not ruta.exists():
        return L + [f"**NO EXISTE** `data/clean/{fichero}`.", ""]
    df = leer(fichero)
    if col_fecha:
        df[col_fecha] = pd.to_datetime(df[col_fecha])
    dup = int(df.duplicated(subset=claves).sum())
    filas = f"{len(df):,}".replace(",", ".")
    L.append(f"`data/clean/{fichero}` — **{filas} filas**, {df.shape[1]} columnas; "
             f"clave `{', '.join(claves)}`; duplicados por clave: **{dup}**.")
    if col_fecha:
        L.append(f"Rango: {df[col_fecha].min().date()} → {df[col_fecha].max().date()}.")
        if grupo == "no_continua":
            L.append("Fechas ausentes: no aplica (tabla de sucesos, no serie continua).")
        elif grupo is None:
            L.append(f"Fechas ausentes en el rango: **{len(fechas_ausentes(df[col_fecha]))}**.")
        else:
            aus = {k: len(fechas_ausentes(g[col_fecha])) for k, g in df.groupby(grupo)}
            con = {k: v for k, v in aus.items() if v}
            L.append(f"Fechas ausentes por `{grupo}` (dentro del rango de cada uno): "
                     + (", ".join(f"{k}: {v}" for k, v in con.items()) if con else "**0 en todos**") + ".")
    nan = (df.isna().mean() * 100).round(2)
    nan = nan[nan > 0].sort_values(ascending=False)
    if len(nan):
        L += ["", "| Columna con NaN | % NaN |", "|---|---|"]
        L += [f"| `{c}` | {v:.2f} |" for c, v in nan.items()]
    else:
        L.append("Sin NaN en ninguna columna.")
    qc = QC / f"{nombre}.json"
    if qc.exists():
        extra = {k: v for k, v in json.loads(qc.read_text(encoding="utf-8")).items()
                 if k not in ("tabla", "filas", "columnas", "claves", "duplicados_por_clave", "nan_pct",
                              "fecha_min", "fecha_max", "fechas_ausentes_global")}
        if extra:
            L += ["", "<details><summary>Comprobaciones específicas del script (data/clean/_qc/"
                  f"{nombre}.json)</summary>", "", "```json",
                  _recortar(json.dumps(extra, ensure_ascii=False, indent=1)), "```", "</details>"]
    if nombre in GRAFICAS:
        L.append("")
        for f in GRAFICAS[nombre](df):
            L.append(f"![{nombre}]({f})")
    return L + [""]


def main():
    L = ["# Control de calidad de la parte B (limpieza, fase 2)", "",
         "Generado por `python -X utf8 src/limpieza_B/control_calidad.py` (no editar a mano). "
         "Cada script de limpieza falla si encuentra duplicados por clave, fechas ausentes en "
         "series que deben ser continuas o valores fuera de rango; este informe recalcula las cifras "
         "desde las tablas de `data/clean/`. Significado de cada columna: `notas/diccionario_B.md`.", "",
         "## Validaciones manuales", "",
         "- Calendario: muestra aleatoria contrastada contra los PDF originales y comprobación de "
         "Semana Santa en `notas/fuentes/calendarios/validacion_calendario.md` (resumen abajo).",
         "- Unión: `src/limpieza_B/test_unir_B.py` (datos sintéticos) y prueba con las tablas reales "
         "y `config/mapeo_zonas_ejemplo.csv` (IDs ficticios; tabla `factores_B_ejemplo` abajo).", ""]
    val = NOTAS / "fuentes" / "calendarios" / "validacion_calendario.md"
    if val.exists():
        txt = val.read_text(encoding="utf-8")
        res = [l for l in txt.splitlines() if l.lower().startswith(("**resultado", "resultado"))]
        L += [f"Resumen de la validación del calendario: {res[0] if res else '(ver el fichero)'}", ""]
    L += ["## Hallazgos de la limpieza (revisados a mano)", "",
          "- **La muestra de fiestas locales de la auditoría (`notas/historico/auditoria_fase_B.md` §3.3) no es fiable.** "
          "El `.txt` de pdftotext desalinea las filas de la tabla del BOPA. Ejemplo: el texto pone "
          "«Cangas de Onís 16 de mayo San Isidro» (2022), pero la imagen del PDF da 13 de junio "
          "(San Antonio) y 25 de julio (Pastor). Comprobado renderizando la página. "
          "`festivos_locales` está validada contra la imagen del PDF, no contra el `.txt`.",
          "- **Erratas en el BOPA**, conservadas y marcadas con `dia_semana_coherente=False`: "
          "Grado 2022-07-26 («lunes», pero fue martes) y Pravia 2024-09-06 («miércoles», pero fue viernes).",
          "- **El tramo de reanálisis de Open-Meteo también es más frío en temperatura**: en Covadonga, la "
          "Tmax media de julio y agosto es 22,5 °C en 2022 frente a 24,8–25,8 °C en 2023–2026. En AEMET "
          "1186P, el verano de 2022 es el más caluroso (26,5 °C). Ver la primera gráfica de Open-Meteo.",
          "- El pico de 120 mm del 2026-10-07 en Covadonga es real: AEMET 1186P registra 57 mm y la "
          "previsión a 1 día daba 78 mm.",
          "- Datos imposibles en la fuente, puestos a NaN y marcados: 206 valores negativos de `pintMax` "
          "en AEMET, 5 horas de racha imposibles y 1 hora de precipitación negativa en Previous Runs "
          "(2025-06-15, en 3 zonas).", ""]
    for nombre, (fichero, claves, col_fecha, grupo) in TABLAS.items():
        L += bloque_tabla(nombre, fichero, claves, col_fecha, grupo)
    (NOTAS / "control_calidad_B.md").write_text("\n".join(L), encoding="utf-8")
    print(f"notas/control_calidad_B.md escrito; figuras en {FIG}")


if __name__ == "__main__":
    main()
