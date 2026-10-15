"""Comparación LightGBM frente a XGBoost en la validación por bloques
(experimento base) y elección del algoritmo con la regla fijada de antemano.

Regla (notas/modelo.md, fijada el 2026-10-15, antes de ver datos reales):
1. Gana el de mayor recall de días rojos en los bloques de verano (2023-S2 y 2024-S2).
2. Si la diferencia es menor de 3 puntos, el de menor WAPE medio.
3. Si también la diferencia de WAPE es menor de 1 punto, LightGBM.

Cómo se calcula cada cifra (también fijado ahora):
- recall de verano = media, entre el modelo de corto plazo (todas las filas de
  h = 1..7) y el de largo plazo, del recall de días rojos agregado sobre los dos
  bloques de verano.
- WAPE medio = media del WAPE de los 4 bloques × 2 modelos (corto y largo).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

import metricas as MT
from util import AVISO_SINTETICO, NOTAS, SALIDAS, cfg, guardar_json, mae, metricas_color, wape

MARCA_INI = "<!-- comparacion_algoritmos:inicio (generado por src/modelo/comparacion.py) -->"
MARCA_FIN = "<!-- comparacion_algoritmos:fin -->"


def _metricas(g: pd.DataFrame) -> dict:
    mc = metricas_color(g["color_obs"], g["color_pred"])
    return {"n": int(len(g)), "wape": wape(g["visitas_obs"], g["visitas_pred"]),
            "mae": mae(g["visitas_obs"], g["visitas_pred"]), "acierto_color": mc["acierto_color"],
            "rojos_obs": mc["rojos_obs"], "recall_rojo": mc["recall_rojo"], "precision_rojo": mc["precision_rojo"]}


def tabla(bt: pd.DataFrame) -> pd.DataFrame:
    b = bt[bt["experimento"] == "base"].assign(horizonte_txt=lambda d: d["horizonte"].map(MT.etiqueta_horizonte))
    filas = []
    for (alg, bl, mod, h), g in b.groupby(["algoritmo", "bloque", "modelo", "horizonte_txt"]):
        filas.append({"algoritmo": alg, "bloque": bl, "modelo": mod, "horizonte_txt": h, **_metricas(g),
                      # tiempo del modelo que produce ese horizonte (el de corto plazo es uno para h = 1..7)
                      "segundos_entrenamiento": float(g["segundos_entrenamiento"].iloc[0])})
    return pd.DataFrame(filas)


def criterios(bt: pd.DataFrame) -> pd.DataFrame:
    sel = cfg()["seleccion_algoritmo"]
    b = bt[bt["experimento"] == "base"]
    filas = []
    for alg, g in b.groupby("algoritmo"):
        ver = g[g["bloque"].isin(sel["bloques_verano"])]
        rec = [metricas_color(x["color_obs"], x["color_pred"])["recall_rojo"] for _, x in ver.groupby("modelo")]
        wapes = [wape(x["visitas_obs"], x["visitas_pred"]) for _, x in g.groupby(["bloque", "modelo"])]
        seg = g.drop_duplicates(["bloque", "modelo"])["segundos_entrenamiento"].sum()
        filas.append({"algoritmo": alg, "recall_rojo_verano": float(np.nanmean(rec)), "wape_medio": float(np.mean(wapes)),
                      "segundos_entrenamiento_total": float(seg)})
    return pd.DataFrame(filas).set_index("algoritmo")


def elegir(c: pd.DataFrame) -> dict:
    sel = cfg()["seleccion_algoritmo"]
    l, x = c.loc["lightgbm"], c.loc["xgboost"]
    d_rec = x["recall_rojo_verano"] - l["recall_rojo_verano"]
    d_wape = x["wape_medio"] - l["wape_medio"]
    if abs(d_rec) >= sel["margen_recall_rojo"]:
        g, paso = ("xgboost" if d_rec > 0 else "lightgbm"), 1
        motivo = f"recall de días rojos en verano {abs(d_rec) * 100:.1f} puntos mayor (≥ 3)"
    elif abs(d_wape) >= sel["margen_wape"]:
        g, paso = ("xgboost" if d_wape < 0 else "lightgbm"), 2
        motivo = (f"recall de verano empatado ({abs(d_rec) * 100:.1f} < 3 puntos); "
                  f"WAPE medio {abs(d_wape) * 100:.1f} puntos menor (≥ 1)")
    else:
        g, paso = sel["desempate"], 3
        motivo = (f"empate: recall de verano a {abs(d_rec) * 100:.1f} puntos (< 3) y WAPE medio a "
                  f"{abs(d_wape) * 100:.1f} puntos (< 1) -> LightGBM por regla")
    return {"ganador": g, "paso_de_la_regla": paso, "motivo": motivo,
            "diferencia_recall_rojo_verano_xgb_menos_lgb": d_rec, "diferencia_wape_medio_xgb_menos_lgb": d_wape}


def _pct(v) -> str:
    return "—" if v is None or not np.isfinite(v) else f"{v * 100:.1f}".replace(".", ",")


def tabla_markdown(t: pd.DataFrame, c: pd.DataFrame, e: dict, sintetico: bool, objetivo: str) -> str:
    lin = []
    if sintetico:
        lin.append(f"> **⚠ {AVISO_SINTETICO}.** Esta comparación usa el objetivo sintético y **no sirve para elegir "
                   "algoritmo**: los dos modelos aprenden efectos inventados por nosotros. Hay que repetirla con "
                   "`--objetivo real --algoritmo ambos`.")
        lin.append("")
    lin.append(f"Objetivo: `{objetivo}`. Experimento base. Generado el {pd.Timestamp.now():%Y-%m-%d %H:%M}.")
    lin.append("")
    lin.append("| Criterio de la regla | LightGBM | XGBoost |")
    lin.append("|---|---|---|")
    lin.append(f"| Recall de días rojos en verano (%) | {_pct(c.loc['lightgbm', 'recall_rojo_verano'])} | "
               f"{_pct(c.loc['xgboost', 'recall_rojo_verano'])} |")
    lin.append(f"| WAPE medio (%) | {_pct(c.loc['lightgbm', 'wape_medio'])} | {_pct(c.loc['xgboost', 'wape_medio'])} |")
    seg = {k: f"{c.loc[k, 'segundos_entrenamiento_total']:.1f}".replace(".", ",") for k in ("lightgbm", "xgboost")}
    lin.append(f"| Tiempo total de entrenamiento (s) | {seg['lightgbm']} | {seg['xgboost']} |")
    lin.append("")
    lin.append(f"**Resultado de la regla{' (SINTÉTICO, no vale para elegir)' if sintetico else ''}:** "
               f"{e['ganador']} (paso {e['paso_de_la_regla']}: {e['motivo']}).")
    lin.append("")
    lin.append("Detalle por bloque y horizonte (WAPE, acierto de color, recall y precisión de rojos en %; MAE en "
               "visitantes; tiempo = entrenamiento del modelo que produce ese horizonte, en segundos). "
               "Corto plazo: media de h = 1-7.")
    lin.append("")
    lin.append("| Bloque | Horizonte | Algoritmo | WAPE | MAE | Acierto color | Recall rojo | Precisión rojo | Rojos obs. | Tiempo (s) |")
    lin.append("|---|---|---|---|---|---|---|---|---|---|")
    t = t.copy()
    t["h"] = np.where(t["modelo"] == "corto", "1-7 (corto)", "8+ (largo)")
    agg = []
    for (bl, h, alg), g in t.groupby(["bloque", "h", "algoritmo"]):
        w = g["n"] / g["n"].sum()
        agg.append((bl, h, alg, (g["wape"] * w).sum(), (g["mae"] * w).sum(), (g["acierto_color"] * w).sum(),
                    np.nanmean(g["recall_rojo"]), np.nanmean(g["precision_rojo"]), int(g["rojos_obs"].iloc[0]),
                    g["segundos_entrenamiento"].iloc[0]))
    for bl, h, alg, wp, ma, ac, rc, pr, ro, sg in agg:
        lin.append(f"| {bl} | {h} | {alg} | {_pct(wp)} | {ma:.0f} | {_pct(ac)} | {_pct(rc)} | {_pct(pr)} | {ro} | {f'{sg:.2f}'.replace('.', ',')} |")
    lin.append("")
    lin.append("El detalle por cada horizonte (1, 2, … 7, 8+) está en `salidas/comparacion_algoritmos.json → tabla`.")
    return "\n".join(lin)


def escribir_en_notas(md: str, ruta: Path = NOTAS / "modelo.md") -> None:
    texto = ruta.read_text(encoding="utf-8")
    bloque = f"{MARCA_INI}\n{md}\n{MARCA_FIN}"
    if MARCA_INI in texto:
        texto = re.sub(re.escape(MARCA_INI) + r".*?" + re.escape(MARCA_FIN), lambda _: bloque, texto, flags=re.S)
    else:
        texto = texto.rstrip() + "\n\n" + bloque + "\n"
    ruta.write_text(texto, encoding="utf-8")


def ejecutar(bt: pd.DataFrame, D, escribir_notas: bool = True) -> dict:
    t = tabla(bt)
    c = criterios(bt)
    e = elegir(c)
    res = {
        "sintetico": D.sintetico,
        "aviso": (AVISO_SINTETICO + ": esta comparación no sirve para elegir algoritmo; repetir con datos reales.")
        if D.sintetico else None,
        "generado": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "objetivo": D.objetivo,
        "regla": {
            "texto": ["Gana el de mayor recall de días rojos en los bloques de verano (2023-S2 y 2024-S2).",
                      "Si la diferencia es menor de 3 puntos, el de menor WAPE medio.",
                      "Si también la diferencia de WAPE es menor de 1 punto, LightGBM."],
            "parametros": cfg()["seleccion_algoritmo"],
            "calculo": ("recall de verano = media (corto, largo) del recall de rojos agregado en los bloques de verano; "
                        "WAPE medio = media de 4 bloques × 2 modelos."),
        },
        "criterios": c.reset_index().to_dict(orient="records"),
        "eleccion": e,
        "tabla": t.to_dict(orient="records"),
    }
    guardar_json(res, SALIDAS / "comparacion_algoritmos.json")
    if escribir_notas:
        escribir_en_notas(tabla_markdown(t, c, e, D.sintetico, D.objetivo))
    return res
