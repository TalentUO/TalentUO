"""Resumen compacto de los JSON Open-Meteo presentes ahora mismo (para re-ejecutar al final)."""
import json, glob, os, csv
zonas = [r["zona"] for r in csv.DictReader(open("config/zonas_meteo.csv"))]
for f in sorted(glob.glob("data/raw/openmeteo_*.json")):
    d = json.load(open(f, encoding="utf-8")); blk = "daily" if "daily" in d else "hourly"; t = d[blk]["time"]
    nul = {k: sum(x is None for x in v) for k, v in d[blk].items() if k != "time"}
    print(f"{os.path.basename(f):45} n={len(t):6} {t[0][:10]}..{t[-1][:10]} dup={len(t)-len(set(t))} elev={d.get('elevation')} lat/lon={d.get('latitude')},{d.get('longitude')} nulos_total={sum(nul.values())} pedida={d.get('_descarga',{}).get('lat_pedida')},{d.get('_descarga',{}).get('lon_pedida')}")
hist = {os.path.basename(f)[10:-5] for f in glob.glob("data/raw/openmeteo_*.json") if not any(x in f for x in ("previous", "archive", "prevision"))}
prev = {os.path.basename(f)[19:-5] for f in glob.glob("data/raw/openmeteo_previous_*.json")}
print("zonas config:", len(zonas), "| hist faltan:", sorted(set(zonas)-hist), "| previous faltan:", sorted(set(zonas)-prev), "| archive:", sorted(os.path.basename(f)[19:-5] for f in glob.glob("data/raw/openmeteo_archive_*.json")), "| prevision_ejemplo:", os.path.exists("data/raw/openmeteo_prevision_ejemplo.json"))
