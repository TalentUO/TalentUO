"""Auditoria AEMET (solo lectura). Uso: python -I src/auditoria/aud_aemet.py"""
import json, glob, os, re
from datetime import date, timedelta
from collections import Counter
R = "data/raw/"
inv = json.load(open(R+"aemet_inventario.json", encoding="utf-8"))
print("inventario:", type(inv).__name__, len(inv), "claves:", sorted(inv[0].keys()))
idx = {e["indicativo"]: e for e in inv}
dup_inv = [k for k, v in Counter(e["indicativo"] for e in inv).items() if v > 1]
print("duplicados inventario:", dup_inv)
est_md = open("notas/estaciones_aemet.md", encoding="utf-8").read()
listadas = sorted(set(re.findall(r"\|\s*\**(\d{4}[A-Z]?|\d{4})\**\s*\|", est_md)))
print("listadas en estaciones_aemet.md:", listadas)
files = sorted(glob.glob(R+"aemet_diario_*.json"))
print("ficheros diarios:", [os.path.basename(f) for f in files])
cob = open("notas/cobertura_aemet.md", encoding="utf-8").read()
for f in files:
    ind = re.search(r"diario_(.+)\.json", f).group(1)
    d = json.load(open(f, encoding="utf-8"))
    fechas = [r["fecha"] for r in d]
    c = Counter(fechas); dups = {k: v for k, v in c.items() if v > 1}
    s = sorted(set(fechas))
    a, b = date.fromisoformat(s[0]), date.fromisoformat(s[-1])
    allr = {a+timedelta(i) for i in range((b-a).days+1)}
    miss = sorted(allr - {date.fromisoformat(x) for x in s})
    # huecos agrupados
    gaps = []
    for m in miss:
        if gaps and (m-gaps[-1][1]).days == 1: gaps[-1][1] = m
        else: gaps.append([m, m])
    big = [(str(x), str(y), (y-x).days+1) for x, y in gaps if (y-x).days+1 >= 5]
    ini = date(2022,1,1); fin = date(2026,10,14)
    falt_ini = (a-ini).days; 
    keys = Counter(k for r in d for k in r)
    e = idx.get(ind)
    # cobertura declarada
    m = re.search(r"## %s .*?\n\nRango real: (\S+) a (\S+); (\d+) dias" % re.escape(ind), cob, re.S)
    unsorted = fechas != sorted(fechas)
    print(f"\n[{ind}] {e['nombre'] if e else 'NO EN INVENTARIO'} alt={e['altitud'] if e else '-'} prov={e['provincia'] if e else '-'} lat={e['latitud'] if e else '-'} lon={e['longitud'] if e else '-'}")
    print(f"  registros={len(d)} distintas={len(s)} dup={len(dups)} rango={s[0]}..{s[-1]} dias_rango={len(allr)+len(miss)-len(miss)} faltan_dentro_rango={len(miss)} huecos>=5d={big}")
    print(f"  retraso vs 2026-10-15: {(date(2026,10,15)-b).days} d; empieza {falt_ini} d tras 2022-01-01; ordenado={not unsorted}")
    print(f"  cobertura.md declara: {m.groups() if m else 'NO ENCONTRADO'}")
    print(f"  campos: {dict(keys)}")
    vals = Counter(); 
    for r in d:
        for k in ("tmax","tmin","prec","sol","velmedia"):
            v = r.get(k)
            if v is not None and not re.fullmatch(r"-?\d+(,\d+)?", str(v)): vals[(k,v)] += 1
    print("  valores no numericos:", dict(vals))
    print("  tipos de valor:", Counter(type(r.get("tmax")).__name__ for r in d))
