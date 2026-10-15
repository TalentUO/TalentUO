"""Divide los CSV anuales del MITMA (filtrados a Asturias) en ficheros mensuales, sin tocar los anuales.

Entrada : <raw>/mitma_viajes_<año>.csv y <raw>/mitma_pernoctaciones_<año>.csv (una cabecera + filas con `fecha` AAAAMMDD en la 1.ª columna).
Salida  : <raw>/mitma_viajes/AAAA-MM.csv y <raw>/mitma_pernoctaciones/AAAA-MM.csv (misma cabecera, mismas líneas, byte a byte).
No transforma nada: cada línea se copia tal cual al fichero de su mes. Comprueba que el total de filas cuadra.
Uso: python scripts/dividir_mitma_mensual.py [--raw C:/ruta/a/data/raw]
"""
import argparse
from pathlib import Path

TIPOS = ("viajes", "pernoctaciones")


def dividir(raw: Path, tipo: str) -> dict:
    destino = raw / f"mitma_{tipo}"
    destino.mkdir(exist_ok=True)
    cuentas = {}
    for anual in sorted(raw.glob(f"mitma_{tipo}_20??.csv")):
        salidas = {}
        filas_entrada = 0
        with open(anual, "rb") as f:
            cab = f.readline()
            for linea in f:
                mes = linea[:6].decode()
                h = salidas.get(mes)
                if h is None:
                    # modo "wb": si el mes ya existe de una ejecución anterior se reescribe entero
                    h = salidas[mes] = open(destino / f"{mes[:4]}-{mes[4:]}.csv", "wb")
                    h.write(cab)
                h.write(linea)
                filas_entrada += 1
        for h in salidas.values():
            h.close()
        total_meses = 0
        for mes in salidas:
            with open(destino / f"{mes[:4]}-{mes[4:]}.csv", "rb") as g:
                n = sum(1 for _ in g) - 1
            cuentas[mes] = n
            total_meses += n
        assert total_meses == filas_entrada, f"{anual.name}: {total_meses} != {filas_entrada}"
        print(f"{anual.name}: {filas_entrada} filas -> {len(salidas)} meses")
    return cuentas


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(Path(__file__).resolve().parent.parent / "data" / "raw"))
    a = ap.parse_args()
    for t in TIPOS:
        c = dividir(Path(a.raw), t)
        print(t, "meses:", len(c), "filas:", sum(c.values()))
