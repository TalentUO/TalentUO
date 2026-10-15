"""Prueba anti-fuga: ninguna variable usa información posterior a d - h.

Método: para varias fechas de disponibilidad a = d - h, se corrompe (valores
absurdos) todo lo que en las fuentes se conoce después de a y se vuelven a
calcular las variables de la fecha d con horizonte h. Si alguna variable
cambia, es que usaba información del futuro.
- Wikipedia: visitas de días > a.
- Trends: semanas que no han terminado antes de a (sábado >= a).
- Tiempo: previsión `_prev{k}` emitida en fecha - k > a, y la serie base
  (plazo ~0, emitida el propio día) de días > a.
Además: las variables de calendario/eventos no dependen del objetivo y la lista
de variables no contiene observación (AEMET), ERA5, cruceros ni el objetivo.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import features as F  # noqa: E402
from util import leer_mapeo  # noqa: E402

HORIZONTES = [1, 2, 3, 4, 5, 6, 7]
DISPONIBILIDAD = ["2023-03-15", "2024-02-03", "2024-08-10", "2025-01-04", "2025-06-01"]


@pytest.fixture(scope="module")
def entorno():
    return leer_mapeo("sintetico"), F.cargar_tablas()


def _corromper_interes(tablas, a):
    rng = np.random.default_rng(0)
    w = tablas["wikipedia_diario"].copy()
    fut = w["fecha"] > a
    w.loc[fut, "visitas"] = rng.integers(10**6, 10**7, fut.sum())
    t = tablas["trends_semanal"].copy()
    fin_semana = pd.to_datetime(t["semana_inicio"]) + pd.Timedelta(days=6)
    fut = fin_semana >= a
    t.loc[fut, "valor"] = 999
    return w, t


def _corromper_tiempo(om, a):
    om = om.copy()
    for c in om.columns:
        m = None
        for k in (1, 2, 3):
            if c.endswith(f"_prev{k}"):
                m = (om["fecha"] - pd.Timedelta(days=k)) > a
        if m is None and c in F.VARS_TIEMPO.values():
            m = om["fecha"] > a
        if m is not None:
            om.loc[m, c] = -999.0
    return om


def _iguales(a: pd.DataFrame, b: pd.DataFrame, cols):
    for c in cols:
        x, y = a[c].to_numpy(dtype=float), b[c].to_numpy(dtype=float)
        assert np.array_equal(np.isnan(x), np.isnan(y)) and np.allclose(x[~np.isnan(x)], y[~np.isnan(y)]), c


@pytest.mark.parametrize("a", DISPONIBILIDAD)
@pytest.mark.parametrize("h", HORIZONTES)
def test_interes_sin_futuro(entorno, a, h):
    mapeo, tablas = entorno
    a = pd.Timestamp(a)
    d = pd.DatetimeIndex([a + pd.Timedelta(days=h)])
    limpio = F.interes(tablas["wikipedia_diario"], tablas["trends_semanal"], mapeo, h, d)
    w, t = _corromper_interes(tablas, a)
    corrupto = F.interes(w, t, mapeo, h, d)
    cols = [c for c in limpio.columns if c.startswith("int_")]
    assert len(cols) >= 3
    _iguales(limpio, corrupto, cols)
    assert limpio[cols].notna().any().any()


@pytest.mark.parametrize("a", DISPONIBILIDAD)
@pytest.mark.parametrize("h", HORIZONTES)
def test_tiempo_sin_futuro(entorno, a, h):
    mapeo, tablas = entorno
    a = pd.Timestamp(a)
    d = a + pd.Timedelta(days=h)
    om = tablas["openmeteo_diario"]
    limpio = F.tiempo(om, mapeo, h, modo="estricto")
    corrupto = F.tiempo(_corromper_tiempo(om, a), mapeo, h, modo="estricto")
    limpio, corrupto = limpio[limpio["fecha"] == d], corrupto[corrupto["fecha"] == d]
    _iguales(limpio, corrupto, [c for c in limpio.columns if c.startswith(("tv_", "tm_"))])


def test_la_prueba_detecta_fuga_en_modo_aproximado(entorno):
    """Control: el modo `aproximado` usa la serie base (emitida el propio día) y
    la prueba debe detectarlo. Si esto no fallara, la prueba no serviría."""
    mapeo, tablas = entorno
    a, h = pd.Timestamp("2024-08-10"), 5
    d = a + pd.Timedelta(days=h)
    om = tablas["openmeteo_diario"]
    limpio = F.tiempo(om, mapeo, h, modo="aproximado")
    corrupto = F.tiempo(_corromper_tiempo(om, a), mapeo, h, modo="aproximado")
    x = limpio[limpio["fecha"] == d]["tv_tmax"].to_numpy()
    y = corrupto[corrupto["fecha"] == d]["tv_tmax"].to_numpy()
    assert not np.allclose(x, y)


def test_lista_de_variables_sin_fuentes_prohibidas(entorno):
    mapeo, tablas = entorno
    base = F.tabla_base(mapeo, tablas)
    fechas = pd.date_range("2024-06-01", "2024-06-03")
    corto = F.tabla_corto(base, mapeo, tablas, fechas, horizontes=[1, 7])
    largo = F.tabla_largo(base[base["fecha"].isin(fechas)], list(mapeo["zona_mitma_id"]))
    prohibidas = ("om_", "aemet_", "era5", "wiki_", "trends_", "crucero", "llegadas", "pernoctaciones",
                  "visitas", "normal", "b1_", "calidad", "ev_crucero", "ev_partido_futbol")
    for tipo, t in (("corto", corto), ("largo", largo)):
        feats = F.columnas_modelo(t, tipo)
        malas = [f for f in feats if f.startswith(prohibidas)]
        assert not malas, (tipo, malas)
        if tipo == "largo":
            assert not [f for f in feats if f.startswith(("tv_", "tm_", "int_"))], "largo plazo sin tiempo ni interés"


def test_calendario_no_depende_del_objetivo(entorno):
    """tabla_base no recibe el objetivo: sus variables son las mismas con
    cualquier objetivo (se conoce de antemano)."""
    import inspect
    for fn in (F.tabla_base, F.tabla_corto, F.tabla_largo, F.tiempo, F.interes):
        params = set(inspect.signature(fn).parameters)
        assert not params & {"obj", "objetivo", "y"}, fn.__name__
