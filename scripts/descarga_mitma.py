"""Descarga MITMA (estudios básicos, municipios, v2) filtrando a Asturias día a día.

- Viajes: se queda con filas cuyo `destino` está en zonas_mitma_asturias.csv.
- Pernoctaciones: se queda con filas cuyo `zona_pernoctacion` está en esa lista.
- Añade al fichero anual data/raw/mitma_{viajes,pernoctaciones}_<año>.csv y BORRA el .csv.gz original.
- Reanudable: data/raw/_mitma_estado.jsonl guarda, por día y tipo, el estado y el tamaño
  de los CSV anuales tras escribirlo. Al arrancar se truncan los CSV a ese tamaño, así un
  corte a mitad de día no deja filas duplicadas ni a medias.
- Log: logs/descarga_mitma.log. Los datos faltantes quedan ausentes (nunca se rellenan con 0).

Uso:  python scripts/descarga_mitma.py [--inicio 2022-01-01] [--fin 2025-06-30] [--solo 2024-08-15]
Varios procesos a la vez son seguros si cada uno cubre años distintos (--inicio/--fin dentro de un año).
Se lee todo como texto (dtype=str, keep_default_na=False) para conservar 'NA' y ceros a la izquierda.
"""
import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
TMP = RAW / "_mitma_tmp"
ESTADO = RAW / "_mitma_estado.jsonl"
LOG = RAIZ / "logs" / "descarga_mitma.log"
BASE = "https://movilidad-opendata.mitma.es/estudios_basicos/por-municipios"
TIPOS = {
    # tipo: (carpeta URL, nombre fichero, columna filtro, prefijo salida)
    "viajes": ("viajes", "Viajes", "destino", "mitma_viajes"),
    "pernoctaciones": ("pernoctaciones", "Pernoctaciones", "zona_pernoctacion", "mitma_pernoctaciones"),
}
CHUNK = 2_000_000
REINTENTOS = 5


def url(tipo, d):
    carpeta, nombre, _, _ = TIPOS[tipo]
    return f"{BASE}/{carpeta}/ficheros-diarios/{d:%Y-%m}/{d:%Y%m%d}_{nombre}_municipios.csv.gz"


def salida(tipo, anio):
    return RAW / f"{TIPOS[tipo][3]}_{anio}.csv"


def descargar(tipo, d):
    """Devuelve ('OK', ruta) | ('NO_DISPONIBLE', None) | ('ERROR', msg)."""
    destino = TMP / f"{d:%Y%m%d}_{tipo}.csv.gz"
    ultimo = ""
    for i in range(1, REINTENTOS + 1):
        try:
            with requests.get(url(tipo, d), stream=True, timeout=(30, 120)) as r:
                if r.status_code == 404:
                    return "NO_DISPONIBLE", None
                r.raise_for_status()
                esperado = int(r.headers.get("Content-Length", -1))
                with open(destino, "wb") as f:
                    for bloque in r.iter_content(1 << 20):
                        f.write(bloque)
            if esperado >= 0 and destino.stat().st_size != esperado:
                raise IOError(f"tamaño {destino.stat().st_size} != Content-Length {esperado}")
            return "OK", destino
        except Exception as e:  # red, HTTP, truncado
            ultimo = f"{type(e).__name__}: {e}"
            logging.warning("%s %s intento %d/%d: %s", tipo, d, i, REINTENTOS, ultimo)
            time.sleep(min(60, 5 * i))
    return "ERROR", ultimo


def filtrar_y_anexar(tipo, d, ruta, zonas, columnas_ref):
    """Filtra a Asturias y anexa al CSV anual. Devuelve dict con estadísticas."""
    col = TIPOS[tipo][2]
    out = salida(tipo, d.year)
    leidas = guardadas = 0
    columnas = None
    with open(out, "ab") as f:
        escribir_cabecera = f.tell() == 0
        for trozo in pd.read_csv(ruta, sep="|", dtype=str, keep_default_na=False, chunksize=CHUNK):
            if columnas is None:
                columnas = list(trozo.columns)
                if columnas_ref.setdefault(tipo, columnas) != columnas:
                    raise ValueError(f"columnas distintas: {columnas} vs {columnas_ref[tipo]}")
            leidas += len(trozo)
            sel = trozo[trozo[col].isin(zonas)]
            if len(sel):
                sel.to_csv(f, sep=",", index=False, header=escribir_cabecera, lineterminator="\n")
                escribir_cabecera = False
                guardadas += len(sel)
    return {"filas_origen": leidas, "filas_asturias": guardadas, "columnas": columnas}


def cargar_estado():
    estado = {}
    if ESTADO.exists():
        for linea in ESTADO.read_text(encoding="utf-8").splitlines():
            if linea.strip():
                r = json.loads(linea)
                estado[(r["tipo"], r["fecha"])] = r
    return estado


