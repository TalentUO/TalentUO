"""Explicación de factores: comprobación de SHAP, gráficas y, con el objetivo
sintético, comprobación de que SHAP recupera los efectos usados para generarlo."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import modelo as M  # noqa: E402
from util import AVISO_SINTETICO, FIGURAS, SALIDAS, cfg, guardar_json, umbrales  # noqa: E402

# Estilo sobrio (tinta neutra, rejilla tenue, un solo eje).
TINTA, TINTA2, MUTED, REJILLA, FONDO = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
AZUL, NARANJA = "#2a78d6", "#eb6834"
SEMAFORO = {"verde": "#0ca30c", "ambar": "#fab219", "rojo": "#d03b3b", "gris": "#c3c2b7"}
plt.rcParams.update({"figure.facecolor": FONDO, "axes.facecolor": FONDO, "axes.edgecolor": "#c3c2b7",
                     "axes.labelcolor": TINTA2, "xtick.color": MUTED, "ytick.color": TINTA2,
                     "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})


def _titulo(ax_o_fig, texto: str, sintetico: bool):
    t = f"[{AVISO_SINTETICO}]\n{texto}" if sintetico else texto
    ax_o_fig.suptitle(t, color=TINTA, fontsize=11, x=0.02, ha="left") if hasattr(ax_o_fig, "suptitle") \
        else ax_o_fig.set_title(t, color=TINTA, fontsize=11, loc="left")


def comprobar_treeexplainer(m, x: pd.DataFrame, feats: list[str], n: int = 300) -> dict:
    """Compara el TreeSHAP nativo de LightGBM con shap.TreeExplainer."""
    import shap
    s = x[feats].head(n)
    nativo, _ = M.shap(m, s, feats)
    try:
        te = shap.TreeExplainer(m).shap_values(s)
        dif = float(np.max(np.abs(np.asarray(te) - nativo)))
        return {"comparado_con": "shap.TreeExplainer", "filas": len(s), "max_dif_abs": dif, "coinciden": dif < 1e-6}
    except Exception as e:  # noqa: BLE001
        return {"comparado_con": "shap.TreeExplainer", "error": repr(e)}


# --------------------------------------------------------------------------
# Gráficas
# --------------------------------------------------------------------------

def importancia_global(bt: pd.DataFrame, sintetico: bool) -> pd.DataFrame:
    b = bt[bt["experimento"] == "base"]
    fx = [c for c in b.columns if c.startswith("fx_")]
    filas = []
    for etiqueta, g in (("Largo plazo (8+ días)", b[b["modelo"] == "largo"]),
                        ("Corto plazo (1 día)", b[(b["modelo"] == "corto") & (b["horizonte"] == 1)])):
        imp = g[fx].abs().mean().rename(lambda c: c[3:])
        for k, v in imp.items():
            filas.append({"modelo": etiqueta, "factor": k, "media_abs_shap_log": v,
                          "efecto_tipico_pct": float(np.expm1(v) * 100)})
    imp = pd.DataFrame(filas)
    visibles = set(M.factores_mostrables())
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=False)
    for ax, (mod, g) in zip(axes, imp.groupby("modelo", sort=False)):
        g = g[g["factor"].isin(visibles) & (g["media_abs_shap_log"] > 0)].sort_values("efecto_tipico_pct")
        ax.barh(g["factor"], g["efecto_tipico_pct"], color=AZUL, height=0.6)
        for y, v in enumerate(g["efecto_tipico_pct"]):
            ax.text(v, y, f" {v:.0f} %", va="center", color=TINTA2, fontsize=9)
        ax.set_title(mod, color=TINTA, fontsize=10, loc="left")
        ax.set_xlabel("Efecto típico (media de |SHAP|, %)")
        ax.grid(axis="y", visible=False)
    _titulo(fig, "¿Qué factores mueven la afluencia? Importancia global por factor (validación fuera de muestra)",
            sintetico)
    fig.tight_layout()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURAS / "importancia_factores.png", dpi=150)
    plt.close(fig)
    return imp


def ejemplo_dia_rojo(bt: pd.DataFrame, zona: str, nombre_zona: str, sintetico: bool) -> dict | None:
    b = bt[(bt["experimento"] == "base") & (bt["modelo"] == "largo") & (bt["zona_mitma_id"] == zona)
           & (bt["color_pred"] == "rojo") & (bt["color_obs"] == "rojo")]
    if b.empty:
        b = bt[(bt["experimento"] == "base") & (bt["modelo"] == "largo") & (bt["color_pred"] == "rojo")]
    if b.empty:
        return None
    fila = b.sort_values("cociente_pred", ascending=False).iloc[len(b) // 4]
    fx = {c[3:]: fila[c] for c in bt.columns if c.startswith("fx_") and c[3:] in M.factores_mostrables()}
    fx = pd.Series(fx).sort_values(key=np.abs, ascending=True)
    fx = fx[fx.abs() > 0.005]
    pct = np.expm1(fx) * 100
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(pct.index, pct.values, color=[AZUL if v >= 0 else NARANJA for v in pct.values], height=0.6)
    for y, v in enumerate(pct.values):
        ax.text(v, y, f" {v:+.0f} %" if v >= 0 else f"{v:+.0f} % ", va="center",
                ha="left" if v >= 0 else "right", color=TINTA2, fontsize=9)
    ax.axvline(0, color="#c3c2b7", lw=1)
    ax.set_xlim(min(pct.min() * 1.5, 0) - 8, max(pct.max() * 1.15, 0) + 8)
    ax.set_xlabel("Efecto sobre la afluencia prevista (%): azul suma, naranja resta")
    ax.grid(axis="y", visible=False)
    f = fila["fecha"].strftime("%d-%m-%Y")
    _titulo(fig, f"Por qué {nombre_zona} está en ROJO el {f}
Previsto {fila['cociente_pred']:.1f}× el normal "
                 f"(observado {fila['cociente_obs']:.1f}×); factores del modelo de largo plazo", sintetico)
    fig.tight_layout()
    fig.savefig(FIGURAS / "ejemplo_dia_rojo.png", dpi=150)
    plt.close(fig)
    return {"fecha": fila["fecha"], "zona_mitma_id": fila["zona_mitma_id"], "cociente_pred": fila["cociente_pred"],
            "cociente_obs": fila["cociente_obs"], "factores_pct": pct.round(1).to_dict()}


def serie_validacion(bt: pd.DataFrame, zona: str, nombre_zona: str, sintetico: bool) -> None:
    b = bt[(bt["experimento"] == "base") & (bt["modelo"] == "largo") & (bt["zona_mitma_id"] == zona)]
    b = b.sort_values("fecha")
    a, r = umbrales(zona)
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axhspan(a, r, color=SEMAFORO["ambar"], alpha=0.12, lw=0)
    ax.axhspan(r, max(b["cociente_obs"].max(), b["cociente_pred"].max()) * 1.05, color=SEMAFORO["rojo"], alpha=0.10, lw=0)
    for _, g in b.groupby("bloque"):
        ax.plot(g["fecha"], g["cociente_obs"], color=TINTA2, lw=1.2)
        ax.plot(g["fecha"], g["cociente_pred"], color=AZUL, lw=2)
    ax.plot([], [], color=TINTA2, lw=1.2, label="Observado")
    ax.plot([], [], color=AZUL, lw=2, label="Previsto (largo plazo, fuera de muestra)")
    x_fin = b["fecha"].max() + pd.Timedelta(days=5)
    ax.text(x_fin, (a + r) / 2, " ámbar", va="center", color=TINTA2, fontsize=8)
    ax.text(x_fin, r + 0.15, " rojo", va="bottom", color=TINTA2, fontsize=8)
    ax.set_ylabel("Visitantes / día normal")
    ax.legend(loc="upper right", frameon=False)
    _titulo(fig, f"{nombre_zona}: afluencia observada y prevista en los bloques de validación", sintetico)
    fig.tight_layout()
    fig.savefig(FIGURAS / "validacion_serie_zona_principal.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Comprobación con el objetivo sintético
# --------------------------------------------------------------------------

def recuperacion_sintetico(bt: pd.DataFrame) -> dict:
    """¿Recupera SHAP el orden y el signo de los efectos del generador?

    Se compara, fila a fila (predicciones fuera de muestra del experimento
    base), la contribución verdadera de cada factor con la suma de SHAP de su
    grupo. El efecto 'Fin de semana' verdadero se centra por zona y día de la
    semana, porque el día normal (por día de la semana) ya lo absorbe.
    Importancia = desviación típica de la contribución (no depende del nivel de
    referencia); signo = signo de la correlación.
    """
    import json
    import objetivo_sintetico as S
    con = pd.read_parquet(SALIDAS / "sintetico" / "contribuciones.parquet")
    efectos = json.loads((SALIDAS / "sintetico_efectos_reales.json").read_text(encoding="utf-8"))
    res = {"sintetico": True, "aviso": AVISO_SINTETICO, "modelos": {}}
    for etiqueta, sel in (("largo", (bt["modelo"] == "largo")),
                          ("corto_h1", (bt["modelo"] == "corto") & (bt["horizonte"] == 1)),
                          ("corto_h1_con_prevision_tiempo",
                           (bt["modelo"] == "corto") & (bt["horizonte"] == 1) & (bt["fecha"] >= "2024-07-01"))):
        b = bt[(bt["experimento"] == "base") & sel].merge(con, on=["fecha", "zona_mitma_id"], how="left")
        dow = b["fecha"].dt.dayofweek
        b["Fin de semana"] = b["Fin de semana"] - b.groupby([b["zona_mitma_id"], dow])["Fin de semana"].transform("mean")
        filas = []
        for fac in [f for f in S.FACTORES if f != "Ruido"]:
            v = b[fac].to_numpy(float)
            s = b[f"fx_{fac}"].to_numpy(float) if f"fx_{fac}" in b.columns else np.zeros(len(b))
            corr = float(np.corrcoef(v, s)[0, 1]) if v.std() > 1e-9 and s.std() > 1e-9 else float("nan")
            filas.append({"factor": fac, "importancia_real": float(v.std()), "importancia_shap": float(s.std()),
                          "correlacion": corr,
                          "signo_real": efectos["resumen_por_factor"][fac]["signo_esperado"]})
        t = pd.DataFrame(filas)
        # Factores con efecto real apreciable (> 0,02 en log) y los que no tienen efecto
        relevantes = t[t["importancia_real"] > 0.02].copy()
        relevantes["rango_real"] = relevantes["importancia_real"].rank(ascending=False)
        relevantes["rango_shap"] = relevantes["importancia_shap"].rank(ascending=False)
        rho = float(relevantes[["rango_real", "rango_shap"]].corr(method="spearman").iloc[0, 1]) \
            if len(relevantes) > 2 else float("nan")
        signo_ok = relevantes["correlacion"] > 0.3
        top3_real = relevantes.sort_values("importancia_real", ascending=False)["factor"].head(3).tolist()
        top3_shap = relevantes.sort_values("importancia_shap", ascending=False)["factor"].head(3).tolist()
        sin_efecto = {}
        for fac in ["Interés en internet", "Acceso regulado a los Lagos"]:
            c = f"fx_{fac}"
            sin_efecto[fac] = float(b[c].std()) if c in b.columns else 0.0
        epo_vac = (b["Época del año"] + b["Vacaciones escolares"]).to_numpy()
        epo_vac_s = sum(b[f"fx_{f}"] for f in ["Época del año", "Vacaciones escolares"] if f"fx_{f}" in b.columns)
        res["modelos"][etiqueta] = {
            "filas": int(len(b)),
            "tabla": t.round(4).to_dict(orient="records"),
            "spearman_orden_importancia": rho,
            "signos_recuperados": f"{int(signo_ok.sum())}/{len(relevantes)}",
            "factores_con_signo_no_recuperado": relevantes.loc[~signo_ok, "factor"].tolist(),
            "top3_real": top3_real, "top3_shap": top3_shap,
            "correlacion_epoca_mas_vacaciones": float(np.corrcoef(epo_vac, epo_vac_s)[0, 1]),
            "desv_shap_factores_sin_efecto_real": sin_efecto,
        }
    return res


def grafica_recuperacion(rec: dict) -> None:
    t = pd.DataFrame(rec["modelos"]["corto_h1_con_prevision_tiempo"]["tabla"])
    t = t[(t["importancia_real"] > 0.005) | (t["importancia_shap"] > 0.005)].sort_values("importancia_real")
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(y + 0.2, t["importancia_real"], height=0.36, color=TINTA2, label="Efecto real (generador)")
    ax.barh(y - 0.2, t["importancia_shap"], height=0.36, color=AZUL, label="Recuperado por SHAP")
    ax.set_yticks(y, t["factor"])
    ax.set_xlabel("Importancia (desviación típica de la contribución, escala log)")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="y", visible=False)
    _titulo(fig, "Comprobación: ¿recupera el modelo los efectos con los que se generaron los datos?\n"
                 "(corto plazo, 1 día, jul-2024 a jun-2025)", True)
    fig.tight_layout()
    fig.savefig(FIGURAS / "sintetico_recuperacion_factores.png", dpi=150)
    plt.close(fig)


def ejecutar(bt: pd.DataFrame, D, modelo_muestra=None) -> dict:
    out = {"importancia": importancia_global(bt, D.sintetico).round(4).to_dict(orient="records")}
    zp = D.zona_principal or D.zonas[0]
    out["ejemplo_dia_rojo"] = ejemplo_dia_rojo(bt, zp, D.nombres[zp], D.sintetico)
    serie_validacion(bt, zp, D.nombres[zp], D.sintetico)
    if modelo_muestra is not None:
        out["comprobacion_treeexplainer"] = comprobar_treeexplainer(*modelo_muestra)
    if D.sintetico:
        rec = recuperacion_sintetico(bt)
        guardar_json(rec, SALIDAS / "sintetico_recuperacion_factores.json")
        grafica_recuperacion(rec)
        out["recuperacion_sintetico"] = rec
    out["sintetico"] = D.sintetico
    guardar_json(out, SALIDAS / "explicacion_factores.json")
    return out
