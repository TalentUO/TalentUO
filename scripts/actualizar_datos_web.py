"""Copia las salidas del modelo a la carpeta de datos de la web.

    python -X utf8 scripts/actualizar_datos_web.py

Mañana, con datos reales: ejecutar el modelo y después este script. Nada más.

Qué hace:
1. Copia los cinco JSON del contrato (notas/contrato_web.md) de salidas/ a
   «Afluencia Asturias/datos/modelo/», sin modificarlos.
2. Copia el mapeo de zonas a concejos (config/mapeo_zonas.csv). Si los IDs de
   zona de predicciones.json no están en ese fichero (modo sintético, IDs
   EJEMPLO_*), usa config/mapeo_zonas_ejemplo.csv.
3. Escribe «datos/modelo/salidas.js» con todo lo anterior, para que la web se
   abra con doble clic (desde file:// el navegador no deja leer JSON con fetch).
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDAS = RAIZ / "salidas"
CONFIG = RAIZ / "config"
DESTINO = RAIZ / "Afluencia Asturias" / "datos" / "modelo"
FICHEROS = ("predicciones", "alternativas", "regulacion", "perfil", "metricas")


def leer_mapeo(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8", newline="") as f:
        return [
            {
                "zona_mitma_id": (r.get("zona_mitma_id") or "").strip(),
                "nombre": (r.get("nombre") or "").strip(),
                "concejos_ine": [c.strip() for c in (r.get("concejos_ine") or "").split(";") if c.strip()],
            }
            for r in csv.DictReader(f)
        ]


def elegir_mapeo(ids_zonas: set[str]) -> tuple[Path, list[dict]]:
    """El mapeo real si cubre las zonas de las predicciones; si no, el de ejemplo."""
    candidatos = [CONFIG / "mapeo_zonas.csv", CONFIG / "mapeo_zonas_ejemplo.csv"]
    for ruta in candidatos:
        if not ruta.exists():
            continue
        filas = leer_mapeo(ruta)
        if ids_zonas <= {f["zona_mitma_id"] for f in filas if f["zona_mitma_id"]}:
            return ruta, filas
    sys.exit(f"ERROR: ningún mapeo de config/ cubre las zonas de predicciones.json: {sorted(ids_zonas)}")


def main() -> None:
    faltan = [n for n in FICHEROS if not (SALIDAS / f"{n}.json").exists()]
    if faltan:
        sys.exit(f"ERROR: faltan en salidas/: {', '.join(n + '.json' for n in faltan)}")

    # Mismo validador que usa el modelo (si está disponible)
    sys.path.insert(0, str(RAIZ / "src" / "modelo"))
    try:
        from validar_salidas import validar
    except ImportError:
        validar = None
    if validar:
        errores = validar(SALIDAS)
        if errores:
            print("\n".join(errores[:20]))
            sys.exit(f"ERROR: las salidas no cumplen el contrato ({len(errores)} problemas). No se copia nada.")

    datos = {n: json.loads((SALIDAS / f"{n}.json").read_text(encoding="utf-8")) for n in FICHEROS}
    ids = {z["zona_mitma_id"] for z in datos["predicciones"]["zonas"]}
    ruta_mapeo, mapeo = elegir_mapeo(ids)

    DESTINO.mkdir(parents=True, exist_ok=True)
    for n in FICHEROS:
        shutil.copyfile(SALIDAS / f"{n}.json", DESTINO / f"{n}.json")
    (DESTINO / "mapeo_zonas.json").write_text(
        json.dumps({"origen": f"config/{ruta_mapeo.name}", "zonas": mapeo}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    paquete = dict(datos, mapeo={"origen": f"config/{ruta_mapeo.name}", "zonas": mapeo})
    (DESTINO / "salidas.js").write_text(
        "// GENERADO por scripts/actualizar_datos_web.py. No editar a mano.\n"
        "window.SALIDAS_MODELO = " + json.dumps(paquete, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")

    sint = {d.get("sintetico") for d in datos.values()}
    print(f"Copiados {len(FICHEROS)} JSON a {DESTINO.relative_to(RAIZ)}")
    print(f"Mapeo de zonas: config/{ruta_mapeo.name} ({len(mapeo)} zonas)")
    print(f"sintetico = {sint}  generado = {datos['predicciones'].get('generado')}  fecha_hoy = {datos['predicciones'].get('fecha_hoy')}")


if __name__ == "__main__":
    main()
