# TalentUO

Repositorio compartido (privado) para datos y notas del proyecto.

**Hackathon TalentUO 2026 (Universidad de Oviedo), reto de NTT DATA «Predicción de Afluencia Turística en Asturias».** Es un sistema de alerta temprana de presión turística para la administración (ayuntamientos, Principado y Parque Nacional). Un modelo de *machine learning* (LightGBM, con XGBoost como alternativa) predice, por día y zona, cuántos visitantes llegarán y cuánto supone frente a un «día normal». A partir de los datos de movilidad del MITMA y de factores conocidos de antemano (calendario, festivos de Asturias y de las comunidades de origen, vacaciones escolares, eventos, previsión del tiempo e interés en internet), lo muestra en una web como semáforo, con los factores que lo explican. La zona principal es la puerta de los Picos de Europa (Cangas de Onís, con Covadonga y los Lagos).

> **Las salidas del modelo (`salidas/`) son REALES** desde el 2026-10-16 (rama `resultados-reales`), con el objetivo del MITMA de la parte A. Los JSON de la web llevan `sintetico=false`. Resultados, con cada cifra y su fichero de origen: `notas/resultados_reales.md`. Quedan en `salidas/` dos ficheros de la prueba sintética, `sintetico_efectos_reales.json` y `sintetico_recuperacion_factores.json`, que no usa la web.

## Estado

- **Parte B (factores explicativos): terminada.** Descarga, auditoría y limpieza en `data/clean/`, con diccionario (`notas/diccionario_B.md`) y control de calidad (`notas/control_calidad_B.md`).
- **Parte A (demanda y movilidad, MITMA): entregada.** `data/clean/objetivo_diario.parquet`: 5 zonas, 2022-01-01 → 2025-06-30, días sin dato oficial en NaN. Validación en `notas/estado_resultados.md`.
- **Modelo: entrenado con datos reales.** Algoritmo **LightGBM**, por la regla de elección (empate técnico con XGBoost). Modelos de corto plazo (1-7 días) y largo plazo (8 o más días), validación por bloques temporales, prueba anti-fuga, SHAP, intervalos, calibración con la regulación de los Lagos y JSON para la web. Documentación en `notas/modelo.md`.
  - **Resultados principales** (`salidas/metricas.json`, todos los bloques): error en visitantes (WAPE) del 8,8 % a corto plazo y del 9,3 % a largo, frente al 13,2 % de suponer un día normal y al 9,9 % de repetir el año anterior. Detecta el 78-80 % de los días rojos, con una precisión del 94-96 %.
  - **Zona de los Picos** (`salidas/regulacion.json`): 39 días rojos en 2023 y 48 en 2024; 85 de esos 87 ya caían en días de acceso regulado a los Lagos. Previsión para 2026: 36 (29-66).
  - **Limitaciones:**
    - sin visitantes extranjeros (el MITMA solo cuenta residentes en España);
    - datos diarios solo hasta junio de 2025;
    - el umbral del semáforo (1,5× y 2,0×) lo hemos definido nosotros;
    - cruceros fuera;
    - el modelo se queda corto en volumen (entre −4 % y −11 %) y no gana al día normal en Gijón y Oviedo en 2025;
    - falla en los puentes de diciembre;
    - los intervalos cubren el 77,7 % en lugar del 80 %.
  - Detalle: `notas/resultados_reales.md`.

## Estructura

