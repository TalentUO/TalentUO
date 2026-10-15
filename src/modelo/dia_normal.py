"""Día normal por zona y día de la semana.

Definición (misma idea que el MITMA): mediana del objetivo por zona y día de la
semana en el periodo de referencia (2024), sin julio ni agosto, sin festivos
(nacional, de Asturias o local de la zona) y sin días con problemas del MITMA.

- `normal_referencia`: define el semáforo (cociente = visitantes / normal).
- `normal_ventana`: la misma regla sobre los N días anteriores a una fecha;
  la usa la validación para no mirar el futuro.
- Si A encuentra los estadísticos oficiales del MITMA, basta con poner
  `dia_normal.fuente: mitma` en config/modelo.yaml y dejar el fichero
  (zona_mitma_id, dia_semana, normal) en `dia_normal.mitma_fichero`.
"""
from __future__ import annotations

import pandas as pd

from util import cfg, ruta


def _mediana(obj: pd.DataFrame, base: pd.DataFrame, objetivo: str, ini, fin) -> pd.DataFrame:
    c = cfg()["dia_normal"]
    x = obj.merge(base[["fecha", "zona_mitma_id", "cal_dia_semana", "cal_festivo_nacional",
                        "cal_festivo_ast", "cal_festivo_local"]],
                  on=["fecha", "zona_mitma_id"], how="left", validate="one_to_one")
    ok = ((x["fecha"] >= pd.Timestamp(ini)) & (x["fecha"] <= pd.Timestamp(fin))
          & ~x["fecha"].dt.month.isin(c["excluir_meses"])
          & (x[["cal_festivo_nacional", "cal_festivo_ast", "cal_festivo_local"]].fillna(0).sum(axis=1) == 0)
          & (x["calidad"] == "completa") & x[objetivo].notna())
    n = (x[ok].groupby(["zona_mitma_id", "cal_dia_semana"])[objetivo]
         .agg(normal="median", n_dias="size").reset_index()
         .rename(columns={"cal_dia_semana": "dia_semana"}))
    return n


def normal_referencia(obj: pd.DataFrame, base: pd.DataFrame, objetivo: str) -> pd.DataFrame:
    c = cfg()["dia_normal"]
    if c["fuente"] == "mitma":
        n = pd.read_csv(ruta(c["mitma_fichero"]), dtype={"zona_mitma_id": str})
        n = n[["zona_mitma_id", "dia_semana", "normal"]].copy()
        n["n_dias"] = pd.NA
        n["fuente"] = "MITMA (estadísticos oficiales)"
        return n
    a = int(c["anio_referencia"])
    n = _mediana(obj, base, objetivo, f"{a}-01-01", f"{a}-12-31")
    n["fuente"] = f"propio: mediana {a} sin jul-ago ni festivos"
    return n


def normal_ventana(obj: pd.DataFrame, base: pd.DataFrame, objetivo: str, antes_de) -> pd.DataFrame:
    dias = int(cfg()["dia_normal"]["ventana_backtest_dias"])
    fin = pd.Timestamp(antes_de) - pd.Timedelta(days=1)
    return _mediana(obj, base, objetivo, fin - pd.Timedelta(days=dias - 1), fin)


def anadir_normal(df: pd.DataFrame, normal: pd.DataFrame, col: str = "normal") -> pd.DataFrame:
    n = normal[["zona_mitma_id", "dia_semana", "normal"]].rename(columns={"normal": col, "dia_semana": "cal_dia_semana"})
    return df.merge(n, on=["zona_mitma_id", "cal_dia_semana"], how="left", validate="many_to_one")
