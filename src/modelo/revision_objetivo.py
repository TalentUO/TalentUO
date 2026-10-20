"""Revisión rápida de data/clean/objetivo_diario.parquet -> notas/historico/revision_objetivo.md + notas/historico/figuras_objetivo/*.png

Uso: python -X utf8 src/modelo/revision_objetivo.py
Solo lee data/clean/objetivo_diario.parquet, calendario_diario.parquet y el mapeo de zonas. No modifica ningún dato.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import CLEAN, NOTAS, RAIZ  # noqa: E402

PICOS = "33012"
# Paleta categórica validada (scripts/validate_palette.py, modo claro): ranuras 1-5 en orden fijo, una por zona.
COLOR = {"33012": "#2a78d6", "33036": "#eb6834", "33056": "#1baf7a", "33024": "#eda100", "33044": "#e87ba4"}
SUPERFICIE, TEXTO, TEXTO2 = "#fcfcfb", "#0b0b0b", "#52514e"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def tabla_md(df: pd.DataFrame, fmt: str = "{:,.0f}") -> str:
    cab = "| " + " | ".join(str(c) for c in df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    filas = ""
    for _, r in df.iterrows():
        celdas = [(fmt.format(v).replace(",", " ") if isinstance(v, (float, np.floating)) and not pd.isna(v) else
                   ("" if (isinstance(v, float) and pd.isna(v)) else str(v))) for v in r]
        filas += "| " + " | ".join(celdas) + " |\n"
    return cab + filas


def main() -> None:
    o = pd.read_parquet(CLEAN / "objetivo_diario.parquet")
    cal = pd.read_parquet(CLEAN / "calendario_diario.parquet")
    mapeo = pd.read_csv(RAIZ / "config" / "mapeo_zonas.csv", dtype=str, keep_default_na=False)
    nombre = {r.zona_mitma_id: r.nombre.split(" (")[0] for r in mapeo.itertuples()}
    cal["fecha"] = cal["fecha"].astype("datetime64[us]")
    o = o.merge(cal[["fecha", "dia_semana", "festivo_ast", "es_fin_de_semana", "puente_ast", "finde_largo_ast", "semana_santa"]],
                on="fecha", how="left", validate="many_to_one")
    V = ["llegadas_total", "llegadas_ocio", "llegadas_desde_asturias", "llegadas_resto_espana",
         "llegadas_total_desde_asturias", "llegadas_total_resto_espana", "pernoctaciones_no_residentes"]
    figs = NOTAS / "historico" / "figuras_objetivo"
    figs.mkdir(exist_ok=True)

    # 1) Serie diaria por zona (una escala por zona: pequeños múltiplos, sin doble eje)
    orden = [PICOS, "33036", "33056", "33024", "33044"]
    fig, axs = plt.subplots(len(orden), 1, figsize=(11, 9.5), sharex=True, facecolor=SUPERFICIE)
    anom = o.loc[o.calidad == "anomalia_mitma", "fecha"].unique()
    for ax, z in zip(axs, orden):
        d = o[o.zona_mitma_id == z].sort_values("fecha")
        ax.set_facecolor(SUPERFICIE)
        ax.plot(d["fecha"], d["llegadas_ocio"], color=COLOR[z], lw=1.1)       # NaN = hueco en la línea (no 0)
        for a in anom:
            ax.axvspan(a - pd.Timedelta(hours=12), a + pd.Timedelta(hours=12), color="#c3c2b7", alpha=0.6, lw=0)
        sd = d.loc[d.calidad == "sin_dato_mitma", "fecha"]
        ax.plot(sd, np.zeros(len(sd)), "|", color=TEXTO2, ms=8, lw=0)
        ax.set_ylim(bottom=0)
        ax.set_title(f"{nombre[z]} ({z})", loc="left", fontsize=10.5, color=TEXTO, fontweight="bold")
        ax.tick_params(colors=TEXTO2, labelsize=8.5)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", " ")))
        ax.grid(axis="y", color="#e6e5e0", lw=0.6)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#c3c2b7")
    axs[0].text(1, 1.22, "marcas | = día sin dato MITMA (NaN); franja gris = anomalía DANA (29-31 oct 2024)", transform=axs[0].transAxes,
                ha="right", fontsize=8.5, color=TEXTO2)
    fig.suptitle("Llegadas de ocio por día y zona (MITMA, 2022-01 a 2025-06)", x=0.01, ha="left", fontsize=12.5, color=TEXTO)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(figs / "serie_llegadas_ocio.png", dpi=110, facecolor=SUPERFICIE)
    plt.close(fig)

    # 2) Día normal: mediana por día de la semana de 2024, sin julio, agosto ni festivos (solo días `completa`)
    n = o[(o.fecha.dt.year == 2024) & ~o.fecha.dt.month.isin([7, 8]) & ~o.festivo_ast & (o.calidad == "completa")]
    normal = n.pivot_table(index="zona_mitma_id", columns="dia_semana", values="llegadas_ocio", aggfunc="median")
    normal.columns = [DIAS[int(c)] for c in normal.columns]
    normal = normal.reindex(orden)
    normal.insert(0, "zona", [nombre[z] for z in normal.index])
    ndias = n[n.zona_mitma_id == PICOS].groupby("dia_semana").size()

    # 3) Los 20 días más altos de la zona de los Picos
    p = o[(o.zona_mitma_id == PICOS) & (o.calidad != "sin_dato_mitma")].nlargest(20, "llegadas_ocio").copy()
    p["etiqueta"] = p.apply(lambda r: ", ".join(x for x in [
        "agosto" if r.fecha.month == 8 else "", "Semana Santa" if r.semana_santa else "",
        "festivo AST" if r.festivo_ast else "", "puente" if r.puente_ast else "",
        "finde largo" if r.finde_largo_ast else "", "fin de semana" if r.es_fin_de_semana else "",
        "ANOMALÍA" if r.calidad == "anomalia_mitma" else ""] if x), axis=1)
    top = pd.DataFrame({"#": range(1, 21), "fecha": p.fecha.dt.strftime("%Y-%m-%d").values,
                        "día": [DIAS[int(i)] for i in p.dia_semana], "llegadas_ocio": p.llegadas_ocio.values,
                        "desde Asturias": p.llegadas_desde_asturias.values, "resto de España": p.llegadas_resto_espana.values,
                        "qué es": p.etiqueta.values})
    cuenta = pd.Series({"agosto": int((p.fecha.dt.month == 8).sum()), "Semana Santa": int(p.semana_santa.sum()),
                        "festivo": int(p.festivo_ast.sum()), "puente o finde largo": int((p.puente_ast | p.finde_largo_ast).sum()),
                        "sábado/domingo": int(p.es_fin_de_semana.sum())})

    # 4) Días sin dato = NaN y no 0
    sd = o[o.calidad == "sin_dato_mitma"]
    ok = o[o.calidad != "sin_dato_mitma"]
    dias_sd = sorted({d.strftime("%Y-%m-%d") for d in sd.fecha})
    nan_ok = sd[V].isna().all().all()
    ceros_sd = int((sd[V] == 0).sum().sum())
    nan_en_datos = int(ok[V].isna().sum().sum())
    ceros_reales = int((ok[V] == 0).sum().sum())

    # 5) Reparto en los Picos
    pi = o[(o.zona_mitma_id == PICOS) & (o.calidad == "completa")].copy()
    pi["anio"] = pi.fecha.dt.year
    por_anio = pi.groupby("anio").agg(dias=("fecha", "size"), ocio=("llegadas_ocio", "mean"), ast=("llegadas_desde_asturias", "mean"),
                                      resto=("llegadas_resto_espana", "mean"), tot_ast=("llegadas_total_desde_asturias", "mean"),
                                      tot_resto=("llegadas_total_resto_espana", "mean"), pern=("pernoctaciones_no_residentes", "mean"))
    por_anio["% Asturias (ocio)"] = 100 * por_anio.ast / (por_anio.ast + por_anio.resto)
    por_anio["% resto de España (ocio)"] = 100 - por_anio["% Asturias (ocio)"]
    pi24 = pi[pi.anio == 2024]
    por_mes = pi24.groupby(pi24.fecha.dt.month).agg(ocio=("llegadas_ocio", "mean"), ast=("llegadas_desde_asturias", "mean"),
                                                      resto=("llegadas_resto_espana", "mean"), pern=("pernoctaciones_no_residentes", "mean"))
    por_mes["% Asturias (ocio)"] = 100 * por_mes.ast / (por_mes.ast + por_mes.resto)
    por_mes["pernoctantes ÷ llegadas de ocio"] = por_mes.pern / por_mes.ocio
    por_mes.index = [MESES[i - 1] for i in por_mes.index]

    # 6) Rarezas
    rarezas = []
    for z in orden:
        d = ok[ok.zona_mitma_id == z]
        i = d["pernoctaciones_no_residentes"].idxmax()
        n = lambda v: f"{v:,.0f}".replace(",", " ")   # separador de miles (solo en los números)
        rarezas.append(f"- {nombre[z]}: llegadas_ocio diarias entre {n(d.llegadas_ocio.min())} y {n(d.llegadas_ocio.max())}; "
                       f"pernoctaciones_no_residentes máx. {n(d.loc[i, 'pernoctaciones_no_residentes'])} ({d.loc[i, 'fecha']:%Y-%m-%d}).")
    ratio = (o.llegadas_resto_espana / o.llegadas_total_resto_espana)
    ratio_txt = f"{ratio.min():.3f}–{ratio.max():.3f}"

    md = f"""# Revisión rápida del objetivo (`data/clean/objetivo_diario.parquet`)