- `data/raw/` – datos descargados tal cual de la fuente (no editar a mano).
- `data/manual/` – datos introducidos o corregidos manualmente.
- `data/clean/` – tablas limpias de la parte B (factores) y, cuando exista, `objetivo_diario.parquet` (objetivo real del MITMA).
- `data/prevision/` – previsiones de Open-Meteo en bruto, por fecha de emisión.
- `notas/registro_descargas.md` – registro de cada descarga (fecha, fuente, archivo).
- `notas/decisiones_y_consideraciones.md` – decisiones importantes y límites de los datos.
- `scripts/` – `descarga_mitma.py` (descarga MITMA día a día, filtrada a Asturias, reanudable) y `verificar_mitma.py`; `descarga_sadei.py` (tablas PC-Axis de SADEI vía el visor PxWeb, en partes si superan 100 000 celdas) y `verificar_sadei.py`.
- `logs/` – logs de las descargas (locales, no versionados).
- `data/raw/LEEME_datos_no_versionados.md` – qué ficheros pesados no se suben y cómo regenerarlos.
- `notas/registro_senales.md`, `notas/notas_senales.md`, `notas/decisiones_senales.md` – señales adelantadas (Wikipedia, Google Trends, OAPN): registro, hallazgos por fuente y decisiones pendientes. Script: `src/descarga_senales.py`.
- `src/descarga_*.py` – descargas de la parte B (AEMET, Open-Meteo, calendarios y señales).
- `src/auditoria/` – auditoría de los datos en bruto de B.
- `src/limpieza_B/` – limpieza de la parte B y unión de factores por zona (`unir_B.py`).
- `src/modelo/` – modelo: objetivo, variables, validación, SHAP, salidas de la web y pruebas (`tests/`).
- `config/` – mapeo de zonas (`mapeo_zonas.csv`), puntos meteorológicos y configuración del modelo, del semáforo y de los factores.
- `salidas/` – salidas del modelo con datos reales: JSON de la web, `backtest.parquet`, figuras y `tablas_resultados_reales.md`.
- `notas/` – diccionario, control de calidad, `modelo.md`, `contrato_objetivo.md` (entrada de la parte A), `contrato_web.md` (salida para la web) y `guion_modelo.md` (presentación).

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell/cmd)
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

`requirements-lock.txt` contiene las versiones exactas probadas (Python 3.11):
`pip install -r requirements-lock.txt`.

Dependencias principales: pandas, requests, openpyxl, pyaxis, pySpainMobility. El modelo usa también lightgbm, xgboost, shap, scikit-learn, pyyaml, matplotlib, pyarrow y pytest.

**Contacto del User-Agent.** Los scripts de descarga se identifican ante las API (por ejemplo, Wikimedia) con un User-Agent que incluye un contacto. Ese contacto se toma de la variable de entorno `TALENTUO_CONTACTO`; si no está definida, se usa «equipo TalentUO». No se versiona ningún dato personal. La clave de AEMET va en la variable de entorno `AEMET_API_KEY`, nunca en el repositorio.

## Cómo ejecutar

```bash
# Parte B: limpieza completa (unos 50 s; se detiene si falla alguna comprobación)
python -X utf8 src/limpieza_B/ejecutar_todo.py

# Previsión meteorológica de 7 días para todas las zonas (opcional; la demo ya trae una)
python -X utf8 src/modelo/descargar_prevision.py

# Modelo de principio a fin (1-2 min). Objetivo: sintetico | real.
# Algoritmo: lightgbm (por defecto) | xgboost | ambos (compara y elige con la regla de notas/modelo.md)
python -X utf8 src/modelo/ejecutar.py --objetivo sintetico --algoritmo lightgbm
python -X utf8 src/modelo/ejecutar.py --objetivo sintetico --algoritmo ambos

# Pruebas: anti-fuga, constructor del objetivo, regla de elección y contrato de la web
python -X utf8 -m pytest -q -m "not lento" src/modelo/tests   # rápidas (~1 min)
python -X utf8 -m pytest -q src/modelo/tests                  # todas (~4 min; incluye la cadena completa con cada algoritmo)
```

## Qué necesita la parte A para conectar los datos reales

**Hecho** (2026-10-16): la parte A entregó directamente `data/clean/objetivo_diario.parquet`, así que no hace falta el paso 4 de `construir_objetivo.py`. Basta con `python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos`.

Resumen de `notas/contrato_objetivo.md`:

