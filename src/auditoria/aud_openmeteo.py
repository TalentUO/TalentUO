"""Auditoria Open-Meteo (solo lectura)."""
import json, glob, os, csv, re
from collections import Counter
R = "data/raw/"
zonas = [r["zona"] for r in csv.DictReader(open("config/zonas_meteo.csv"))]
print("zonas config:", zonas)
for f in sorted(glob.glob(R+"openmeteo_*.json")):
    d = json.load(open(f, encoding="utf-8"))
    blk = "daily" if "daily" in d else "hourly"
    t = d[blk]["time"]
    dups = len(t) - len(set(t))
    nul = {k: sum(x is None for x in v) for k, v in d[blk].items() if k != "time"}
    nz = {k: v for k, v in nul.items() if v}
    print(f"\n{os.path.basename(f)}: top-level keys={[k for k in d if k not in (blk,)]}")
    print(f"  bloque={blk} n={len(t)} rango={t[0]}..{t[-1]} dup={dups} ordenado={t==sorted(t)}")
    print(f"  lat/lon devueltas={d.get('latitude')},{d.get('longitude')} elevation={d.get('elevation')} tz={d.get('timezone')} utc_off={d.get('utc_offset_seconds')}")
    print(f"  variables={[k for k in d[blk] if k!='time']}")
    print(f"  nulos distintos de 0: {nz}")
    dd = d.get("_descarga")
    if dd:
        print(f"  _descarga: zona={dd['zona']} pedida=({dd['lat_pedida']},{dd['lon_pedida']}) rango_real={dd['rango_real']} n={dd['n_registros']} extra_keys={list(dd['parametros_extra'])}")
        print("  elevations por tramo:", Counter(x["elevation"] for x in dd["tramos"]), "latlon:", Counter((x["latitude"],x["longitude"]) for x in dd["tramos"]))
        # coherencia declarada vs real
        real_nul = nul
        print("  nulos declarados==reales:", dd["nulos"] == real_nul)
    if blk == "daily":
        # huecos de fecha
        from datetime import date, timedelta
        a, b = date.fromisoformat(t[0]), date.fromisoformat(t[-1])
        print("  dias faltantes:", (b-a).days+1-len(set(t)))
    else:
        from datetime import datetime, timedelta
        a, b = datetime.fromisoformat(t[0]), datetime.fromisoformat(t[-1])
        print("  horas esperadas", int((b-a).total_seconds()//3600)+1, "reales", len(t))
        # primer dato no nulo por variable
        pn = {}
        for k, v in d[blk].items():
            if k == "time": continue
            for i, x in enumerate(v):
                if x is not None: pn[k] = t[i]; break
        print("  primer no nulo:", {k:v for k,v in pn.items() if "previous" in k and k.startswith(("temperature","precip"))})
    print("  units:", d.get(blk+"_units"))
