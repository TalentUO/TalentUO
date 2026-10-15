"""Contraste AEMET contra la API (la clave se lee del entorno; no se imprime)."""
import os, json, time, requests
k = os.environ["AEMET_API_KEY"]; B = "https://opendata.aemet.es/opendata"
def get(path):
    for i in range(6):
        r = requests.get(B+path, headers={"api_key": k}, timeout=60)
        if r.status_code == 429: time.sleep(10*(i+1)); continue
        return r
def datos(path):
    j = get(path).json()
    if not j.get("datos"): return j, None
    return j, requests.get(j["datos"], timeout=60)
j, r2 = datos("/api/valores/climatologicos/diarios/datos/fechaini/2024-08-01T00:00:00UTC/fechafin/2024-08-10T23:59:59UTC/estacion/1186P")
try: live = json.loads(r2.content.decode("utf-8"))
except Exception: live = json.loads(r2.content.decode("latin-1"))
saved = {x["fecha"]: x for x in json.load(open("data/raw/aemet_diario_1186P.json", encoding="utf-8"))}
dif = [x["fecha"] for x in live if saved.get(x["fecha"]) != x]
print("1186P 2024-08-01..10: live", len(live), "guardados", sum(1 for x in live if x["fecha"] in saved), "distintos", dif)
time.sleep(3)
j, r2 = datos("/api/prediccion/especifica/municipio/diaria/33012")
print("pred content-type:", r2.headers.get("content-type"), "encoding:", r2.encoding)
print("bytes nombre:", r2.content[r2.content.find(b'"nombre"'):r2.content.find(b'"nombre"')+40])
time.sleep(3)
j, r2 = datos("/api/valores/climatologicos/diarios/datos/fechaini/2026-10-05T00:00:00UTC/fechafin/2026-10-14T23:59:59UTC/estacion/1212E")
d = json.loads(r2.content.decode("utf-8")); print("1212E ultima fecha en API hoy:", d[-1]["fecha"])
time.sleep(3)
j, r2 = datos("/api/valores/climatologicos/diarios/datos/fechaini/2026-06-01T00:00:00UTC/fechafin/2026-06-30T23:59:59UTC/estacion/1203D")
print("1203D jun-2026 API:", j.get("estado"), (len(json.loads(r2.content.decode('utf-8'))) if r2 is not None else None), "dias; guardado:", sum(1 for x in json.load(open("data/raw/aemet_diario_1203D.json",encoding="utf-8")) if x["fecha"].startswith("2026-06")))
