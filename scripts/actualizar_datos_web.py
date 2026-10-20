"""Copia las salidas del modelo a la carpeta de datos de la web.

    python -X utf8 scripts/actualizar_datos_web.py

Flujo: ejecutar el modelo (src/modelo/ejecutar.py) y después este script.

Qué hace:
1. Copia los cinco JSON del contrato (notas/contrato_web.md) de salidas/ a
   «Afluencia Asturias/datos/modelo/», sin modificarlos.
2. Copia el mapeo de zonas a concejos (config/mapeo_zonas.csv). Si los IDs de
   zona de predicciones.json no están en ese fichero (modo sintético, IDs
   EJEMPLO_*), usa config/mapeo_zonas_ejemplo.csv.
3. Resume el calendario oficial (data/clean/calendario_diario.parquet: festivos
   de Asturias, puentes, vacaciones escolares y regulación de los Lagos) para los
   botones de fecha de la web. Si no está, la web usa su calendario aproximado.
4. Resume las llegadas de ocio por hora (data/clean/llegadas_por_hora.parquet) para el
   patrón horario de Gestión. Si no está, Gestión lo marca como pendiente de datos.
5. Escribe «datos/modelo/salidas.js» (completo) y «salidas-inicio.js» (lo que usa Inicio) con todo lo anterior, para que la web se
   abra con doble clic (desde file:// el navegador no deja leer JSON con fetch).
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDAS = RAIZ / "salidas"
CONFIG = RAIZ / "config"
DESTINO = RAIZ / "Afluencia Asturias" / "datos" / "modelo"
FICHEROS = ("predicciones", "alternativas", "regulacion", "perfil", "metricas")
# Grandes eventos de eventos_diario que salen en la web (tipo -> categoría visible)
CATEGORIA_EVENTO = {"fiesta": "Fiestas", "festival": "Festival", "feria": "Feria", "romeria": "Romería",
                    "deportivo": "Deporte"}
MIN_FILAS_COMPACTAR = 50  # listas más cortas se dejan tal cual en los .js (no compensa)


def leer_mapeo(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8", newline="") as f:
        return [
            {
                "zona_mitma_id": (r.get("zona_mitma_id") or "").strip(),
                "nombre": (r.get("nombre") or "").strip(),
                "concejos_ine": [c.strip() for c in (r.get("concejos_ine") or "").split(";") if c.strip()],
            }
            for r in csv.DictReader(f)
        ]


def elegir_mapeo(ids_zonas: set[str]) -> tuple[Path, list[dict]]:
    """El mapeo real si cubre las zonas de las predicciones; si no, el de ejemplo."""
    candidatos = [CONFIG / "mapeo_zonas.csv", CONFIG / "mapeo_zonas_ejemplo.csv"]
    for ruta in candidatos:
        if not ruta.exists():
            continue
        filas = leer_mapeo(ruta)
        if ids_zonas <= {f["zona_mitma_id"] for f in filas if f["zona_mitma_id"]}:
            return ruta, filas
    sys.exit(f"ERROR: ningún mapeo de config/ cubre las zonas de predicciones.json: {sorted(ids_zonas)}")


def leer_calendario() -> dict | None:
    ruta = RAIZ / "data" / "clean" / "calendario_diario.parquet"
    try:
        import pandas as pd
        d = pd.read_parquet(ruta)
    except Exception as e:  # sin pandas/pyarrow o sin fichero: la web sigue funcionando
        print(f"AVISO: sin calendario oficial ({e}); la web usará su calendario aproximado")
        return None
    texto = lambda v: None if pd.isna(v) else str(v)
    si = lambda v: False if pd.isna(v) else bool(v)
    dias = [
        {
            "fecha": r.fecha.strftime("%Y-%m-%d"),
            "finde": si(r.es_fin_de_semana),
            "festivo": texto(r.nombre_festivo_ast) if si(r.festivo_ast) else None,
            "puente": si(r.finde_largo_con_puente_ast),
            "vacaciones": texto(r.periodo_escolar_ast) if si(r.vacaciones_escolares_ast) else None,
            "lagos_regulado": None if pd.isna(r.lagos_regulado) else bool(r.lagos_regulado),
        }
        for r in d.sort_values("fecha").itertuples()
    ]
    return {"origen": "data/clean/calendario_diario.parquet", "dias": dias}


def _norm_concejo(s) -> str:
    """Misma clave que src/limpieza_B/unir_B.py: sin tildes, minúsculas, parte castellana."""
    import unicodedata
    s = str(s).split("/")[0].strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(s.lower().replace("-", " ").split())


def leer_agenda(mapeo: list[dict]) -> dict | None:
    """Festivos, partidos de fútbol en casa y grandes eventos, para la sección de eventos de la web.

    Fuentes: data/clean/calendario_diario.parquet (festivos de Asturias), festivos_locales.parquet
    (BOPA, un festivo por concejo) y eventos_diario.parquet (partidos del Real Oviedo y del Sporting
    en su estadio, y fiestas, festivales, ferias, romerías y pruebas deportivas recopilados de fuentes
    públicas: data/manual/eventos_recopilado.csv). Son los mismos eventos que usa el modelo; los cruceros
    se dejan fuera, como en el modelo. concejo = código INE o null si es de toda Asturias.
    """
    try:
        import pandas as pd
        cal = pd.read_parquet(RAIZ / "data" / "clean" / "calendario_diario.parquet")
        loc = pd.read_parquet(RAIZ / "data" / "clean" / "festivos_locales.parquet")
        ev = pd.read_parquet(RAIZ / "data" / "clean" / "eventos_diario.parquet")
    except Exception as e:
        print(f"AVISO: sin festivos ni eventos ({e}); la sección de eventos saldrá vacía")
        return None
    # Nombre de concejo -> INE, con los concejos del mapeo (concejo_eventos e INE en el mismo orden)
    ine = {}
    with (CONFIG / "mapeo_zonas.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            for n, c in zip((r.get("concejo_eventos") or "").split(";"), (r.get("concejos_ine") or "").split(";")):
                if n.strip() and c.strip():
                    ine[_norm_concejo(n)] = c.strip()
    texto = lambda v: None if pd.isna(v) or str(v).strip() == "" else str(v).strip()
    dia = lambda v: pd.Timestamp(v).strftime("%Y-%m-%d")
    out, sin = [], set()

    for r in cal[cal["festivo_ast"].fillna(False).astype(bool)].itertuples():
        out.append({"id": f"fa-{dia(r.fecha)}", "titulo": texto(r.nombre_festivo_ast) or "Festivo",
                    "categoria": "Festivo en Asturias", "inicio": dia(r.fecha), "fin": dia(r.fecha), "hora": None,
                    "lugar": "Toda Asturias", "concejo": None, "asistencia": None})
    for r in loc.itertuples():
        c = ine.get(_norm_concejo(r.concejo))
        if not c:
            sin.add(r.concejo)
            continue
        ambito = texto(r.ambito)
        # ambito (notas/diccionario_B.md): concejo | parcial | dudoso_villa_o_concejo | sin_nombre
        lugar = {"parcial": "Solo en parte del concejo",
                 "dudoso_villa_o_concejo": "En la villa o en todo el concejo"}.get(ambito, "")
        out.append({"id": f"fl-{dia(r.fecha)}-{c}", "titulo": texto(r.nombre) or "Festivo local",
                    "categoria": "Festivo local", "inicio": dia(r.fecha), "fin": dia(r.fecha), "hora": None,
                    "lugar": lugar, "concejo": c, "asistencia": None})
    fut = ev[ev["tipo"] == "partido_futbol"]
    for r in fut.itertuples():
        c = ine.get(_norm_concejo(r.concejo))
        if not c:
            sin.add(r.concejo)
            continue
        confirmado = False if pd.isna(r.calendario_confirmado) else bool(r.calendario_confirmado)
        lugar = texto(r.lugar) or ""
        if not confirmado:
            lugar = (lugar + " · " if lugar else "") + "fecha provisional"
        out.append({"id": f"pf-{dia(r.fecha)}-{c}", "titulo": texto(r.evento) or "Partido de fútbol",
                    "categoria": "Fútbol", "inicio": dia(r.fecha), "fin": dia(r.fecha), "hora": texto(r.hora_ini),
                    "lugar": lugar, "concejo": c, "asistencia": None})
    grandes = ev[ev["tipo"].isin(CATEGORIA_EVENTO)].drop_duplicates(["evento", "fecha_ini"])  # uno por evento
    for r in grandes.itertuples():
        c = ine.get(_norm_concejo(r.concejo))
        if not c:
            sin.add(r.concejo)
            continue
        aforo = None if pd.isna(r.aforo) else int(r.aforo)
        out.append({"id": f"ev-{dia(r.fecha_ini)}-{c}-{_norm_concejo(r.evento)[:40].replace(' ', '-')}",
                    "titulo": texto(r.evento), "categoria": CATEGORIA_EVENTO[r.tipo],
                    "inicio": dia(r.fecha_ini), "fin": dia(r.fecha_fin), "hora": texto(r.hora_ini),
                    "lugar": texto(r.lugar) or (" y ".join(r.concejos_evento.split(";"))
                                                if r.evento_multiconcejo else ""),
                    "concejo": c, "asistencia": aforo})
    if sin:
        print(f"AVISO: concejos sin código INE en el mapeo (se omiten): {sorted(sin)}")
    out.sort(key=lambda e: (e["inicio"], e["categoria"], e["titulo"]))
    return {"origen": "data/clean/calendario_diario.parquet, festivos_locales.parquet, eventos_diario.parquet",
            "hasta": max(e["fin"] for e in out) if out else None, "eventos": out}


def leer_comarcas() -> dict | None:
    """Comarcas de Asturias (config/comarcas_asturias.csv; las líneas con # son la fuente)."""
    ruta = CONFIG / "comarcas_asturias.csv"
    if not ruta.exists():
        print("AVISO: sin config/comarcas_asturias.csv; los filtros por comarca no estarán")
        return None
    with ruta.open(encoding="utf-8", newline="") as f:
        lineas = [l for l in f if not l.startswith("#")]
    filas = [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(lineas)]
    return {"origen": "config/comarcas_asturias.csv (Decreto 11/1991, de 24 de enero)", "concejos": filas}


def leer_validacion(algoritmo: str) -> dict | None:
    """Real frente a previsto en la validación fuera de muestra (salidas/backtest.parquet), para la gráfica de
    Fiabilidad: experimento base, modelo de largo plazo (8 días de antelación), el algoritmo de las salidas.
    Por zona: [fecha, llegadas observadas, previstas, día normal del semáforo, bloque]."""
    try:
        import pandas as pd
        b = pd.read_parquet(SALIDAS / "backtest.parquet",
                            columns=["fecha", "zona_mitma_id", "experimento", "modelo", "algoritmo", "horizonte", "bloque",
                                     "visitas_obs", "visitas_pred", "normal_ref"])
    except Exception as e:
        print(f"AVISO: sin validación para la gráfica de Fiabilidad ({e})")
        return None
    b = b[(b["experimento"] == "base") & (b["modelo"] == "largo") & (b["algoritmo"] == algoritmo)].dropna(subset=["visitas_obs", "visitas_pred"])
    if b.empty:
        return None
    b = b.sort_values(["zona_mitma_id", "fecha"])
    bloques = sorted(b["bloque"].unique())
    filas = {z: [[f.strftime("%Y-%m-%d"), round(float(o)), round(float(p)), round(float(n)), bloques.index(bl)]
                 for f, o, p, n, bl in zip(g["fecha"], g["visitas_obs"], g["visitas_pred"], g["normal_ref"], g["bloque"])]
             for z, g in b.groupby("zona_mitma_id")}
    return {"origen": "salidas/backtest.parquet (experimento base, largo plazo)", "algoritmo": algoritmo,
            "horizonte": int(b["horizonte"].min()), "bloques": bloques, "filas": filas}


def leer_horas() -> dict | None:
    """Llegadas de ocio por hora (zona × mes × tipo de día), para el patrón horario de Gestión."""
    ruta = RAIZ / "data" / "clean" / "llegadas_por_hora.parquet"
    try:
        import pandas as pd
        d = pd.read_parquet(ruta)
    except Exception as e:  # sin pandas/pyarrow o sin fichero: Gestión lo marca como pendiente de datos
        print(f"AVISO: sin llegadas por hora ({e}); el patrón horario saldrá como pendiente de datos")
        return None
    filas = [
        {
            "zona_mitma_id": str(r.zona_mitma_id), "mes": int(r.mes), "tipo_dia": str(r.tipo_dia),
            "hora": int(r.hora), "llegadas_ocio_media": float(r.llegadas_ocio_media), "n_dias": int(r.n_dias),
        }
        for r in d.sort_values(["zona_mitma_id", "mes", "tipo_dia", "hora"]).itertuples()
    ]
    return {"origen": "data/clean/llegadas_por_hora.parquet", "filas": filas}


def compactar(v):
    """Listas largas de objetos con las mismas claves -> {"__columnas": [...], "__filas": [[...], ...]}.

    Solo en los .js de la web (los JSON del contrato no cambian): las claves dejan de repetirse en cada fila
    y el fichero pesa menos de la mitad. `expandir` de datos/datos.js reconstruye los mismos objetos.
    """
    if isinstance(v, dict):
        return {k: compactar(x) for k, x in v.items()}
    if isinstance(v, list):
        if len(v) >= MIN_FILAS_COMPACTAR and all(isinstance(x, dict) for x in v):
            cols = list(v[0])
            if all(list(x) == cols for x in v):
                return {"__columnas": cols, "__filas": [[compactar(x[c]) for c in cols] for x in v]}
        return [compactar(x) for x in v]
    return v


def escribir_js(ruta: Path, variable: str, datos: dict, nota: str = "") -> None:
    ruta.write_text(
        f"// GENERADO por scripts/actualizar_datos_web.py. No editar a mano.{nota}\n"
        f"window.{variable} = " + json.dumps(compactar(datos), ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")


def main() -> None:
    faltan = [n for n in FICHEROS if not (SALIDAS / f"{n}.json").exists()]
    if faltan:
        sys.exit(f"ERROR: faltan en salidas/: {', '.join(n + '.json' for n in faltan)}")

    # Mismo validador que usa el modelo (si está disponible)
    sys.path.insert(0, str(RAIZ / "src" / "modelo"))
    try:
        from validar_salidas import validar
    except ImportError:
        validar = None
    if validar:
        errores = validar(SALIDAS)
        if errores:
            print("\n".join(errores[:20]))
            sys.exit(f"ERROR: las salidas no cumplen el contrato ({len(errores)} problemas). No se copia nada.")

    datos = {n: json.loads((SALIDAS / f"{n}.json").read_text(encoding="utf-8")) for n in FICHEROS}
    ids = {z["zona_mitma_id"] for z in datos["predicciones"]["zonas"]}
    ruta_mapeo, mapeo = elegir_mapeo(ids)

    DESTINO.mkdir(parents=True, exist_ok=True)
    for n in FICHEROS:
        shutil.copyfile(SALIDAS / f"{n}.json", DESTINO / f"{n}.json")
    (DESTINO / "mapeo_zonas.json").write_text(
        json.dumps({"origen": f"config/{ruta_mapeo.name}", "zonas": mapeo}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    paquete = dict(datos, mapeo={"origen": f"config/{ruta_mapeo.name}", "zonas": mapeo})
    calendario = leer_calendario()
    if calendario:
        paquete["calendario"] = calendario
        (DESTINO / "calendario.json").write_text(json.dumps(calendario, ensure_ascii=False), encoding="utf-8")
    validacion = leer_validacion(datos["metricas"].get("algoritmo", "lightgbm"))
    if validacion:
        paquete["validacion"] = validacion
        (DESTINO / "validacion.json").write_text(json.dumps(validacion, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    comarcas = leer_comarcas()
    if comarcas:
        paquete["comarcas"] = comarcas
        (DESTINO / "comarcas.json").write_text(json.dumps(comarcas, ensure_ascii=False), encoding="utf-8")
    agenda = leer_agenda(mapeo)
    if agenda:
        paquete["agenda"] = agenda
        (DESTINO / "agenda.json").write_text(json.dumps(agenda, ensure_ascii=False), encoding="utf-8")
    horas = leer_horas()
    if horas:
        paquete["horas"] = horas
        (DESTINO / "horas.json").write_text(json.dumps(horas, ensure_ascii=False), encoding="utf-8")
    escribir_js(DESTINO / "salidas.js", "SALIDAS_MODELO", paquete)

    # Versión ligera para la pestaña Inicio (la que carga index.html al principio): sin regulacion,
    # métricas solo con cabecera, algoritmo y fiabilidad, y el calendario recortado a las fechas útiles.
    # Gestión pide salidas.js (completo) al abrirse.
    metricas = datos["metricas"]
    inicio = {
        "predicciones": datos["predicciones"],
        "alternativas": datos["alternativas"],
        "perfil": datos["perfil"],
        "metricas": {k: metricas[k] for k in ("sintetico", "aviso", "generado", "objetivo", "umbrales", "algoritmo", "fiabilidad") if k in metricas},
        "mapeo": paquete["mapeo"],
    }
    if agenda:
        inicio["agenda"] = agenda
    if calendario:
        fechas = sorted(r["fecha"] for r in datos["predicciones"]["predicciones"])
        desde = (date.fromisoformat(fechas[0]) - timedelta(days=31)).isoformat()
        hasta = (date.fromisoformat(max(fechas[-1], datos["predicciones"]["fecha_hoy"])) + timedelta(days=400)).isoformat()
        inicio["calendario"] = dict(calendario, dias=[d for d in calendario["dias"] if desde <= d["fecha"] <= hasta])
    escribir_js(DESTINO / "salidas-inicio.js", "SALIDAS_MODELO_INICIO", inicio, " Datos de la pestaña Inicio.")

    sint = {d.get("sintetico") for d in datos.values()}
    print(f"Copiados {len(FICHEROS)} JSON a {DESTINO.relative_to(RAIZ)}")
    print(f"Mapeo de zonas: config/{ruta_mapeo.name} ({len(mapeo)} zonas)")
    print(f"sintetico = {sint}  generado = {datos['predicciones'].get('generado')}  fecha_hoy = {datos['predicciones'].get('fecha_hoy')}")


if __name__ == "__main__":
    main()
