"""Prueba de unir_B con un conjunto pequeño y sintético (no usa data/clean).

    python -X utf8 src/limpieza_B/test_unir_B.py

Casos cubiertos: zona con dos concejos (un mismo evento en ambos cuenta una
vez), zona sin estación AEMET, hueco en AEMET (fila presente con NaN),
evento de varios días, festivo local con nombre bilingüe, artículos de
Wikipedia en ancho, y error si el mapeo está incompleto.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from unir_B import unir_B  # noqa: E402

F = pd.date_range("2024-07-01", "2024-07-10", freq="D")


def tablas():
    cal = pd.DataFrame({"fecha": F, "es_fin_de_semana": F.dayofweek >= 5, "festivo_ast": False})
    om = pd.concat([pd.DataFrame({"fecha": F, "zona_meteo": z, "tmax": np.arange(len(F)) + k,
                                  "es_reanalisis": False, "fuente": "x"})
                    for k, z in enumerate(["covadonga", "gijon", "lagos_enol"])])
    ae = pd.DataFrame({"fecha": F, "estacion": "1186P", "tmax": np.arange(len(F), dtype=float),
                       "prec": 1.0, "fuente": "x", "nombre": "AMIEVA"})
    ae = ae[ae["fecha"] != "2024-07-05"]                      # hueco en la fuente
    ae.loc[ae["fecha"] == "2024-07-06", "tmax"] = np.nan
    fl = pd.DataFrame({"fecha": pd.to_datetime(["2024-07-08", "2024-07-09", "2024-07-03", "2024-07-03", "2024-07-06"]),
                       "concejo": ["Gijón/Xixón", "Oviedo", "Onís", "Cangas de Onís", "Onís"],
                       "nombre": ["Begoña", "x", "San X en Benia", "Fiesta", "San Y en Benia"],
                       "festivo_parcial": pd.array([False, False, True, False, True], dtype="boolean")})
    ev = pd.DataFrame({
        "fecha": pd.to_datetime(["2024-07-02", "2024-07-03", "2024-07-04", "2024-07-04", "2024-07-07"]),
        "concejo": ["Cangas de Onís", "Cangas de Onís", "Onís", "Cangas de Onís", "Gijón"],
        "evento": ["Feria A", "Feria A", "Romería B", "Romería B", "Partido"],
        "tipo": ["feria", "feria", "romeria", "romeria", "partido_futbol"],
        "estado": ["verificado", "verificado", "probable", "probable", "probable"],
        "partido_oviedo": False, "partido_sporting": [False] * 4 + [True]})
    wk = pd.concat([pd.DataFrame({"fecha": F, "articulo": a, "visitas": 10,
                                  "visitas_media7_ant": [np.nan] * 7 + [10.0] * 3})
                    for a in ["covadonga", "llanes"]])
    # Trends: semanas que empiezan en domingo (2024-06-23, 06-30, 07-07)
    tr = pd.DataFrame({"semana_inicio": pd.to_datetime(["2024-06-23", "2024-06-30", "2024-07-07"] * 2),
                       "termino": ["lagos de covadonga"] * 3 + ["llanes"] * 3, "geo": "ES",
                       "valor": [1, 2, 3, 4, 5, 6], "is_partial": [False, False, True] * 2,
                       "fiable": [True] * 3 + [False] * 3})
    pa = pd.DataFrame({"fecha": F, "partido_oviedo": False, "partido_sporting": F == "2024-07-07"})
    return {"trends_semanal": tr, "partidos_diario": pa, "calendario_diario": cal, "openmeteo_diario": om, "aemet_diario": ae,
            "festivos_locales": fl, "eventos_diario": ev, "wikipedia_diario": wk}


MAPEO = pd.DataFrame({
    "zona_mitma_id": ["Z1", "Z2"], "nombre": ["Cangas+Onís", "Gijón"],
    "concejos_ine": ["33012;33043", "33024"], "zona_meteo": ["covadonga", "gijon"],
    "zona_meteo_montana": ["lagos_enol", None],
    "estacion_aemet": ["1186P", None], "concejo_eventos": ["Cangas de Onís;Onís", "Gijón"]})


def test_basico():
    out = unir_B(MAPEO, tablas=tablas(), fecha_ini="2024-07-01", fecha_fin="2024-07-10", salida=None)
    assert len(out) == 20 and not out.duplicated(["fecha", "zona_mitma_id"]).any()
    z1 = out[out.zona_mitma_id == "Z1"].set_index("fecha")
    z2 = out[out.zona_mitma_id == "Z2"].set_index("fecha")
    # meteo por zona
    assert z2.loc["2024-07-01", "om_tmax"] == 1 and z1.loc["2024-07-01", "om_tmax"] == 0
    # AEMET: hueco -> fila presente con NaN; zona sin estación -> NaN
    assert np.isnan(z1.loc["2024-07-05", "aemet_tmax"]) and np.isnan(z1.loc["2024-07-06", "aemet_tmax"])
    assert z2["aemet_tmax"].isna().all()
    # eventos: el mismo evento en dos concejos de Z1 cuenta una vez
    assert z1.loc["2024-07-04", "ev_n"] == 1 and z1.loc["2024-07-02", "ev_n_verificado"] == 1
    assert z1["ev_feria"].sum() == 2 and z1.loc["2024-07-01", "ev_n"] == 0
    # partidos: por concejo en ev_*, y globales (todas las zonas) en futbol_*
    assert z2.loc["2024-07-07", "ev_partido_futbol"] and not z1["ev_partido_futbol"].any()
    assert z1.loc["2024-07-07", "futbol_partido_sporting"] and z2.loc["2024-07-07", "futbol_partido_sporting"]
    # festivo local con nombre bilingüe
    assert z2.loc["2024-07-08", "festivo_local"] and z2["festivo_local"].sum() == 1
    assert "aemet_nombre" not in out.columns and "om_fuente" not in out.columns
    # punto de montaña solo en Z1
    assert z1.loc["2024-07-01", "om_montana_tmax"] == 2 and z2["om_montana_tmax"].isna().all()
    # fiestas parciales: 07-03 hay una de todo el concejo -> no parcial; 07-06 solo parcial
    assert z1.loc["2024-07-03", "festivo_local"] and not z1.loc["2024-07-03", "festivo_local_parcial"]
    assert z1.loc["2024-07-06", "festivo_local"] and z1.loc["2024-07-06", "festivo_local_parcial"]
    assert not z1.loc["2024-07-01", "festivo_local_parcial"]
    # Wikipedia: solo la media de 7 días anteriores, no el valor del mismo día
    assert {"wiki_covadonga_media7_ant", "wiki_llanes_media7_ant"} <= set(out.columns)
    assert "wiki_covadonga" not in out.columns and np.isnan(z1.loc["2024-07-01", "wiki_covadonga_media7_ant"])
    # Trends: semana anterior completa; 07-01..06 (semana del 06-30) -> semana 06-23 = 1;
    # 07-07 (semana del 07-07) -> semana 06-30 = 2; serie no fiable fuera
    t = z1["trends_lagos_de_covadonga_ES_sem_ant"]
    assert (t.loc["2024-07-01":"2024-07-06"] == 1).all() and (t.loc["2024-07-07":] == 2).all()
    assert not any(c.startswith("trends_llanes") for c in out.columns)


def test_mapeo_incompleto():
    m = MAPEO.copy()
    m.loc[0, "zona_mitma_id"] = None
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "m.csv"
        m.to_csv(p, index=False)
        try:
            unir_B(p, tablas=tablas(), salida=None)
        except ValueError as e:
            assert "zona_mitma_id" in str(e)
        else:
            raise AssertionError("debería fallar con mapeo incompleto")


if __name__ == "__main__":
    test_basico()
    test_mapeo_incompleto()
    print("test_unir_B: OK (2 pruebas)")
