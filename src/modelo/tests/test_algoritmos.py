"""Pruebas de los dos algoritmos (LightGBM y XGBoost).

1. Anti-fuga de punta a punta: con cada algoritmo, un modelo de corto plazo
   entrenado una vez da exactamente la misma predicción para (d, h) tanto si
   las fuentes están intactas como si se corrompe todo lo publicado después
   de d - h. (La prueba de variables está en test_antifuga.py y no depende del
   algoritmo.)
2. Contrato de la web: la cadena completa con el objetivo sintético y cada
   algoritmo genera JSON que cumplen notas/contrato_web.md. Se escribe en una
   carpeta temporal (MODELO_SALIDAS) para no tocar salidas/. Tarda ~1-2 min
   por algoritmo.
"""
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import features as F  # noqa: E402
import modelo as M  # noqa: E402
from test_antifuga import _corromper_interes, _corromper_tiempo  # noqa: E402
from util import leer_mapeo  # noqa: E402
from validar_salidas import validar  # noqa: E402


@pytest.fixture(scope="module")
def entorno():
    mapeo, tablas = leer_mapeo("sintetico"), F.cargar_tablas()
    base = F.tabla_base(mapeo, tablas)
    fechas = pd.date_range("2024-01-22", "2024-12-31")
    t = F.tabla_corto(base, mapeo, tablas, fechas)
    feats = F.columnas_modelo(t, "corto")
    # objetivo cualquiera (determinista) que depende de tiempo e interés, para que el modelo los use
    rng = np.random.default_rng(0)
    y = (0.5 * t["cal_fin_de_semana"] - 0.05 * t["tv_prec"].fillna(0) + 0.1 * t["int_wiki_picos"].fillna(6)
         + rng.normal(0, 0.05, len(t))).to_numpy()
    return mapeo, tablas, base, t, feats, y


@pytest.mark.parametrize("algoritmo", M.ALGORITMOS)
@pytest.mark.parametrize("a", ["2024-08-10", "2025-01-04"])
def test_prediccion_sin_futuro(entorno, algoritmo, a):
    mapeo, tablas, base, t, feats, y = entorno
    m, _ = M.entrenar(t, feats, y, algoritmo)
    a = pd.Timestamp(a)
    for h in (1, 3, 7):
        d = pd.DatetimeIndex([a + pd.Timedelta(days=h)])
        limpio = F.tabla_corto(base, mapeo, tablas, d, horizontes=[h])
        w, tr = _corromper_interes(tablas, a)
        corr = dict(tablas, wikipedia_diario=w, trends_semanal=tr,
                    openmeteo_diario=_corromper_tiempo(tablas["openmeteo_diario"], a))
        corrupto = F.tabla_corto(base, mapeo, corr, d, horizontes=[h])
        p1, p2 = M.predecir(m, limpio), M.predecir(m, corrupto)
        assert np.allclose(p1, p2), (algoritmo, a, h)
        s1, _ = M.shap(m, limpio)
        s2, _ = M.shap(m, corrupto)
        assert np.allclose(s1, s2), (algoritmo, a, h)


@pytest.mark.parametrize("algoritmo", M.ALGORITMOS)
def test_shap_suma_la_prediccion(entorno, algoritmo):
    mapeo, tablas, base, t, feats, y = entorno
    m, _ = M.entrenar(t, feats, y, algoritmo)
    x = t.head(200)
    sv, b = M.shap(m, x)
    assert np.allclose(sv.sum(axis=1) + b, M.predecir(m, x), atol=1e-4)


@pytest.mark.lento
@pytest.mark.parametrize("algoritmo", M.ALGORITMOS)
def test_contrato_web_con_cada_algoritmo(tmp_path, algoritmo):
    env = dict(os.environ, MODELO_SALIDAS=str(tmp_path))
    r = subprocess.run([sys.executable, "-X", "utf8", str(AQUI / "ejecutar.py"), "--objetivo", "sintetico",
                        "--algoritmo", algoritmo], env=env, capture_output=True, text=True, encoding="utf-8",
                       timeout=900)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
    assert validar(tmp_path) == []
    import json
    m = json.loads((tmp_path / "metricas.json").read_text(encoding="utf-8"))
    assert m["algoritmo"] == algoritmo and m["sintetico"] is True


def _crit(rl, pl, fl, wl, rx, px, fx, wx):
    return pd.DataFrame({"recall_rojo_verano": [rl, rx], "precision_rojo_verano": [pl, px],
                         "f1_rojo_verano": [fl, fx], "wape_medio": [wl, wx],
                         "segundos_entrenamiento_total": [1, 1]}, index=["lightgbm", "xgboost"])


@pytest.mark.parametrize("caso,esperado,paso,criterio", [
    # más recall sin perder más de 5 puntos de precisión -> decide el recall
    (_crit(.70, .80, .75, .12, .75, .77, .76, .12), "xgboost", 1, "recall"),
    # más recall pero 8 puntos menos de precisión -> decide el F1 (LightGBM, +4)
    (_crit(.70, .85, .77, .12, .75, .77, .73, .12), "lightgbm", 1, "F1"),
    # F1 empatado (< 3 puntos) -> menor WAPE (XGBoost, -2 puntos)
    (_crit(.70, .85, .77, .12, .75, .77, .76, .10), "xgboost", 2, "F1"),
    # todo empatado -> LightGBM
    (_crit(.70, .80, .75, .12, .72, .79, .75, .115), "lightgbm", 3, "recall"),
    # recall empatado aunque XGBoost tenga algo más -> WAPE (LightGBM mejor)
    (_crit(.70, .80, .75, .10, .72, .80, .76, .12), "lightgbm", 2, "recall"),
])
def test_regla_de_eleccion(caso, esperado, paso, criterio):
    import comparacion
    e = comparacion.elegir(caso)
    assert e["ganador"] == esperado and e["paso_de_la_regla"] == paso and criterio in e["criterio_decisivo"], e
