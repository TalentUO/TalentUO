"""Limpieza de eventos (parte B, tabla 4).

Entrada: data/manual/eventos_recopilado.csv (no se modifica).
Salidas:
  data/clean/eventos_diario.parquet        una fila por fecha, concejo y evento
  data/clean/partidos_diario.parquet       una fila por fecha (indicadores por club)
  data/clean/eventos_sin_fecha.csv         filas `no_encontrado` sin fecha (no se expanden)
  data/clean/_qc/eventos_diario.json, partidos_diario.json

Uso: python -X utf8 src/limpieza_B/limpia_eventos.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import (CLEAN, MANUAL, asegurar_dirs, comprobar_continuidad,  # noqa: E402
                   comprobar_rango, comprobar_sin_duplicados, escribir_parquet, resumen_qc)

ENTRADA = MANUAL / "eventos_recopilado.csv"
ESTADOS = {"verificado", "probable", "no_encontrado"}
FUENTE_TIPOS = {"oficial", "secundaria", "prensa"}

CONCEJOS = {"Cangas de Onis": "Cangas de Onís", "Gijon": "Gijón"}

# Nombre canónico de club. Football-data usa nombres cortos en inglés/sin
# tildes y LaLiga (2026-27) el nombre social completo; se unifican aquí.
CLUBS = {
    "Real Oviedo": "Real Oviedo", "Real Oviedo SAD": "Real Oviedo", "Oviedo": "Real Oviedo",
    "Sporting de Gijón": "Real Sporting de Gijón", "Real Sporting de Gijón SAD": "Real Sporting de Gijón",
    "Sp Gijon": "Real Sporting de Gijón",
    "AD Ceuta FC": "Ceuta", "Albacete Balompié SAD": "Albacete", "Burgos CF": "Burgos",
    "CD Castellón": "Castellón", "Castellon": "Castellón",
    "Centre d’ Esports Sabadell Fútbol Club SAD": "Sabadell", "Club Deportivo Eldense": "Eldense",
    "Club Deportivo Leganés SAD": "Leganés", "Leganes": "Leganés",
    "Club Deportivo Tenerife SAD": "Tenerife", "Cordoba": "Córdoba", "Córdoba Club de Fútbol": "Córdoba",
    "Cádiz Club de Fútbol SAD": "Cádiz", "Cadiz": "Cádiz", "FC Andorra": "Andorra",
    "Girona Fútbol Club SAD": "Girona", "Granada Club de Fútbol SAD": "Granada",
    "R. Sociedad B": "Real Sociedad B", "RC Celta Fortuna": "Celta Fortuna",
    "Real Club Deportivo Mallorca SAD": "Mallorca", "Real Valladolid Club de Fútbol SAD": "Valladolid",
    "Sociedad Deportiva Eibar SAD": "Eibar", "Unión Deportiva Almería SAD": "Almería", "Almeria": "Almería",
    "Unión Deportiva Las Palmas SAD": "Las Palmas", "Alaves": "Alavés", "Alcorcon": "Alcorcón",
    "Ath Bilbao": "Athletic Club", "Ath Madrid": "Atlético de Madrid", "Espanol": "Espanyol",
    "Malaga": "Málaga", "Mirandes": "Mirandés", "Santander": "Racing de Santander",
    "Sociedad": "Real Sociedad", "Vallecano": "Rayo Vallecano", "Deportivo": "Deportivo de La Coruña",
    "Betis": "Real Betis",
}
CLUB_LOCAL_COL = {"Real Oviedo": "partido_oviedo", "Real Sporting de Gijón": "partido_sporting"}


def categoria(competicion: str | float) -> str | float:
    if not isinstance(competicion, str):
        return float("nan")
    if "(1ª)" in competicion:
        return "Primera"
    if "(2ª)" in competicion:
        return "Segunda"
    return float("nan")


def temporada_de(fecha: pd.Timestamp) -> str:
    a = fecha.year if fecha.month >= 7 else fecha.year - 1
    return f"{a}-{str(a + 1)[-2:]}"


def cargar() -> pd.DataFrame:
    df = pd.read_csv(ENTRADA, encoding="utf-8-sig", dtype=str)
    assert len(df) == 378, f"Se esperaban 378 filas en el CSV manual, hay {len(df)}"
    assert set(df["estado"]) <= ESTADOS, f"estados no válidos: {set(df['estado']) - ESTADOS}"
    assert set(df["fuente_tipo"]) <= FUENTE_TIPOS, f"fuente_tipo no válido: {set(df['fuente_tipo'])}"
    assert df["fuente_url"].notna().all(), "filas sin fuente_url"
    for c in ("fecha_ini", "fecha_fin"):
        df[c] = pd.to_datetime(df[c], format="%Y-%m-%d", errors="raise")
    con_fecha = df["fecha_ini"].notna()
    assert (df.loc[con_fecha, "fecha_fin"] >= df.loc[con_fecha, "fecha_ini"]).all(), "fecha_fin < fecha_ini"
    assert (df.loc[~con_fecha, "estado"] == "no_encontrado").all(), "fila sin fecha que no es no_encontrado"
    df["aforo_o_pasajeros"] = pd.to_numeric(df["aforo_o_pasajeros"])
    df["concejo"] = df["concejo"].replace(CONCEJOS)
    return df


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["id_evento_original"] = df.index + 2  # nº de línea en el CSV (cabecera = 1)

    # --- Partidos ---------------------------------------------------------
    es_partido = (df["tipo"] == "partido_futbol") & df["fecha_ini"].notna()
    partes = df.loc[es_partido, "evento"].str.split(" - ", n=1, expand=True)
    local = partes[0].map(CLUBS)
    rival = partes[1].map(lambda x: CLUBS.get(x, x))
    assert local.notna().all(), f"club local no reconocido: {partes[0][local.isna()].unique()}"
    df.loc[es_partido, "club_local"] = local
    df.loc[es_partido, "rival"] = rival
    df.loc[es_partido, "evento"] = local + " - " + rival
    df["partido_oviedo"] = df["club_local"].eq("Real Oviedo")
    df["partido_sporting"] = df["club_local"].eq("Real Sporting de Gijón")
    df["derbi_asturiano"] = es_partido & df["rival"].isin(["Real Oviedo", "Real Sporting de Gijón"])
    df["hora_partido"] = df["hora_ini"].where(es_partido)
    df["categoria_temporada"] = df["competicion"].map(categoria).where(es_partido)
    df["temporada"] = df["competicion"].str.extract(r"(\d{4}-\d{2})$")[0].where(es_partido)
    df["calendario_confirmado"] = pd.Series(pd.NA, index=df.index, dtype="boolean")
    df.loc[es_partido, "calendario_confirmado"] = ~df.loc[es_partido, "notas"].fillna("").str.contains(
        "calendario no confirmado", case=False)

    # --- Cruceros ---------------------------------------------------------
    es_crucero = df["tipo"] == "crucero_gijon"
    df["es_prevision"] = pd.Series(pd.NA, index=df.index, dtype="boolean")
    df.loc[es_crucero & df["fecha_ini"].notna(), "es_prevision"] = df.loc[
        es_crucero & df["fecha_ini"].notna(), "notas"].str.contains("Previsión", case=False)
    assert df.loc[es_crucero & df["fecha_ini"].notna(), "es_prevision"].all(), \
        "hay escalas de crucero que no figuran como previsión: revisar"
    df["pasajeros_capacidad"] = df["aforo_o_pasajeros"].where(es_crucero)
    df["aforo"] = df["aforo_o_pasajeros"].where(~es_crucero)

    # --- Calidad ----------------------------------------------------------
    df["nota_calidad"] = pd.NA
    fidma25 = df["evento"].str.startswith("FIDMA") & (df["fecha_ini"] == "2025-08-01")
    assert fidma25.sum() == 1
    df.loc[fidma25, "nota_calidad"] = ("Discrepancia no resuelta en fecha_ini: 1-ago (festivalesdeespana) "
                                       "frente a 2-ago (Diario de León, asturias.com). Fecha sin cambiar.")
    return df


def expandir(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for _, r in df[df["fecha_ini"].notna()].iterrows():
        dias = pd.date_range(r["fecha_ini"], r["fecha_fin"], freq="D")
        concejos = [c.strip() for c in r["concejo"].split(";")]
        for i, d in enumerate(dias, start=1):
            for c in concejos:
                f = r.to_dict()
                f.update(fecha=d, concejo=c, dia_evento=i, n_dias_evento=len(dias),
                         evento_multiconcejo=len(concejos) > 1, concejos_evento=r["concejo"])
                filas.append(f)
    out = pd.DataFrame(filas)
    out["fecha"] = pd.to_datetime(out["fecha"]).dt.normalize()
    cols = ["fecha", "concejo", "evento", "tipo", "dia_evento", "n_dias_evento", "fecha_ini", "fecha_fin",
            "hora_ini", "lugar", "evento_multiconcejo", "concejos_evento", "estado", "fuente_tipo",
            "fuente_url", "aforo", "pasajeros_capacidad", "es_prevision", "competicion", "temporada",
            "club_local", "rival", "partido_oviedo", "partido_sporting", "derbi_asturiano", "hora_partido",
            "categoria_temporada", "calendario_confirmado", "nota_calidad", "notas", "id_evento_original"]
    out = out[cols].sort_values(["fecha", "concejo", "evento"]).reset_index(drop=True)
    for c in ("dia_evento", "n_dias_evento", "id_evento_original"):
        out[c] = out[c].astype("int64")
    for c in ("partido_oviedo", "partido_sporting", "derbi_asturiano", "evento_multiconcejo"):
        out[c] = out[c].astype(bool)
    for c in ("es_prevision", "calendario_confirmado"):
        out[c] = out[c].astype("boolean")
    return out


def partidos_diario(ev: pd.DataFrame) -> pd.DataFrame:
    """Una fila por día entre el primer y el último partido en casa recopilado.

    Días sin partido = False (el calendario de liga está completo en ese rango:
    football-data 2021-22..2025-26 y LaLiga 2026-27). Copa del Rey no recopilada.
    """
    p = ev[ev["tipo"] == "partido_futbol"]
    dias = pd.DataFrame({"fecha": pd.date_range(p["fecha"].min(), p["fecha"].max(), freq="D")})
    dias["temporada"] = dias["fecha"].map(temporada_de)
    cat = p.groupby(["club_local", "temporada"])["categoria_temporada"].agg(lambda s: s.dropna().unique())
    assert cat.map(len).eq(1).all(), "un club con dos categorías en la misma temporada"
    cat = cat.map(lambda a: a[0])
    for club, sufijo in (("Real Oviedo", "oviedo"), ("Real Sporting de Gijón", "sporting")):
        g = p[p["club_local"] == club].set_index("fecha")
        assert not g.index.duplicated().any(), f"{club}: dos partidos en casa el mismo día"
        dias[f"partido_{sufijo}"] = dias["fecha"].isin(g.index)
        dias[f"hora_partido_{sufijo}"] = dias["fecha"].map(g["hora_partido"])
        dias[f"rival_{sufijo}"] = dias["fecha"].map(g["rival"])
        dias[f"estado_partido_{sufijo}"] = dias["fecha"].map(g["estado"])
        dias[f"calendario_confirmado_{sufijo}"] = dias["fecha"].map(g["calendario_confirmado"]).astype("boolean")
        dias[f"categoria_temporada_{sufijo}"] = [cat.get((club, t), pd.NA) for t in dias["temporada"]]
    dias["derbi_asturiano"] = dias["fecha"].isin(p.loc[p["derbi_asturiano"], "fecha"])
    dias["fuente"] = "football-data.co.uk (2021-22..2025-26), laliga.com (2026-27)"
    return dias


def main() -> None:
    asegurar_dirs()
    df = enriquecer(cargar())

    sin_fecha = df[df["fecha_ini"].isna()]
    sin_fecha[["id_evento_original", "evento", "tipo", "concejo", "estado", "fuente_url", "notas"]].to_csv(
        CLEAN / "eventos_sin_fecha.csv", index=False, encoding="utf-8")

    ev = expandir(df)
    comprobar_sin_duplicados(ev, ["fecha", "concejo", "evento"], "eventos_diario")
    assert set(ev["estado"]) <= {"verificado", "probable"}
    comprobar_rango(ev, "dia_evento", 1, 31, "eventos_diario")
    comprobar_rango(ev, "pasajeros_capacidad", 1, 10000, "eventos_diario")
    assert (ev["dia_evento"] <= ev["n_dias_evento"]).all()
    # Nº de días expandidos = suma de duraciones × concejos
    con_f = df[df["fecha_ini"].notna()]
    esperado = int(((con_f["fecha_fin"] - con_f["fecha_ini"]).dt.days + 1).mul(
        con_f["concejo"].str.count(";") + 1).sum())
    assert len(ev) == esperado, f"expansión: {len(ev)} filas, esperadas {esperado}"
    assert ev["hora_partido"].dropna().str.fullmatch(r"\d{2}:\d{2}").all()
    assert ev.loc[ev["tipo"] == "crucero_gijon", "fecha"].dt.year.isin([2025, 2026]).all()
    escribir_parquet(ev, "eventos_diario.parquet")

    pdia = partidos_diario(ev)
    comprobar_sin_duplicados(pdia, ["fecha"], "partidos_diario")
    comprobar_continuidad(pdia, "fecha", None, "partidos_diario")
    escribir_parquet(pdia, "partidos_diario.parquet")

    resumen_qc(ev, "eventos_diario", ["fecha", "concejo", "evento"], extra={
        "filas_csv_origen": 378, "filas_sin_fecha_no_expandidas": int(len(sin_fecha)),
        "por_tipo": ev["tipo"].value_counts().to_dict(),
        "por_estado": ev["estado"].value_counts().to_dict(),
        "eventos_por_estado_origen": df["estado"].value_counts().to_dict(),
        "cruceros_escalas": int((ev["tipo"] == "crucero_gijon").sum()),
        "cruceros_anios": sorted(ev.loc[ev["tipo"] == "crucero_gijon", "fecha"].dt.year.unique().tolist()),
        "partidos_calendario_no_confirmado": int((ev["calendario_confirmado"] == False).sum()),  # noqa: E712
        "validaciones": ["sin duplicados (fecha, concejo, evento)", "fecha_fin >= fecha_ini",
                         "estados y fuente_tipo válidos", "nº de filas expandidas = suma de duraciones",
                         "cruceros solo 2025-2026 y todos previsión", "hora HH:MM"],
    })
    resumen_qc(pdia, "partidos_diario", ["fecha"], extra={
        "dias_partido_oviedo": int(pdia["partido_oviedo"].sum()),
        "dias_partido_sporting": int(pdia["partido_sporting"].sum()),
        "dias_con_ambos": int((pdia["partido_oviedo"] & pdia["partido_sporting"]).sum()),
        "derbis": int(pdia["derbi_asturiano"].sum()),
    })
    print(f"eventos_diario: {len(ev)} filas, {ev['fecha'].min():%Y-%m-%d}..{ev['fecha'].max():%Y-%m-%d}")
    print(f"partidos_diario: {len(pdia)} días; Oviedo {pdia['partido_oviedo'].sum()}, "
          f"Sporting {pdia['partido_sporting'].sum()}, derbis {pdia['derbi_asturiano'].sum()}")
    print(f"sin fecha (no expandidas): {len(sin_fecha)}")


if __name__ == "__main__":
    main()
