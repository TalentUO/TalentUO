"""Ejecuta el modelo de principio a fin.

    python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos   # el que publica la web
    python -X utf8 src/modelo/ejecutar.py --objetivo sintetico                # prueba de la cadena con efectos conocidos

Pasos: datos y variables -> (objetivo sintético) -> validación por bloques y
experimentos -> métricas y fiabilidad -> modelos finales -> factores (SHAP) ->
calibración con la regulación de los Lagos -> JSON de la web -> comprobación
del contrato. Todo con semilla fija; con datos reales y --algoritmo ambos tarda unos 15 min.
"""
from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Solo los avisos informativos de las librerías del modelo; los de pandas y numpy siguen saliendo.
warnings.filterwarnings("ignore", category=UserWarning, module=r"(lightgbm|xgboost|shap|sklearn)")

import backtest  # noqa: E402
import calibracion  # noqa: E402
import comparacion  # noqa: E402
import datos  # noqa: E402
import explicar  # noqa: E402
import metricas  # noqa: E402
import modelo as M  # noqa: E402
import pandas as pd  # noqa: E402
import produccion  # noqa: E402
import validar_salidas  # noqa: E402
import web_salidas  # noqa: E402
from util import SALIDAS, cfg, guardar_json  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--objetivo", choices=["sintetico", "real"], required=True)
    ap.add_argument("--variable", default=None, help="columna objetivo (por defecto, la de config/modelo.yaml)")
    ap.add_argument("--algoritmo", choices=["lightgbm", "xgboost", "ambos"], default=None,
                    help="por defecto, el de config/modelo.yaml (lightgbm)")
    a = ap.parse_args()
    t0 = time.time()

    def log(m):
        print(f"[{time.time() - t0:6.1f} s] {m}", flush=True)

    SALIDAS.mkdir(exist_ok=True)
    log(f"1. Datos ({a.objetivo})")
    D = datos.cargar(a.objetivo, a.variable)
    if D.sintetico:
        log("   OBJETIVO SINTÉTICO: todas las salidas llevan sintetico=True")
    alg = a.algoritmo or cfg().get("algoritmo", "lightgbm")
    comp = None
    log(f"2. Validación por bloques y experimentos (algoritmo: {alg})")
    if alg == "ambos":
        bt_base = backtest.ejecutar(D, ["base"], algoritmos=list(M.ALGORITMOS), log=log)
        comp = comparacion.ejecutar(bt_base, D)
        ganador = comp["eleccion"]["ganador"]
        log(f"   Regla de elección -> {ganador} ({comp['eleccion']['motivo']})"
            + (" [SINTÉTICO: no sirve para elegir]" if D.sintetico else ""))
        resto = [e for e in backtest.EXPERIMENTOS if e != "base"]
        bt_all = pd.concat([bt_base, backtest.ejecutar(D, resto, algoritmos=[ganador], log=log)], ignore_index=True)
    else:
        ganador = alg
        bt_all = backtest.ejecutar(D, algoritmos=[ganador], log=log)
    bt_all.to_parquet(SALIDAS / "backtest.parquet", index=False, compression="zstd", compression_level=9)
    bt = bt_all[bt_all["algoritmo"] == ganador].reset_index(drop=True)

    log("3. Métricas y fiabilidad")
    tablas = metricas.todas(bt)
    cuant = metricas.cuantiles_error(bt)
    notas = metricas.notas(bt)

    log("4. Modelos finales")
    finales = produccion.entrenar_finales(D, ganador, log=log)
    f = finales["corto"]

    log("5. Factores (SHAP)")
    expl = explicar.ejecutar(bt, D, modelo_muestra=(f["modelo"], f["muestra"], f["feats"]))

    log("6. Calibración con la regulación de los Lagos")
    calib = calibracion.ejecutar(D, bt)
    guardar_json(calib, SALIDAS / "calibracion_lagos.json")

    log("7. Salidas para la web")
    resumen_exp = tablas["global"].query("metodo == 'modelo'")[["experimento", "modelo", "n", "wape", "acierto_color",
                                                                 "recall_rojo", "precision_rojo"]]
    extra = {"algoritmo": ganador,
             "experimentos": resumen_exp.to_dict(orient="records"),
             "modelos_finales": {k: v["info"] for k, v in finales.items()},
             "dia_normal": D.normal_ref.to_dict(orient="records"),
             "comprobacion_treeexplainer": expl.get("comprobacion_treeexplainer"),
             "calibracion_lagos": calibracion.resumen(calib)}
    if D.sintetico:
        rec = expl["recuperacion_sintetico"]["modelos"]
        extra["recuperacion_sintetico"] = {k: {kk: vv for kk, vv in v.items() if kk != "tabla"} for k, v in rec.items()}
    web = web_salidas.ejecutar(D, bt, finales, cuant, tablas, notas, calib, extra, log=log)

    log("8. Comprobación del contrato de la web")
    errores = validar_salidas.validar(SALIDAS)
    if errores:
        for e in errores[:30]:
            print("   ERROR:", e)
        raise SystemExit(f"{len(errores)} errores de contrato")

    g = tablas["global"]
    base = g[g["experimento"] == "base"].set_index(["modelo", "metodo"])
    resumen = {
        "sintetico": D.sintetico, "objetivo": D.objetivo, "algoritmo": ganador,
        "seleccion_algoritmo": comp["eleccion"] if comp else None,
        "segundos": round(time.time() - t0, 1),
        "wape": {f"{m}/{met}": base.loc[(m, met), "wape"] for m, met in base.index},
        "recall_rojo": {f"{m}/{met}": base.loc[(m, met), "recall_rojo"] for m, met in base.index},
        "experimentos": resumen_exp.to_dict(orient="records"),
        "calibracion_lagos": {f"{k}/{v}": calib[k][v]["mejor_umbral"]
                              for k in ("observado_2023_2024", "previsto_fuera_de_muestra") if k in calib
                              for v in ("relativo", "absoluto")},
        "info_corto_plazo": web["info_corto"],
    }
    guardar_json(resumen, SALIDAS / "resumen_ejecucion.json")
    titulo = "RESULTADOS SINTÉTICOS (NO REALES)" if D.sintetico else "RESULTADOS"
    if comp:
        print(f"\n=== Comparación de algoritmos "
              f"({'SINTÉTICA: NO SIRVE PARA ELEGIR' if D.sintetico else 'datos reales'}) ===")
        print(pd.DataFrame(comp["criterios"]).round(4).to_string(index=False))
        print(f"Ganador por la regla: {ganador} — {comp['eleccion']['motivo']}")
    print(f"\n=== {titulo} — experimento base, todos los bloques, algoritmo {ganador} ===")
    print(g[g["experimento"] == "base"][["modelo", "metodo", "n", "wape", "acierto_color", "recall_rojo",
                                          "precision_rojo"]].round(3).to_string(index=False))
    log("Hecho. Salidas en salidas/")


if __name__ == "__main__":
    main()
