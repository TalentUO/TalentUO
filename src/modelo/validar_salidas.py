"""Comprueba que los JSON de salidas/ cumplen notas/contrato_web.md.

    python -X utf8 src/modelo/validar_salidas.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
COLORES = {"verde", "ambar", "rojo", "gris"}
NUM = (int, float)

CABECERA = {"sintetico": bool, "generado": str, "objetivo": str, "umbrales": dict}

PRED = {"fecha": "fecha", "zona_mitma_id": str, "nombre_zona": str, "horizonte": int,
        "prediccion": NUM + (type(None),), "normal": NUM + (type(None),), "cociente": NUM + (type(None),),
        "pct_sobre_normal": NUM + (type(None),), "color": "color", "p10": NUM + (type(None),),
        "p90": NUM + (type(None),), "incierto": bool, "factores": list, "sintetico": bool,
        "modelo": ("corto", "largo"), "conjunto": ("futuro_largo", "futuro_corto", "historico")}
FACTOR = {"nombre": str, "efecto_pct": NUM, "signo": ("+", "-")}
ALT = {"fecha": "fecha", "zona_mitma_id": str, "nombre_zona": str, "conjunto": str, "modelo": str,
       "horizonte": int, "cociente": NUM, "color": ("ambar", "rojo"), "mejor_dia": (dict, type(None)),
       "zona_alternativa": (dict, type(None)), "sintetico": bool}
ANIO = {"anio": int, "tipo": ("observado", "previsto"), "dias_con_dato": int, "dias_rojos": int,
        "dias_ambar": int, "dias_alerta": int}
CAL = {"fecha": "fecha", "zona_mitma_id": str, "prediccion": NUM + (type(None),), "cociente": NUM + (type(None),),
       "color": "color", "p10": NUM + (type(None),), "p90": NUM + (type(None),), "incierto": bool,
       "lagos_regulado": (bool, type(None)), "calendario_supuesto": bool, "sintetico": bool}
PERFIL = {"zona_mitma_id": str, "nombre_zona": str, "mes": int, "dias": int,
          "pct_desde_asturias": NUM + (type(None),), "pct_resto_espana": NUM + (type(None),),
          "pernoctaciones_por_100_llegadas": NUM + (type(None),), "pct_excursionistas_aprox": NUM + (type(None),),
          "sintetico": bool}
FIAB = {"zona_mitma_id": str, "nombre_zona": str, "horizonte_txt": str, "acierto_color": NUM + (type(None),),
        "recall_rojo": NUM + (type(None),), "nota": str, "q10": NUM, "q90": NUM}


def _tipo_ok(v, t) -> bool:
    if t == "fecha":
        return isinstance(v, str) and bool(FECHA.match(v))
    if t == "color":
        return v in COLORES
    if isinstance(t, tuple) and t and isinstance(t[0], str):
        return v in t
    if t is int or t == (int,):
        return isinstance(v, int) and not isinstance(v, bool)
    if isinstance(t, tuple):
        return isinstance(v, t) and not (isinstance(v, bool) and bool not in t)
    return isinstance(v, t) and not (isinstance(v, bool) and t is not bool)


def _registro(r: dict, esquema: dict, donde: str, errores: list) -> None:
    for k, t in esquema.items():
        if k not in r:
            errores.append(f"{donde}: falta '{k}'")
        elif not _tipo_ok(r[k], t):
            errores.append(f"{donde}: '{k}'={r[k]!r} no cumple {t}")


def validar(salidas: Path) -> list[str]:
    err: list[str] = []
    datos = {}
    for n in ("predicciones", "alternativas", "regulacion", "perfil", "metricas"):
        p = salidas / f"{n}.json"
        if not p.exists():
            err.append(f"falta {p.name}")
            continue
        datos[n] = json.loads(p.read_text(encoding="utf-8"))
        _registro(datos[n], CABECERA, n, err)
    sint = {d.get("sintetico") for d in datos.values()}
    if len(sint) > 1:
        err.append("todos los JSON deben tener el mismo valor de 'sintetico'")
    s = next(iter(sint), None)

    if "predicciones" in datos:
        d = datos["predicciones"]
        for k in ("fecha_hoy", "zonas", "predicciones"):
            if k not in d:
                err.append(f"predicciones: falta '{k}'")
        for i, r in enumerate(d.get("predicciones", [])):
            _registro(r, PRED, f"predicciones[{i}]", err)
            if r.get("sintetico") != s:
                err.append(f"predicciones[{i}]: sintetico distinto de la cabecera")
            if r.get("color") != "gris" and len(r.get("factores", [])) != 3:
                err.append(f"predicciones[{i}]: debe tener 3 factores")
            for j, f in enumerate(r.get("factores", [])):
                _registro(f, FACTOR, f"predicciones[{i}].factores[{j}]", err)
            if r.get("p10") is not None and r.get("p90") is not None and r["p10"] > r["p90"]:
                err.append(f"predicciones[{i}]: p10 > p90")
        if not any(r.get("conjunto") == "futuro_largo" for r in d.get("predicciones", [])):
            err.append("predicciones: falta el conjunto futuro_largo")
    if "alternativas" in datos:
        for i, r in enumerate(datos["alternativas"].get("alternativas", [])):
            _registro(r, ALT, f"alternativas[{i}]", err)
    if "regulacion" in datos:
        d = datos["regulacion"]
        for k in ("por_zona", "lagos", "calendario_alertas"):
            if k not in d:
                err.append(f"regulacion: falta '{k}'")
        for z in d.get("por_zona", []):
            for i, a in enumerate(z.get("anios", [])):
                _registro(a, ANIO, f"regulacion.{z.get('zona_mitma_id')}.anios[{i}]", err)
        for i, r in enumerate(d.get("calendario_alertas", [])[:2000]):
            _registro(r, CAL, f"regulacion.calendario_alertas[{i}]", err)
    if "perfil" in datos:
        for i, r in enumerate(datos["perfil"].get("perfil", [])):
            _registro(r, PERFIL, f"perfil[{i}]", err)
    if "metricas" in datos:
        d = datos["metricas"]
        if d.get("algoritmo") not in ("lightgbm", "xgboost"):
            err.append(f"metricas: 'algoritmo' debe ser lightgbm o xgboost (es {d.get('algoritmo')!r})")
        for k in ("tablas", "fiabilidad", "experimentos"):
            if k not in d:
                err.append(f"metricas: falta '{k}'")
        for i, r in enumerate(d.get("fiabilidad", [])):
            _registro(r, FIAB, f"metricas.fiabilidad[{i}]", err)
    return err


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from util import SALIDAS
    e = validar(SALIDAS)
    print("\n".join(e) if e else "Contrato OK")
    sys.exit(1 if e else 0)