Generado con `src/modelo/revision_objetivo.py`. Periodo 2022-01-01 a 2025-06-30, 5 zonas MITMA (una por zona del mapeo). Es una revisión rápida, no el análisis completo.

## 1. Serie diaria de llegadas de ocio

![Llegadas de ocio por día y zona](figuras_objetivo/serie_llegadas_ocio.png)

Una escala por zona (las zonas no son comparables en magnitud). Los huecos de la línea son días sin dato (NaN, nunca 0); las marcas `|` en la base los señalan; la franja gris es la anomalía de la DANA.

## 2. «Día normal» por zona

Mediana de `llegadas_ocio` por día de la semana, **solo 2024, sin julio, agosto ni festivos de Asturias** y solo días con calidad `completa`. Días que entran en cada mediana (zona de los Picos): {", ".join(f"{DIAS[int(k)]} {v}" for k, v in ndias.items())}.

{tabla_md(normal.reset_index(drop=True))}
## 3. Los 20 días más altos de la zona de los Picos (Cangas de Onís, `{PICOS}`)

{tabla_md(top)}
Resumen de esos 20 días: {", ".join(f"{k} {v}" for k, v in cuenta.items())}. (Las etiquetas salen del calendario de la parte B: `semana_santa`, `festivo_ast`, `puente_ast`, `finde_largo_ast`, `es_fin_de_semana`.)

