"""Calcula umbrales del semáforo por zona a partir de su propia historia y los escribe en config/semaforo.yaml.

    python -X utf8 scripts/umbrales_por_zona.py            # muestra y escribe
    python -X utf8 scripts/umbrales_por_zona.py --solo-ver # solo muestra

Criterio (decisión del equipo, 2026-10-16; notas/umbrales_por_zona.md):
- cociente = llegadas de ocio observadas / día normal de la zona (el mismo del semáforo:
  mediana de 2024 sin julio, agosto ni festivos, por día de la semana);
- días con dato completo de los años enteros 2022, 2023 y 2024;
- alta (ámbar)  = percentil 90 de la zona: el 10 % de días más concurridos, y al menos +15 %;
- saturación (rojo) = percentil 97: el 3 % de días más concurridos, y al menos +30 % y 0,10 por encima del ámbar.
Los mínimos evitan que el ruido diario del MITMA en las zonas muy estables (ciudades) dispare alertas.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src" / "modelo"))
import datos as DM  # noqa: E402
import dia_normal  # noqa: E402

P_AMBAR, P_ROJO = 0.90, 0.97
MIN_AMBAR, MIN_ROJO, SEPARACION = 1.15, 1.30, 0.10
ANIOS = (2022, 2023, 2024)


def calcular() -> pd.DataFrame:
    D = DM.cargar("real")
    o = D.obj.merge(D.base[["fecha", "zona_mitma_id", "cal_dia_semana"]], on=["fecha", "zona_mitma_id"])
    o = dia_normal.anadir_normal(o, D.normal_ref, "normal")
    o = o[(o["calidad"] == "completa") & (o["fecha"].dt.year.isin(ANIOS))].copy()
    o["cociente"] = o[D.objetivo] / o["normal"]
    g = o.groupby("zona_mitma_id")["cociente"]
    t = pd.DataFrame({"p90": g.quantile(P_AMBAR), "p97": g.quantile(P_ROJO), "dias": g.size()})
    t["umbral_ambar"] = t["p90"].clip(lower=MIN_AMBAR).round(2)
    t["umbral_rojo"] = pd.concat([t["p97"], t["umbral_ambar"] + SEPARACION], axis=1).max(axis=1).clip(lower=MIN_ROJO).round(2)
    t["nombre"] = t.index.map(D.nombres)
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--solo-ver", action="store_true")
    a = ap.parse_args()
    t = calcular()
    pd.set_option("display.width", 200)
    print(t.sort_values("umbral_rojo", ascending=False).round(2).to_string())
    if a.solo_ver:
        return
    ruta = RAIZ / "config" / "semaforo.yaml"
    texto = ruta.read_text(encoding="utf-8")
    cab = texto.split("\npor_zona:")[0]
    resto = texto.split("\npor_zona:")[1].split("\n", 1)[1] if "\npor_zona:" in texto else ""
    bloque = ("\n# Umbrales por zona: scripts/umbrales_por_zona.py (percentiles 90 y 97 de 2022-2024; mínimos +15 % y +30 %).\n"
              "por_zona:\n" + "".join(f"  \"{z}\": {{umbral_ambar: {r.umbral_ambar}, umbral_rojo: {r.umbral_rojo}}}  # {r.nombre}\n"
                                      for z, r in t.sort_index().iterrows()))
    ruta.write_text(cab + bloque + resto, encoding="utf-8")
    yaml.safe_load(ruta.read_text(encoding="utf-8"))  # comprueba que el YAML es válido
    print(f"Escrito en {ruta.relative_to(RAIZ)}: {len(t)} zonas")


if __name__ == "__main__":
    main()
