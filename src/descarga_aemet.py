"""Descarga en bruto de AEMET OpenData (observacion diaria, inventario, prevision).

Uso (la clave se lee SOLO de la variable de entorno AEMET_API_KEY):
    python src/descarga_aemet.py inventario
    python src/descarga_aemet.py diarios [--hasta AAAA-MM-DD]
    python src/descarga_aemet.py cobertura
    python src/descarga_aemet.py prediccion

Reanudable: un tramo ya descargado (JSON valido) o registrado como "sin datos" se salta.
No se transforma ningun valor: se guarda lo que devuelve la API.
"""
import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = "https://opendata.aemet.es/opendata"
RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
TRAMOS = RAW / "aemet" / "tramos"
ESTADO_TRAMOS = RAW / "aemet" / "estado_tramos.json"
INICIO = date(2022, 1, 1)

# Estaciones confirmadas contra el inventario (ver notas/estaciones_aemet.md).
ESTACIONES = {
    "1212E": "Asturias Aeropuerto",
    "1249X": "Oviedo",
    "1183X": "Llanes",
    # candidatas cercanas a Cangas de Onis / Covadonga / Lagos
    "1186P": "Amieva, Panizales",
    "1179B": "Cabrales",
    "1178R": "Sotres, Parque Nacional Picos de Europa",
    "1199X": "Pilona, Bargaú",
    "1203D": "Colunga",
    # otras zonas de Asturias
    # 1208 (Gijon) devuelve 404 en todos los tramos: sin datos; 1208A tambien vacia; se usa Campus
    "1207U": "Gijon, Campus",
    "1210X": "Cabo Penas",
    # ciudades de origen de visitantes
    "3195": "Madrid, Retiro",
    "5783": "Sevilla Aeropuerto",
}

_sesion = requests.Session()


def clave():
    k = os.environ.get("AEMET_API_KEY")
    if not k:
        sys.exit("Falta la variable de entorno AEMET_API_KEY")
    return k


def _get(url, max_intentos=8, **kw):
    """GET con cabecera api_key y backoff exponencial ante 429/5xx/red."""
    espera = 5
    for intento in range(1, max_intentos + 1):
        try:
            r = _sesion.get(url, headers={"api_key": clave(), "Accept": "application/json"},
                            timeout=60, **kw)
        except requests.RequestException as e:
            print(f"  red: {type(e).__name__}; reintento en {espera}s", flush=True)
            r = None
        if r is not None and r.status_code not in (429, 500, 502, 503, 504):
            return r
        if r is not None:
            print(f"  HTTP {r.status_code}; reintento en {espera}s (intento {intento})", flush=True)
        time.sleep(espera)
        espera = min(espera * 2, 120)
    return r


def consulta(ruta):
    """Peticion en dos pasos. Devuelve (estado, descripcion, datos, metadatos).

    estado = estado devuelto por la API (o el codigo HTTP si no hay JSON valido).
    datos  = JSON final de la segunda URL (None si no hay).
    """
    r1 = _get(BASE + ruta)
    if r1 is None:
        return "error_red", "sin respuesta", None, None
    try:
        j = r1.json()
    except ValueError:
        return r1.status_code, "respuesta no JSON", None, None
    estado = j.get("estado", r1.status_code)
    if estado != 200 or not j.get("datos"):
        return estado, j.get("descripcion", ""), None, None
    r2 = _get(j["datos"])
    if r2 is None:
        return "error_red", "fallo en segunda URL", None, None
    if r2.status_code != 200:
        return r2.status_code, "segunda URL: HTTP " + str(r2.status_code), None, None
    # AEMET sirve latin-1 en algunos endpoints; se guarda el texto tal cual se decodifica.
    try:
        datos = json.loads(r2.content.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        datos = json.loads(r2.content.decode("latin-1"))
    return 200, j.get("descripcion", ""), datos, j.get("metadatos")


def guardar_json(ruta, obj):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ruta)


def cargar_json(ruta, defecto=None):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defecto


# ---------------------------------------------------------------- inventario
def cmd_inventario(_a):
    destino = RAW / "aemet_inventario.json"
    ruta = "/api/valores/climatologicos/inventarioestaciones/todasestaciones"
    estado, desc, datos, _ = consulta(ruta)
    if estado != 200:
        sys.exit(f"Inventario fallido: estado={estado} {desc}")
    guardar_json(destino, datos)
    print(f"Inventario: {len(datos)} estaciones -> {destino.relative_to(RAIZ)}")


# ------------------------------------------------------------------- diarios
def tramos(ini, fin):
    """Tramos de como maximo 6 meses naturales: ene-jun y jul-dic de cada anio."""
    out = []
    y = ini.year
    while date(y, 1, 1) <= fin:
        for a, b in ((date(y, 1, 1), date(y, 6, 30)), (date(y, 7, 1), date(y, 12, 31))):
            t0, t1 = max(a, ini), min(b, fin)
            if t0 <= t1:
                out.append((t0, t1))
        y += 1
    return out


def fmt(d, fin_dia=False):
    return d.strftime("%Y-%m-%d") + ("T23:59:59UTC" if fin_dia else "T00:00:00UTC")


