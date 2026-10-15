# TalentUO

Repositorio compartido (privado) para datos y notas del proyecto.

## Estructura

- `data/raw/` – datos descargados tal cual de la fuente (no editar a mano).
- `data/manual/` – datos introducidos o corregidos manualmente.
- `notas/registro_descargas.md` – registro de cada descarga (fecha, fuente, archivo).
- `notas/decisiones_y_consideraciones.md` – decisiones importantes y límites de los datos.
- `scripts/` – `descarga_mitma.py` (descarga MITMA día a día, filtrada a Asturias, reanudable) y `verificar_mitma.py`; `descarga_sadei.py` (tablas PC-Axis de SADEI vía el visor PxWeb, en partes si superan 100 000 celdas) y `verificar_sadei.py`.
- `logs/` – logs de las descargas (locales, no versionados).
- `data/raw/LEEME_datos_no_versionados.md` – qué ficheros pesados no se suben y cómo regenerarlos.
- `notas/registro_senales.md`, `notas/notas_senales.md`, `notas/decisiones_senales.md` – señales adelantadas (Wikipedia, Google Trends, OAPN): registro, hallazgos por fuente y decisiones pendientes. Script: `src/descarga_senales.py`.

## Instalación

```bash
python -m venv .venv
.venv\Scriptsctivate        # Windows (PowerShell/cmd)
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

`requirements-lock.txt` contiene las versiones exactas probadas (Python 3.11):
`pip install -r requirements-lock.txt`.

Dependencias principales: pandas, requests, openpyxl, pyaxis, pySpainMobility.

## Estado (Fase 1: solo descarga en bruto)

Persona A (demanda y movilidad): MITMA viajes/pernoctaciones 2022–2025 (Asturias), estadísticos de día normal 2024, INE móviles (turismo interno **interprovincial**: no incluye a los asturianos que viajan dentro de Asturias; Excel 2022–2026 solo con cruces de >30 turistas, y extracto de la tabla 53001 con destino Asturias y origen "Total Nacional", 2019M07–2026M08; en el CSV `.` es separador de miles **y** dato ausente, ausente ≠ 0; `scripts/descarga_ine_moviles.py`), viviendas turísticas INE (semestral 2020–2026) SADEI por concejo (turistas nacionales/extranjeros mensuales, plazas y apartamentos anuales, padrón; ficheros `.px`, el nacional en 4 partes) y residuos COGERSA (**solo anual 2020–2021**, sin detalle mensual). Detalle, fechas reales y límites en `notas/registro_descargas.md`; lo no comprobado figura como **NO VERIFICADO**.

## Descarga MITMA (viajes y pernoctaciones, Asturias)

Fuente: Open Data Movilidad del MITMA, estudios básicos, zonificación municipal v2 (`https://movilidad-opendata.mitma.es/estudios_basicos/por-municipios/...`). Rango: 2022-01-01 a 2025-06-30 (desde julio de 2025 cambia la metodología: **no se mezcla**). Solo cubre residentes en España.

```bash
.venv\Scripts\python.exe scripts/descarga_mitma.py --workers 4      # descarga (reanudable; --tipos viajes|pernoctaciones, --inicio/--fin)
.venv\Scripts\python.exe scripts/descarga_mitma.py --solo-ensamblar # junta los ficheros diarios en los CSV anuales
.venv\Scripts\python.exe scripts/verificar_mitma.py 2024            # filas, días, fechas ausentes, destinos fuera de Asturias
```
Progreso: `Get-Content logs\descarga_mitma.log -Tail 10 -Wait` (PowerShell).

- **Cómo funciona**: descarga cada `.csv.gz` en streaming y lo filtra al vuelo (viajes: `destino`; pernoctaciones: `zona_pernoctacion`; en ambos casos ∈ `data/raw/zonas_mitma_asturias.csv`), sin guardar el original. Único filtro; solo cambia el separador `|` por `,`. Un fichero por día en `data/raw/_mitma_dias/` y ensamblado a `data/raw/mitma_{viajes,pernoctaciones}_<año>.csv`. Estado en `data/raw/_mitma_estado_v2.jsonl` (OK / NO_DISPONIBLE / ERROR por día).
- **Prioridad**: pernoctaciones de todo el periodo, luego viajes 2024-25, 2023 y 2022.
- **Límite real**: el ancho de banda del portal (~190 GB de tráfico en total; medido entre ~2 y ~20 MB/s). Usar **4 workers**: con 10 el rendimiento empeoró. Al parar el script en Windows, comprobar que no quedan workers huérfanos (procesos `python` con `multiprocessing.spawn`).
- **Días sin datos**: un 404 se deja ausente (nunca 0). Detalle y contraste con la lista oficial en `notas/registro_descargas.md`.
- **Para terminar la descarga en otro ordenador: `notas/traspaso_mitma.md`** (estado exacto, comandos, validación, decisiones pendientes). Referencia de filas por día: `notas/mitma_referencia_filas_por_dia.csv`; compararla con `python scripts/comparar_con_referencia.py`.
- Mediciones, decisiones y límites: `notas/decisiones_y_consideraciones.md` (secciones «Paso 2» y «cambio de método»).

