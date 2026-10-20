"""Prueba construir_llegadas_por_hora con los ficheros pequeños inventados de test_construir_objetivo."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from construir_llegadas_por_hora import llegadas_dia_hora, tabla_por_hora  # noqa: E402
from construir_objetivo import construir  # noqa: E402
from test_construir_objetivo import PERN_MITMA, VIAJES_MITMA, VIAJES_SOD  # noqa: E402

ZONAS = ["33012", "33044"]


def _tabla(tmp_path, viajes, trozo=1_000_000):
    fv, fp = tmp_path / "v.csv", tmp_path / "p.csv"
    fv.write_text(viajes, encoding="utf-8")
    fp.write_text(PERN_MITMA, encoding="utf-8")
    obj = construir([fv], [fp], ZONAS, "2023-10-25", "2023-10-29")
    fechas = pd.date_range("2023-10-25", "2023-10-29")
    cal = pd.DataFrame({"fecha": fechas, "es_fin_de_semana": fechas.dayofweek >= 5, "festivo_ast": False})
    dh = llegadas_dia_hora([fv], set(ZONAS), trozo)
    return tabla_por_hora(dh, obj, cal)


def test_horas_y_tipo_de_dia(tmp_path):
    t = _tabla(tmp_path, VIAJES_MITMA).set_index(["zona_mitma_id", "tipo_dia", "hora"])
    # 25-oct (miércoles, completa): 10,5 a las 10 y 20 a las 11; el viaje de trabajo y el interno no cuentan
    assert t.loc[("33012", "laborable", 10), "llegadas_ocio_media"] == 10.5
    assert t.loc[("33012", "laborable", 11), "llegadas_ocio_media"] == 20
    assert t.loc[("33012", "laborable", 12), "llegadas_ocio_media"] == 0           # hora sin ocio en un día con datos = 0 real
    # 28-oct (sábado): 4 a las 10
    assert t.loc[("33012", "fin_de_semana_o_festivo", 10), "llegadas_ocio_media"] == 4
    # 26-oct es sin_dato_mitma por configuración y 29-oct no está en los ficheros: no entran (ni como 0)
    assert (t["n_dias"] == 1).all()
    assert len(t) == 2 * 2 * 24                                                      # 2 zonas x 2 tipos de día x 24 horas


def test_mismo_resultado_con_trozos_y_formato_spanishoddata(tmp_path):
    a = _tabla(tmp_path, VIAJES_MITMA)
    pd.testing.assert_frame_equal(a, _tabla(tmp_path, VIAJES_MITMA, trozo=1))
    pd.testing.assert_frame_equal(a, _tabla(tmp_path, VIAJES_SOD))
