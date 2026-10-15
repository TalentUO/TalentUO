"""Entrenamiento y predicción con LightGBM o XGBoost (un modelo global para
todas las zonas).

El modelo predice y = log((x + 1) / (normal + 1)), con x el objetivo del día
y normal el día normal de la zona y día de la semana.
Visitantes previstos = (normal + 1) * exp(predicción) - 1.

Los dos algoritmos usan exactamente las mismas variables (la zona como
`category`), la misma partición temporal interna para la parada temprana
(últimos `dias_validacion_interna` días) y la misma semilla. Tras la parada
temprana se reentrena con todo el periodo con ese nº de árboles.
"""
from __future__ import annotations

import re
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb

from util import cfg, cfg_factores

ALGORITMOS = ("lightgbm", "xgboost")


class Modelo:
    """Envoltorio común: `predict` y `contrib` (SHAP exacto, TreeSHAP nativo)."""

    def __init__(self, algoritmo: str, nativo, feats: list[str]):
        self.algoritmo, self.nativo, self.feats = algoritmo, nativo, feats

    def predict(self, x: pd.DataFrame) -> np.ndarray:
        return np.asarray(self.nativo.predict(x[self.feats]), dtype=float)

    def contrib(self, x: pd.DataFrame) -> tuple[np.ndarray, float]:
        if self.algoritmo == "lightgbm":
            v = self.nativo.predict(x[self.feats], pred_contrib=True)
        else:
            v = self.nativo.get_booster().predict(xgb.DMatrix(x[self.feats], enable_categorical=True),
                                                  pred_contribs=True)
        v = np.asarray(v, dtype=float)
        return v[:, :-1], float(v[0, -1]) if len(v) else 0.0


def algoritmo_por_defecto() -> str:
    return cfg().get("algoritmo", "lightgbm")


def _particion(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    fechas = df["fecha"]
    corte = fechas.max() - pd.Timedelta(days=int(cfg()["dias_validacion_interna"]))
    return (fechas <= corte).to_numpy(), (fechas > corte).to_numpy()


def _lightgbm(df, feats, y, tr, va):
    c = cfg()
    params = dict(c["lightgbm"], seed=int(c["semilla"]), bagging_seed=int(c["semilla"]),
                  feature_fraction_seed=int(c["semilla"]), data_random_seed=int(c["semilla"]))
    dtr = lgb.Dataset(df.loc[tr, feats], y[tr], free_raw_data=False)
    dva = lgb.Dataset(df.loc[va, feats], y[va], reference=dtr, free_raw_data=False)
    m = lgb.train(params, dtr, num_boost_round=int(c["max_iteraciones"]), valid_sets=[dva],
                  callbacks=[lgb.early_stopping(int(c["parada_temprana"]), verbose=False)])
    n = max(int(m.best_iteration or c["max_iteraciones"]), 20)
    return lgb.train(params, lgb.Dataset(df[feats], y), num_boost_round=n), n


def _xgboost(df, feats, y, tr, va):
    c = cfg()
    params = dict(c["xgboost"], random_state=int(c["semilla"]))
    m = xgb.XGBRegressor(n_estimators=int(c["max_iteraciones"]), early_stopping_rounds=int(c["parada_temprana"]),
                         **params)
    m.fit(df.loc[tr, feats], y[tr], eval_set=[(df.loc[va, feats], y[va])], verbose=False)
    n = max(int(m.best_iteration) + 1, 20)
    final = xgb.XGBRegressor(n_estimators=n, **params)
    final.fit(df[feats], y, verbose=False)
    return final, n


def entrenar(df: pd.DataFrame, feats: list[str], y: np.ndarray, algoritmo: str | None = None) -> tuple[Modelo, dict]:
    algoritmo = algoritmo or algoritmo_por_defecto()
    if algoritmo not in ALGORITMOS:
        raise ValueError(f"algoritmo desconocido: {algoritmo}")
    y = np.asarray(y, dtype=float)
    tr, va = _particion(df)
    t0 = time.perf_counter()
    nativo, n = (_lightgbm if algoritmo == "lightgbm" else _xgboost)(df, feats, y, tr, va)
    seg = time.perf_counter() - t0
    fechas = df["fecha"]
    return Modelo(algoritmo, nativo, feats), {
        "algoritmo": algoritmo, "n_arboles": n, "n_filas": int(len(df)), "segundos_entrenamiento": round(seg, 3),
        "inicio": str(fechas.min().date()), "fin": str(fechas.max().date())}


def predecir(m: Modelo, df: pd.DataFrame, feats: list[str] | None = None) -> np.ndarray:
    return m.predict(df)


# --------------------------------------------------------------------------
# SHAP y factores
# --------------------------------------------------------------------------

def shap(m: Modelo, df: pd.DataFrame, feats: list[str] | None = None) -> tuple[np.ndarray, float]:
    """Valores SHAP exactos (TreeSHAP nativo de LightGBM o XGBoost, el mismo
    algoritmo que shap.TreeExplainer; explicar.py comprueba que coinciden).
    Devuelve (n x n_feats, valor base)."""
    return m.contrib(df)


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
