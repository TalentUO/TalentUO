"""Construye data/clean/objetivo_diario.parquet a partir de los ficheros del MITMA.

Uso:
    python -X utf8 src/modelo/construir_objetivo.py
    python -X utf8 src/modelo/construir_objetivo.py --viajes data/raw/mitma_viajes \
        --pernoctaciones data/raw/mitma_pernoctaciones --mapeo config/mapeo_zonas.csv

Contrato del resultado: notas/contrato_objetivo.md.

Acepta dos formatos de columnas (se detectan por fichero):
- MITMA original. Viajes: fecha, periodo, origen, destino, actividad_origen,
  actividad_destino, residencia, viajes. Pernoctaciones: fecha,
  zona_residencia, zona_pernoctacion, personas.
- spanishoddata. Viajes: date, hour, id_origin, id_destination,
  activity_destination, residence_province_ine_code, n_trips. Pernoctaciones:
  date, id_residence, id_overnight_stay, n_persons.
El separador (`|`, `,` o `;`) se detecta en la primera línea.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import CLEAN, RAW, cfg, cfg_calidad_mitma, ruta  # noqa: E402

COLUMNAS_SALIDA = ["fecha", "zona_mitma_id", "llegadas_total", "llegadas_ocio",
                   "llegadas_desde_asturias", "llegadas_resto_espana",
                   "pernoctaciones_no_residentes", "calidad"]
VALORES = COLUMNAS_SALIDA[2:7]

ALIAS_VIAJES = {
    "fecha": "fecha", "date": "fecha",
    "origen": "origen", "id_origin": "origen",
    "destino": "destino", "id_destination": "destino",
    "actividad_destino": "actividad_destino", "activity_destination": "actividad_destino",
    "residencia": "residencia", "residence_province_ine_code": "residencia",
    "viajes": "viajes", "n_trips": "viajes",
}
ALIAS_PERN = {
    "fecha": "fecha", "date": "fecha",
    "zona_residencia": "residencia", "id_residence": "residencia",
    "zona_pernoctacion": "pernoctacion", "id_overnight_stay": "pernoctacion",
    "personas": "personas", "n_persons": "personas",
}
# Actividad en destino. Ocio = actividad frecuente o no frecuente (sin trabajo,
# estudio ni casa). Se aceptan los valores del MITMA y los de spanishoddata.
ACTIVIDAD = {
    "frecuente": "frequent_activity", "frequent_activity": "frequent_activity",
    "no_frecuente": "infrequent_activity", "infrequent_activity": "infrequent_activity",
    "casa": "home", "home": "home",
    "trabajo_estudio": "work_or_study", "work_or_study": "work_or_study",
}
OCIO = {"frequent_activity", "infrequent_activity"}
PROVINCIA_ASTURIAS = "33"


def _separador(f: Path) -> str:
    with open(f, encoding="utf-8", errors="replace") as fh:
        linea = fh.readline()
    return max(["|", ",", ";"], key=linea.count)


def _leer(f: Path, alias: dict) -> pd.DataFrame:
    cab = pd.read_csv(f, sep=_separador(f), nrows=0).columns
    usar = [c for c in cab if c in alias]
    df = pd.read_csv(f, sep=_separador(f), usecols=usar, dtype=str)
    df = df.rename(columns=alias)
    faltan = sorted(set(alias.values()) - set(df.columns))
    if faltan:
        raise ValueError(f"{f.name}: faltan columnas {faltan} (cabecera: {list(cab)})")
    return df


def _fecha(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip().str.slice(0, 10)
    compacta = s.str.fullmatch(r"\d{8}")
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[us]")
    out[compacta] = pd.to_datetime(s[compacta], format="%Y%m%d")
    out[~compacta] = pd.to_datetime(s[~compacta], format="%Y-%m-%d")
    return out


def _provincia(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    return s.where(~s.str.fullmatch(r"\d{1}"), s.str.zfill(2))


def agregar_viajes(df: pd.DataFrame, zonas: set[str]) -> pd.DataFrame:
    """Viajes -> llegadas por (fecha, zona). Solo destinos de `zonas`, origen fuera."""
    df = df[df["destino"].isin(zonas) & (df["origen"] != df["destino"])].copy()
    df["viajes"] = pd.to_numeric(df["viajes"].str.replace(",", "."), errors="raise")
    act = df["actividad_destino"].str.strip().str.lower()
    desconocidas = sorted(set(act.dropna()) - set(ACTIVIDAD))
    if desconocidas:
        raise ValueError(f"actividad_destino desconocida: {desconocidas}")
    ocio = act.map(ACTIVIDAD).isin(OCIO)
    prov = _provincia(df["residencia"])
    df["fecha"] = _fecha(df["fecha"])
    df["llegadas_total"] = df["viajes"]
    df["llegadas_ocio"] = df["viajes"].where(ocio, 0.0)
    # Residencia (provincia) de las llegadas de ocio: ver contrato_objetivo.md.
    df["llegadas_desde_asturias"] = df["llegadas_ocio"].where(prov == PROVINCIA_ASTURIAS, 0.0)
    df["llegadas_resto_espana"] = df["llegadas_ocio"].where(
        (prov != PROVINCIA_ASTURIAS) & prov.str.fullmatch(r"\d{2}"), 0.0)
    return (df.rename(columns={"destino": "zona_mitma_id"})
            .groupby(["fecha", "zona_mitma_id"], as_index=False)
            [["llegadas_total", "llegadas_ocio", "llegadas_desde_asturias", "llegadas_resto_espana"]].sum())


def agregar_pernoctaciones(df: pd.DataFrame, zonas: set[str]) -> pd.DataFrame:
    df = df[df["pernoctacion"].isin(zonas) & (df["residencia"] != df["pernoctacion"])].copy()
    df["personas"] = pd.to_numeric(df["personas"].str.replace(",", "."), errors="raise")
    df["fecha"] = _fecha(df["fecha"])
    return (df.rename(columns={"pernoctacion": "zona_mitma_id", "personas": "pernoctaciones_no_residentes"})
            .groupby(["fecha", "zona_mitma_id"], as_index=False)["pernoctaciones_no_residentes"].sum())


def construir(ficheros_viajes: list[Path], ficheros_pern: list[Path], zonas: list[str],
              inicio: str, fin: str) -> pd.DataFrame:
    zs = set(zonas)
    v = [agregar_viajes(_leer(f, ALIAS_VIAJES), zs) for f in ficheros_viajes]
    p = [agregar_pernoctaciones(_leer(f, ALIAS_PERN), zs) for f in ficheros_pern]
    v = pd.concat(v, ignore_index=True) if v else pd.DataFrame(columns=["fecha", "zona_mitma_id"])
    p = pd.concat(p, ignore_index=True) if p else pd.DataFrame(columns=["fecha", "zona_mitma_id"])
    fechas_con_viajes = set(pd.to_datetime(v["fecha"]))
    fechas_con_pern = set(pd.to_datetime(p["fecha"]))

    fechas = pd.date_range(inicio, fin, freq="D")
    base = pd.MultiIndex.from_product([fechas, sorted(zs)], names=["fecha", "zona_mitma_id"]).to_frame(index=False)
    base["fecha"] = base["fecha"].astype("datetime64[us]")
    for t in (v, p):
        if len(t):
            t["fecha"] = t["fecha"].astype("datetime64[us]")
    out = base.merge(v, on=["fecha", "zona_mitma_id"], how="left", validate="one_to_one")
    out = out.merge(p, on=["fecha", "zona_mitma_id"], how="left", validate="one_to_one")
    for c in VALORES:
        if c not in out.columns:
            out[c] = np.nan
    # Si el fichero tiene ese día, una zona sin filas tiene 0 llegadas (dato real);
    # si el día no está en ningún fichero, es ausente (NaN), nunca 0.
    hay_v = out["fecha"].isin(fechas_con_viajes)
    hay_p = out["fecha"].isin(fechas_con_pern)
    for c in VALORES[:4]:
        out.loc[hay_v, c] = out.loc[hay_v, c].fillna(0.0)
    out.loc[hay_p, "pernoctaciones_no_residentes"] = out.loc[hay_p, "pernoctaciones_no_residentes"].fillna(0.0)

    q = cfg_calidad_mitma()
    sin = pd.to_datetime(q["sin_dato_mitma"])
    anom = pd.to_datetime(q["anomalia_mitma"])
    out["calidad"] = "completa"
    out.loc[out["fecha"].isin(anom), "calidad"] = "anomalia_mitma"
    falta = out["fecha"].isin(sin) | ~hay_v
    out.loc[falta, "calidad"] = "sin_dato_mitma"
    out.loc[falta, VALORES] = np.nan
    assert not out.duplicated(["fecha", "zona_mitma_id"]).any()
    return out[COLUMNAS_SALIDA].sort_values(["zona_mitma_id", "fecha"]).reset_index(drop=True)


def leer_zonas(ruta_zonas: Path) -> pd.DataFrame:
    z = pd.read_csv(ruta_zonas, dtype=str)
    if "zona_mitma_id" not in z.columns and "id" in z.columns:
        z = z.rename(columns={"id": "zona_mitma_id"})
    if "zona_mitma_id" not in z.columns:
        raise ValueError(f"{ruta_zonas}: falta la columna zona_mitma_id (o id)")
    return z


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--viajes", default=str(RAW / "mitma_viajes"))
    ap.add_argument("--pernoctaciones", default=str(RAW / "mitma_pernoctaciones"))
    ap.add_argument("--zonas", default=str(RAW / "zonas_mitma_asturias.csv"))
    ap.add_argument("--mapeo", default=cfg()["fuentes"]["real"]["mapeo"])
    ap.add_argument("--salida", default=str(CLEAN / "objetivo_diario.parquet"))
    a = ap.parse_args()

    mapeo = pd.read_csv(ruta(a.mapeo), dtype=str, keep_default_na=False)
    ids = [x for x in mapeo["zona_mitma_id"] if x.strip()]
    if len(ids) != len(mapeo):
        raise SystemExit(f"{a.mapeo}: hay zonas sin zona_mitma_id; rellénalo con los IDs de la parte A.")
    zonas = leer_zonas(Path(a.zonas))
    desconocidas = sorted(set(ids) - set(zonas["zona_mitma_id"]))
    if desconocidas:
        raise SystemExit(f"zona_mitma_id del mapeo que no están en {a.zonas}: {desconocidas}")

    fv = sorted(Path(a.viajes).glob("*.csv"))
    fp = sorted(Path(a.pernoctaciones).glob("*.csv"))
    if not fv:
        raise SystemExit(f"No hay ficheros de viajes en {a.viajes}")
    per = cfg()["objetivo_periodo"]
    out = construir(fv, fp, ids, per["inicio"], per["fin"])
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(a.salida, index=False)
    print(f"{a.salida}: {len(out)} filas, {out['zona_mitma_id'].nunique()} zonas; "
          f"calidad: {out['calidad'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
