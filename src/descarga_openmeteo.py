"""Descarga en bruto de Open-Meteo para las zonas de config/zonas_meteo.csv.

Fuentes (todas gratuitas, uso no comercial, CC BY 4.0):
  * Historical Forecast API  -> data/raw/openmeteo_<zona>.json          (diario)
  * Previous Runs API        -> data/raw/openmeteo_previous_<zona>.json (horario, dias 0-3 antes)
  * Archive API (ERA5)       -> data/raw/openmeteo_archive_<zona>.json  (solo contraste)
  * Forecast API (en vivo)   -> data/raw/openmeteo_prevision_ejemplo.json

Las respuestas se guardan SIN modificar en data/raw/_chunks/ (un fichero por zona y
tramo de fechas) y el JSON final por zona es la concatenacion mecanica de esos tramos
(sin limpieza ni imputacion). Es reanudable: un tramo ya descargado no se repite.
Al cambiar config/zonas_meteo.csv basta con relanzar.

Uso:  python src/descarga_openmeteo.py [--hasta AAAA-MM-DD] [--solo hist|previous|archive|vivo]
"""
import argparse
import csv
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "config" / "zonas_meteo.csv"
RAW = RAIZ / "data" / "raw"
CHUNKS = RAW / "_chunks"
MANIFEST = CHUNKS / "manifest.json"
REGISTRO = RAIZ / "notas" / "registro_openmeteo.md"

TZ = "Europe/Madrid"
INICIO_HIST = date(2022, 1, 1)
INICIO_PREVIOUS = date(2024, 1, 1)  # la doc dice que la mayoria de modelos se archivan desde ene-2024
ZONAS_ARCHIVE = ("covadonga", "cangas_de_onis", "lagos_enol", "llanes", "ribadesella", "gijon", "oviedo", "madrid", "sevilla")  # todas: la comparacion hist-vs-ERA5 por zona lo necesita
PAUSA = 6.0  # segundos entre llamadas (limite gratuito: 600/min, 5000/h, 10000/dia, ponderadas)

DIARIAS = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "precipitation_hours",
           "sunshine_duration", "wind_speed_10m_max", "wind_gusts_10m_max", "weather_code"]
# Previous Runs no ofrece agregados diarios (probado: error "invalid String value"): se pide horario.
HORARIAS_BASE = ["temperature_2m", "precipitation", "wind_speed_10m", "wind_gusts_10m",
                 "weather_code", "sunshine_duration"]
HORARIAS_PREVIOUS = [b + s for b in HORARIAS_BASE
                     for s in ("", "_previous_day1", "_previous_day2", "_previous_day3")]

URL_HIST = "https://historical-forecast-api.open-meteo.com/v1/forecast"
URL_PREVIOUS = "https://previous-runs-api.open-meteo.com/v1/forecast"
URL_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
URL_VIVO = "https://api.open-meteo.com/v1/forecast"

ZONAS_PROVISIONALES = [
    ("covadonga", 43.31, -5.05), ("lagos_enol", 43.27, -4.99), ("cangas_de_onis", 43.35, -5.13),
    ("llanes", 43.42, -4.75), ("ribadesella", 43.46, -5.06), ("gijon", 43.53, -5.66),
    ("oviedo", 43.36, -5.86), ("madrid", 40.42, -3.70), ("sevilla", 37.39, -5.98),
]


def log(*a):
    print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def cargar_zonas():
    if not CONFIG.exists():
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["zona", "lat", "lon", "provisional"])
            for z, la, lo in ZONAS_PROVISIONALES:
                w.writerow([z, la, lo, "si"])
        log("Creado", CONFIG, "con la lista provisional")
    with CONFIG.open(newline="", encoding="utf-8") as f:
        return [{"zona": r["zona"].strip(), "lat": float(r["lat"]), "lon": float(r["lon"])}
                for r in csv.DictReader(f) if r["zona"].strip()]


def tramos(inicio, fin):
    """Un tramo por ano natural (la API pondera mas las peticiones largas)."""
    out = []
    for y in range(inicio.year, fin.year + 1):
        a, b = max(date(y, 1, 1), inicio), min(date(y, 12, 31), fin)
        if a <= b:
            out.append((a, b))
    return out


