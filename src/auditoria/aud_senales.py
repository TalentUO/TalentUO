"""Auditoria senales: Wikipedia, Trends, OAPN (solo lectura + verificacion en vivo de muestras)."""
import json, glob, os, requests
from datetime import date
R = "data/raw/"
H = {"User-Agent": "auditoria-TalentUO/1.0 (hackathon; contacto repo)"}
for f in sorted(glob.glob(R+"wikipedia_*.json")):
    j = json.load(open(f, encoding="utf-8")); n = os.path.basename(f)
    if "sonda" in n: print(n, "keys", list(j)[:6]); continue
    meta = j["meta"]; items = j["respuesta"]["items"]
    ts = [i["timestamp"][:8] for i in items]; vs = [i["views"] for i in items]
    a, b = date(int(ts[0][:4]), int(ts[0][4:6]), int(ts[0][6:])), date(int(ts[-1][:4]), int(ts[-1][4:6]), int(ts[-1][6:]))
    esp = (b-a).days+1
    print(f"{n}: n={len(items)} rango={ts[0]}..{ts[-1]} faltan={esp-len(set(ts))} dup={len(ts)-len(set(ts))} ceros={sum(v==0 for v in vs)} max={max(vs)} min={min(vs)} meta={ {k:meta[k] for k in meta if k in ('proyecto','articulo','project','article','titulo')} } keys_meta={list(meta)}")
# redirecciones: consultar la API de Wikipedia para cada titulo
print("\nRedirecciones (API live):")
seen = {}
for f in sorted(glob.glob(R+"wikipedia_*.json")):
    j = json.load(open(f, encoding="utf-8"))
    if "meta" not in j or "sonda" in f: continue
    m = j["meta"]; art = m.get("titulo"); proy = m.get("proyecto") or m.get("project")
    if not art: print(os.path.basename(f), "meta:", m); continue
    lang = (proy or "es.wikipedia").split(".")[0]
    r = requests.get(f"https://{lang}.wikipedia.org/w/api.php", params={"action": "query", "titles": art.replace("_", " "), "redirects": 1, "format": "json"}, headers=H, timeout=30).json()
    red = r["query"].get("redirects"); pg = list(r["query"]["pages"].values())[0]
    print(f"  {lang}:{art} -> redirect={red} existe={'missing' not in pg}")
