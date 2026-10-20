"""INE: turismo con móviles, interno (estadística experimental).

Descarga en bruto a data/raw/ (no limpia, no modela):
  - ine_moviles_interno_<año>.xlsx  (2022-2026, un Excel por año, una hoja por mes)
  - ine_moviles_53001.csv           (EXTRACTO de la tabla 53001: destino = municipios de
                                     Asturias, origen = "Total Nacional")

El CSV completo de la 53001 pesa >2,3 GB, así que se lee en streaming y se corta al
acabar el bloque "Total Nacional" (el INE lo sirve el primero). Ver notas/fuentes/demanda/registro_descargas.md.
NO VERIFICADO de principio a fin: la única prueba se cortó por un reset de conexión del INE
a los 14 min (el servidor va lento); las filas descargadas coincidieron byte a byte con el extracto
hecho a mano. Si falla, repetir o exportar desde https://www.ine.es/jaxiT3/Tabla.htm?t=53001&L=0.

Uso:  python scripts/descarga_ine_moviles.py [--out data/raw] [--sin-excel]
"""
import argparse
import sys
from pathlib import Path

import requests

URL_XLSX = "https://www.ine.es/experimental/turismo_moviles/exp_tmov_interno_mun_{year}.xlsx"
URL_CSV = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/53001.csv"
AÑOS = range(2022, 2027)


def descargar_excel(out: Path) -> None:
    for year in AÑOS:
        dest = out / f"ine_moviles_interno_{year}.xlsx"
        if dest.exists() and dest.stat().st_size > 0:
            print(f"{dest.name}: ya existe, se omite")
            continue
        with requests.get(URL_XLSX.format(year=year), stream=True, timeout=120) as r:
            r.raise_for_status()  # si da 404, buscar el enlace en ine.es/dynt3/inebase (padre=8578)
            with open(dest, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        print(f"{dest.name}: {dest.stat().st_size / 1e6:.1f} MB")


def descargar_53001_asturias(out: Path) -> None:
    """Filtra destino 33xxx y origen 'Total Nacional' sin CCAA/provincia; corta al cambiar de origen.

    Se escriben los bytes tal cual (UTF-8 con BOM, aunque la cabecera HTTP diga ISO-8859-15), sin recodificar.
    """
    dest = out / "ine_moviles_53001.csv"
    n = 0
    visto_total = False
    with requests.get(URL_CSV, stream=True, timeout=120) as r, open(dest, "wb") as f:
        r.raise_for_status()
        for i, linea in enumerate(_lineas(r)):
            if i == 0:
                f.write(linea)  # cabecera
                continue
            c = linea.decode("utf-8").split(";")
            es_total = c[0] == "Total Nacional" and c[1] == "" and c[2] == ""
            if es_total:
                visto_total = True
                if c[3].startswith("33"):
                    f.write(linea)
                    n += 1
            elif visto_total:
                break  # ya empezó otro origen: el bloque nacional terminó
    print(f"{dest.name}: {n} filas (esperado 6708 = 78 municipios x 86 meses a 2026M08)")


def _lineas(r):
    """Líneas de la respuesta en bytes, conservando el salto de línea."""
    buf = b""
    for chunk in r.iter_content(1 << 20):
        buf += chunk
        *completas, buf = buf.split(b"\n")
        for b in completas:
            yield b + b"\n"
    if buf:
        yield buf


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--sin-excel", action="store_true", help="solo el extracto de la 53001")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if not a.sin_excel:
        descargar_excel(out)
    descargar_53001_asturias(out)
    sys.exit(0)
