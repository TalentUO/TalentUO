"""Comprobación independiente de las cifras observadas de regulacion.json (zona de los Picos, 2023-2024).

    python -X utf8 scripts/verificar_regulacion.py

Recalcula desde data/clean/objetivo_diario.parquet, data/clean/calendario_diario.parquet y el día normal de
salidas/metricas.json: días rojos y ámbar por año, cruce con lagos_regulado y umbral de máximo F1.
No usa el código del modelo (a propósito); solo lee los umbrales y la zona principal de config/.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

R = Path(__file__).resolve().parents[1]
sem = yaml.safe_load((R / "config/semaforo.yaml").read_text(encoding="utf-8"))
AMBAR, ROJO = sem["umbral_ambar"], sem["umbral_rojo"]
ZONA = str(yaml.safe_load((R / "config/modelo.yaml").read_text(encoding="utf-8"))["zona_principal_concejo_ine"])
m = json.loads((R / "salidas/metricas.json").read_text(encoding="utf-8"))
assert m["sintetico"] is False
normal = pd.DataFrame(m["dia_normal"]).query("zona_mitma_id == @ZONA").set_index("dia_semana")["normal"]
o = pd.read_parquet(R / "data/clean/objetivo_diario.parquet")
o = o[(o.zona_mitma_id == ZONA) & (o.calidad == "completa")]
c = pd.read_parquet(R / "data/clean/calendario_diario.parquet")[["fecha", "lagos_regulado"]]
d = o.merge(c, on="fecha")
d = d[d.fecha.dt.year.isin([2023, 2024])].copy()
d["cociente"] = d.llegadas_ocio / d.fecha.dt.dayofweek.map(normal)
d["reg"] = d.lagos_regulado.astype(bool)
for a, g in d.groupby(d.fecha.dt.year):
    rojo, ambar = g.cociente >= ROJO, (g.cociente >= AMBAR) & (g.cociente < ROJO)
    print(f"{a}: días con dato {len(g)}, rojos {rojo.sum()}, ámbar {ambar.sum()}, regulados {g.reg.sum()}, "
          f"rojos en regulados {(rojo & g.reg).sum()}, alerta en regulados {((rojo | ambar) & g.reg).sum()}, "
          f"regulados con cociente < 1 {(g.reg & (g.cociente < 1)).sum()}, "
          f"regulados por debajo de ámbar {(g.reg & (g.cociente < AMBAR)).sum()}")
    print("   rojos por mes:", g[rojo].fecha.dt.month.value_counts().sort_index().to_dict())
    print("   regulados por mes:", g[g.reg].fecha.dt.month.value_counts().sort_index().to_dict())
best = None
for u in np.round(np.arange(0.5, 3.01, 0.05), 2):
    al = d.cociente >= u
    tp = (al & d.reg).sum()
    p, r = tp / al.sum(), tp / d.reg.sum()
    f1 = 2 * p * r / (p + r)
    if best is None or f1 > best[1]:
        best = (u, f1, p, r, al.sum())
    if u in (1.0, 1.1, 1.5, 2.0):
        print(f"umbral {u}: F1 {f1:.3f}, precisión {p:.3f}, recall {r:.3f}, días en alerta {al.sum()}")
print("mejor umbral (F1):", best)
