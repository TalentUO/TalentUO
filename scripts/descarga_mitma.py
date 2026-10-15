"""Descarga MITMA (estudios básicos, municipios, v2) filtrando a Asturias en streaming.

Por cada día y tipo, un worker descarga el .csv.gz del portal y lo descomprime al vuelo SIN guardarlo
en disco; solo conserva las líneas de Asturias (viajes: `destino`; pernoctaciones: `zona_pernoctacion`,
usando data/raw/zonas_mitma_asturias.csv). Es el único filtro: las líneas no se agregan ni recodifican;
solo se cambia el separador `|` por `,` (se aborta si algún valor ya contiene una coma).

- Resultado por día: data/raw/_mitma_dias/<tipo>/AAAAMMDD.csv (con cabecera). Escritura atómica.
- Estado: data/raw/_mitma_estado_v2.jsonl (OK / NO_DISPONIBLE (404) / ERROR por día y tipo). Reanudable:
  se salta lo ya hecho. Un 404 queda ausente, nunca 0.
- Al acabar, ensambla data/raw/mitma_<tipo>_<año>.csv (orden por fecha) y, si las filas cuadran con el
  estado, borra los ficheros diarios.
- Log: logs/descarga_mitma.log. Aborta si queda menos de 20 GB libres.

Uso: python scripts/descarga_mitma.py [--inicio 2022-01-01] [--fin 2025-06-30] [--workers 4] [--tipos viajes pernoctaciones] [--solo-ensamblar]
"""
import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
DIAS = RAW / "_mitma_dias"
ESTADO = RAW / "_mitma_estado_v2.jsonl"
LOG = RAIZ / "logs" / "descarga_mitma.log"
BASE = "https://movilidad-opendata.mitma.es/estudios_basicos/por-municipios"
MIN_LIBRE_GB = 20
REINTENTOS = 5
# tipo: (carpeta URL, nombre en fichero, nº de campos '|' antes de la columna filtro)
TIPOS = {"viajes": ("viajes", "Viajes", 3), "pernoctaciones": ("pernoctaciones", "Pernoctaciones", 2)}


def url(tipo, d):
    carpeta, nombre, _ = TIPOS[tipo]
    return f"{BASE}/{carpeta}/ficheros-diarios/{d:%Y-%m}/{d:%Y%m%d}_{nombre}_municipios.csv.gz"


def ruta_dia(tipo, d):
    return DIAS / tipo / f"{d:%Y%m%d}.csv"


def libre_gb():
    return shutil.disk_usage(RAW).free / 1e9


def _procesar(tipo, d, zonas):
    """Una descarga completa. Devuelve dict con el resultado o lanza excepción."""
    patron = re.compile(
        rb"^" + d.strftime("%Y%m%d").encode() + rb"\|" + rb"[^|\n]*\|" * (TIPOS[tipo][2] - 1)
        + rb"(?:" + b"|".join(re.escape(z.encode()) for z in sorted(zonas)) + rb")\|[^\n]*\n",
        re.M,
    )
    with requests.get(url(tipo, d), stream=True, timeout=(30, 120)) as r:
        if r.status_code == 404:
            return {"estado": "NO_DISPONIBLE"}
        r.raise_for_status()
        esperado = int(r.headers.get("Content-Length", -1))
        dec = zlib.decompressobj(wbits=31)  # gzip; verifica CRC al final
        cabecera, resto, total, bajados = None, b"", 0, 0
        partes, filas, filas_origen = [], 0, 0
        for bloque in r.iter_content(1 << 22):
            bajados += len(bloque)
            datos = resto + dec.decompress(bloque)
            if cabecera is None:
                if b"\n" not in datos:
                    resto = datos
                    continue
                cabecera, datos = datos.split(b"\n", 1)
            corte = datos.rfind(b"\n") + 1
            resto, datos = datos[corte:], datos[:corte]
            filas_origen += datos.count(b"\n")
            for m in patron.findall(datos):
                partes.append(m)
            if len(partes) > 200000:  # vuelca a bytes para no acumular listas enormes
                partes = [b"".join(partes)]
        resto += dec.flush()
        if not dec.eof:
            raise IOError("gzip truncado (sin fin de flujo)")
        if esperado >= 0 and bajados != esperado:
            raise IOError(f"descargados {bajados} B != Content-Length {esperado}")
        if resto:
            resto += b"\n"
            filas_origen += 1
            partes.extend(patron.findall(resto))
    cuerpo = b"".join(partes)
    if b"," in cuerpo or b"," in cabecera or b"\r" in cuerpo:
        raise ValueError("el fichero contiene comas o \\r: no se puede cambiar el separador sin comillas")
    filas = cuerpo.count(b"\n")
    salida = ruta_dia(tipo, d)
    salida.parent.mkdir(parents=True, exist_ok=True)
    tmp = salida.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        f.write(cabecera.replace(b"|", b",") + b"\n" + cuerpo.replace(b"|", b","))
    os.replace(tmp, salida)
    return {"estado": "OK", "filas_origen": filas_origen, "filas_asturias": filas, "MB_bajados": round(bajados / 1e6, 1),
            "cabecera": cabecera.decode()}


