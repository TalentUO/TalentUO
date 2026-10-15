"""Detecta, por zona, en que fecha la serie Historical Forecast de Open-Meteo deja de ser
identica a ERA5 (reanalisis) y pasa a ser prevision archivada.

Solo lectura sobre data/raw/openmeteo_<zona>.json y openmeteo_archive_<zona>.json.
Uso: python -X utf8 src/auditoria/tramo_2022_openmeteo.py
"""
import csv
import json
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
VARS = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "precipitation_hours",
        "sunshine_duration", "wind_speed_10m_max", "wind_gusts_10m_max", "weather_code"]
# variables en las que el reanalisis y la prevision coinciden exactamente cuando la "prevision" es ERA5
CLAVE = ["precipitation_sum", "precipitation_hours", "wind_speed_10m_max", "wind_gusts_10m_max", "weather_code"]
TOL = 1e-6


def carga(p):
    return json.loads(p.read_text("utf-8"))["daily"]


def main():
    zonas = [r["zona"] for r in csv.DictReader(open(RAW.parent.parent / "config" / "zonas_meteo.csv", encoding="utf-8"))]
    resumen = []
    for z in zonas:
        h, a = carga(RAW / f"openmeteo_{z}.json"), carga(RAW / f"openmeteo_archive_{z}.json")
        assert h["time"] == a["time"]
        t = h["time"]
        ident = {v: [abs(x - y) <= TOL for x, y in zip(h[v], a[v])] for v in VARS}
        todas5 = [all(ident[v][i] for v in CLAVE) for i in range(len(t))]
        # ultima fecha con las 5 variables clave identicas dentro de 2022-2023 (fin del tramo reanalisis)
        ult = max(i for i, d in enumerate(t) if d < "2024-01-01" and todas5[i])
        # inicio del ultimo bloque continuo de identidad que acaba en ult (>= 7 dias)
        # primera fecha tras la cual ya no hay ninguna racha de >= 7 dias identicos
        racha, fin_racha = 0, None
        for i, d in enumerate(t):
            racha = racha + 1 if todas5[i] else 0
            if racha >= 7:
                fin_racha = i
        pre = range(0, ult + 1)
        post = range(ult + 1, len(t))
        mes = {}
        for i, d in enumerate(t[:ult + 120]):
            mes.setdefault(d[:7], []).append(todas5[i])
        fila = {
            "zona": z, "ultimo_dia_identico_5_vars": t[ult], "primer_dia_prevision": t[ult + 1],
            "dias_reanalisis_2022": len(pre),
            "ident_pre_%": {v: round(100 * sum(ident[v][i] for i in pre) / len(pre), 1) for v in VARS},
            "ident_post_%": {v: round(100 * sum(ident[v][i] for i in post) / len(post), 1) for v in VARS},
            "ultima_racha>=7_dias": t[fin_racha],
            "mensual_5vars_%": {m: round(100 * sum(v) / len(v)) for m, v in mes.items() if m >= "2022-08"},
        }
        resumen.append(fila)
        print(json.dumps(fila, ensure_ascii=False))
    return resumen


if __name__ == "__main__":
    main()