1. **Lista de zonas MITMA de Asturias**, en `data/raw/zonas_mitma_asturias.csv`, con `zona_mitma_id` (o `id`) y `nombre`.
2. **`zona_mitma_id` de cada zona del proyecto** en `config/mapeo_zonas.csv` (hoy, columna vacía). La zona principal es la del concejo INE 33012 (Cangas de Onís).
3. **Viajes y pernoctaciones del 2022-01-01 al 2025-06-30**, en formato MITMA original o de spanishoddata (se detecta solo; separador `|`, `,` o `;`):
   - viajes: `fecha, periodo, origen, destino, actividad_origen, actividad_destino, residencia, viajes`;
   - pernoctaciones: `fecha, zona_residencia, zona_pernoctacion, personas`.
4. Después: `python -X utf8 src/modelo/construir_objetivo.py` (genera `data/clean/objetivo_diario.parquet`) y `python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos`.

El objetivo por defecto son las **llegadas de ocio**: viajes con destino en la zona, origen fuera de ella y actividad frecuente o no frecuente. Los días sin datos del MITMA quedan ausentes (nunca 0) y no se usan para entrenar ni evaluar.

## Estado (Fase 1: solo descarga en bruto)

Persona A (demanda y movilidad): MITMA viajes/pernoctaciones 2022–2025 (Asturias), estadísticos de día normal 2024, INE móviles (turismo interno **interprovincial**: no incluye a los asturianos que viajan dentro de Asturias; Excel 2022–2026 solo con cruces de >30 turistas, y extracto de la tabla 53001 con destino Asturias y origen "Total Nacional", 2019M07–2026M08; en el CSV `.` es separador de miles **y** dato ausente, ausente ≠ 0; `scripts/descarga_ine_moviles.py`), viviendas turísticas INE (semestral 2020–2026) SADEI por concejo (turistas nacionales/extranjeros mensuales, plazas y apartamentos anuales, padrón; ficheros `.px`, el nacional en 4 partes) y residuos COGERSA (**solo anual 2020–2021**, sin detalle mensual). Detalle, fechas reales y límites en `notas/registro_descargas.md`; lo no comprobado figura como **NO VERIFICADO**.

## Descarga MITMA (viajes y pernoctaciones, Asturias)

Fuente: Open Data Movilidad del MITMA, estudios básicos, zonificación municipal v2 (`https://movilidad-opendata.mitma.es/estudios_basicos/por-municipios/...`). Rango: 2022-01-01 a 2025-06-30 (desde julio de 2025 cambia la metodología: **no se mezcla**). Solo cubre residentes en España.

```bash
.venv\Scripts\python.exe scripts/descarga_mitma.py --workers 4      # descarga (reanudable: relanzar el mismo comando)
.venv\Scripts\python.exe scripts/descarga_mitma.py --solo-ensamblar # junta los ficheros diarios en los CSV anuales
.venv\Scripts\python.exe scripts/verificar_mitma.py 2024            # filas, días, fechas ausentes, destinos fuera de Asturias
```
Progreso: `Get-Content logs\descarga_mitma.log -Tail 10 -Wait` (PowerShell).

- **Cómo funciona**: descarga cada `.csv.gz` en streaming y lo filtra al vuelo (viajes: `destino`; pernoctaciones: `zona_pernoctacion`; en ambos casos ∈ `data/raw/zonas_mitma_asturias.csv`), sin guardar el original. Único filtro; solo cambia el separador `|` por `,`. Un fichero por día en `data/raw/_mitma_dias/` y ensamblado a `data/raw/mitma_{viajes,pernoctaciones}_<año>.csv`. Estado en `data/raw/_mitma_estado_v2.jsonl` (OK / NO_DISPONIBLE / ERROR por día).
- **Prioridad**: pernoctaciones de todo el periodo, luego viajes 2024-25, 2023 y 2022.
- **Límite real**: el ancho de banda del portal (~190 GB de tráfico en total; medido entre ~2 y ~20 MB/s). Usar **4 workers**: con 10 el rendimiento empeoró. Al parar el script en Windows, comprobar que no quedan workers huérfanos (procesos `python` con `multiprocessing.spawn`).
- **Días sin datos**: un 404 se deja ausente (nunca 0). Detalle y contraste con la lista oficial en `notas/registro_descargas.md`.
- Mediciones, decisiones y límites: `notas/decisiones_y_consideraciones.md` (secciones «Paso 2» y «cambio de método»).