def peticion(url, params):
    """GET con espera entre llamadas y reintento con espera creciente (429, 5xx, timeouts)."""
    espera = 30
    for intento in range(1, 11):
        try:
            r = requests.get(url, params=params, timeout=300)
            texto_limite = "limit exceeded" in r.text[:300].lower()
            if r.status_code == 429 or texto_limite or r.status_code >= 500:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:150]}")
            if r.status_code != 200:
                raise ValueError(f"HTTP {r.status_code}: {r.text[:300]}")  # error de parametros: no se reintenta
            time.sleep(PAUSA)
            return r
        except (requests.RequestException, RuntimeError) as e:
            if "hourly" in str(e).lower():
                espera = max(espera, 1800)  # la cuota horaria solo se renueva pasada la hora
            log(f"  intento {intento} fallido ({e}); espero {espera}s")
            time.sleep(espera)
            espera = min(espera * 2, 1800)
    raise SystemExit("Demasiados fallos: abortado (relanzar mas tarde; lo hecho se conserva)")


def manifest_cargar():
    return json.loads(MANIFEST.read_text("utf-8")) if MANIFEST.exists() else {}


def manifest_guardar(m):
    MANIFEST.write_text(json.dumps(m, indent=1, ensure_ascii=False, sort_keys=True), "utf-8")


def descargar_tramo(tipo, url, zona, a, b, extra, manifest):
    carpeta = CHUNKS / tipo
    carpeta.mkdir(parents=True, exist_ok=True)
    f = carpeta / f"{zona['zona']}_{a}_{b}.json"
    clave = f.relative_to(RAW).as_posix()
    if f.exists() and clave in manifest:
        return f
    params = {"latitude": zona["lat"], "longitude": zona["lon"], "start_date": a.isoformat(),
              "end_date": b.isoformat(), "timezone": TZ, **extra}
    log(f"{tipo} {zona['zona']} {a}..{b}")
    r = peticion(url, params)
    f.write_bytes(r.content)  # respuesta tal cual
    manifest[clave] = {"url": r.url, "descargado": datetime.now().isoformat(timespec="seconds")}
    manifest_guardar(manifest)
    return f


def ensamblar(tipo, bloque, zona, plan, destino, endpoint, extra, manifest):
    """Concatena los tramos (orden cronologico) en un unico JSON por zona. No limpia nada."""
    base, datos, resumen_tramos = None, {}, []
    for a, b in plan:
        f = CHUNKS / tipo / f"{zona['zona']}_{a}_{b}.json"
        d = json.loads(f.read_text("utf-8"))
        if base is None:
            base = {k: v for k, v in d.items() if k not in (bloque, "generationtime_ms")}
        for k, v in d[bloque].items():
            datos.setdefault(k, []).extend(v)
        resumen_tramos.append({"inicio": str(a), "fin": str(b), "elevation": d.get("elevation"),
                               "latitude": d.get("latitude"), "longitude": d.get("longitude"),
                               **manifest.get(f.relative_to(RAW).as_posix(), {})})
    tiempos = datos["time"]
    assert len(set(tiempos)) == len(tiempos), "fechas duplicadas"
    assert tiempos == sorted(tiempos), "fechas desordenadas"
    nulos, primero, ultimo = {}, {}, {}
    for k, v in datos.items():
        if k == "time":
            continue
        idx = [i for i, x in enumerate(v) if x is not None]
        nulos[k] = len(v) - len(idx)
        primero[k] = tiempos[idx[0]] if idx else None
        ultimo[k] = tiempos[idx[-1]] if idx else None
    base[bloque] = datos
    base["_descarga"] = {
        "endpoint": endpoint, "parametros_extra": extra, "zona": zona["zona"],
        "lat_pedida": zona["lat"], "lon_pedida": zona["lon"],
        "fecha_descarga_ultimo_tramo": max(t.get("descargado", "") for t in resumen_tramos),
        "n_registros": len(tiempos), "rango_pedido": [str(plan[0][0]), str(plan[-1][1])],
        "rango_real": [tiempos[0], tiempos[-1]], "nulos": nulos,
        "primer_dato_no_nulo": primero, "ultimo_dato_no_nulo": ultimo, "tramos": resumen_tramos,
    }
    destino.write_text(json.dumps(base, ensure_ascii=False), "utf-8")
    return base["_descarga"]