def trabajo(tipo, d, zonas):
    t0 = time.time()
    ultimo = ""
    for i in range(1, REINTENTOS + 1):
        try:
            r = _procesar(tipo, d, zonas)
            r["seg"] = round(time.time() - t0, 1)
            return tipo, d, r
        except Exception as e:
            ultimo = f"{type(e).__name__}: {e}"
            logging.warning("%s %s intento %d/%d: %s", tipo, d, i, REINTENTOS, ultimo)
            time.sleep(min(60, 5 * i))
    return tipo, d, {"estado": "ERROR", "error": ultimo}


def cargar_estado():
    est = {}
    if ESTADO.exists():
        for l in ESTADO.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                est[(r["tipo"], r["fecha"])] = r
    return est


def ensamblar(estado, dias, tipos=tuple(TIPOS)):
    """Concatena los ficheros diarios en los CSV anuales y borra los diarios si las filas cuadran."""
    for tipo in tipos:
        for anio in sorted({d.year for d in dias}):
            ok = [d for d in dias if d.year == anio and estado.get((tipo, d.isoformat()), {}).get("estado") == "OK"
                  and ruta_dia(tipo, d).exists()]
            if not ok:
                continue
            destino = RAW / f"mitma_{tipo}_{anio}.csv"
            tmp = destino.with_suffix(".tmp")
            cab, filas, previo = None, 0, 0
            with open(tmp, "wb") as out:
                if destino.exists():  # anexa a lo ya ensamblado (cuyos diarios ya se borraron)
                    with open(destino, "rb") as f:
                        cab = f.readline()
                        f.seek(0)
                        for bloque in iter(lambda: f.read(1 << 24), b""):
                            out.write(bloque)
                    previo = destino.stat().st_size
                for d in ok:
                    with open(ruta_dia(tipo, d), "rb") as f:
                        c = f.readline()
                        if cab is None:
                            cab = c
                            out.write(c)
                        elif c != cab:
                            raise ValueError(f"cabecera distinta en {tipo} {d}")
                        for bloque in iter(lambda: f.read(1 << 24), b""):
                            out.write(bloque)
                    filas += estado[(tipo, d.isoformat())]["filas_asturias"]
            os.replace(tmp, destino)
            logging.info("Ensamblado %s: %d días, %d filas esperadas según estado", destino.name, len(ok), filas)
            # Las filas reales se comprueban con scripts/verificar_mitma.py; los diarios se borran solo si
            # el tamaño cuadra con la suma de los diarios.
            tam = previo + sum(ruta_dia(tipo, d).stat().st_size - (len(cab) if previo or d != ok[0] else 0) for d in ok)
            if destino.stat().st_size == tam:
                with open(ESTADO, "a", encoding="utf-8") as fe:
                    for d in ok:
                        ruta_dia(tipo, d).unlink()
                        reg = {**estado[(tipo, d.isoformat())], "ensamblado": True,
                               "ts_ensamblado": time.strftime("%Y-%m-%d %H:%M:%S")}
                        fe.write(json.dumps(reg, ensure_ascii=False) + "\n")
                        estado[(tipo, d.isoformat())] = reg
            else:
                logging.error("Tamaño de %s no cuadra (%d vs %d): NO se borran los diarios", destino.name,
                              destino.stat().st_size, tam)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", default="2022-01-01")
    ap.add_argument("--fin", default="2025-06-30")
    ap.add_argument("--workers", type=int, default=4)  # con 10 el portal rindió peor (medido)
    ap.add_argument("--solo-ensamblar", action="store_true")
    ap.add_argument("--tipos", nargs="+", choices=list(TIPOS), default=list(TIPOS), help="limita ensamblado y descarga a estos tipos")
    ap.add_argument("--reintentar-no-disponibles", action="store_true")
    a = ap.parse_args()
    LOG.parent.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(LOG, encoding="utf-8"), logging.StreamHandler(sys.stdout)])
    zonas = set(pd.read_csv(RAW / "zonas_mitma_asturias.csv", dtype=str)["id_zona_mitma"])
    assert len(zonas) == 46, len(zonas)
    ini, fin = date.fromisoformat(a.inicio), date.fromisoformat(a.fin)
    assert fin <= date(2025, 6, 30), "No descargar desde julio de 2025 (cambio de metodología)"
    dias = [ini + timedelta(n) for n in range((fin - ini).days + 1)]
    estado = cargar_estado()

    def hecho(tipo, d):
        r = estado.get((tipo, d.isoformat()))
        if not r:
            return False
        if r["estado"] == "OK":
            # Un OK solo vale si el fichero diario existe o el día ya se ensambló en el CSV anual.
            # Así el estado (que viaja por git) no da por hechos días cuyos datos no están en este PC.
            return ruta_dia(tipo, d).exists() or bool(r.get("ensamblado"))
        return r["estado"] == "NO_DISPONIBLE" and not a.reintentar_no_disponibles

    if not a.solo_ensamblar:
        tareas = [(t, d) for d in dias for t in a.tipos if not hecho(t, d)]
        # Prioridad: pernoctaciones (pesan poco), luego viajes 2024-25, 2023 y 2022 (cada bloque por fecha).
        tareas.sort(key=lambda x: (x[0] != "pernoctaciones", 0 if x[1].year >= 2024 else 2024 - x[1].year, x[1]))
        logging.info("Inicio: %d tareas pendientes de %d, %d workers, %.0f GB libres", len(tareas),
                     len(dias) * len(TIPOS), a.workers, libre_gb())
        t0, n = time.time(), 0
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            it = iter(tareas)
            vivos = set()

            def lanzar():
                if libre_gb() < MIN_LIBRE_GB:
                    raise SystemExit(f"Quedan menos de {MIN_LIBRE_GB} GB libres: abortando")
                t = next(it, None)
                if t:
                    vivos.add(pool.submit(trabajo, t[0], t[1], zonas))
                return t

            for _ in range(a.workers * 2):
                if not lanzar():
                    break
            while vivos:
                for fut in as_completed(list(vivos)):
                    vivos.discard(fut)
                    tipo, d, r = fut.result()
                    reg = {"tipo": tipo, "fecha": d.isoformat(), "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **r}
                    with open(ESTADO, "a", encoding="utf-8") as f:
                        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
                    estado[(tipo, d.isoformat())] = reg
                    n += 1
                    if r["estado"] == "OK":
                        logging.info("%s %s OK: %d -> %d filas, %.0f MB, %.0fs (%d/%d, %.1f min)", tipo, d,
                                     r["filas_origen"], r["filas_asturias"], r["MB_bajados"], r["seg"], n,
                                     len(tareas), (time.time() - t0) / 60)
                    else:
                        logging.warning("%s %s %s %s", tipo, d, r["estado"], r.get("error", ""))
                    lanzar()
                    break
    ensamblar(estado, dias, tuple(a.tipos))
    logging.info("FIN. Resumen: %s", {e: sum(1 for r in estado.values() if r["estado"] == e)
                                      for e in ("OK", "NO_DISPONIBLE", "ERROR")})


if __name__ == "__main__":
    main()
