"""Comprobaciones de los CSV anuales MITMA: días distintos, primera/última fecha, filas,
fechas ausentes y (viajes) que todos los destinos estén en Asturias. Uso: python scripts/verificar_mitma.py 2022"""
import sys
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

raw = Path(__file__).resolve().parent.parent / "data" / "raw"
zonas = set(pd.read_csv(raw / "zonas_mitma_asturias.csv", dtype=str)["id_zona_mitma"])
anio = int(sys.argv[1])
fin = date(anio, 6, 30) if anio == 2025 else date(anio, 12, 31)
esperadas = {(date(anio, 1, 1) + timedelta(n)).strftime("%Y%m%d") for n in range((fin - date(anio, 1, 1)).days + 1)}
for tipo, col in (("viajes", "destino"), ("pernoctaciones", "zona_pernoctacion")):
    f = raw / f"mitma_{tipo}_{anio}.csv"
    fechas, filas, fuera = set(), 0, 0
    for t in pd.read_csv(f, dtype=str, keep_default_na=False, chunksize=2_000_000, usecols=["fecha", col]):
        filas += len(t); fechas |= set(t["fecha"].unique()); fuera += (~t[col].isin(zonas)).sum()
    print(f"{f.name}: filas={filas} dias_distintos={len(fechas)} primera={min(fechas)} ultima={max(fechas)} "
          f"filas_con_{col}_fuera_de_Asturias={fuera}")
    print("  fechas NO presentes:", sorted(esperadas - fechas))
    print("  fechas fuera de rango:", sorted(fechas - esperadas))
