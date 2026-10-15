"""Ejecuta toda la limpieza de la parte B de principio a fin.

    python -X utf8 src/limpieza_B/ejecutar_todo.py

Orden: tablas 1-5, prueba de unir_B con datos sintéticos, prueba de unir_B
con las tablas reales y un mapeo de ejemplo, y control de calidad. Se detiene
en el primer script que falle (las comprobaciones automáticas lanzan
AssertionError).
"""
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]

PASOS = [
    ["limpia_aemet.py"],
    ["limpia_openmeteo.py"],
    ["limpia_calendario.py"],
    ["limpia_eventos.py"],
    ["limpia_senales.py"],
    ["elige_estaciones.py"],
    ["test_unir_B.py"],
    ["unir_B.py", "--mapeo", "config/mapeo_zonas_ejemplo.csv",
     "--salida", "data/clean/_prueba/factores_B_ejemplo.parquet"],
    ["control_calidad.py"],
]

for paso in PASOS:
    print(f"\n=== {' '.join(paso)} ===", flush=True)
    r = subprocess.run([sys.executable, "-X", "utf8", str(AQUI / paso[0]), *paso[1:]], cwd=RAIZ)
    if r.returncode != 0:
        sys.exit(f"FALLO en {paso[0]} (código {r.returncode})")
print("\nLimpieza B completa.")
