"""Genera los JSON que consume la web (contrato: notas/contrato_web.md).

salidas/predicciones.json, alternativas.json, regulacion.json, perfil.json y
metricas.json. Todos llevan `sintetico` en la raíz y en cada registro.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import calibracion
import metricas as MT
import produccion as P
from datos import Datos
from util import AVISO_SINTETICO, CONFIG, SALIDAS, cfg, cfg_semaforo, distancia_km, guardar_json, umbrales

CAMPOS_PRED = ["fecha", "zona_mitma_id", "nombre_zona", "horizonte", "prediccion", "normal", "cociente",
               "pct_sobre_normal", "color", "p10", "p90", "incierto", "factores", "sintetico"]
EXTRA_PRED = ["modelo", "conjunto", "fecha_emision", "observado", "cociente_observado", "color_observado"]


def _cabecera(D: Datos) -> dict:
    s = cfg_semaforo()
    return {
        "sintetico": D.sintetico,
        "aviso": AVISO_SINTETICO if D.sintetico else None,
        "generado": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "objetivo": D.objetivo,
        "umbrales": {"ambar": s["umbral_ambar"], "rojo": s["umbral_rojo"], "por_zona": s.get("por_zona") or {}},
    }


def zonas_info(D: Datos) -> list[dict]:
    zm = pd.read_csv(CONFIG / "zonas_meteo.csv").set_index("zona")
    out = []
    for z, nombre, punto in zip(D.mapeo["zona_mitma_id"], D.mapeo["nombre"], D.mapeo["zona_meteo"]):
        out.append({"zona_mitma_id": z, "nombre_zona": nombre, "lat": float(zm.loc[punto, "lat"]),
                    "lon": float(zm.loc[punto, "lon"]), "es_principal": z == D.zona_principal})
    return out


def _registros(D: Datos, r: pd.DataFrame, conjunto: str) -> list[dict]:
    r = r.copy()
    r["nombre_zona"] = r["zona_mitma_id"].map(D.nombres)
    r["conjunto"] = conjunto
    for c in EXTRA_PRED:
        if c not in r.columns:
            r[c] = None
    for c in ("prediccion", "normal", "p10", "p90"):
        r[c] = r[c].round(0)
    r["cociente"] = r["cociente"].round(3)
    r["pct_sobre_normal"] = r["pct_sobre_normal"].round(1)
    return r[CAMPOS_PRED + EXTRA_PRED].to_dict(orient="records")


def historico(D: Datos, bt: pd.DataFrame, cuantiles: pd.DataFrame) -> pd.DataFrame:
    """Predicciones fuera de muestra (validación) de dos periodos de demo."""
    import modelo as M
    periodos = [("2024-12-05", "2024-12-09"), ("2024-08-01", "2024-08-31")]
    sel = pd.Series(False, index=bt.index)
    for a, b in periodos:
        sel |= (bt["fecha"] >= a) & (bt["fecha"] <= b)
    b = bt[sel & (bt["experimento"] == "base") & ((bt["modelo"] == "largo") | (bt["horizonte"] == 1))].copy()
    b["horizonte_txt"] = b["horizonte"].map(MT.etiqueta_horizonte)
    b = b.merge(cuantiles[["zona_mitma_id", "horizonte_txt", "q10", "q90"]], on=["zona_mitma_id", "horizonte_txt"])
    r = b[["fecha", "zona_mitma_id", "horizonte", "modelo"]].copy()
    r["prediccion"] = b["visitas_pred"]
    r["normal"] = b["normal_ref"]
    r["cociente"] = b["cociente_pred"]
    r["pct_sobre_normal"] = (r["cociente"] - 1) * 100
    r["color"] = b["color_pred"]
    r["p10"], r["p90"] = MT.intervalo(b["visitas_pred"], b["q10"], b["q90"])
    from util import colores
    r["incierto"] = (colores(r["p10"] / r["normal"], r["zona_mitma_id"])
                     != colores(r["p90"] / r["normal"], r["zona_mitma_id"])).to_numpy()
    fx = b[[c for c in b.columns if c.startswith("fx_")]].rename(columns=lambda c: c[3:]).fillna(0.0)
    r["factores"] = M.top_factores(fx.reset_index(drop=True))
    r["observado"] = b["visitas_obs"].round(0)
    r["cociente_observado"] = b["cociente_obs"].round(3)
    r["color_observado"] = b["color_obs"]
    r["fecha_emision"] = (b["fecha"] - pd.to_timedelta(np.where(b["modelo"] == "largo", 8, b["horizonte"]), unit="D"))
    r["sintetico"] = D.sintetico
    return r


def alternativas(D: Datos, preds: pd.DataFrame) -> list[dict]:
    margen = int(cfg()["alternativas"]["dias_margen"])
    km = float(cfg()["alternativas"]["km_zona_cercana"])
    zi = {z["zona_mitma_id"]: z for z in zonas_info(D)}
    out = []
    for (conj, mod), g in preds.groupby(["conjunto", "modelo"]):
        if conj == "historico" and mod == "corto":
            g = g[g["horizonte"] == 1]
        idx = g.set_index(["zona_mitma_id", "fecha"])
        for _, p in g[g["color"].isin(["rojo", "ambar"])].iterrows():
            z, f = p["zona_mitma_id"], p["fecha"]
            cerca = g[(g["zona_mitma_id"] == z) & ((g["fecha"] - f).abs() <= pd.Timedelta(days=margen))
                      & (g["fecha"] != f) & (g["cociente"] < p["cociente"])]
            mejor = None
            if len(cerca):
                c = cerca.loc[cerca["cociente"].idxmin()]
                mejor = {"fecha": c["fecha"], "cociente": c["cociente"], "color": c["color"],
                         "prediccion": round(c["prediccion"]),
                         "diferencia_pct": (c["prediccion"] / p["prediccion"] - 1) * 100}
            otras = []
            for z2, info in zi.items():
                if z2 == z or (z2, f) not in idx.index:
                    continue
                d = distancia_km(zi[z]["lat"], zi[z]["lon"], info["lat"], info["lon"])
                q = idx.loc[(z2, f)]
                if d <= km and q["cociente"] < p["cociente"]:
                    otras.append({"zona_mitma_id": z2, "nombre_zona": info["nombre_zona"], "distancia_km": round(d, 1),
                                  "cociente": q["cociente"], "color": q["color"]})
            zona_alt = min(otras, key=lambda x: x["cociente"]) if otras else None
            out.append({"fecha": f, "zona_mitma_id": z, "nombre_zona": D.nombres[z], "conjunto": conj,
                        "modelo": mod, "horizonte": int(p["horizonte"]), "cociente": p["cociente"],
                        "color": p["color"], "mejor_dia": mejor, "zona_alternativa": zona_alt,
                        "sintetico": D.sintetico})
    return out


def regulacion(D: Datos, prev: pd.DataFrame, calib: dict) -> dict:
    """prev: predicciones de largo plazo de los años previstos (todas las fechas)."""
    c = cfg()["regulacion"]
    obs = D.obj.merge(D.base[["fecha", "zona_mitma_id", "cal_dia_semana", "cal_lagos_regulado"]],
                      on=["fecha", "zona_mitma_id"])
    import dia_normal
    obs = dia_normal.anadir_normal(obs, D.normal_ref, "normal")
    obs["cociente"] = obs[D.objetivo] / obs["normal"]
    obs = obs[obs["calidad"] == "completa"]
    from util import colores
    obs["color"] = colores(obs["cociente"], obs["zona_mitma_id"])
    prev = prev.merge(D.base[["fecha", "zona_mitma_id", "cal_lagos_regulado"]], on=["fecha", "zona_mitma_id"])
    prev["c10"], prev["c90"] = prev["p10"] / prev["normal"], prev["p90"] / prev["normal"]
    por_zona = []
    for z in D.zonas:
        ua, ur = umbrales(z)
        anios, curva = [], []
        for a in c["anios_observados"]:
            o = obs[(obs["zona_mitma_id"] == z) & (obs["fecha"].dt.year == a)]
            anios.append({"anio": a, "tipo": "observado", "dias_con_dato": int(len(o)),
                          "dias_rojos": int((o["color"] == "rojo").sum()),
                          "dias_ambar": int((o["color"] == "ambar").sum()),
                          "dias_alerta": int(o["color"].isin(["ambar", "rojo"]).sum())})
            for u in c["umbrales_curva"]:
                curva.append({"anio": a, "tipo": "observado", "umbral": u, "dias": int((o["cociente"] >= u).sum())})
        for a in c["anios_previstos"]:
            p = prev[(prev["zona_mitma_id"] == z) & (prev["fecha"].dt.year == a)]
            anios.append({"anio": a, "tipo": "previsto", "dias_con_dato": int(len(p)),
                          "dias_rojos": int((p["color"] == "rojo").sum()),
                          "dias_rojos_min": int((p["c10"] >= ur).sum()), "dias_rojos_max": int((p["c90"] >= ur).sum()),
                          "dias_ambar": int((p["color"] == "ambar").sum()),
                          "dias_alerta": int(p["color"].isin(["ambar", "rojo"]).sum()),
                          "dias_alerta_min": int((p["c10"] >= ua).sum()), "dias_alerta_max": int((p["c90"] >= ua).sum()),
                          "calendario_supuesto_dias": int(p.get("calendario_supuesto", pd.Series(dtype=bool)).sum())})
            for u in c["umbrales_curva"]:
                curva.append({"anio": a, "tipo": "previsto", "umbral": u, "dias": int((p["cociente"] >= u).sum()),
                              "dias_min": int((p["c10"] >= u).sum()), "dias_max": int((p["c90"] >= u).sum())})
        por_zona.append({"zona_mitma_id": z, "nombre_zona": D.nombres[z], "anios": anios, "curva_umbral": curva})

    lagos = None
    zp = D.zona_principal
    if zp:
        filas = []
        for a in c["anios_observados"]:
            o = obs[(obs["zona_mitma_id"] == zp) & (obs["fecha"].dt.year == a)]
            reg = o["cal_lagos_regulado"].fillna(False).astype(bool)
            filas.append({"anio": a, "tipo": "observado", "dias_regulados": int(reg.sum()),
                          "rojos_en_dias_regulados": int(((o["color"] == "rojo") & reg).sum()),
                          "rojos_fuera_de_regulacion": int(((o["color"] == "rojo") & ~reg).sum()),
                          "alerta_en_dias_regulados": int((o["color"].isin(["ambar", "rojo"]) & reg).sum()),
                          "alerta_fuera_de_regulacion": int((o["color"].isin(["ambar", "rojo"]) & ~reg).sum())})
        for a in c["anios_previstos"]:
            p = prev[(prev["zona_mitma_id"] == zp) & (prev["fecha"].dt.year == a)]
            reg = p["cal_lagos_regulado"].fillna(False).astype(bool)
            sup = bool(p.get("calendario_supuesto", pd.Series(False)).any())
            filas.append({"anio": a, "tipo": "previsto", "dias_regulados": int(reg.sum()),
                          "regulacion_supuesta": sup,
                          "rojos_en_dias_regulados": int(((p["color"] == "rojo") & reg).sum()),
                          "rojos_fuera_de_regulacion": int(((p["color"] == "rojo") & ~reg).sum()),
                          "alerta_en_dias_regulados": int((p["color"].isin(["ambar", "rojo"]) & reg).sum()),
                          "alerta_fuera_de_regulacion": int((p["color"].isin(["ambar", "rojo"]) & ~reg).sum())})
        lagos = {"zona_mitma_id": zp, "nombre_zona": D.nombres[zp], "por_anio": filas,
                 "calibracion": calibracion.resumen(calib)}
    cal = prev[["fecha", "zona_mitma_id", "prediccion", "normal", "cociente", "color", "p10", "p90", "incierto",
                "cal_lagos_regulado"]].copy()
    cal["calendario_supuesto"] = prev.get("calendario_supuesto", False)
    cal["lagos_regulado"] = cal.pop("cal_lagos_regulado").map(lambda v: None if pd.isna(v) else bool(v))
    for col in ("prediccion", "normal", "p10", "p90"):
        cal[col] = cal[col].round(0)
    cal["cociente"] = cal["cociente"].round(3)
    cal["sintetico"] = D.sintetico
    return {"por_zona": por_zona, "lagos": lagos, "calendario_alertas": cal.to_dict(orient="records")}


def perfil(D: Datos) -> list[dict]:
    o = D.obj[D.obj["calidad"] == "completa"].copy()
    o["mes"] = o["fecha"].dt.month
    out = []
    for (z, m), g in o.groupby(["zona_mitma_id", "mes"]):
        ocio = g["llegadas_ocio"].sum()
        pern = g["pernoctaciones_no_residentes"].sum()
        ast, resto = g["llegadas_desde_asturias"].sum(), g["llegadas_resto_espana"].sum()
        out.append({"zona_mitma_id": z, "nombre_zona": D.nombres[z], "mes": int(m), "dias": int(len(g)),
                    "llegadas_ocio_media_dia": ocio / len(g),
                    "pct_desde_asturias": 100 * ast / (ast + resto) if ast + resto else None,
                    "pct_resto_espana": 100 * resto / (ast + resto) if ast + resto else None,
                    "pernoctaciones_por_100_llegadas": 100 * pern / ocio if ocio else None,
                    "pct_excursionistas_aprox": max(0.0, 100 * (1 - pern / ocio)) if ocio else None,
                    "sintetico": D.sintetico})
    return out


def metricas_json(D: Datos, tablas: dict, notas: pd.DataFrame, cuantiles: pd.DataFrame, extra: dict) -> dict:
    return {
        "tablas": {k: v.to_dict(orient="records") for k, v in tablas.items()},
        "fiabilidad": notas.merge(cuantiles, on=["zona_mitma_id", "horizonte_txt"], how="left")
                           .assign(nombre_zona=lambda d: d["zona_mitma_id"].map(D.nombres))
                           .to_dict(orient="records"),
        **extra,
    }


def ejecutar(D: Datos, bt: pd.DataFrame, finales: dict, cuantiles: pd.DataFrame, tablas_met: dict,
             notas: pd.DataFrame, calib: dict, extra_metricas: dict, log=print) -> dict:
    cab = _cabecera(D)
    hoy = pd.Timestamp(cfg()["fecha_hoy_demo"])
    n = int(cfg()["dias_futuro_demo"])
    fl = P.futuro_largo(D, finales, cuantiles, hoy + pd.Timedelta(days=1), hoy + pd.Timedelta(days=n))
    fl["horizonte"] = (fl["fecha"] - hoy).dt.days
    fl["fecha_emision"] = hoy
    fc, info_corto = P.futuro_corto_con_prevision(D, finales, cuantiles)
    hi = historico(D, bt, cuantiles)
    preds = pd.concat([fl.assign(conjunto="futuro_largo"), fc.assign(conjunto="futuro_corto"),
                       hi.assign(conjunto="historico")], ignore_index=True)
    registros = (_registros(D, fl, "futuro_largo") + _registros(D, fc, "futuro_corto")
                 + _registros(D, hi, "historico"))
    guardar_json({**cab, "fecha_hoy": hoy, "zonas": zonas_info(D),
                  "conjuntos": {
                      "futuro_largo": f"Largo plazo (solo calendario y eventos), {n} días desde {hoy.date()}.",
                      "futuro_corto": ("Corto plazo con la previsión meteorológica de ejemplo emitida el "
                                       f"{info_corto['fecha_emision'].date()} (punto {info_corto['punto_prevision']}, "
                                       "aplicada al valle de la zona principal; resto de zonas sin tiempo)."),
                      "historico": ("Predicciones fuera de muestra de la validación (puente de diciembre y agosto de "
                                    "2024), con el valor observado, para enseñar un caso rojo con su explicación."),
                  },
                  "info_corto_plazo": info_corto,
                  "predicciones": registros}, SALIDAS / "predicciones.json")

    alt = alternativas(D, preds)
    guardar_json({**cab, "parametros": cfg()["alternativas"], "alternativas": alt}, SALIDAS / "alternativas.json")

    anios = cfg()["regulacion"]["anios_previstos"]
    prev = P.futuro_largo(D, finales, cuantiles, f"{min(anios)}-01-01", f"{max(anios)}-12-31")
    reg = regulacion(D, prev, calib)
    guardar_json({**cab, **reg}, SALIDAS / "regulacion.json")

    guardar_json({**cab, "perfil": perfil(D),
                  "nota": ("Reparto de las llegadas de ocio por residencia (Asturias / resto de España; el MITMA no "
                           "incluye extranjeros). 'pct_excursionistas_aprox' = 1 - pernoctaciones / llegadas: "
                           "aproximación, porque una persona puede pernoctar varias noches.")},
                 SALIDAS / "perfil.json")
    guardar_json({**cab, **metricas_json(D, tablas_met, notas, cuantiles, extra_metricas)}, SALIDAS / "metricas.json")
    log(f"  predicciones: {len(registros)} | alternativas: {len(alt)} | calendario de alertas: "
        f"{len(reg['calendario_alertas'])}")
    return {"predicciones": preds, "prev_anual": prev, "info_corto": info_corto}
