"""Descarga la previsión de 7 días de Open-Meteo para todas las zonas de
config/zonas_meteo.csv (incluido el punto de montaña de los Lagos, lagos_enol).

    python -X utf8 src/modelo/descargar_prevision.py

- Respuestas en bruto: data/prevision/AAAA-MM-DD/<zona>.json (AAAA-MM-DD =
  fecha de emisión = primer día de la previsión). No se toca data/raw/.
- Tabla limpia: data/clean/openmeteo_prevision.parquet, con exactamente las
  mismas columnas y dtypes que openmeteo_prevision_ejemplo (y openmeteo_diario):
  se reutiliza la transformación `diario()` de src/limpieza_B/limpia_openmeteo.py
  sin modificarla. `*_prevN` = NaN; `fuente` = Forecast API (previsión en vivo).
En producción se ejecuta cada mañana antes de `ejecutar.py`.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import CLEAN, CONFIG, RAIZ, importar_limpieza_B  # noqa: E402

URL = "https://api.open-meteo.com/v1/forecast"
TZ = "Europe/Madrid"
DIARIAS = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "precipitation_hours",
           "sunshine_duration", "wind_speed_10m_max", "wind_gusts_10m_max", "weather_code"]
DESTINO = CLEAN / "openmeteo_prevision.parquet"


def descargar(zonas: pd.DataFrame, carpeta: Path) -> dict[str, dict]:
    out = {}
    for z in zonas.itertuples():
        params = {"latitude": z.lat, "longitude": z.lon, "forecast_days": 7, "timezone": TZ,
                  "daily": ",".join(DIARIAS)}
        for intento in range(4):
            try:
                r = requests.get(URL, params=params, timeout=60)
                r.raise_for_status()
                break
            except requests.RequestException as e:
                if intento == 3:
                    raise
                print(f"  {z.zona}: fallo ({e}); reintento")
                time.sleep(5 * (intento + 1))
        d = r.json()
        d["_descarga"] = {"url": r.url, "descargado": datetime.now().isoformat(timespec="seconds"), "zona": z.zona}
        out[z.zona] = d
        time.sleep(1)
    emision = out[next(iter(out))]["daily"]["time"][0]
    destino = carpeta / emision
    destino.mkdir(parents=True, exist_ok=True)
    for zona, d in out.items():
        (destino / f"{zona}.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return out


def limpiar(crudos: dict[str, dict]) -> pd.DataFrame:
    importar_limpieza_B()
    from limpia_openmeteo import FUENTE_PREV, diario  # noqa: E402
    ref = pd.read_parquet(CLEAN / "openmeteo_prevision_ejemplo.parquet")
    partes = []
    for zona, d in crudos.items():
        p = diario(d, zona)
        for c in ref.columns:
            if c not in p.columns:
                p[c] = np.nan
        p["es_reanalisis"] = False
        p["dia_posiblemente_incompleto"] = False
        p["fuente"] = FUENTE_PREV
        partes.append(p[ref.columns].astype(ref.dtypes.to_dict()))
    out = pd.concat(partes, ignore_index=True)
    assert list(out.columns) == list(ref.columns)
    assert all(out[c].dtype == ref[c].dtype for c in ref.columns), "dtypes distintos del ejemplo"
    assert not out.duplicated(["fecha", "zona_meteo"]).any()
    return out


def main() -> None:
    zonas = pd.read_csv(CONFIG / "zonas_meteo.csv")
    crudos = descargar(zonas, RAIZ / "data" / "prevision")
    df = limpiar(crudos)
    df.to_parquet(DESTINO, index=False)
    print(f"{DESTINO.relative_to(RAIZ)}: {len(df)} filas, {df['zona_meteo'].nunique()} zonas, "
          f"{df['fecha'].min().date()} .. {df['fecha'].max().date()}")


if __name__ == "__main__":
    main()
