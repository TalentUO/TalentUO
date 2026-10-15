"""Objetivo SINTÉTICO (falso) con el mismo esquema que objetivo_diario.

Sirve para probar el modelo de principio a fin mientras llegan los datos del
MITMA. NADA de lo que sale de aquí es real: todas las salidas llevan
`sintetico=True` y los informes lo dicen en el título.

Construcción (escala log, efectos aditivos => multiplicativos en visitantes):
    log(llegadas_ocio) = log(nivel base de la zona)
        + fin de semana (perfil por día de la semana)
        + época del año (verano, más fuerte en la zona de los Picos)
        + puente o festivo en Asturias (incluye Semana Santa y fiesta local)
        + festivo en origen (Madrid, Castilla y León)
        + vacaciones escolares fuera del verano (Navidad, Semana Santa)
        + tiempo en el valle (lluvia y frío, negativos)
        + tiempo en la montaña (solo zona de los Picos, con más peso)
        + eventos en el concejo y partidos en casa
        + ruido (independiente + AR(1))
El tiempo que "causa" la afluencia es la serie base de Open-Meteo (lo más
parecido al tiempo que hizo); el modelo solo ve previsiones archivadas.
El interés en internet NO tiene efecto (debe salir pequeño en SHAP).

Salidas: el objetivo en `salidas/sintetico/objetivo_diario_sintetico.parquet`,
las contribuciones por fila en `salidas/sintetico/contribuciones.parquet` y
los efectos usados en `salidas/sintetico_efectos_reales.json`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from util import SALIDAS, cfg, cfg_calidad_mitma, guardar_json, ruta

# Parámetros por tipo de zona (se asignan por el punto meteorológico de la zona).
PARAMS = {
    "cangas_de_onis": dict(base=2500, temporada=0.95, sens=1.3, trabajo=900, peso_valle=0.4, montana=True,
                           pern=0.55, ast=0.45),
    "llanes": dict(base=3000, temporada=0.75, sens=1.1, trabajo=1500, peso_valle=1.0, pern=0.60, ast=0.40),
    "ribadesella": dict(base=3800, temporada=0.70, sens=1.0, trabajo=2200, peso_valle=1.0, pern=0.50, ast=0.45),
    "gijon": dict(base=9000, temporada=0.30, sens=0.6, trabajo=12000, peso_valle=0.5, pern=0.25, ast=0.65,
                  club="sporting"),
    "oviedo": dict(base=10000, temporada=0.12, sens=0.5, trabajo=15000, peso_valle=0.3, pern=0.20, ast=0.60,
                   club="oviedo"),
}
PERFIL_SEMANA = np.array([-0.12, -0.15, -0.15, -0.08, 0.05, 0.35, 0.22])
EFECTOS = {
    "festivo_ast_laborable": 0.22, "puente_ast": 0.18, "finde_largo_ast": 0.10, "semana_santa": 0.25,
    "festivo_local": 0.08, "festivo_mad": 0.22, "finde_largo_mad": 0.10, "festivo_cyl": 0.12,
    "vacaciones_mad_fuera_verano": 0.12, "vacaciones_ast_fuera_verano": 0.08,
    "lluvia_valle_por_log1p_mm": -0.09, "frio_valle_por_grado_bajo_17": -0.015,
    "lluvia_montana_por_log1p_mm": -0.14, "frio_montana_por_grado_bajo_14": -0.025,
    "evento_por_evento_max2": 0.15, "festival_extra": 0.10, "partido_en_casa": 0.18, "derbi_extra": 0.10,
    "ruido_sd": 0.07, "ruido_ar1_sd": 0.04, "ruido_ar1_phi": 0.6, "anomalia_factor": 0.45,
}
FACTORES = ["Fin de semana", "Época del año", "Puente o festivo en Asturias",
            "Festivo en origen (Madrid o Castilla y León)", "Vacaciones escolares",
            "Tiempo en el valle", "Tiempo en la montaña", "Evento", "Partido", "Ruido"]


def _gauss(doy, centro, ancho):
    return np.exp(-((doy - centro) / ancho) ** 2)


def generar(mapeo: pd.DataFrame, base: pd.DataFrame, om: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    rng = np.random.default_rng(int(cfg()["semilla"]))
    per = cfg()["objetivo_periodo"]
    E = EFECTOS
    filas, contribs = [], []
    for z, zm, zmm in zip(mapeo["zona_mitma_id"], mapeo["zona_meteo"], mapeo["zona_meteo_montana"]):
        p = PARAMS[zm]
        s = p["sens"]
        b = base[(base["zona_mitma_id"] == z) & (base["fecha"] >= per["inicio"]) & (base["fecha"] <= per["fin"])]
        b = b.sort_values("fecha").reset_index(drop=True)
        f = b["fecha"]
        doy = f.dt.dayofyear.to_numpy()
        val = om[om["zona_meteo"] == zm].set_index("fecha").reindex(f)
        c = pd.DataFrame({"fecha": f, "zona_mitma_id": z})
        c["Fin de semana"] = PERFIL_SEMANA[b["cal_dia_semana"].to_numpy()] * (0.6 + 0.4 * s)
        c["Época del año"] = (p["temporada"] * _gauss(doy, 212, 30) + 0.2 * p["temporada"] * _gauss(doy, 150, 25)
                              - 0.06 * s * _gauss(doy, 30, 25))
        laborable = 1 - b["cal_fin_de_semana"]
        c["Puente o festivo en Asturias"] = s * (
            E["festivo_ast_laborable"] * b["cal_festivo_ast"] * laborable + E["puente_ast"] * b["cal_puente_ast"]
            + E["finde_largo_ast"] * b["cal_finde_largo_con_puente_ast"] + E["semana_santa"] * b["cal_semana_santa"]
        ) + E["festivo_local"] * b["cal_festivo_local"]
        c["Festivo en origen (Madrid o Castilla y León)"] = s * (
            E["festivo_mad"] * np.maximum(b["cal_festivo_mad"] * laborable, b["cal_puente_mad"])
            + E["finde_largo_mad"] * b["cal_finde_largo_con_puente_mad"]
            + E["festivo_cyl"] * np.maximum(b["cal_festivo_cyl"] * laborable, b["cal_puente_cyl"]))
        fuera_verano = ~f.dt.month.isin([6, 7, 8, 9]).to_numpy()
        c["Vacaciones escolares"] = s * fuera_verano * (
            E["vacaciones_mad_fuera_verano"] * b["cal_vacaciones_mad"].fillna(0)
            + E["vacaciones_ast_fuera_verano"] * b["cal_vacaciones_ast"].fillna(0))
        c["Tiempo en el valle"] = p["peso_valle"] * (
            E["lluvia_valle_por_log1p_mm"] * np.log1p(val["prec_mm"].to_numpy())
            + E["frio_valle_por_grado_bajo_17"] * np.maximum(0, 17 - val["tmax_c"].to_numpy()))
        if p.get("montana") and isinstance(zmm, str):
            mt = om[om["zona_meteo"] == zmm].set_index("fecha").reindex(f)
            c["Tiempo en la montaña"] = (E["lluvia_montana_por_log1p_mm"] * np.log1p(mt["prec_mm"].to_numpy())
                                         + E["frio_montana_por_grado_bajo_14"] * np.maximum(0, 14 - mt["tmax_c"].to_numpy()))
        else:
            c["Tiempo en la montaña"] = 0.0
        c["Evento"] = E["evento_por_evento_max2"] * np.minimum(b["ev_n"], 2) + E["festival_extra"] * b["ev_festival"]
        club = p.get("club")
        c["Partido"] = 0.0 if club is None else (
            E["partido_en_casa"] * b[f"futbol_partido_{club}"].fillna(0)
            + E["derbi_extra"] * b["futbol_derbi_asturiano"].fillna(0))
        ar = np.zeros(len(b))
        eps = rng.normal(0, E["ruido_ar1_sd"], len(b))
        for i in range(1, len(b)):
            ar[i] = E["ruido_ar1_phi"] * ar[i - 1] + eps[i]
        c["Ruido"] = rng.normal(0, E["ruido_sd"], len(b)) + ar
        c[FACTORES] = c[FACTORES].astype(float).fillna(0.0)

        log_ocio = np.log(p["base"]) + c[FACTORES].sum(axis=1).to_numpy()
        ocio = np.exp(log_ocio)
        fest = np.maximum(b["cal_festivo_ast"], b["cal_festivo_nacional"]).to_numpy()
        perfil_trab = np.where(b["cal_dia_semana"] == 5, 0.45, np.where(b["cal_dia_semana"] == 6, 0.3, 1.0))
        perfil_trab = np.where(fest > 0, 0.35, perfil_trab)
        trabajo = p["trabajo"] * perfil_trab * np.exp(rng.normal(0, 0.05, len(b)))
        epo = c["Época del año"].to_numpy() / max(p["temporada"], 1e-6)
        ori = (c["Festivo en origen (Madrid o Castilla y León)"].to_numpy() > 0).astype(float)
        vac = (c["Vacaciones escolares"].to_numpy() > 0).astype(float)
        pern = ocio * p["pern"] * np.exp(0.5 * epo + 0.4 * ori + 0.3 * vac + rng.normal(0, 0.08, len(b)))
        pern = np.minimum(pern, 1.2 * ocio)
        logit = np.log(p["ast"] / (1 - p["ast"])) - 1.2 * epo - 1.2 * ori - 0.8 * vac + rng.normal(0, 0.1, len(b))
        cuota_ast = 1 / (1 + np.exp(-logit))
        cuota_ast_trabajo = 0.95   # quien viaja por trabajo o estudio vive casi siempre en Asturias
        filas.append(pd.DataFrame({
            "fecha": f, "zona_mitma_id": z,
            "llegadas_total": np.round(ocio + trabajo, 1),
            "llegadas_ocio": np.round(ocio, 1),
            "llegadas_desde_asturias": np.round(ocio * cuota_ast, 1),
            "llegadas_resto_espana": np.round(ocio * (1 - cuota_ast), 1),
            "llegadas_total_desde_asturias": np.round(ocio * cuota_ast + trabajo * cuota_ast_trabajo, 1),
            "llegadas_total_resto_espana": np.round(ocio * (1 - cuota_ast) + trabajo * (1 - cuota_ast_trabajo), 1),
            "pernoctaciones_no_residentes": np.round(pern, 1),
        }))
        contribs.append(c)

    obj = pd.concat(filas, ignore_index=True)
    con = pd.concat(contribs, ignore_index=True)
    q = cfg_calidad_mitma()
    obj["calidad"] = "completa"
    vals = ["llegadas_total", "llegadas_ocio", "llegadas_desde_asturias", "llegadas_resto_espana",
            "llegadas_total_desde_asturias", "llegadas_total_resto_espana", "pernoctaciones_no_residentes"]
    anom = obj["fecha"].isin(pd.to_datetime(q["anomalia_mitma"]))
    obj.loc[anom, vals] = (obj.loc[anom, vals] * E["anomalia_factor"]).round(1)
    obj.loc[anom, "calidad"] = "anomalia_mitma"
    sin = obj["fecha"].isin(pd.to_datetime(q["sin_dato_mitma"]))
    obj.loc[sin, vals] = np.nan
    obj.loc[sin, "calidad"] = "sin_dato_mitma"
    obj["sintetico"] = True

    resumen = {}
    for fac in FACTORES:
        v = con[fac]
        activo = v.abs() > 1e-9
        resumen[fac] = {
            "desv_tipica_log": float(v.std()),
            "media_abs_log": float(v.abs().mean()),
            "efecto_medio_pct_cuando_activo": float(np.expm1(v[activo].mean())) * 100 if activo.any() else 0.0,
            "pct_dias_activo": float(activo.mean() * 100),
            "signo_esperado": ("+" if v[activo].mean() > 0 else "-") if activo.any() else "0",
        }
    efectos = {
        "sintetico": True,
        "aviso": "DATOS SINTÉTICOS: efectos inventados para probar el modelo. No describen Asturias.",
        "parametros_zona": {zm: PARAMS[zm] for zm in mapeo["zona_meteo"]},
        "zonas": dict(zip(mapeo["zona_mitma_id"], mapeo["zona_meteo"])),
        "perfil_semana_log": PERFIL_SEMANA.tolist(),
        "efectos_log": EFECTOS,
        "interes_en_internet": "sin efecto (0) por construcción",
        "acceso_regulado_lagos": "sin efecto (0) por construcción",
        "resumen_por_factor": resumen,
        "nota": ("El efecto 'Fin de semana' queda absorbido por el día normal (que es por día de la semana): "
                 "no debe aparecer en SHAP. 'Época del año' y 'Vacaciones escolares' están correlacionadas."),
    }
    return obj, con, efectos


def ejecutar(mapeo: pd.DataFrame, base: pd.DataFrame, om: pd.DataFrame) -> pd.DataFrame:
    obj, con, efectos = generar(mapeo, base, om)
    destino = ruta(cfg()["fuentes"]["sintetico"]["objetivo"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    obj.to_parquet(destino, index=False)
    con.to_parquet(destino.parent / "contribuciones.parquet", index=False)
    guardar_json(efectos, SALIDAS / "sintetico_efectos_reales.json")
    return obj