## 4. Días sin dato: NaN y no 0

- Días `sin_dato_mitma` ({len(dias_sd)}): {", ".join(dias_sd)}.
- En esos días las 7 columnas de valores son NaN en las 5 zonas: **{"sí" if nan_en_datos == 0 and nan_ok else "NO"}** · ceros en esos días: **{ceros_sd}** · NaN en días con dato: **{nan_en_datos}**.
- Ceros reales (días con fichero y zona sin viajes): {ceros_reales}.
- `anomalia_mitma` (29-31 oct 2024, se conservan los valores): {int((o.calidad == "anomalia_mitma").sum())} filas.
- **Atención:** `config/mitma_calidad.yaml` marca como `sin_dato_mitma` los días 2024-04-04, 2024-04-19 y 2024-11-11, **aunque el portal sí los publicó** (están en los ficheros descargados). Quedan en NaN por esa configuración. Además faltan en el portal 2024-11-09 y 2024-11-26 (no están en la lista oficial; también quedan NaN). Ver `notas/fuentes/mitma/cobertura_mitma.md`.

## 5. Quién llega a los Picos (Cangas de Onís, días `completa`)

Media diaria por año. Asturias frente al resto de España se calcula sobre llegadas de **ocio** (decisión del equipo); los no residentes en España no aparecen en el MITMA.

{tabla_md(por_anio.reset_index().assign(anio=lambda t: t["anio"].astype(str)).rename(columns={"anio": "año","dias": "días", "ocio": "llegadas_ocio", "ast": "desde Asturias", "resto": "resto de España", "tot_ast": "total desde Asturias", "tot_resto": "total resto de España", "pern": "pernoctaciones no residentes"}))}
**Excursionistas frente a pernoctantes (indicativo).** El MITMA no da esa partición directamente. Se comparan dos magnitudes distintas, no comparables como partes de un todo: personas que pernoctan en la zona y viven fuera (`pernoctaciones_no_residentes`, un stock diario) y llegadas de ocio (un flujo). Media diaria de 2024 por mes:

{tabla_md(por_mes.reset_index().rename(columns={"index": "mes", "ocio": "llegadas_ocio", "ast": "desde Asturias", "resto": "resto de España", "pern": "pernoctantes no residentes"}).drop(columns=["% Asturias (ocio)"]).assign(**{"% Asturias (ocio)": por_mes["% Asturias (ocio)"].values.round(1), "pernoctantes ÷ llegadas de ocio": por_mes["pernoctantes ÷ llegadas de ocio"].values.round(2)}), fmt="{:,.1f}")}
En los Picos el cociente va de {por_mes["pernoctantes ÷ llegadas de ocio"].min():.2f} (invierno) a {por_mes["pernoctantes ÷ llegadas de ocio"].max():.2f} (verano). No es «la proporción de pernoctantes»: el numerador cuenta personas que duermen en la zona (incluidos asturianos de otras zonas y estancias de varios días) y el denominador, llegadas de un día. **NO VERIFICADO** que esta comparación sirva para separar excursionistas de pernoctantes; hace falta una definición de la sesión del modelo. Nota: 2025 solo tiene enero-junio, así que su reparto (más peso de Asturias) no es comparable con los años completos.

## 6. Cosas raras / a vigilar

{chr(10).join(rarezas)}
- `llegadas_resto_espana / llegadas_total_resto_espana` (todas las zonas y días): {ratio_txt}. Los visitantes de fuera de Asturias casi siempre cuentan como ocio por construcción del MITMA (su «actividad frecuente» es la de su residencia), así que ambos repartos son casi iguales para el resto de España.
- `pernoctaciones_no_residentes` cuenta cualquier persona cuya zona de residencia es distinta de la de pernoctación, incluidos asturianos de otras zonas: no es «turistas».
- El MITMA solo cubre residentes en España y la unidad mínima es el municipio: Covadonga y Lagos no se pueden separar de Cangas de Onís.
"""
    (NOTAS / "historico" / "revision_objetivo.md").write_text(md, encoding="utf-8")
    print("notas/historico/revision_objetivo.md escrito;", len(md), "caracteres")


if __name__ == "__main__":
    main()
