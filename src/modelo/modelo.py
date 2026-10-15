"""Entrenamiento y predicción con LightGBM (un modelo global para todas las zonas).

El modelo predice y = log((x + 1) / (normal + 1)), con x el objetivo del día
y normal el día normal de la zona y día de la semana.
Visitantes previstos = (normal + 1) * exp(predicción) - 1.
"""
from __future__ import annotations

import re

import lightgbm as lgb
import numpy as np
import pandas as pd

from util import cfg, cfg_factores


def entrenar(df: pd.DataFrame, feats: list[str], y: np.ndarray) -> tuple[lgb.Booster, dict]:
    """Parada temprana con los últimos días como validación interna (partición
    temporal) y reentrenamiento con todo el periodo con ese nº de árboles."""
    c = cfg()
    params = dict(c["lightgbm"], seed=int(c["semilla"]), bagging_seed=int(c["semilla"]),
                  feature_fraction_seed=int(c["semilla"]), data_random_seed=int(c["semilla"]))
    fechas = df["fecha"]
    corte = fechas.max() - pd.Timedelta(days=int(c["dias_validacion_interna"]))
    tr, va = (fechas <= corte).to_numpy(), (fechas > corte).to_numpy()
    dtr = lgb.Dataset(df.loc[tr, feats], y[tr], free_raw_data=False)
    dva = lgb.Dataset(df.loc[va, feats], y[va], reference=dtr, free_raw_data=False)
    m = lgb.train(params, dtr, num_boost_round=int(c["max_iteraciones"]), valid_sets=[dva],
                  callbacks=[lgb.early_stopping(int(c["parada_temprana"]), verbose=False)])
    n = max(int(m.best_iteration or c["max_iteraciones"]), 20)
    final = lgb.train(params, lgb.Dataset(df[feats], y), num_boost_round=n)
    return final, {"n_arboles": n, "n_filas": int(len(df)), "inicio": str(fechas.min().date()),
                   "fin": str(fechas.max().date())}


def predecir(m: lgb.Booster, df: pd.DataFrame, feats: list[str]) -> np.ndarray:
    return m.predict(df[feats])


# --------------------------------------------------------------------------
# SHAP y factores
# --------------------------------------------------------------------------

def shap(m: lgb.Booster, df: pd.DataFrame, feats: list[str]) -> tuple[np.ndarray, float]:
    """Valores SHAP exactos (TreeSHAP nativo de LightGBM, el mismo algoritmo que
    shap.TreeExplainer; explicar.py comprueba que coinciden). Devuelve
    (n x n_feats, valor base)."""
    v = m.predict(df[feats], pred_contrib=True)
    return v[:, :-1], float(v[0, -1]) if len(v) else 0.0


def factor_de(feat: str) -> str:
    for f in cfg_factores():
        if re.search(f["patron"], feat):
            return f["nombre"]
    return "Otros"


def factores_mostrables() -> list[str]:
    return [f["nombre"] for f in cfg_factores() if f.get("mostrar", True)]


def sumar_por_factor(valores: np.ndarray, feats: list[str]) -> pd.DataFrame:
    grupos = pd.Series([factor_de(f) for f in feats])
    out = {}
    for g in grupos.unique():
        out[g] = valores[:, (grupos == g).to_numpy()].sum(axis=1)
    return pd.DataFrame(out)


def top_factores(fx: pd.DataFrame, k: int = 3) -> list[list[dict]]:
    """Por fila: los k factores mostrables con mayor |efecto|, con efecto en %."""
    cols = [c for c in fx.columns if c in factores_mostrables()]
    vals = fx[cols].to_numpy()
    orden = np.argsort(-np.abs(vals), axis=1)[:, :k]
    res = []
    for i in range(len(fx)):
        fila = []
        for j in orden[i]:
            v = vals[i, j]
            fila.append({"nombre": cols[j], "efecto_pct": round(float(np.expm1(v) * 100), 1),
                         "signo": "+" if v >= 0 else "-"})
        res.append(fila)
    return res
