"""Compara el estado de TU descarga (data/raw/_mitma_estado_v2.jsonl) con la tabla de referencia
notas/fuentes/mitma/mitma_referencia_filas_por_dia.csv (filas de Asturias por día y tipo, de la descarga original).
Un día descargado por ti debe dar EXACTAMENTE las mismas filas_origen y filas_asturias que en la referencia.
Uso: python scripts/comparar_con_referencia.py"""
import json
from pathlib import Path
import pandas as pd

raiz = Path(__file__).resolve().parent.parent
ref = pd.read_csv(raiz / "notas" / "fuentes" / "mitma" / "mitma_referencia_filas_por_dia.csv", dtype={"fecha": str})
est = {}
for l in (raiz / "data" / "raw" / "_mitma_estado_v2.jsonl").read_text(encoding="utf-8").splitlines():
    if l.strip():
        r = json.loads(l)
        est[(r["tipo"], r["fecha"])] = r
mios = pd.DataFrame([{"tipo": t, "fecha": f, "estado_tuyo": r["estado"], "filas_origen_tuyo": r.get("filas_origen"),
                      "filas_asturias_tuyo": r.get("filas_asturias")} for (t, f), r in est.items()])
m = ref.merge(mios, on=["tipo", "fecha"], how="left")
hechos = m[m["estado_tuyo"].notna()].fillna(-1)  # -1 = sin dato (días NO_DISPONIBLE): así dos vacíos cuentan como iguales
dif = hechos[(hechos["estado"] != hechos["estado_tuyo"]) | (hechos["filas_origen"] != hechos["filas_origen_tuyo"])
             | (hechos["filas_asturias"] != hechos["filas_asturias_tuyo"])]
print(f"Referencia: {len(ref)} días-tipo. Tú tienes {len(hechos)} comparables y {len(m) - len(hechos)} sin descargar aún.")
print(f"Diferencias: {len(dif)}")
if len(dif):
    print(dif.to_string(index=False))
print("Sin descargar aún (resumen):", m[m['estado_tuyo'].isna()].groupby(['tipo', m['fecha'].str[:4]]).size().to_dict())
