"""Métricas de la validación por bloques y fiabilidad (intervalos y notas).

Métodos comparados: modelo, B0 (día normal) y B1 (mismo día de la semana del
año anterior; solo referencia). Métricas: WAPE y MAE en visitantes y, para el
semáforo, acierto de color, recall y precisión de los días rojos y matriz de
confusión.

Fiabilidad (conformal simple): cuantiles 10 y 90 del error en escala log,
r = log((obs + 1) / (pred + 1)), por zona y horizonte, con los errores de los
bloques de validación del experimento base. Intervalo de una predicción P:
p10 = (P + 1) * exp(q10) - 1, p90 = (P + 1) * exp(q90) - 1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from util import mae, metricas_color, wape

METODOS = {"modelo": ("visitas_pred", "color_pred"), "B0": ("b0_visitas", "color_b0"),
           "B1": ("b1_visitas", "color_b1")}


def etiqueta_horizonte(h) -> str:
    return "8+" if int(h) >= 8 else str(int(h))


def _fila(g: pd.DataFrame) -> list[dict]:
    out = []
    for met, (cv, cc) in METODOS.items():
        x = g[g[cv].notna()]
        mc = metricas_color(x["color_obs"], x[cc])
        out.append({"metodo": met, "n": int(len(x)), "wape": wape(x["visitas_obs"], x[cv]),
                    "mae": mae(x["visitas_obs"], x[cv]), **{k: v for k, v in mc.items() if k != "n"}})
    return out


def tabla(bt: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    bt = bt.assign(horizonte_txt=bt["horizonte"].map(etiqueta_horizonte), mes=bt["fecha"].dt.month)
    filas = []
    for clave, g in bt.groupby(por, sort=True, observed=True):
        clave = clave if isinstance(clave, tuple) else (clave,)
        for f in _fila(g):
            filas.append({**dict(zip(por, clave)), **f})
    return pd.DataFrame(filas)


def todas(bt: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "global": tabla(bt, ["experimento", "modelo"]),
        "bloque": tabla(bt, ["experimento", "modelo", "bloque"]),
        "zona": tabla(bt, ["experimento", "modelo", "zona_mitma_id"]),
        "horizonte": tabla(bt, ["experimento", "horizonte_txt"]),
        "mes": tabla(bt, ["experimento", "modelo", "mes"]),
        "bloque_zona_horizonte": tabla(bt[bt["experimento"] == "base"],
                                       ["bloque", "zona_mitma_id", "horizonte_txt"]),
    }


# --------------------------------------------------------------------------
# Fiabilidad
# --------------------------------------------------------------------------

def cuantiles_error(bt: pd.DataFrame) -> pd.DataFrame:
    b = bt[bt["experimento"] == "base"].copy()
    b["horizonte_txt"] = b["horizonte"].map(etiqueta_horizonte)
    q = (b.groupby(["zona_mitma_id", "horizonte_txt"])["residuo_log"]
         .agg(q10=lambda s: s.quantile(0.10), q90=lambda s: s.quantile(0.90), n_errores="size").reset_index())
    # Cobertura honesta del intervalo p10-p90 (objetivo: 80 %): para cada bloque,
    # cuantiles calculados con los OTROS bloques y evaluados en este.
    partes = []
    for bl in b["bloque"].unique():
        otros = (b[b["bloque"] != bl].groupby(["zona_mitma_id", "horizonte_txt"])["residuo_log"]
                 .agg(a=lambda s: s.quantile(0.10), z=lambda s: s.quantile(0.90)).reset_index())
        x = b[b["bloque"] == bl].merge(otros, on=["zona_mitma_id", "horizonte_txt"])
        x["dentro"] = (x["residuo_log"] >= x["a"]) & (x["residuo_log"] <= x["z"])
        partes.append(x[["zona_mitma_id", "horizonte_txt", "dentro"]])
    cob = pd.concat(partes).groupby(["zona_mitma_id", "horizonte_txt"])["dentro"].mean().rename("cobertura")
    return q.merge(cob.reset_index(), on=["zona_mitma_id", "horizonte_txt"], how="left")


def intervalo(pred, q10, q90) -> tuple[np.ndarray, np.ndarray]:
    pred = np.asarray(pred, float)
    return (np.maximum((pred + 1) * np.exp(q10) - 1, 0), np.maximum((pred + 1) * np.exp(q90) - 1, 0))


def nota_fiabilidad(acierto: float, rojos_obs: int, recall_rojo: float) -> str:
    t = f"Acierta el color en el {acierto * 100:.0f} % de los días"
    if rojos_obs >= 5 and np.isfinite(recall_rojo):
        t += f"; detecta {recall_rojo * 10:.0f} de cada 10 días rojos"
    elif rojos_obs > 0:
        t += f"; solo {rojos_obs} días rojos en la validación (pocos para medir la detección)"
    else:
        t += "; no hubo días rojos en la validación"
    return t + "."


def notas(bt: pd.DataFrame) -> pd.DataFrame:
    t = tabla(bt[bt["experimento"] == "base"], ["zona_mitma_id", "horizonte_txt"])
    t = t[t["metodo"] == "modelo"].copy()
    t["nota"] = [nota_fiabilidad(a, r, rc) for a, r, rc in zip(t["acierto_color"], t["rojos_obs"], t["recall_rojo"])]
    return t[["zona_mitma_id", "horizonte_txt", "n", "wape", "acierto_color", "rojos_obs", "recall_rojo",
              "precision_rojo", "nota"]]
