"""Carga de todo lo que necesita el modelo para un modo (`sintetico` o `real`)."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

import dia_normal
import features as F
import objetivo_sintetico
from util import cfg, leer_mapeo, ruta, zona_principal


@dataclass
class Datos:
    modo: str
    sintetico: bool
    objetivo: str                 # columna a predecir
    mapeo: pd.DataFrame
    tablas: dict
    base: pd.DataFrame            # (fecha, zona) calendario + eventos + partidos, 2022..2027
    obj: pd.DataFrame             # objetivo_diario
    normal_ref: pd.DataFrame      # día normal de referencia (semáforo)
    zona_principal: str | None
    zonas: list[str] = field(default_factory=list)
    nombres: dict = field(default_factory=dict)


def cargar(modo: str, objetivo: str | None = None) -> Datos:
    objetivo = objetivo or cfg()["objetivo"]
    mapeo = leer_mapeo(modo)
    tablas = F.cargar_tablas()
    base = F.tabla_base(mapeo, tablas)
    if modo == "sintetico":
        obj = objetivo_sintetico.ejecutar(mapeo, base, tablas["openmeteo_diario"])
    else:
        p = ruta(cfg()["fuentes"]["real"]["objetivo"])
        if not p.exists():
            raise SystemExit(f"No existe {p}. Ejecuta antes: python -X utf8 src/modelo/construir_objetivo.py")
        obj = pd.read_parquet(p)
        obj["sintetico"] = False
    obj["fecha"] = pd.to_datetime(obj["fecha"]).dt.normalize()
    obj["zona_mitma_id"] = obj["zona_mitma_id"].astype(str)
    faltan = set(mapeo["zona_mitma_id"]) - set(obj["zona_mitma_id"])
    if faltan:
        raise SystemExit(f"El objetivo no tiene las zonas del mapeo: {sorted(faltan)}")
    obj = obj[obj["zona_mitma_id"].isin(mapeo["zona_mitma_id"])]
    if objetivo not in obj.columns:
        raise SystemExit(f"El objetivo no tiene la columna {objetivo}")
    normal = dia_normal.normal_referencia(obj, base, objetivo)
    return Datos(modo=modo, sintetico=(modo == "sintetico"), objetivo=objetivo, mapeo=mapeo, tablas=tablas,
                 base=base, obj=obj, normal_ref=normal, zona_principal=zona_principal(mapeo),
                 zonas=list(mapeo["zona_mitma_id"]), nombres=dict(zip(mapeo["zona_mitma_id"], mapeo["nombre"])))
