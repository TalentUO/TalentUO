"""La previsión en vivo de Open-Meteo llega a las variables del corto plazo (produccion.tiempo_previsto)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import features as F  # noqa: E402
from produccion import tiempo_previsto  # noqa: E402


def test_tiempo_previsto_conserva_las_variables():
    a = pd.Timestamp("2026-10-16")
    prev = pd.DataFrame({"fecha": pd.date_range(a, periods=5), "zona_meteo": "oviedo"})
    for i, v in enumerate(F.VARS_TIEMPO.values()):
        prev[v] = [10.0 * (i + 1) + d for d in range(5)]
    extra, hs = tiempo_previsto(prev, a, max_lead=3)
    assert hs == [1, 2, 3]
    assert len(extra) == 3
    for h in hs:
        fila = extra[extra["fecha"] == a + pd.Timedelta(days=h)].iloc[0]
        for i, v in enumerate(F.VARS_TIEMPO.values()):
            assert fila[f"{v}_prev{h}"] == 10.0 * (i + 1) + h


def test_tiempo_previsto_sin_filas():
    a = pd.Timestamp("2026-10-16")
    extra, hs = tiempo_previsto(pd.DataFrame({"fecha": [a], "zona_meteo": ["oviedo"]}), a, max_lead=3)
    assert hs == [] and list(extra.columns) == ["fecha", "zona_meteo"] and extra.empty