def truncar_a_ultimo_estado(estado, anios):
    """Deja cada CSV anual (solo de `anios`) exactamente como estaba tras el último día registrado.
    Se limita a los años de esta ejecución: otros procesos pueden estar escribiendo los demás."""
    ultimo = {}
    for (tipo, fecha), r in estado.items():
        if "tam" in r:
            ultimo[(tipo, fecha[:4])] = max(ultimo.get((tipo, fecha[:4]), 0), r["tam"])
    for tipo in TIPOS:
        for f in RAW.glob(f"{TIPOS[tipo][3]}_*.csv"):
            anio = f.stem.rsplit("_", 1)[1]
            if anio not in anios:
                continue
            tam = ultimo.get((tipo, anio), 0)
            if f.stat().st_size > tam:
                logging.warning("Truncando %s de %d a %d bytes (resto de un corte)", f.name, f.stat().st_size, tam)
                with open(f, "r+b") as fh:
                    fh.truncate(tam)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", default="2022-01-01")
    ap.add_argument("--fin", default="2025-06-30")
    ap.add_argument("--solo", help="procesa un único día YYYY-MM-DD (para pruebas)")
    ap.add_argument("--reintentar-no-disponibles", action="store_true")
    a = ap.parse_args()

    LOG.parent.mkdir(exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    zonas = set(pd.read_csv(RAW / "zonas_mitma_asturias.csv", dtype=str)["id_zona_mitma"])
    assert len(zonas) == 46, len(zonas)

    ini = fin = date.fromisoformat(a.solo) if a.solo else None
    if not a.solo:
        ini, fin = date.fromisoformat(a.inicio), date.fromisoformat(a.fin)
    assert fin <= date(2025, 6, 30), "No descargar desde julio de 2025 (cambio de metodología)"
    dias = [ini + timedelta(n) for n in range((fin - ini).days + 1)]

    estado = cargar_estado()
    anios = {str(d.year) for d in dias}
    truncar_a_ultimo_estado(estado, anios)
    columnas_ref = {}

    def hecho(tipo, d):
        r = estado.get((tipo, d.isoformat()))
        if not r:
            return False
        if r["estado"] == "OK":
            return True
        return r["estado"] == "NO_DISPONIBLE" and not a.reintentar_no_disponibles

    tareas = [(d, t) for d in dias for t in TIPOS if not hecho(t, d)]
    logging.info("Inicio: %d tareas pendientes de %d", len(tareas), len(dias) * len(TIPOS))

    def registrar(tipo, d, est, **extra):
        reg = {"tipo": tipo, "fecha": d.isoformat(), "estado": est, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **extra}
        with open(ESTADO, "a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
        estado[(tipo, d.isoformat())] = reg

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=1) as pool:  # descarga la siguiente mientras se procesa la actual
        futuro = pool.submit(descargar, tareas[0][1], tareas[0][0]) if tareas else None
        for i, (d, tipo) in enumerate(tareas):
            est, res = futuro.result()
            futuro = pool.submit(descargar, tareas[i + 1][1], tareas[i + 1][0]) if i + 1 < len(tareas) else None
            if est == "NO_DISPONIBLE":
                logging.warning("%s %s: 404, no publicado (se deja ausente)", tipo, d)
                registrar(tipo, d, "NO_DISPONIBLE")
            elif est == "ERROR":
                logging.error("%s %s: ERROR tras %d intentos: %s", tipo, d, REINTENTOS, res)
                registrar(tipo, d, "ERROR", error=res)
            else:
                try:
                    s = filtrar_y_anexar(tipo, d, res, zonas, columnas_ref)
                except Exception as e:
                    logging.exception("%s %s: fallo al procesar", tipo, d)
                    truncar_a_ultimo_estado(estado, anios)  # deshace lo escrito a medias
                    registrar(tipo, d, "ERROR", error=f"{type(e).__name__}: {e}")
                    continue
                finally:
                    if res and Path(res).exists():
                        Path(res).unlink()  # BORRA el original
                registrar(tipo, d, "OK", tam=salida(tipo, d.year).stat().st_size,
                          filas_origen=s["filas_origen"], filas_asturias=s["filas_asturias"], columnas=s["columnas"])
                logging.info("%s %s OK: %d -> %d filas (%d/%d, %.0f min)", tipo, d, s["filas_origen"],
                             s["filas_asturias"], i + 1, len(tareas), (time.time() - t0) / 60)
    logging.info("FIN. Resumen: %s", {e: sum(1 for r in estado.values() if r["estado"] == e)
                                      for e in ("OK", "NO_DISPONIBLE", "ERROR")})


if __name__ == "__main__":
    main()
