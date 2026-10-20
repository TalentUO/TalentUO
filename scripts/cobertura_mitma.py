"""Tabla de cobertura de los ficheros mensuales del MITMA (solo lectura).

Para cada mes 2022-01..2025-06 y tipo (viajes, pernoctaciones): ¿existe y abre?, filas, días presentes frente a esperados,
huecos oficiales / no oficiales, días oficialmente «sin datos» que SÍ están publicados, y filas cuyo destino
(viajes) o zona de pernoctación (pernoctaciones) no es una zona de Asturias.
Uso: python scripts/cobertura_mitma.py --raw C:/ruta/data/raw --zonas C:/ruta/zonas_mitma_asturias.csv --salida notas/fuentes/mitma/cobertura_mitma.md
"""
import argparse
import calendar
import csv
from datetime import date
from pathlib import Path

# Días sin datos que declara el MITMA en su página (lista del equipo)
OFICIALES = {date.fromisoformat(d) for d in (
    "2023-10-26", "2023-10-27", "2023-10-30", "2023-10-31", "2023-11-01", "2023-11-02", "2023-11-03",
    "2024-04-04", "2024-04-18", "2024-04-19", "2024-11-10", "2024-11-11", "2025-04-28", "2025-04-29")}
ANOMALIAS = {date.fromisoformat(d) for d in ("2024-10-29", "2024-10-30", "2024-10-31")}
CAMPO = {"viajes": 3, "pernoctaciones": 2}  # posición (0-based) del campo destino / zona_pernoctacion


def meses():
    for a in range(2022, 2026):
        for m in range(1, 13):
            if (a, m) <= (2025, 6):
                yield a, m


def revisar(f: Path, tipo: str, zonas: set):
    fechas, filas, fuera = set(), 0, 0
    k = CAMPO[tipo]
    with open(f, "rb") as fh:
        cab = fh.readline().decode().strip()
        for linea in fh:
            c = linea.split(b",", k + 1)
            fechas.add(c[0])
            filas += 1
            if c[k].decode() not in zonas:
                fuera += 1
    return cab, filas, {date(int(x[:4]), int(x[4:6]), int(x[6:8])) for x in fechas}, fuera


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--zonas", required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    raw = Path(a.raw)
    with open(a.zonas, encoding="utf-8", newline="") as fh:
        zonas = {r.get("id_zona_mitma") or r.get("zona_mitma_id") or r.get("id") for r in csv.DictReader(fh)}
    lineas, problemas = [], []
    for tipo in ("viajes", "pernoctaciones"):
        for y, m in meses():
            f = raw / f"mitma_{tipo}" / f"{y}-{m:02d}.csv"
            esperadas = {date(y, m, d) for d in range(1, calendar.monthrange(y, m)[1] + 1)}
            if not f.exists():
                lineas.append(f"| {y}-{m:02d} | {tipo} | **NO EXISTE** | | | | | | |")
                problemas.append(f"{tipo} {y}-{m:02d}: fichero ausente")
                continue
            cab, filas, pres, fuera = revisar(f, tipo, zonas)
            aus = sorted(esperadas - pres)
            of = [d for d in aus if d in OFICIALES]
            no_of = [d for d in aus if d not in OFICIALES]
            publicado_of = sorted(d for d in pres if d in OFICIALES)
            extra = sorted(d for d in pres if d not in esperadas)
            if no_of:
                problemas.append(f"{tipo} {y}-{m:02d}: huecos NO oficiales {[d.isoformat() for d in no_of]}")
            if fuera or extra:
                problemas.append(f"{tipo} {y}-{m:02d}: fuera_de_Asturias={fuera} fechas_fuera_de_mes={extra}")
            fmt = lambda L: ", ".join(d.strftime("%d") for d in L) or "—"
            lineas.append(f"| {y}-{m:02d} | {tipo} | {filas:,} | {len(pres)}/{len(esperadas)} | {fmt(of)} | {fmt(no_of)} | "
                          f"{fmt(publicado_of)} | {fuera} | {'sí' if any(d in ANOMALIAS for d in pres) else '—'} |".replace(",", " "))
    cab = ("# Cobertura de los ficheros mensuales del MITMA (2022-01 a 2025-06)\n\n"
           "Generado con `scripts/cobertura_mitma.py` (solo lectura). `fuera` = filas cuyo destino (viajes) o zona de pernoctación "
           "no está en `zonas_mitma_asturias.csv` (debe ser 0). Los días sin datos oficiales y los publicados se indican por día del mes.\n\n"
           "| Mes | Tipo | Filas | Días presentes | Ausentes oficiales | Ausentes NO oficiales | Oficialmente sin datos pero PUBLICADOS | Fuera de Asturias | Con anomalía (DANA) |\n"
           "|---|---|---|---|---|---|---|---|---|\n")
    resumen = "\n\n## Problemas detectados\n\n" + ("\n".join(f"- {p}" for p in problemas) if problemas else "Ninguno.") + "\n"
    Path(a.salida).write_text(cab + "\n".join(lineas) + resumen, encoding="utf-8")
    print(f"{len(lineas)} filas; problemas: {len(problemas)}")


if __name__ == "__main__":
    main()
