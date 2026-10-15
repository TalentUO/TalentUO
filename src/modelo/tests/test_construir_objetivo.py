"""Prueba construir_objetivo con ficheros pequeños inventados en los dos formatos."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from construir_objetivo import construir, leer_zonas  # noqa: E402

VIAJES_MITMA = """fecha|periodo|origen|destino|actividad_origen|actividad_destino|residencia|viajes
20231025|10|33044|33012|casa|frecuente|33|10.5
20231025|11|28079|33012|casa|no_frecuente|28|20
20231025|12|33044|33012|casa|trabajo_estudio|33|7
20231025|12|33012|33012|casa|frecuente|33|99
20231025|13|33012|33044|frecuente|casa|33|3
20231026|10|33044|33012|casa|frecuente|33|5
20231028|10|28079|33012|casa|no_frecuente|28|4
"""
VIAJES_SOD = """date,hour,id_origin,id_destination,activity_destination,residence_province_ine_code,n_trips
2023-10-25,10,33044,33012,frequent_activity,33,10.5
2023-10-25,11,28079,33012,infrequent_activity,28,20
2023-10-25,12,33044,33012,work_or_study,33,7
2023-10-25,12,33012,33012,frequent_activity,33,99
2023-10-25,13,33012,33044,home,33,3
2023-10-26,10,33044,33012,frequent_activity,33,5
2023-10-28,10,28079,33012,infrequent_activity,28,4
"""
PERN_MITMA = """fecha|zona_residencia|zona_pernoctacion|personas
20231025|28079|33012|12
20231025|33012|33012|500
20231025|33044|33012|3
20231028|28079|33012|2
"""
PERN_SOD = """date,id_residence,id_overnight_stay,n_persons
2023-10-25,28079,33012,12
2023-10-25,33012,33012,500
2023-10-25,33044,33012,3
2023-10-28,28079,33012,2
"""


def _caso(tmp_path, viajes, pern, nombre):
    fv, fp = tmp_path / f"v_{nombre}.csv", tmp_path / f"p_{nombre}.csv"
    fv.write_text(viajes, encoding="utf-8")
    fp.write_text(pern, encoding="utf-8")
    return construir([fv], [fp], ["33012", "33044"], "2023-10-25", "2023-10-29")


def _comprobar(out):
    c = out.set_index(["zona_mitma_id", "fecha"])
    d25 = c.loc[("33012", pd.Timestamp("2023-10-25"))]
    assert d25["llegadas_total"] == 37.5          # sin el viaje interno (origen = destino)
    assert d25["llegadas_ocio"] == 30.5           # sin trabajo/estudio
    assert d25["llegadas_desde_asturias"] == 10.5
    assert d25["llegadas_resto_espana"] == 20
    assert d25["llegadas_total_desde_asturias"] == 17.5   # ocio 10,5 + trabajo 7
    assert d25["llegadas_total_resto_espana"] == 20
    assert d25["pernoctaciones_no_residentes"] == 15  # sin los residentes de la zona
    assert d25["calidad"] == "completa"
    # 33044 recibe un viaje de vuelta a casa: llega, pero no es ocio
    o25 = c.loc[("33044", pd.Timestamp("2023-10-25"))]
    assert o25["llegadas_total"] == 3 and o25["llegadas_ocio"] == 0
    # 26-oct-2023 es sin_dato_mitma por configuración aunque haya filas -> NaN
    d26 = c.loc[("33012", pd.Timestamp("2023-10-26"))]
    assert d26["calidad"] == "sin_dato_mitma" and np.isnan(d26["llegadas_ocio"])
    # 29-oct no está en los ficheros -> ausente (NaN), nunca 0
    d29 = c.loc[("33012", pd.Timestamp("2023-10-29"))]
    assert d29["calidad"] == "sin_dato_mitma" and np.isnan(d29["llegadas_total"])
    # 28-oct tiene datos de otra zona: 33044 sin llegadas ese día = 0 real
    o28 = c.loc[("33044", pd.Timestamp("2023-10-28"))]
    assert o28["calidad"] == "completa" and o28["llegadas_total"] == 0
    assert len(out) == 2 * 5


def test_formato_mitma(tmp_path):
    _comprobar(_caso(tmp_path, VIAJES_MITMA, PERN_MITMA, "mitma"))


def test_formato_spanishoddata(tmp_path):
    _comprobar(_caso(tmp_path, VIAJES_SOD, PERN_SOD, "sod"))


def test_los_dos_formatos_dan_lo_mismo(tmp_path):
    a = _caso(tmp_path, VIAJES_MITMA, PERN_MITMA, "mitma")
    b = _caso(tmp_path, VIAJES_SOD, PERN_SOD, "sod")
    pd.testing.assert_frame_equal(a, b)


def test_lectura_por_trozos_da_lo_mismo(tmp_path):
    """Con trozos de 1 fila (un mes real no cabe entero en memoria) el resultado es idéntico."""
    fv, fp = tmp_path / "v.csv", tmp_path / "p.csv"
    fv.write_text(VIAJES_MITMA, encoding="utf-8")
    fp.write_text(PERN_MITMA, encoding="utf-8")
    entero = construir([fv], [fp], ["33012", "33044"], "2023-10-25", "2023-10-29")
    for trozo in (1, 2, 3):
        pd.testing.assert_frame_equal(
            entero, construir([fv], [fp], ["33012", "33044"], "2023-10-25", "2023-10-29", trozo=trozo))


def test_zonas_con_columna_id_zona_mitma(tmp_path):
    """zonas_mitma_asturias.csv (parte A) usa `id_zona_mitma`; debe aceptarse igual que `zona_mitma_id` o `id`."""
    for col in ("id_zona_mitma", "zona_mitma_id", "id"):
        f = tmp_path / f"zonas_{col}.csv"
        f.write_text(f"{col},nombre\n33012,Cangas de Onís\n33044,Oviedo\n", encoding="utf-8")
        assert leer_zonas(f)["zona_mitma_id"].tolist() == ["33012", "33044"]
