"""Tablas de notas/resultados_reales.md a partir de las salidas del modelo.

    python -X utf8 scripts/tablas_resultados_reales.py > salidas/tablas_resultados_reales.md

Lee solo salidas/backtest.parquet, salidas/metricas.json y salidas/explicacion_factores.json
(experimento base, algoritmo ganador) y los datos limpios de data/clean/ para el signo de los
factores. No entrena nada.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SAL = RAIZ / "salidas"
CLEAN = RAIZ / "data" / "clean"
PICOS = "33012"

m = json.loads((SAL / "metricas.json").read_text(encoding="utf-8"))
assert m["sintetico"] is False, "metricas.json es sintético"
ALG = m["algoritmo"]
bt = pd.read_parquet(SAL / "backtest.parquet")
assert not bt["sintetico"].any(), "backtest.parquet tiene filas sintéticas"
NOMBRES = {f["zona_mitma_id"]: f["nombre_zona"].split(" (")[0] for f in m["fiabilidad"]}


def pct(v, dec=1):
    return "—" if v is None or not np.isfinite(v) else f"{v * 100:.{dec}f}".replace(".", ",")


def met(g: pd.DataFrame, pred: str, color: str) -> dict:
    g = g[g[pred].notna()]
    obs_r, pred_r = g["color_obs"] == "rojo", g[color] == "rojo"
    tp = int((obs_r & pred_r).sum())
    return {"n": len(g), "wape": (g["visitas_obs"] - g[pred]).abs().sum() / g["visitas_obs"].sum(),
            "sesgo": g[pred].sum() / g["visitas_obs"].sum() - 1,
            "acierto": (g["color_obs"] == g[color]).mean(), "rojos": int(obs_r.sum()),
            "recall": tp / obs_r.sum() if obs_r.sum() else np.nan,
            "precision": tp / pred_r.sum() if pred_r.sum() else np.nan}


def tabla_bzh(b: pd.DataFrame) -> None:
    print("| bloque | zona | modelo | n | WAPE modelo | WAPE B0 | WAPE B1 | sesgo modelo | acierto color modelo / B1 "
          "| rojos obs. | recall rojo modelo / B1 | precisión rojo modelo / B1 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for (bl, z, mod), g in b.groupby(["bloque", "zona_mitma_id", "grupo"], sort=True):
        a, b0, b1 = met(g, "visitas_pred", "color_pred"), met(g, "b0_visitas", "color_b0"), met(g, "b1_visitas", "color_b1")
        print(f"| {bl} | {NOMBRES[z]} | {mod} | {a['n']} | {pct(a['wape'])} | {pct(b0['wape'])} | {pct(b1['wape'])} "
              f"| {pct(a['sesgo'])} | {pct(a['acierto'])} / {pct(b1['acierto'])} | {a['rojos']} "
              f"| {pct(a['recall'])} / {pct(b1['recall'])} | {pct(a['precision'])} / {pct(b1['precision'])} |")


base = bt[(bt["experimento"] == "base") & (bt["algoritmo"] == ALG)].copy()
base["grupo"] = np.where(base["modelo"] == "largo", "largo (8+)",
                         np.where(base["horizonte"] <= 3, "corto h1-3", "corto h4-7"))

print(f"# Tablas generadas (algoritmo {ALG}, experimento base)\n")
print("Fuente: `salidas/backtest.parquet`. WAPE y sesgo en visitantes (sesgo = previsto / observado − 1); "
      "color frente al día normal de referencia (2024). B0 = día normal del bloque; B1 = mismo día de la "
      "semana 364 días antes (solo referencia). Métricas en %.\n")
print("## Bloque × zona × horizonte\n")
tabla_bzh(base)

print("\n## Bloque × modelo (todas las zonas)\n")
print("| bloque | modelo | WAPE modelo | WAPE B0 | WAPE B1 | sesgo modelo | sesgo B0 | recall rojo modelo / B1 | precisión rojo modelo / B1 |")
print("|---|---|---|---|---|---|---|---|---|")
for (bl, mod), g in base.groupby(["bloque", "modelo"]):
    a, b0, b1 = met(g, "visitas_pred", "color_pred"), met(g, "b0_visitas", "color_b0"), met(g, "b1_visitas", "color_b1")
    print(f"| {bl} | {mod} | {pct(a['wape'])} | {pct(b0['wape'])} | {pct(b1['wape'])} | {pct(a['sesgo'])} "
          f"| {pct(b0['sesgo'])} | {pct(a['recall'])} / {pct(b1['recall'])} | {pct(a['precision'])} / {pct(b1['precision'])} |")

print("\n## Factores: media de |SHAP| fuera de muestra (escala log)\n")
fx = [c for c in base.columns if c.startswith("fx_")]
filas = {"global, largo": base[base["modelo"] == "largo"], "global, corto h=1": base[base["horizonte"] == 1].query("modelo == 'corto'"),
         "Picos, largo": base[(base["modelo"] == "largo") & (base["zona_mitma_id"] == PICOS)],
         "Picos, corto h=1": base[(base["modelo"] == "corto") & (base["horizonte"] == 1) & (base["zona_mitma_id"] == PICOS)]}
t = pd.DataFrame({k: v[fx].abs().mean() for k, v in filas.items()})
t.index = [i[3:] for i in t.index]
t = t.sort_values("Picos, largo", ascending=False)
print("| factor | " + " | ".join(t.columns) + " |")
print("|---|" + "---|" * len(t.columns))
for f, r in t.iterrows():
    print(f"| {f} | " + " | ".join("—" if not np.isfinite(v) else f"{v:.3f}".replace(".", ",") for v in r) + " |")

print("\n## Signo de los factores en los Picos (SHAP medio fuera de muestra, en % sobre el día medio del modelo)\n")
cal = pd.read_parquet(CLEAN / "calendario_diario.parquet")
cal["fecha"] = pd.to_datetime(cal["fecha"]).dt.normalize()
p = base[(base["modelo"] == "largo") & (base["zona_mitma_id"] == PICOS)].merge(cal, on="fecha", how="left")
print("| factor | condición | n días | efecto medio con la condición | sin ella |")
print("|---|---|---|---|---|")
for lab, mask, col in [
        ("Puente o festivo en Asturias", p["puente_ast"] | p["festivo_ast"] | p["finde_largo_ast"], "fx_Puente o festivo en Asturias"),
        ("Festivo en origen", (p["festivo_mad"] | p["festivo_cyl"]) & ~p["festivo_ast"], "fx_Festivo en origen (Madrid o Castilla y León)"),
        ("Vacaciones escolares", p["vacaciones_escolares_mad"].fillna(False).astype(bool), "fx_Vacaciones escolares"),
        ("Acceso regulado a los Lagos", p["lagos_regulado"].fillna(False).astype(bool), "fx_Acceso regulado a los Lagos")]:
    a, b = p.loc[mask, col].mean(), p.loc[~mask, col].mean()
    print(f"| {lab} | {'vacaciones escolares de Madrid' if lab == 'Vacaciones escolares' else 'sí'} | {int(mask.sum())} "
          f"| {pct(np.exp(a) - 1)} | {pct(np.exp(b) - 1)} |")
ep = p.groupby(p["fecha"].dt.month)["fx_Época del año"].mean()
print("\nÉpoca del año, Picos, largo plazo (efecto medio por mes, %): "
      + ", ".join(f"{k}: {pct(np.exp(v) - 1, 0)}" for k, v in ep.items()))

om = pd.read_parquet(CLEAN / "openmeteo_diario.parquet")
om = om[om["zona_meteo"] == "cangas_de_onis"][["fecha", "prec_mm_prev1", "tmax_c_prev1"]]
om["fecha"] = pd.to_datetime(om["fecha"]).dt.normalize()
q = base[(base["modelo"] == "corto") & (base["horizonte"] == 1) & (base["zona_mitma_id"] == PICOS)].merge(om, on="fecha", how="left")
q = q[q["prec_mm_prev1"].notna() & q["fx_Tiempo en el valle"].notna()]
q["lluvia"] = pd.cut(q["prec_mm_prev1"], [-0.1, 0.5, 5, 15, 1000], labels=["< 0,5 mm", "0,5-5 mm", "5-15 mm", "> 15 mm"])
r = q.groupby("lluvia", observed=True)["fx_Tiempo en el valle"].agg(["mean", "count"])
print("\nTiempo en el valle, Picos, corto plazo h=1, por lluvia prevista a 1 día (Open-Meteo, `prec_mm_prev1`): "
      + "; ".join(f"{k}: {pct(np.exp(v['mean']) - 1)} % (n={int(v['count'])})" for k, v in r.iterrows())
      + f". Correlación SHAP-lluvia {q['fx_Tiempo en el valle'].corr(q['prec_mm_prev1']):.2f}; "
        f"SHAP-tmax {q['fx_Tiempo en el valle'].corr(q['tmax_c_prev1']):.2f}.")
g1 = base[(base["modelo"] == "corto") & (base["horizonte"] == 1)]
ia = g1.groupby(g1["fecha"].dt.year)["fx_Interés en internet"].mean()
print("\nInterés en internet, global, corto h=1 (efecto medio por año, %): "
      + ", ".join(f"{k}: {pct(np.exp(v) - 1)}" for k, v in ia.items())
      + f". Correlación con «Época del año»: {g1['fx_Interés en internet'].corr(g1['fx_Época del año']):.2f}.")

print("\n## Cobertura de los intervalos p10-p90 (`metricas.json → fiabilidad`)\n")
f = pd.DataFrame(m["fiabilidad"])
print("| zona | mínima | media | máxima |")
print("|---|---|---|---|")
for z, g in f.groupby("zona_mitma_id"):
    print(f"| {NOMBRES[z]} | {pct(g['cobertura'].min())} | {pct(g['cobertura'].mean())} | {pct(g['cobertura'].max())} |")
print(f"| todas (40 combinaciones zona × horizonte) | {pct(f['cobertura'].min())} | {pct(f['cobertura'].mean())} "
      f"| {pct(f['cobertura'].max())} |")
print(f"\nCombinaciones con cobertura ≥ 80 %: {int((f['cobertura'] >= 0.8).sum())} de {len(f)}.")

print("\n## Experimentos de sensibilidad (`metricas.json → tablas.global`, solo el modelo)\n")
g = pd.DataFrame(m["tablas"]["global"]).query("metodo == 'modelo'")
print("| experimento | modelo | WAPE | acierto color | recall rojo | precisión rojo |")
print("|---|---|---|---|---|---|")
for _, r in g.iterrows():
    print(f"| {r['experimento']} | {r['modelo']} | {pct(r['wape'])} | {pct(r['acierto_color'])} | {pct(r['recall_rojo'])} "
          f"| {pct(r['precision_rojo'])} |")