def tarea(tipo, zona, inicio, fin, manifest, filas):
    if tipo == "hist":
        url, bloque, extra = URL_HIST, "daily", {"daily": ",".join(DIARIAS)}
        destino = RAW / f"openmeteo_{zona['zona']}.json"
    elif tipo == "previous":
        url, bloque, extra = URL_PREVIOUS, "hourly", {"hourly": ",".join(HORARIAS_PREVIOUS)}
        destino = RAW / f"openmeteo_previous_{zona['zona']}.json"
    else:
        url, bloque, extra = URL_ARCHIVE, "daily", {"daily": ",".join(DIARIAS)}
        destino = RAW / f"openmeteo_archive_{zona['zona']}.json"
    plan = tramos(inicio, fin)
    for a, b in plan:
        descargar_tramo(tipo, url, zona, a, b, extra, manifest)
    filas[destino.name] = ensamblar(tipo, bloque, zona, plan, destino, url, extra, manifest)


def vivo(zona):
    destino = RAW / "openmeteo_prevision_ejemplo.json"
    params = {"latitude": zona["lat"], "longitude": zona["lon"], "forecast_days": 7, "timezone": TZ,
              "daily": ",".join(DIARIAS)}
    log("prevision en vivo", zona["zona"])
    r = peticion(URL_VIVO, params)
    destino.write_bytes(r.content)
    m = manifest_cargar()
    m[destino.relative_to(RAW).as_posix()] = {"url": r.url,
                                              "descargado": datetime.now().isoformat(timespec="seconds")}
    manifest_guardar(m)


def escribir_registro(filas, manifest):
    """Regenera la tabla de ficheros entre marcadores en notas/registro_openmeteo.md."""
    lineas = ["| Fichero | Endpoint | Descargado | Rango real | N reg. | Nulos por variable | Incidencias |",
              "|---|---|---|---|---|---|---|"]
    for p in sorted(RAW.glob("openmeteo_*.json")):
        d = json.loads(p.read_text("utf-8"))
        info = d.get("_descarga")
        if info:
            nulos = ", ".join(f"{k}={v}" for k, v in info["nulos"].items())
            lineas.append(f"| `{p.name}` | {info['endpoint'].split('//')[1].split('/')[0]} | "
                          f"{info['fecha_descarga_ultimo_tramo'][:10]} | {info['rango_real'][0][:10]} → "
                          f"{info['rango_real'][1][:10]} | {info['n_registros']} | {nulos} | ver notas |")
        else:
            m = manifest.get(p.relative_to(RAW).as_posix(), {})
            lineas.append(f"| `{p.name}` | api.open-meteo.com/v1/forecast | {m.get('descargado', '?')[:10]} | "
                          f"{d['daily']['time'][0]} → {d['daily']['time'][-1]} | {len(d['daily']['time'])} | - | - |")
    tabla = "\n".join(lineas)
    ini, fin = "<!-- TABLA:INICIO -->", "<!-- TABLA:FIN -->"
    txt = REGISTRO.read_text("utf-8") if REGISTRO.exists() else f"# Registro Open-Meteo\n\n{ini}\n{fin}\n"
    if ini not in txt:
        txt += f"\n{ini}\n{fin}\n"
    antes, resto = txt.split(ini, 1)
    despues = resto.split(fin, 1)[1]
    REGISTRO.write_text(f"{antes}{ini}\n{tabla}\n{fin}{despues}", "utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hasta", default=date.today().isoformat())
    ap.add_argument("--solo", choices=["hist", "previous", "archive", "vivo"])
    args = ap.parse_args()
    hasta = date.fromisoformat(args.hasta)
    zonas = cargar_zonas()
    manifest = manifest_cargar()
    filas = {}
    RAW.mkdir(parents=True, exist_ok=True)
    for z in zonas:
        if args.solo in (None, "hist"):
            tarea("hist", z, INICIO_HIST, hasta, manifest, filas)
        if args.solo in (None, "previous"):
            tarea("previous", z, INICIO_PREVIOUS, hasta, manifest, filas)
        if args.solo in (None, "archive") and z["zona"] in ZONAS_ARCHIVE:
            tarea("archive", z, INICIO_HIST, hasta, manifest, filas)
    if args.solo in (None, "vivo"):
        cov = next((z for z in zonas if z["zona"] == "covadonga"), zonas[0])
        vivo(cov)
    escribir_registro(filas, manifest_cargar())
    log("Hecho")


if __name__ == "__main__":
    sys.exit(main())
