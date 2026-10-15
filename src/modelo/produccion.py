"""Modelos finales (entrenados con todos los datos) y predicción con
intervalo, semáforo y factores principales."""
from __future__ import annotations

import numpy as np
import pandas as pd

import dia_normal
import features as F
import metricas
import modelo as M
from backtest import inicio_entrenamiento
from datos import Datos
from util import a_log_cociente, cfg, colores, desde_log_cociente


def entrenar_finales(D: Datos, algoritmo: str | None = None, log=print) -> dict:
    ini = inicio_entrenamiento()
    fin = pd.Timestamp(cfg()["objetivo_periodo"]["fin"])
    fechas = pd.date_range(ini, fin, freq="D")
    obj = D.obj[["fecha", "zona_mitma_id", D.objetivo, "calidad"]]
    out = {}
    for tipo in ("largo", "corto"):
        t = (F.tabla_largo(D.base[D.base["fecha"].isin(fechas)], D.zonas) if tipo == "largo"
             else F.tabla_corto(D.base, D.mapeo, D.tablas, fechas))
        t = t.merge(obj, on=["fecha", "zona_mitma_id"], how="left", validate="many_to_one")
        t = dia_normal.anadir_normal(t, D.normal_ref, "normal_ref")
        ok = (t["calidad"] == "completa") & t[D.objetivo].notna() & t["normal_ref"].notna()
        t = t[ok].reset_index(drop=True)
        feats = F.columnas_modelo(t, tipo)
        m, info = M.entrenar(t, feats, a_log_cociente(t[D.objetivo], t["normal_ref"]), algoritmo)
        out[tipo] = {"modelo": m, "feats": feats, "info": info, "muestra": t}
        log(f"  modelo final {tipo}: {info}")
    return out


def predecir(D: Datos, finales: dict, tipo: str, t: pd.DataFrame, cuantiles: pd.DataFrame) -> pd.DataFrame:
    """t: tabla de variables (largo o corto). Devuelve una fila por predicción."""
    f = finales[tipo]
    t = dia_normal.anadir_normal(t.reset_index(drop=True), D.normal_ref, "normal")
    p = M.predecir(f["modelo"], t, f["feats"])
    sv, _ = M.shap(f["modelo"], t, f["feats"])
    fx = M.sumar_por_factor(sv, f["feats"])
    r = t[["fecha", "zona_mitma_id", "normal"]].copy()
    r["horizonte"] = t["horizonte"].astype(int).to_numpy()
    r["horizonte_txt"] = "8+" if tipo == "largo" else r["horizonte"].map(metricas.etiqueta_horizonte)
    r["modelo"] = tipo
    r["prediccion"] = desde_log_cociente(p, t["normal"])
    r.loc[t["normal"].isna(), "prediccion"] = np.nan
    r = r.merge(cuantiles[["zona_mitma_id", "horizonte_txt", "q10", "q90"]],
                on=["zona_mitma_id", "horizonte_txt"], how="left")
    r["p10"], r["p90"] = metricas.intervalo(r["prediccion"], r["q10"], r["q90"])
    r["cociente"] = r["prediccion"] / r["normal"]
    r["pct_sobre_normal"] = (r["cociente"] - 1) * 100
    r["color"] = colores(r["cociente"], r["zona_mitma_id"])
    c10 = colores(r["p10"] / r["normal"], r["zona_mitma_id"])
    c90 = colores(r["p90"] / r["normal"], r["zona_mitma_id"])
    r["incierto"] = (c10 != c90) & (r["color"] != "gris")
    r["factores"] = M.top_factores(fx)
    for c in fx.columns:
        r[f"fx_{c}"] = fx[c].to_numpy()
    if "calendario_supuesto" in t.columns:
        r["calendario_supuesto"] = t["calendario_supuesto"].fillna(False).astype(bool).to_numpy()
    r["sintetico"] = D.sintetico
    return r


def futuro_largo(D: Datos, finales: dict, cuantiles: pd.DataFrame, desde, hasta) -> pd.DataFrame:
    b = D.base[(D.base["fecha"] >= pd.Timestamp(desde)) & (D.base["fecha"] <= pd.Timestamp(hasta))]
    return predecir(D, finales, "largo", F.tabla_largo(b, D.zonas), cuantiles)


def futuro_corto_con_prevision(D: Datos, finales: dict, cuantiles: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Corto plazo con la previsión en vivo de ejemplo (data/clean/openmeteo_prevision_ejemplo.parquet).

    La previsión es del punto `covadonga` y se emitió el día de su primera
    fila (a). Para la fecha d = a + h se coloca como `_prev{h}` del punto de
    valle de la zona principal (covadonga está en el concejo de Cangas de Onís:
    se usa como aproximación del valle; la montaña queda sin previsión). El
    resto de zonas no tiene previsión en el ejemplo: su tiempo es NaN y el
    modelo predice solo con calendario e interés.
    Interés: en producción la Wikipedia del día a aún no está publicada, así
    que se usa la ventana que termina en a - 1 (más conservador).
    """
    from util import CLEAN
    prev = pd.read_parquet(CLEAN / "openmeteo_prevision_ejemplo.parquet")
    prev["fecha"] = pd.to_datetime(prev["fecha"]).dt.normalize()
    a = prev["fecha"].min()
    zp = D.zona_principal
    info = {"fecha_emision": a, "punto_prevision": str(prev["zona_meteo"].iloc[0]),
            "zona_aplicada": zp, "horizontes_con_tiempo": []}
    if zp is None:
        return pd.DataFrame(), {**info, "error": "sin zona principal"}
    valle = D.mapeo.set_index("zona_mitma_id").loc[zp, "zona_meteo"]
    om = D.tablas["openmeteo_diario"]
    horizontes = cfg()["horizontes_corto"]
    max_lead = int(cfg()["tiempo"]["max_lead_archivado"])
    filas = []
    for _, p in prev.iterrows():
        h = int((p["fecha"] - a).days)
        if 1 <= h <= max_lead:
            fila = {"fecha": p["fecha"], "zona_meteo": valle}
            for v in F.VARS_TIEMPO.values():
                fila[f"{v}_prev{h}"] = p[v]
            filas.append(fila)
            info["horizontes_con_tiempo"].append(h)
    extra = pd.DataFrame(filas)
    om2 = pd.concat([om[~((om["zona_meteo"] == valle) & om["fecha"].isin(extra["fecha"]))], extra], ignore_index=True)
    tablas = dict(D.tablas, openmeteo_diario=om2)
    fechas = pd.DatetimeIndex([a + pd.Timedelta(days=h) for h in horizontes])
    partes = []
    for h in horizontes:
        d = pd.DatetimeIndex([a + pd.Timedelta(days=h)])
        t = F.tabla_corto(D.base, D.mapeo, tablas, d, horizontes=[h])
        i = F.interes(D.tablas["wikipedia_diario"], D.tablas["trends_semanal"], D.mapeo, h + 1, d)
        t = t.drop(columns=[c for c in t.columns if c.startswith("int_")]).merge(i, on=["fecha", "zona_mitma_id"])
        partes.append(t)
    t = pd.concat(partes, ignore_index=True)
    t["zona"] = pd.Categorical(t["zona_mitma_id"], categories=sorted(D.zonas))
    r = predecir(D, finales, "corto", t, cuantiles)
    r["fecha_emision"] = a
    info["fechas"] = [str(x.date()) for x in fechas]
    return r, info
