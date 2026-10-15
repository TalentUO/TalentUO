"""Construye data/clean/llegadas_por_hora.parquet: a qué hora suelen llegar los visitantes de ocio a cada zona.

Uso:
    python -X utf8 src/modelo/construir_llegadas_por_hora.py \
        --viajes data/raw/mitma_viajes --objetivo data/clean/objetivo_diario.parquet

Tabla resultante (una fila por zona_mitma_id x mes x tipo_dia x hora):
    zona_mitma_id         texto   zona MITMA de destino (la del mapeo)
    mes                   int     1-12
    tipo_dia              texto   `laborable` | `fin_de_semana_o_festivo`
    hora                  int     0-23 (columna `periodo` del MITMA, hora local)
    llegadas_ocio_media   float   media por día de las llegadas de ocio de esa hora (viajes con destino en la zona, origen
                                  distinto, actividad de destino frecuente o no frecuente; igual que `llegadas_ocio` del objetivo)
    n_dias                int     días que entran en la media

Reglas:
- tipo_dia = `fin_de_semana_o_festivo` si es sábado/domingo o festivo autonómico de Asturias (`calendario_diario.parquet`:
  `es_fin_de_semana` o `festivo_ast`); los festivos locales de cada concejo NO se tienen en cuenta.
- Solo entran los días con calidad `completa` del objetivo: se excluyen `sin_dato_mitma` y `anomalia_mitma`.
- En un día completo, una hora sin filas vale 0 (dato real); un día sin datos nunca entra como 0.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construir_objetivo import (ACTIVIDAD, ALIAS_VIAJES, OCIO, TROZO, _fecha,  # noqa: E402
                                _leer_trozos)
from util import CLEAN  # noqa: E402

ALIAS_HORA = {**ALIAS_VIAJES, "periodo": "hora", "hour": "hora"}


def agregar_horas(df: pd.DataFrame, zonas: set[str]) -> pd.DataFrame:
    """Llegadas de ocio por (fecha, zona, hora) de un trozo de viajes."""
    df = df[df["destino"].isin(zonas) & (df["origen"] != df["destino"])].copy()
    act = df["actividad_destino"].str.strip().str.lower()
    desconocidas = sorted(set(act.dropna()) - set(ACTIVIDAD))
    if desconocidas:
        raise ValueError(f"actividad_destino desconocida: {desconocidas}")
    df["viajes"] = pd.to_numeric(df["viajes"].str.replace(",", "."), errors="raise")
    df["llegadas_ocio"] = df["viajes"].where(act.map(ACTIVIDAD).isin(OCIO), 0.0)
    df["fecha"] = _fecha(df["fecha"])
    df["hora"] = pd.to_numeric(df["hora"], errors="raise").astype(int)
    return (df.rename(columns={"destino": "zona_mitma_id"})
            .groupby(["fecha", "zona_mitma_id", "hora"], as_index=False)["llegadas_ocio"].sum())


def llegadas_dia_hora(ficheros: list[Path], zonas: set[str], trozo: int = TROZO) -> pd.DataFrame:
    partes = []
    for f in ficheros:
        for t in _leer_trozos(f, ALIAS_HORA, trozo):
            p = agregar_horas(t, zonas)
            if len(p):
                partes.append(p)
    return pd.concat(partes, ignore_index=True).groupby(["fecha", "zona_mitma_id", "hora"], as_index=False).sum()


def tabla_por_hora(dh: pd.DataFrame, objetivo: pd.DataFrame, calendario: pd.DataFrame) -> pd.DataFrame:
    """Media por día de cada hora, por zona, mes y tipo de día, solo con días `completa`."""
    ok = objetivo.loc[objetivo["calidad"] == "completa", ["fecha", "zona_mitma_id"]]
    cal = calendario[["fecha", "es_fin_de_semana", "festivo_ast"]].copy()
    cal["tipo_dia"] = (cal["es_fin_de_semana"] | cal["festivo_ast"]).map(
        {True: "fin_de_semana_o_festivo", False: "laborable"})
    base = ok.merge(pd.DataFrame({"hora": range(24)}), how="cross")           # día completo x 24 horas
    base["fecha"] = base["fecha"].astype("datetime64[us]")
    dh = dh.assign(fecha=dh["fecha"].astype("datetime64[us]"))
    x = base.merge(dh, on=["fecha", "zona_mitma_id", "hora"], how="left", validate="one_to_one")
    x["llegadas_ocio"] = x["llegadas_ocio"].fillna(0.0)                       # día con datos, hora sin filas = 0 real
    cal["fecha"] = cal["fecha"].astype("datetime64[us]")
    x = x.merge(cal[["fecha", "tipo_dia"]], on="fecha", how="left", validate="many_to_one")
    assert x["tipo_dia"].notna().all(), "faltan fechas en el calendario"
    x["mes"] = x["fecha"].dt.month
    out = (x.groupby(["zona_mitma_id", "mes", "tipo_dia", "hora"], as_index=False)
           .agg(llegadas_ocio_media=("llegadas_ocio", "mean"), n_dias=("fecha", "nunique")))
    return out.sort_values(["zona_mitma_id", "mes", "tipo_dia", "hora"]).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--viajes", default=str(Path("data/raw/mitma_viajes")))
    ap.add_argument("--objetivo", default=str(CLEAN / "objetivo_diario.parquet"))
    ap.add_argument("--calendario", default=str(CLEAN / "calendario_diario.parquet"))
    ap.add_argument("--salida", default=str(CLEAN / "llegadas_por_hora.parquet"))
    a = ap.parse_args()
    obj = pd.read_parquet(a.objetivo)
    zonas = set(obj["zona_mitma_id"].unique())
    ficheros = sorted(Path(a.viajes).glob("*.csv"))
    if not ficheros:
        raise SystemExit(f"No hay ficheros de viajes en {a.viajes}")
    dh = llegadas_dia_hora(ficheros, zonas)
    out = tabla_por_hora(dh, obj, pd.read_parquet(a.calendario))
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(a.salida, index=False)
    print(f"{a.salida}: {len(out)} filas, {out['zona_mitma_id'].nunique()} zonas, "
          f"{out['tipo_dia'].nunique()} tipos de día, n_dias {out['n_dias'].min()}-{out['n_dias'].max()}")


if __name__ == "__main__":
    main()
