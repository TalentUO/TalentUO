"""Validación por bloques temporales y experimentos de sensibilidad.

Para cada bloque se entrena con todo lo anterior (desde el inicio de
entrenamiento) y se evalúa en el bloque. El día normal del bloque se calcula
con los 365 días anteriores (sin fuga); el semáforo usa el normal de
referencia. Líneas base:
- B0 (día normal): cociente 1 siempre -> visitantes = normal del bloque.
- B1 (mismo día de la semana del año anterior, 364 días antes): solo
  referencia, no desplegable (el MITMA no se publica en tiempo real).
Los días sin dato o con anomalía del MITMA no se entrenan ni se evalúan.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import dia_normal
import features as F
import modelo as M
from datos import Datos
from util import a_log_cociente, cfg, colores, desde_log_cociente

EXPERIMENTOS = {
    "base": dict(desde=None, modo="estricto", verificados=False, modelos=("largo", "corto")),
    # sensibilidad: entrenar solo desde el corte del reanálisis (2022-11-09), como antes de 2026-10-15
    "desde_corte": dict(desde="corte", modo="estricto", verificados=False, modelos=("largo", "corto")),
    "solo_eventos_verificados": dict(desde=None, modo="estricto", verificados=True, modelos=("largo", "corto")),
    "tiempo_aproximado": dict(desde=None, modo="aproximado", verificados=False, modelos=("corto",)),
}


def inicio_entrenamiento(desde: str | None = None) -> pd.Timestamp:
    v = desde or cfg()["inicio_entrenamiento"]
    return pd.Timestamp(cfg()["corte_reanalisis"] if v == "corte" else v)


def tablas_experimento(D: Datos, exp: dict) -> dict[str, pd.DataFrame]:
    ini = inicio_entrenamiento(exp["desde"])
    fin = pd.Timestamp(cfg()["objetivo_periodo"]["fin"])
    base = F.tabla_base(D.mapeo, D.tablas, solo_eventos_verificados=True) if exp["verificados"] else D.base
    fechas = pd.date_range(ini, fin, freq="D")
    obj = D.obj[["fecha", "zona_mitma_id", D.objetivo, "calidad"]]
    b1 = D.obj[["fecha", "zona_mitma_id", D.objetivo, "calidad"]].copy()
    b1 = b1[b1["calidad"] == "completa"]
    b1["fecha"] = b1["fecha"] + pd.Timedelta(days=364)
    b1 = b1.rename(columns={D.objetivo: "b1_visitas"})[["fecha", "zona_mitma_id", "b1_visitas"]]
    out = {}
    for tipo in exp["modelos"]:
        if tipo == "largo":
            t = F.tabla_largo(base[base["fecha"].isin(fechas)], D.zonas)
        else:
            t = F.tabla_corto(base, D.mapeo, D.tablas, fechas, modo_tiempo=exp["modo"],
                              desde_reanalisis=False)  # el tiempo del reanálisis no se usa nunca
        t = (t.merge(obj, on=["fecha", "zona_mitma_id"], how="left", validate="many_to_one")
             .merge(b1, on=["fecha", "zona_mitma_id"], how="left", validate="many_to_one"))
        t = dia_normal.anadir_normal(t, D.normal_ref, "normal_ref")
        out[tipo] = t
    return out


def ejecutar(D: Datos, experimentos: list[str] | None = None, algoritmos: list[str] | None = None,
            log=print) -> pd.DataFrame:
    """Una fila por predicción de prueba; columnas `algoritmo` y `segundos_entrenamiento`."""
    experimentos = experimentos or list(EXPERIMENTOS)
    algoritmos = algoritmos or [M.algoritmo_por_defecto()]
    filas = []
    for nombre in experimentos:
        exp = EXPERIMENTOS[nombre]
        tabs = tablas_experimento(D, exp)
        for bl in cfg()["bloques_validacion"]:
            ini, fin = pd.Timestamp(bl["inicio"]), pd.Timestamp(bl["fin"])
            nb = dia_normal.normal_ventana(D.obj, D.base, D.objetivo, ini)
            for tipo, t, alg in [(tp, tb, a) for tp, tb in tabs.items() for a in algoritmos]:
                t = dia_normal.anadir_normal(t, nb, "normal_bt")
                feats = F.columnas_modelo(t, tipo)
                ok = (t["calidad"] == "completa") & t[D.objetivo].notna() & t["normal_bt"].notna()
                tr = ok & (t["fecha"] < ini)
                te = ok & (t["fecha"] >= ini) & (t["fecha"] <= fin)
                y = a_log_cociente(t[D.objetivo], t["normal_bt"])
                m, info = M.entrenar(t[tr].reset_index(drop=True), feats, y[tr.to_numpy()], alg)
                x = t[te].reset_index(drop=True)
                p = M.predecir(m, x, feats)
                r = x[["fecha", "zona_mitma_id", "horizonte", "normal_bt", "normal_ref", "b1_visitas"]].copy()
                r["experimento"], r["modelo"], r["bloque"] = nombre, tipo, bl["nombre"]
                r["visitas_obs"] = x[D.objetivo].to_numpy()
                r["y_pred"] = p
                r["visitas_pred"] = desde_log_cociente(p, x["normal_bt"])
                r["b0_visitas"] = x["normal_bt"].to_numpy()
                r["n_arboles"] = info["n_arboles"]
                r["algoritmo"] = alg
                r["segundos_entrenamiento"] = info["segundos_entrenamiento"]
                if nombre == "base":
                    sv, _ = M.shap(m, x, feats)
                    fx = M.sumar_por_factor(sv, feats)
                    for c in fx.columns:
                        r[f"fx_{c}"] = fx[c].to_numpy()
                filas.append(r)
                log(f"  [{nombre}/{alg}] {bl['nombre']} {tipo}: {tr.sum()} filas de entrenamiento, "
                    f"{te.sum()} de prueba, {info['n_arboles']} árboles, {info['segundos_entrenamiento']:.1f} s")
    bt = pd.concat(filas, ignore_index=True)
    for col, q in (("visitas_obs", "cociente_obs"), ("visitas_pred", "cociente_pred"),
                   ("b0_visitas", "cociente_b0"), ("b1_visitas", "cociente_b1")):
        bt[q] = bt[col] / bt["normal_ref"]
    bt["color_obs"] = colores(bt["cociente_obs"], bt["zona_mitma_id"])
    bt["color_pred"] = colores(bt["cociente_pred"], bt["zona_mitma_id"])
    bt["color_b0"] = colores(bt["cociente_b0"], bt["zona_mitma_id"])
    bt["color_b1"] = colores(bt["cociente_b1"], bt["zona_mitma_id"])
    bt["y_obs_bt"] = a_log_cociente(bt["visitas_obs"], bt["normal_bt"])
    bt["residuo_log"] = np.log((bt["visitas_obs"] + 1) / (bt["visitas_pred"] + 1))
    bt["sintetico"] = D.sintetico
    return bt