def cmd_diarios(a):
    hasta = date.fromisoformat(a.hasta) if a.hasta else date.today() - timedelta(days=1)
    estado_t = cargar_json(ESTADO_TRAMOS, {})
    for idema, nombre in ESTACIONES.items():
        print(f"== {idema} {nombre}", flush=True)
        for t0, t1 in tramos(INICIO, hasta):
            clave_t = f"{idema}_{t0}_{t1}"
            f = TRAMOS / f"{clave_t}.json"
            if f.exists() and isinstance(cargar_json(f), list):
                continue
            prev = estado_t.get(clave_t)
            if prev and prev["estado"] in (404,) and not a.reintentar and t1 < hasta - timedelta(days=30):
                continue
            ruta = ("/api/valores/climatologicos/diarios/datos/fechaini/%s/fechafin/%s/estacion/%s"
                    % (fmt(t0), fmt(t1, True), idema))
            estado, desc, datos, _ = consulta(ruta)
            ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
            if estado == 200 and isinstance(datos, list):
                guardar_json(f, datos)
                estado_t.pop(clave_t, None)
                print(f"  {t0}..{t1}: {len(datos)} registros", flush=True)
            else:
                estado_t[clave_t] = {"estado": estado, "motivo": desc, "fecha": ahora}
                print(f"  {t0}..{t1}: SIN DATOS estado={estado} ({desc})", flush=True)
            guardar_json(ESTADO_TRAMOS, estado_t)
            time.sleep(a.pausa)
        unir(idema)


def unir(idema):
    # Un tramo parcial de una descarga anterior (p. ej. ..._2026-07-01_2026-10-14.json) puede convivir con el
    # mismo tramo más largo de una posterior: cada fecha se queda con el registro del último fichero en orden.
    por_fecha, dup = {}, 0
    for f in sorted(TRAMOS.glob(f"{idema}_*.json")):
        d = cargar_json(f)
        if isinstance(d, list):
            for r in d:
                dup += r.get("fecha") in por_fecha
                por_fecha[r.get("fecha")] = r
    registros = [por_fecha[k] for k in sorted(por_fecha, key=str)]
    guardar_json(RAW / f"aemet_diario_{idema}.json", registros)
    print(f"  unido: {len(registros)} fechas distintas ({dup} duplicadas entre tramos, descartadas)")


# ----------------------------------------------------------------- cobertura
VARS = {"tmax": "tmax", "tmin": "tmin", "tmed": "tmed", "prec": "precipitacion",
        "velmedia": "viento_medio", "racha": "racha", "sol": "sol"}


def cmd_cobertura(_a):
    from collections import defaultdict
    lineas = ["# Cobertura AEMET (dias con dato por mes y variable)\n",
              "Un dia cuenta si el campo existe y no esta vacio en el JSON bruto "
              "(incluye `Ip` en precipitacion; no se convierte ningun valor).\n"]
    for idema, nombre in ESTACIONES.items():
        datos = cargar_json(RAW / f"aemet_diario_{idema}.json", [])
        if not datos:
            lineas.append(f"\n## {idema} {nombre}\n\nSin datos.\n")
            continue
        por_mes = defaultdict(lambda: defaultdict(int))
        fechas = sorted({r["fecha"] for r in datos})
        for r in datos:
            m = r["fecha"][:7]
            por_mes[m]["dias"] += 1
            for k in VARS:
                if r.get(k) not in (None, ""):
                    por_mes[m][k] += 1
        lineas.append(f"\n## {idema} {nombre}\n\nRango real: {fechas[0]} a {fechas[-1]}; "
                      f"{len(fechas)} dias distintos.\n")
        lineas.append("| mes | dias | " + " | ".join(VARS) + " |")
        lineas.append("|---|---|" + "---|" * len(VARS))
        for m in sorted(por_mes):
            c = por_mes[m]
            lineas.append(f"| {m} | {c['dias']} | " + " | ".join(str(c[k]) for k in VARS) + " |")
    (RAIZ / "notas").mkdir(exist_ok=True)
    (RAIZ / "notas" / "cobertura_aemet.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("Escrito notas/cobertura_aemet.md")


# ---------------------------------------------------------------- prevision
def cmd_prediccion(_a):
    # 33012 = Cangas de Onis (incluye Covadonga y Lagos), 33036 = Llanes; ids del maestro /api/maestro/municipios
    salida = {}
    for muni in ("33012", "33036"):
        estado, desc, datos, meta = consulta(f"/api/prediccion/especifica/municipio/diaria/{muni}")
        salida[muni] = {"estado": estado, "descripcion": desc, "datos": datos}
        print(muni, estado, desc)
    guardar_json(RAW / "aemet_prediccion_ejemplo.json", salida)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventario").set_defaults(f=cmd_inventario)
    d = sub.add_parser("diarios")
    d.add_argument("--hasta", help="fecha final AAAA-MM-DD (por defecto, ayer)")
    d.add_argument("--pausa", type=float, default=2.0, help="segundos entre peticiones")
    d.add_argument("--reintentar", action="store_true", help="reintenta tramos registrados sin datos")
    d.set_defaults(f=cmd_diarios)
    sub.add_parser("cobertura").set_defaults(f=cmd_cobertura)
    sub.add_parser("prediccion").set_defaults(f=cmd_prediccion)
    args = ap.parse_args()
    args.f(args)
