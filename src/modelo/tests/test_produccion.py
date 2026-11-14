"""La previsión en vivo de Open-Meteo llega a las variables del corto plazo (produccion.tiempo_previsto)."""
import sys
from pathlib import Path

import pandas as pd
import pytest

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


# --------------------------------------------------------------------------
# Interés en internet del corto plazo publicado (revisión de 2026-11-14)
# --------------------------------------------------------------------------

def _interes_publicado():
    """Variables de interés tal como las pide produccion.futuro_corto_con_prevision con las tablas versionadas."""
    from util import CLEAN, cfg, leer_mapeo
    tablas = F.cargar_tablas()
    mapeo = leer_mapeo("real")
    prev = pd.read_parquet(CLEAN / "openmeteo_prevision.parquet")
    a = pd.to_datetime(prev["fecha"]).dt.normalize().min()          # día en que se emitió la previsión
    partes = []
    for h in cfg()["horizontes_corto"]:
        d = pd.DatetimeIndex([a + pd.Timedelta(days=h)])
        partes.append(F.interes(tablas["wikipedia_diario"], tablas["trends_semanal"], mapeo, h + 1, d).assign(horizonte=h))
    return a, tablas["wikipedia_diario"]["fecha"].max(), pd.concat(partes, ignore_index=True), mapeo, tablas


def test_wikipedia_llega_si_la_ventana_esta_completa():
    """Control: con la ventana de 7 días terminada en el último día descargado, la señal de los Picos existe."""
    _, fin_wiki, _, mapeo, tablas = _interes_publicado()
    i = F.interes(tablas["wikipedia_diario"], tablas["trends_semanal"], mapeo, 1, pd.DatetimeIndex([fin_wiki + pd.Timedelta(days=1)]))
    assert i["int_wiki_picos"].notna().all()


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="Confirmado: el corto plazo publicado va sin Wikipedia. La tabla acaba dos días antes de la "
                          "emisión y producción pide la ventana que termina la víspera. Se arregla al regenerar las "
                          "salidas con Wikipedia al día (revision: codigo.md A2); entonces hay que quitar esta marca.")
def test_wikipedia_del_corto_plazo_publicado():
    a, fin_wiki, i, _, _ = _interes_publicado()
    vacias = int(i["int_wiki_picos"].isna().sum())
    assert vacias == 0, (f"int_wiki_picos vacía en {vacias} de {len(i)} filas del corto plazo "
                         f"(previsión emitida el {a.date()}, Wikipedia hasta el {fin_wiki.date()})")
