"""Elección de estación AEMET por zona (decisión del equipo, 2026-10-15).

    python -X utf8 src/limpieza_B/elige_estaciones.py

Regla acordada: «la estación más cercana con mejor cobertura; en empate,
Llanes 1183X para Ribadesella y Campus 1207U para Gijón».
Cómo se aplica:
- Cobertura = % de días con dato en tmax_c y prec_mm (la menor de las dos),
  desde 2022-01-01 hasta el último día de AEMET. Una estación que deja de
  publicar (1203D Colunga, fin 2026-06-04) no sirve para producción y queda
  fuera.
- Entre las candidatas de cada zona, gana la que es a la vez la más cercana y
  la de mejor cobertura. Si una es más cercana y otra tiene mejor cobertura,
  es un «empate» y se aplica la preferencia del equipo.
- Candidatas: las estaciones de la misma vertiente/emplazamiento que se
  propusieron para cada zona en notas/estaciones_aemet.md y en el mapeo.
  Salida: notas/eleccion_estaciones.md (con todas las distancias, para revisar).
"""
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import CLEAN, CONFIG, NOTAS  # noqa: E402

CANDIDATAS = {           # zona_meteo -> (candidatas, preferencia en empate)
    "cangas_de_onis": (["1186P", "1179B"], "1186P"),
    "lagos_enol": (["1186P", "1179B", "1178R"], "1186P"),
    "llanes": (["1183X"], "1183X"),
    "ribadesella": (["1183X", "1199X", "1203D"], "1183X"),
    "gijon": (["1207U", "1212E", "1210X"], "1207U"),
    "oviedo": (["1249X", "1212E"], "1249X"),
}


def km(a, b, c, d):
    p = math.pi / 180
    h = (math.sin((c - a) * p / 2) ** 2
         + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(h))


def main():
    zonas = pd.read_csv(CONFIG / "zonas_meteo.csv").set_index("zona")
    est = pd.read_csv(CLEAN / "estaciones_aemet.csv", dtype={"indicativo": str}).set_index("indicativo")
    ae = pd.read_parquet(CLEAN / "aemet_diario.parquet")
    ultimo = ae["fecha"].max()
    filas, elegidas = [], {}
    for z, (cands, pref) in CANDIDATAS.items():
        tabla = []
        for e in cands:
            s = ae[ae.estacion == e]
            rango = pd.date_range("2022-01-01", ultimo)
            s = s.set_index("fecha").reindex(rango)
            cob = min(s["tmax_c"].notna().mean(), s["prec_mm"].notna().mean()) * 100
            activa = ae.loc[ae.estacion == e, "fecha"].max() >= ultimo - pd.Timedelta(days=7)
            d = km(zonas.loc[z, "lat"], zonas.loc[z, "lon"], est.loc[e, "lat"], est.loc[e, "lon"])
            tabla.append({"zona_meteo": z, "estacion": e, "nombre": est.loc[e, "nombre"],
                          "altitud_m": est.loc[e, "altitud_m"], "dist_km": round(d, 1),
                          "cobertura_pct": round(cob, 1), "activa": bool(activa)})
        t = pd.DataFrame(tabla)
        v = t[t.activa]
        cerca = v.loc[v.dist_km.idxmin(), "estacion"]
        mejor = v.loc[v.cobertura_pct.idxmax(), "estacion"]
        if cerca == mejor:
            elegida, motivo = cerca, "la más cercana y con mejor cobertura"
        else:
            elegida, motivo = pref, f"empate ({cerca} más cercana, {mejor} mejor cobertura): preferencia del equipo"
        elegidas[z] = (elegida, motivo)
        t["elegida"] = t.estacion == elegida
        filas.append(t)
    res = pd.concat(filas)
    L = ["# Elección de estación AEMET por zona", "",
         "Generado por `python -X utf8 src/limpieza_B/elige_estaciones.py`. La regla y cómo se aplica están en "
         "el docstring del script. La cobertura es el % mínimo de días con tmax y precipitación desde "
         f"2022-01-01 hasta {ultimo.date()}. «activa» = publica hasta la última semana.", "",
         "| zona_meteo | elegida | motivo |", "|---|---|---|"]
    L += [f"| {z} | **{e}** | {m} |" for z, (e, m) in elegidas.items()]
    cols = list(res.columns)
    md = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    md += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for _, r in res.iterrows()]
    L += ["", "Detalle de las candidatas:", "", *md, "",
          "Aviso (no cambia la elección): para Ribadesella, 1186P Amieva-Panizales está algo más cerca "
          f"({km(43.46, -5.06, 43.26667, -5.11917):.1f} km) que Llanes, pero es una estación de valle de "
          "montaña a 370 m. No se ha incluido entre las candidatas de una zona costera."]
    (NOTAS / "eleccion_estaciones.md").write_text("\n".join(L), encoding="utf-8")
    for z, (e, m) in elegidas.items():
        print(f"{z:15s} -> {e}  ({m})")


if __name__ == "__main__":
    main()
