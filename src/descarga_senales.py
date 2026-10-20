"""Descarga en bruto de senales adelantadas de interes (Wikipedia, Google Trends, OAPN).

Uso:
    python src/descarga_senales.py wikipedia [--hasta AAAA-MM-DD]
    python src/descarga_senales.py sonda_wikipedia
    python src/descarga_senales.py trends [--pausa 60]
    python src/descarga_senales.py oapn          (descarga las URLs listadas en OAPN_PDFS)

Reanudable: un fichero ya descargado se salta (borrar para repetir).
No se transforma ningun valor: la respuesta de la API se guarda tal cual dentro de
la clave "respuesta"; "meta" anade parametros y fecha de descarga.
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
TRENDS_DIR = RAW / "trends"
OAPN_DIR = RAW / "oapn"

# Wikimedia pide un User-Agent con contacto: se toma de TALENTUO_CONTACTO (no se
# versiona ningún dato personal).
UA = ("TalentUO-Hackathon-2026/0.1 (proyecto academico Universidad de Oviedo; "
      f"contacto: {os.environ.get('TALENTUO_CONTACTO', 'equipo TalentUO')})")
PAUSA_WIKI = 1.0
INICIO = "20220101"

WIKI_API = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
            "{proyecto}/all-access/user/{titulo}/daily/{ini}/{fin}")

# (proyecto, titulo exacto verificado con action=query&redirects=1 el 2026-10-15)
ARTICULOS = [
    ("es.wikipedia", "Lagos de Covadonga"),
    ("es.wikipedia", "Covadonga"),
    ("es.wikipedia", "Cangas de Onís"),
    ("es.wikipedia", "Llanes"),
    ("es.wikipedia", "Ribadesella"),
    ("es.wikipedia", "Parque nacional de los Picos de Europa"),
    ("es.wikipedia", "Picos de Europa"),
    ("es.wikipedia", "Ruta del Cares"),
    ("es.wikipedia", "Descenso Internacional del Sella"),
    ("es.wikipedia", "Gijón"),
    ("es.wikipedia", "Oviedo"),
    ("es.wikipedia", "Santa Cueva de Covadonga"),  # 'Santuario de Covadonga' redirige aqui
    ("es.wikipedia", "Cabrales"),
    ("es.wikipedia", "Potes"),
    ("es.wikipedia", "Fuente Dé"),
    # indicador de interes extranjero
    ("en.wikipedia", "Picos de Europa"),
    ("en.wikipedia", "Covadonga"),
    ("en.wikipedia", "Picos de Europa National Park"),
    ("fr.wikipedia", "Pics d'Europe"),  # 'Picos de Europa' redirige aqui
    ("fr.wikipedia", "Covadonga"),
]

TRENDS_TERMINOS = ["lagos de covadonga", "llanes", "cangas de onís", "ruta del cares",
                   "covadonga"]
TRENDS_ANCLA = "cabrales"  # por qué esta ancla y no "picos de europa": notas/historico/correcciones_fase_B.md
TRENDS_GEOS = ["ES", "ES-MD", "ES-CL", "ES-AS"]

# URLs de los PDF de la OAPN (ver notas/fuentes/senales/notas_senales.md)
OAPN_BASE = "https://www.miteco.gob.es/content/dam/miteco/es/parques-nacionales-oapn/red-parques-nacionales"
OAPN_PDFS = {
    "oapn_visitantes_2022.pdf": OAPN_BASE + "/gestion/Visitantes-PPNN-2022.pdf",
    "oapn_visitantes_2023.pdf": OAPN_BASE + "/desarrollo-socioeconomico/informes/Visitantes%20a%20los%20Parques%20Nacionales%20Espa%C3%B1oles.%20A%C3%B1o%202023.pdf",
    "oapn_visitantes_2024.pdf": OAPN_BASE + "/desarrollo-socioeconomico/informes/Visitantes%20a%20los%20Parques%20Nacionales%20Espa%C3%B1oles.%20A%C3%B1o%202024.pdf",
    "oapn_visitantes_2025.pdf": OAPN_BASE + "/desarrollo-socioeconomico/informes/Visitantes%20a%20los%20Parques%20Nacionales%20Espa%C3%B1oles.%20A%C3%B1o%202025.pdf",
    "oapn_memoria_red_2018.pdf": OAPN_BASE + "/la-red/memoria-red-2018_tcm30-525157.pdf",
    "oapn_memoria_red_2019.pdf": OAPN_BASE + "/la-red/memoria-red-2019_tcm30-525158.pdf",
    "oapn_memoria_red_2020.pdf": OAPN_BASE + "/la-red/memoriadelaredparquesnacionales-2020_tcm30-543206.pdf",
    "oapn_memoria_red_2021.pdf": OAPN_BASE + "/la-red/Memoria%20Anual%20Red%20de%20Parques%20Nacionales%202021.pdf",
}


def normaliza(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_").lower()


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get(url, **kw):
    r = None
    for intento in range(4):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=60, **kw)
        except requests.RequestException as e:
            print(f"  error de red ({e.__class__.__name__}), reintento", file=sys.stderr)
            time.sleep(10 * (intento + 1))
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            retry = r.headers.get("Retry-After", "")
            espera = int(retry) if retry.isdigit() else 10 * (intento + 1)
            print(f"  HTTP {r.status_code}, espero {espera}s", file=sys.stderr)
            time.sleep(espera)
            continue
        return r
    if r is None:
        raise RuntimeError(f"sin respuesta tras 4 intentos: {url}")
    return r


def fichero_wiki(proyecto, titulo):
    idioma = proyecto.split(".")[0]
    sufijo = "" if idioma == "es" else f"_{idioma}"
    return RAW / f"wikipedia_{normaliza(titulo)}{sufijo}.json"


def wikipedia(hasta, ini=INICIO):
    fin = hasta.replace("-", "")
    for proyecto, titulo in ARTICULOS:
        destino = fichero_wiki(proyecto, titulo)
        if destino.exists():
            print(f"salta {destino.name}")
            continue
        url = WIKI_API.format(proyecto=proyecto, titulo=quote(titulo.replace(" ", "_"), safe=""),
                              ini=ini, fin=fin)
        r = get(url)
        meta = {"fuente": "Wikimedia REST pageviews", "url": url, "proyecto": proyecto,
                "titulo": titulo, "agent": "user", "access": "all-access",
                "granularity": "daily", "solicitado": [ini, fin],
                "descargado_utc": ahora(), "http_status": r.status_code}
        try:
            cuerpo = r.json()
        except ValueError:
            cuerpo = {"texto": r.text}
        if r.status_code != 200:
            # Sin escribir el fichero: así la siguiente ejecución lo vuelve a intentar.
            print(f"ERROR {proyecto}/{titulo}: HTTP {r.status_code}")
            continue
        destino.write_text(json.dumps({"meta": meta, "respuesta": cuerpo}, ensure_ascii=False),
                           encoding="utf-8")
        n = len(cuerpo.get("items", [])) if isinstance(cuerpo, dict) else 0
        print(f"{destino.name}: {n} registros")
        time.sleep(PAUSA_WIKI)


def sonda_wikipedia():
    """Comportamiento con dias sin visitas: articulo de muy poco trafico, ventana corta y larga."""
    salida = RAW / "wikipedia_sonda_dias_ausentes.json"
    casos = [  # titulo poco visitado (elegido tras probar), rangos
        ("es.wikipedia", "Parque_nacional_de_Covadonga", "20220101", "20220131"),  # inexistente
        ("es.wikipedia", "Lago_Enol", "20220101", "20220131"),
        ("es.wikipedia", "Lago_de_la_Ercina", "20220101", "20221231"),
        ("es.wikipedia", "Mirador_de_Entrelagos", "20220101", "20221231"),
        ("es.wikipedia", "Lagos_de_Covadonga", "20150101", "20150630"),  # antes del inicio de datos
    ]
    res = []
    for proyecto, t, a, b in casos:
        url = WIKI_API.format(proyecto=proyecto, titulo=quote(t, safe=""), ini=a, fin=b)
        r = get(url)
        try:
            c = r.json()
        except ValueError:
            c = {"texto": r.text}
        items = c.get("items", []) if isinstance(c, dict) else []
        res.append({"titulo": t, "rango": [a, b], "http": r.status_code, "n_items": len(items),
                    "primer": items[0]["timestamp"] if items else None,
                    "ultimo": items[-1]["timestamp"] if items else None,
                    "respuesta": c if r.status_code != 200 else None})
        print(res[-1]["titulo"], r.status_code, len(items))
        time.sleep(PAUSA_WIKI)
    salida.write_text(json.dumps({"descargado_utc": ahora(), "casos": res}, ensure_ascii=False,
                                 indent=1), encoding="utf-8")


def trends(pausa):
    try:
        from pytrends.request import TrendReq
    except ImportError:
        sys.exit("pip install pytrends")
    TRENDS_DIR.mkdir(parents=True, exist_ok=True)
    py = TrendReq(hl="es-ES", tz=0, timeout=(10, 30))
    hoy = date.today().isoformat()
    # (a) serie semanal completa por termino + ancla, por geografia
    for geo in TRENDS_GEOS:
        for term in TRENDS_TERMINOS:
            destino = TRENDS_DIR / f"ancla_{normaliza(TRENDS_ANCLA)}" / f"trends_semanal_{normaliza(term)}_{geo}.json"
            destino.parent.mkdir(parents=True, exist_ok=True)
            if destino.exists():
                continue
            kw = [TRENDS_ANCLA, term]
            try:
                py.build_payload(kw, geo=geo, timeframe=f"2022-01-01 {hoy}")
                df = py.interest_over_time()
            except Exception as e:  # pytrends lanza TooManyRequestsError, ResponseError...
                print(f"BLOQUEO/ERROR en {geo} {term}: {type(e).__name__}: {e}")
                print("Paro: no se esquiva. Ver instrucciones de exportacion manual.")
                return
            meta = {"fuente": "Google Trends via pytrends (no oficial)", "kw_list": kw,
                    "geo": geo, "timeframe": f"2022-01-01 {hoy}", "descargado_utc": ahora()}
            destino.write_text(json.dumps({"meta": meta,
                                           "respuesta": json.loads(df.to_json(orient="table"))},
                                          ensure_ascii=False), encoding="utf-8")
            print(f"{destino.name}: {len(df)} filas")
            time.sleep(pausa)


def oapn():
    OAPN_DIR.mkdir(parents=True, exist_ok=True)
    for nombre, url in OAPN_PDFS.items():
        destino = OAPN_DIR / nombre
        if destino.exists():
            continue
        parcial = destino.with_suffix(".part")
        for intento in range(4):
            try:
                with requests.get(url, headers={"User-Agent": UA}, timeout=60, stream=True) as r:
                    if r.status_code != 200 or "pdf" not in r.headers.get("content-type", ""):
                        print(f"ERROR {nombre}: HTTP {r.status_code} {r.headers.get('content-type')} {url}")
                        break
                    with open(parcial, "wb") as f:
                        for trozo in r.iter_content(1 << 20):
                            f.write(trozo)
                parcial.rename(destino)
                print(f"{nombre}: {destino.stat().st_size} bytes")
                break
            except requests.exceptions.RequestException as e:
                print(f"  intento {intento + 1} fallido en {nombre}: {type(e).__name__}")
                time.sleep(10)
        time.sleep(2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("orden", choices=["wikipedia", "sonda_wikipedia", "trends", "oapn"])
    ap.add_argument("--hasta", default=None)
    ap.add_argument("--pausa", type=float, default=60)
    a = ap.parse_args()
    if a.orden == "wikipedia":
        wikipedia(a.hasta or "2026-10-14")
    elif a.orden == "sonda_wikipedia":
        sonda_wikipedia()
    elif a.orden == "trends":
        trends(a.pausa)
    else:
        oapn()
