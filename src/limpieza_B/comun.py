"""Utilidades comunes de la limpieza de la parte B.

Rutas, escritura de tablas y comprobaciones automáticas (duplicados,
continuidad de fechas y rangos válidos). Cada script de `src/limpieza_B/`
llama a `comprobar_*` antes de escribir; si una comprobación falla, el
script se detiene con `AssertionError` y no escribe nada.

Además, cada script deja un resumen en `data/clean/_qc/<tabla>.json`
(filas, rango, NaN por columna, duplicados, fechas ausentes y validaciones),
que `control_calidad.py` usa para generar `notas/control_calidad_B.md`.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw"
MANUAL = RAIZ / "data" / "manual"
CLEAN = RAIZ / "data" / "clean"
QC = CLEAN / "_qc"
CONFIG = RAIZ / "config"
NOTAS = RAIZ / "notas"


def asegurar_dirs() -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)
    QC.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Comprobaciones automáticas
# --------------------------------------------------------------------------

def comprobar_sin_duplicados(df: pd.DataFrame, claves: list[str], tabla: str) -> int:
    n = int(df.duplicated(subset=claves).sum())
    assert n == 0, f"[{tabla}] {n} filas duplicadas por {claves}"
    return n


def fechas_ausentes(fechas: pd.Series, ini=None, fin=None) -> list[str]:
    """Fechas del rango [ini, fin] (por defecto, min..max) que no aparecen."""
    f = pd.to_datetime(fechas).dt.normalize()
    ini = pd.Timestamp(ini) if ini is not None else f.min()
    fin = pd.Timestamp(fin) if fin is not None else f.max()
    todas = pd.date_range(ini, fin, freq="D")
    return [d.strftime("%Y-%m-%d") for d in todas.difference(pd.DatetimeIndex(f.unique()))]


def comprobar_continuidad(df: pd.DataFrame, col_fecha: str, por: str | list[str] | None,
                          tabla: str, ini=None, fin=None, permitir_huecos: bool = False) -> dict:
    """Comprueba que cada grupo tiene todas las fechas de su rango.

    Si `permitir_huecos` es True no falla (sirve para series con huecos
    reales, como AEMET) pero devuelve el recuento de fechas ausentes.
    """
    res = {}
    grupos = [((), df)] if por is None else df.groupby(por)
    for clave, g in grupos:
        aus = fechas_ausentes(g[col_fecha], ini, fin)
        res[str(clave if not isinstance(clave, tuple) or len(clave) != 1 else clave[0])] = len(aus)
        if not permitir_huecos:
            assert not aus, f"[{tabla}] grupo {clave}: {len(aus)} fechas ausentes (p. ej. {aus[:3]})"
    return res


def comprobar_rango(df: pd.DataFrame, col: str, minimo=None, maximo=None, tabla: str = "") -> int:
    """Valores no nulos fuera de [minimo, maximo]. Falla si hay alguno."""
    s = df[col].dropna()
    malos = s[((s < minimo) if minimo is not None else False) | ((s > maximo) if maximo is not None else False)]
    assert malos.empty, f"[{tabla}] {col}: {len(malos)} valores fuera de [{minimo}, {maximo}] (p. ej. {malos.head(3).tolist()})"
    return 0


# --------------------------------------------------------------------------
# Resumen de calidad
# --------------------------------------------------------------------------

def resumen_qc(df: pd.DataFrame, tabla: str, claves: list[str], col_fecha: str | None = "fecha",
               extra: dict | None = None) -> dict:
    """Escribe data/clean/_qc/<tabla>.json con el resumen estándar."""
    asegurar_dirs()
    r = {
        "tabla": tabla,
        "filas": int(len(df)),
        "columnas": list(map(str, df.columns)),
        "claves": claves,
        "duplicados_por_clave": int(df.duplicated(subset=claves).sum()),
        "nan_pct": {c: round(float(df[c].isna().mean() * 100), 2)
                    for c in df.columns if df[c].isna().any()},
    }
    if col_fecha and col_fecha in df.columns and len(df):
        f = pd.to_datetime(df[col_fecha])
        r["fecha_min"] = f.min().strftime("%Y-%m-%d")
        r["fecha_max"] = f.max().strftime("%Y-%m-%d")
        r["fechas_ausentes_global"] = len(fechas_ausentes(f))
    if extra:
        r.update(extra)
    (QC / f"{tabla}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1, default=_json_default),
                                      encoding="utf-8")
    return r


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (pd.Timestamp,)):
        return o.strftime("%Y-%m-%d")
    return str(o)


def escribir_parquet(df: pd.DataFrame, nombre: str) -> Path:
    asegurar_dirs()
    ruta = CLEAN / nombre
    df.to_parquet(ruta, index=False)
    return ruta
