"""Utilidades comunes del modelo: rutas, configuración, semáforo y métricas."""
from __future__ import annotations

import json
import math
import os
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "config"
CLEAN = RAIZ / "data" / "clean"
RAW = RAIZ / "data" / "raw"
# MODELO_SALIDAS permite escribir las salidas en otra carpeta (lo usan las pruebas).
SALIDAS = Path(os.environ["MODELO_SALIDAS"]) if os.environ.get("MODELO_SALIDAS") else RAIZ / "salidas"
FIGURAS = SALIDAS / "figuras"
NOTAS = RAIZ / "notas"

COLORES = ["verde", "ambar", "rojo"]
AVISO_SINTETICO = "DATOS SINTÉTICOS — NO SON REALES"


@lru_cache(maxsize=None)
def _yaml(nombre: str) -> dict:
    with open(CONFIG / nombre, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cfg() -> dict:
    return _yaml("modelo.yaml")


def cfg_semaforo() -> dict:
    return _yaml("semaforo.yaml")


def cfg_factores() -> list[dict]:
    return _yaml("factores.yaml")["factores"]


def cfg_calidad_mitma() -> dict:
    return _yaml("mitma_calidad.yaml")


def ruta(rel: str | Path) -> Path:
    p = Path(rel)
    if p.is_absolute():
        return p
    if p.parts and p.parts[0] == "salidas":
        return SALIDAS.joinpath(*p.parts[1:])
    return RAIZ / p


def importar_limpieza_B():
    """Permite `from unir_B import ...` sin tocar el código de limpieza."""
    p = str(RAIZ / "src" / "limpieza_B")
    if p not in sys.path:
        sys.path.insert(0, p)


def norm_texto(s) -> str | None:
    if s is None or (isinstance(s, float) and pd.isna(s)) or str(s).strip() == "":
        return None
    s = str(s).split("/")[0].strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "_".join(s.lower().replace("-", " ").split())


def leer_mapeo(objetivo: str) -> pd.DataFrame:
    m = pd.read_csv(ruta(cfg()["fuentes"][objetivo]["mapeo"]), dtype=str, keep_default_na=False)
    m = m.replace({"": None})
    if m["zona_mitma_id"].isna().any():
        raise SystemExit(
            f"El mapeo {cfg()['fuentes'][objetivo]['mapeo']} tiene zonas sin zona_mitma_id. "
            "Para --objetivo real hay que rellenarlo con los IDs de la parte A (ver notas/modelo.md).")
    return m


def zona_principal(mapeo: pd.DataFrame) -> str | None:
    ine = str(cfg()["zona_principal_concejo_ine"])
    for z, c in zip(mapeo["zona_mitma_id"], mapeo["concejos_ine"]):
        if str(c or "").strip() == ine:
            return z
    for z, c in zip(mapeo["zona_mitma_id"], mapeo["concejos_ine"]):
        if ine in str(c or "").split(";"):
            return z
    return None


# --------------------------------------------------------------------------
# Semáforo
# --------------------------------------------------------------------------

def umbrales(zona: str) -> tuple[float, float]:
    s = cfg_semaforo()
    z = (s.get("por_zona") or {}).get(zona, {})
    return float(z.get("umbral_ambar", s["umbral_ambar"])), float(z.get("umbral_rojo", s["umbral_rojo"]))


def color(cociente, zona: str) -> str:
    if cociente is None or not np.isfinite(cociente):
        return "gris"
    a, r = umbrales(zona)
    return "rojo" if cociente >= r else ("ambar" if cociente >= a else "verde")


def colores(cocientes: pd.Series, zonas: pd.Series) -> pd.Series:
    c = pd.to_numeric(cocientes, errors="coerce").to_numpy(dtype=float)
    z = zonas.astype(str).to_numpy()
    ua = np.array([umbrales(x)[0] for x in z])
    ur = np.array([umbrales(x)[1] for x in z])
    out = np.where(c >= ur, "rojo", np.where(c >= ua, "ambar", "verde")).astype(object)
    out[~np.isfinite(c)] = "gris"
    return pd.Series(out, index=cocientes.index)


# --------------------------------------------------------------------------
# Escala del objetivo: y = log((x + 1) / (normal + 1))
# --------------------------------------------------------------------------

def a_log_cociente(x, normal):
    return np.log((np.asarray(x, dtype=float) + 1.0) / (np.asarray(normal, dtype=float) + 1.0))


def desde_log_cociente(y, normal):
    return np.maximum((np.asarray(normal, dtype=float) + 1.0) * np.exp(np.asarray(y, dtype=float)) - 1.0, 0.0)


# --------------------------------------------------------------------------
# Métricas
# --------------------------------------------------------------------------

def wape(obs, pred) -> float:
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    ok = np.isfinite(obs) & np.isfinite(pred)
    den = np.abs(obs[ok]).sum()
    return float(np.abs(obs[ok] - pred[ok]).sum() / den) if den > 0 else float("nan")


def mae(obs, pred) -> float:
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    ok = np.isfinite(obs) & np.isfinite(pred)
    return float(np.abs(obs[ok] - pred[ok]).mean()) if ok.any() else float("nan")


def metricas_color(obs: pd.Series, pred: pd.Series) -> dict:
    ok = obs.isin(COLORES) & pred.isin(COLORES)
    o, p = obs[ok], pred[ok]
    cm = {f"{a}->{b}": int(((o == a) & (p == b)).sum()) for a in COLORES for b in COLORES}
    n_rojo_obs, n_rojo_pred = int((o == "rojo").sum()), int((p == "rojo").sum())
    tp = int(((o == "rojo") & (p == "rojo")).sum())
    return {
        "n": int(ok.sum()),
        "acierto_color": float((o == p).mean()) if len(o) else float("nan"),
        "rojos_obs": n_rojo_obs,
        "rojos_pred": n_rojo_pred,
        "recall_rojo": tp / n_rojo_obs if n_rojo_obs else float("nan"),
        "precision_rojo": tp / n_rojo_pred if n_rojo_pred else float("nan"),
        # "alerta" = ámbar o rojo
        "recall_alerta": (float(((o != "verde") & (p != "verde")).sum() / (o != "verde").sum())
                          if (o != "verde").any() else float("nan")),
        "matriz_confusion": cm,
    }


# --------------------------------------------------------------------------
# JSON
# --------------------------------------------------------------------------

def _limpio(x):
    if isinstance(x, dict):
        return {str(k): _limpio(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_limpio(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return None if not math.isfinite(float(x)) else round(float(x), 4)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (pd.Timestamp,)):
        return x.strftime("%Y-%m-%d")
    if x is pd.NA or x is pd.NaT:
        return None
    return x


def guardar_json(obj, ruta_salida: Path) -> None:
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(_limpio(obj), f, ensure_ascii=False, indent=1)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", norm_texto(s) or "").strip("_")


def distancia_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
