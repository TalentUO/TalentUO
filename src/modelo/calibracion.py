"""Calibración del umbral con la regulación real de acceso a los Lagos.

Pregunta: ¿qué umbral de cociente (visitantes / día normal) reproduce mejor los
días en que ya se regula el acceso a los Lagos (BOE, `lagos_regulado`)?
Se prueba una rejilla de umbrales y, para cada uno, se compara "día en alerta"
(cociente >= umbral) con "día regulado" en la zona principal: F1, precisión y
recall (positivo = regulado). Se hace con el cociente observado (2023 y 2024) y
con el previsto fuera de muestra por el modelo de largo plazo.
El valor por defecto del semáforo NO se cambia: se anota para la presentación.
Ojo: la regulación es un calendario planificado (fines de semana y verano), no
una medida de saturación; la comparación orienta, no valida.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import dia_normal  # noqa: E402
from explicar import AZUL, TINTA2, _titulo  # noqa: E402
from util import FIGURAS, umbrales  # noqa: E402

REJILLA = np.round(np.arange(0.5, 3.01, 0.05), 2)
VARIANTES = {
    "relativo": "visitantes / día normal de ese día de la semana (la escala del semáforo)",
    "absoluto": "visitantes / día normal medio de la zona (volumen absoluto: un sábado normal ya cuenta)",
}


def _f1(alerta: pd.Series, reg: pd.Series) -> dict:
    tp = int((alerta & reg).sum())
    pa, pr = int(alerta.sum()), int(reg.sum())
    prec = tp / pa if pa else float("nan")
    rec = tp / pr if pr else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if pa and pr and (prec + rec) > 0 else 0.0
    return {"f1": f1, "precision": prec, "recall": rec, "dias_alerta": pa, "dias_regulados": pr, "coinciden": tp}


def ejecutar(D, bt: pd.DataFrame) -> dict:
    zp = D.zona_principal
    if zp is None:
        return {"error": "sin zona principal"}
    cal = D.base[D.base["zona_mitma_id"] == zp][["fecha", "cal_lagos_regulado", "cal_dia_semana"]]
    obs = D.obj[(D.obj["zona_mitma_id"] == zp) & (D.obj["calidad"] == "completa")].merge(cal, on="fecha")
    obs = dia_normal.anadir_normal(obs, D.normal_ref, "normal")
    normal_medio = float(D.normal_ref.loc[D.normal_ref["zona_mitma_id"] == zp, "normal"].mean())
    obs["relativo"] = obs[D.objetivo] / obs["normal"]
    obs["absoluto"] = obs[D.objetivo] / normal_medio
    cal = cal.drop(columns="cal_dia_semana")
    obs = obs[obs["fecha"].dt.year.isin([2023, 2024]) & obs["cal_lagos_regulado"].notna()]
    pred = bt[(bt["experimento"] == "base") & (bt["modelo"] == "largo") & (bt["zona_mitma_id"] == zp)]
    pred = pred.merge(cal, on="fecha")
    pred = pred[pred["cal_lagos_regulado"].notna()].copy()
    pred["relativo"] = pred["cociente_pred"]
    pred["absoluto"] = pred["visitas_pred"] / normal_medio

    a, r = umbrales(zp)
    res = {"zona_mitma_id": zp, "sintetico": D.sintetico, "umbral_por_defecto": {"ambar": a, "rojo": r},
           "normal_medio_zona": normal_medio, "variantes": VARIANTES,
           "nota": ("Umbral que mejor reproduce los días regulados (máximo F1). No cambia el valor por defecto. "
                    "La regulación es un calendario planificado (fines de semana y verano), no una medida de "
                    "saturación: la comparación orienta, no valida.")}
    curvas = {}
    for fuente, df in (("observado_2023_2024", obs), ("previsto_fuera_de_muestra", pred)):
        reg = df["cal_lagos_regulado"].astype(bool)
        res[fuente] = {}
        for var in VARIANTES:
            c = pd.DataFrame([{"umbral": u, **_f1(df[var] >= u, reg)} for u in REJILLA])
            curvas[(fuente, var)] = c
            mejor = c.loc[c["f1"].idxmax()]
            res[fuente][var] = {
                "mejor_umbral": float(mejor["umbral"]), "f1": float(mejor["f1"]),
                "precision": float(mejor["precision"]), "recall": float(mejor["recall"]),
                "dias_regulados": int(mejor["dias_regulados"]),
                "dias_alerta_con_mejor_umbral": int(mejor["dias_alerta"]),
                "mejor_en_borde_de_rejilla": bool(mejor["umbral"] in (REJILLA.min(), REJILLA.max())),
                "con_umbral_ambar": c.iloc[(c["umbral"] - a).abs().argmin()].to_dict(),
                "con_umbral_rojo": c.iloc[(c["umbral"] - r).abs().argmin()].to_dict(),
                "curva": c.round(4).to_dict(orient="records"),
            }
        res[fuente]["mejor_umbral"] = res[fuente]["relativo"]["mejor_umbral"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, var in zip(axes, VARIANTES):
        for fuente, col in (("observado_2023_2024", TINTA2), ("previsto_fuera_de_muestra", AZUL)):
            c = curvas[(fuente, var)]
            lab = "Observado (2023-2024)" if fuente.startswith("obs") else "Previsto (fuera de muestra)"
            ax.plot(c["umbral"], c["f1"], color=col, lw=2, label=lab)
            m = c.loc[c["f1"].idxmax()]
            ax.plot([m["umbral"]], [m["f1"]], "o", color=col, ms=8, mec="#fcfcfb", mew=2)
            ax.annotate(f"{m['umbral']:.2f}×", (m["umbral"], m["f1"]), textcoords="offset points",
                        xytext=(6, 6), color=TINTA2, fontsize=9)
        if var == "relativo":
            for u, t in ((a, "ámbar"), (r, "rojo")):
                ax.axvline(u, color="#c3c2b7", lw=1)
                ax.text(u, 0.02, f" {t}", color=TINTA2, fontsize=8)
        ax.set_title("Frente al normal de ese día de la semana" if var == "relativo"
                     else "Frente al día normal medio (volumen absoluto)", color=TINTA2, fontsize=10, loc="left")
        ax.set_xlabel("Umbral (veces el normal)")
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("Coincidencia con días regulados (F1)")
    axes[1].legend(frameon=False, loc="upper right")
    _titulo(fig, f"¿Qué umbral reproduce la regulación actual de los Lagos? ({D.nombres[zp]})", D.sintetico)
    fig.tight_layout()
    fig.savefig(FIGURAS / "calibracion_lagos.png", dpi=150)
    plt.close(fig)
    return res


def resumen(calib: dict) -> dict:
    """La calibración sin las curvas completas (para metricas.json y regulacion.json)."""
    if isinstance(calib, dict):
        return {k: resumen(v) for k, v in calib.items() if k != "curva"}
    return calib
