# Traspaso: terminar la descarga y el procesamiento de MITMA (viajes y pernoctaciones)

Documento para que **otra persona, en otro ordenador, termine el Paso 2** (descarga MITMA) a partir de lo que hay en GitHub.
Redactado el 2026-10-15 por la Persona A. Todo lo que no se ha podido comprobar figura como **NO VERIFICADO**.

> Alcance: Fase 1 = solo descarga en bruto y filtro a Asturias. **No se limpia, no se agrega, no se modela.**

---

## 1. Qué hay que conseguir

Cuatro más cuatro ficheros, **solo con filas de Asturias** (46 zonas de `data/raw/zonas_mitma_asturias.csv`), del **2022-01-01 al 2025-06-30**:

| Fichero final | Filtro | Estado a 2026-10-15 23:10 |
|---|---|---|
| `data/raw/mitma_pernoctaciones_{2022,2023,2024,2025}.csv` | `zona_pernoctacion` ∈ zonas | **Completos y verificados** en el PC de origen (pesan 87, 95, 112 y 48 MB: **no caben en git**) |
| `data/raw/mitma_viajes_{2022,2023,2024,2025}.csv` | `destino` ∈ zonas | **Incompleto**: 2024 hecho; 2025 hasta el 2025-03-02; 2023 sin empezar; 2022 solo 4 días |

Desde el **2025-07-01 cambia la metodología del MITMA: no descargar nada posterior al 2025-06-30** (el script lo impide con un `assert`). Los datos solo cubren **residentes en España**.

### Qué falta exactamente (a 2026-10-15 23:10)

| Bloque | Días totales | Hechos | Pendientes | Observación |
|---|---|---|---|---|
| Pernoctaciones 2022-01-01..2025-06-30 | 1 277 | 1 264 (+13 días que el MITMA no publica) | 0 | Completo |
| Viajes 2024 | 366 | 362 (+4 sin datos del MITMA) | 0 | Completo |
| Viajes 2025-01-01..2025-06-30 | 181 | 61 (hasta 2025-03-02) | **120** | Prioridad 1 |
| Viajes 2023 | 365 | 0 | **358** (7 días sin datos del MITMA) | Prioridad 2 (opcional, ver §7) |
| Viajes 2022 | 365 | 4 | **361** | Prioridad 3 (opcional, ver §7) |

> Los ficheros diarios ya descargados de viajes (9,9 GB) **no están en git**. Quien continúe **empieza con el estado vacío** y descargará también lo ya hecho si quiere el periodo completo (ver §4 para la alternativa de pasarse los datos por fuera de git).

---

## 2. Qué hay en el repositorio y qué NO

**En git (rama `paso1-zonas-mitma` / PR #2 hacia `main`)**

| Fichero | Para qué |
|---|---|
| `scripts/descarga_mitma.py` | Descarga, filtra, ensambla. Reanudable. |
| `scripts/verificar_mitma.py` | Comprobaciones por año y tipo. |
| `scripts/comparar_con_referencia.py` | Compara tu descarga con la mía, día a día. |
| `notas/mitma_referencia_filas_por_dia.csv` | Referencia: filas de origen y de Asturias por día y tipo (1 708 días-tipo) de la descarga original. |
| `data/raw/zonas_mitma_asturias.csv` | Las 46 zonas de Asturias (Paso 1). **Imprescindible.** |
| `notas/registro_descargas.md`, `notas/decisiones_y_consideraciones.md`, `README.md`, `data/raw/LEEME_datos_no_versionados.md` | Registro, decisiones, límites. |

**NO en git (por tamaño o por ser temporal; lo regenera el script)**: `data/raw/mitma_viajes_*.csv`, `data/raw/mitma_pernoctaciones_*.csv`, `data/raw/_mitma_dias/`, `data/raw/_mitma_viejo/`, `data/raw/_mitma_estado_v2.jsonl`, `logs/`.
*No se sube el fichero de estado a propósito*: da por hechos los días cuyos datos no están en tu PC. Empieza con el tuyo vacío.

---

## 3. Preparación del entorno

Probado en: Windows 11, Python 3.14.8, PowerShell, 8 núcleos/16 hilos, ~4 GB de RAM libres. **Otros sistemas: NO VERIFICADO** (el código usa solo `pathlib`, `zlib`, `requests` y `multiprocessing`, así que en Linux/macOS debería funcionar).

```powershell
git clone https://github.com/hugoomez/TalentUO.git
cd TalentUO
git checkout paso1-zonas-mitma        # hasta que la PR #2 esté fusionada en main
python -m venv .venv
.venv\Scripts\activate                # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt       # el script solo necesita pandas y requests
```
Espacio en disco necesario (estimado a partir de lo medido): ~**60 GB** para viajes de 2024-25 ya filtrados + ~**250 MB** de pernoctaciones; para todo el periodo, unos **50 GB** más de viajes de 2022-23 (≈ 38 MB filtrados por día × 1 277 días ≈ 49 GB; estimación). El script aborta si quedan **menos de 20 GB libres**.
Red: se descargan ~100-150 MB por día de viajes y ~2-4 MB por día de pernoctaciones; **~190 GB de tráfico en total** (no se guardan: se filtran al vuelo).

---

## 4. Terminar la descarga (comandos exactos)

Siempre desde la raíz del repositorio. El script es **reanudable**: si se corta, se relanza el mismo comando.

```powershell
# 1) Pernoctaciones (rápido, ~15 min): todo el periodo
.venv\Scripts\python.exe scripts\descarga_mitma.py --workers 4 --tipos pernoctaciones

# 2) Viajes, en el orden de prioridad que el script aplica solo (2024-25 -> 2023 -> 2022)
.venv\Scripts\python.exe scripts\descarga_mitma.py --workers 4 --tipos viajes
#    Para PARAR tras 2024-25 y decidir antes de seguir:
.venv\Scripts\python.exe scripts\descarga_mitma.py --workers 4 --tipos viajes --inicio 2024-01-01 --fin 2025-06-30

# 3) Ver el progreso (otra ventana)
Get-Content logs\descarga_mitma.log -Tail 10 -Wait
```

Reglas importantes:
- **`--workers 4`**. Con 10 el portal rindió peor (medido). No más de 4-5.
- **No lances dos instancias del script con rangos que compartan año** a la vez: ambas ensamblan y escriben el mismo CSV anual.
- Para pararlo en Windows: el script usa `multiprocessing` y **al matar el proceso principal los workers quedan huérfanos y siguen descargando**. Hay que matar también los procesos `python` cuyo comando contiene `multiprocessing.spawn` y cuyo proceso padre ya no existe.
- Un día con HTTP 404 se registra como `NO_DISPONIBLE` y queda **ausente (nunca 0)**. No se reintenta salvo con `--reintentar-no-disponibles`.
- Fallos de red: 5 reintentos con espera; si persiste queda `ERROR` en el estado y se reintenta al relanzar.
- Si la descarga se cortó con un día a medias, no hay datos corruptos: cada día se escribe de forma atómica (`.tmp` → renombrado).

**Alternativa para no repetir lo hecho**: si el PC de origen te pasa por fuera de git `data/raw/_mitma_dias/` y `data/raw/_mitma_estado_v2.jsonl` (o los CSV anuales + ese estado), copia ambos a tu `data/raw/` y relanza. El script solo salta los días cuyo fichero diario existe o ya constan como `ensamblado`. **Copiar el estado sin los datos haría que se salte esos días.** NO VERIFICADO en otro ordenador.

### Qué hace el script (para poder auditarlo)
1. Lee `data/raw/zonas_mitma_asturias.csv` (debe haber **46** zonas; si no, aborta).
2. Para cada (tipo, día): descarga `https://movilidad-opendata.mitma.es/estudios_basicos/por-municipios/{viajes|pernoctaciones}/ficheros-diarios/AAAA-MM/AAAAMMDD_{Viajes|Pernoctaciones}_municipios.csv.gz` **en streaming**, descomprimiendo al vuelo con `zlib` (comprueba el CRC del gzip y que los bytes coincidan con `Content-Length`).
3. **Único filtro**: se conservan las líneas cuya fecha es la del día y cuyo campo de destino (4.º en viajes, columna `destino`) o de zona de pernoctación (3.º en pernoctaciones, columna `zona_pernoctacion`) está en las 46 zonas, con una expresión regular sobre bytes. Nada se agrega, recodifica ni renombra: se conserva la cabecera original y los valores como texto (`NA` se mantiene como `NA`; los ceros a la izquierda de los códigos, como `01001`, también).
4. **Única transformación**: se cambia el separador `|` por `,`. Si algún valor ya contuviera una coma (o `\r`), el script falla en vez de escribir un CSV roto.
5. Escribe `data/raw/_mitma_dias/<tipo>/AAAAMMDD.csv` y anota el resultado en `data/raw/_mitma_estado_v2.jsonl` (estado, filas leídas, filas de Asturias, MB bajados, segundos).
6. Al final **ensambla** los CSV anuales (`data/raw/mitma_<tipo>_<año>.csv`), anexando a lo ya ensamblado, y borra los diarios si el tamaño cuadra. Anota en el estado `"ensamblado": true`.
7. Comprueba el espacio libre antes de cada tarea.

Columnas (cabecera tal cual del MITMA):
- Viajes (**15**): `fecha, periodo, origen, destino, distancia, actividad_origen, actividad_destino, estudio_origen_posible, estudio_destino_posible, residencia, renta, edad, sexo, viajes, viajes_km` (la guía esperaba 13; las dos `estudio_*_posible` son un hallazgo).
- Pernoctaciones (4): `fecha, zona_residencia, zona_pernoctacion, personas`.

Hay que ensamblar manualmente si se corta antes de terminar: `.venv\Scripts\python.exe scripts\descarga_mitma.py --solo-ensamblar --tipos viajes` (con `--inicio/--fin` si procede). Los CSV anuales **no quedan ordenados por fecha** si se descarga por tramos (se anexa en el orden de ensamblado); si el siguiente paso lo necesita, ordenar en la fase de procesamiento, no aquí.

---

## 5. Procesamiento / validación (todo lo que hay que hacer al terminar)

Fase 1 no incluye limpieza. "Procesar" aquí = **ensamblar y comprobar**.

```powershell
# a) Ensamblar (si el script no lo hizo ya al acabar)
.venv\Scripts\python.exe scripts\descarga_mitma.py --solo-ensamblar

# b) Comprobar cada año y tipo: filas, días distintos, primera/última fecha, fechas ausentes,
#    filas con destino/pernoctación fuera de Asturias (debe ser 0)
.venv\Scripts\python.exe scripts\verificar_mitma.py 2022
.venv\Scripts\python.exe scripts\verificar_mitma.py 2023
.venv\Scripts\python.exe scripts\verificar_mitma.py 2024
.venv\Scripts\python.exe scripts\verificar_mitma.py 2025
#    (admite un segundo argumento: viajes | pernoctaciones)

# c) Comparar tus filas con la referencia de la descarga original (debe dar "Diferencias: 0")
.venv\Scripts\python.exe scripts\comparar_con_referencia.py
```

### Resultados esperados (de la descarga original)
**Pernoctaciones — verificado** con `verificar_mitma.py` el 2026-10-15:

| Año | Filas | Días distintos | Fechas ausentes | Filas fuera de Asturias |
|---|---|---|---|---|
| 2022 | 2 964 041 | 365 | ninguna | 0 |
| 2023 | 3 244 975 | 358 | 2023-10-26, 27, 30, 31; 2023-11-01, 02, 03 | 0 |
| 2024 | 3 834 878 | 362 | 2024-04-18; 2024-11-09, 10, 26 | 0 |
| 2025 (hasta 06-30) | 1 653 463 | 179 | 2025-04-28, 29 | 0 |

(2 964 041 = 2 945 927 + 18 114: las 18 114 filas son las de la prueba del 2022-01-02 y 03, que se ensamblaron antes.)

**Viajes — parcial.** Las filas esperadas por día están en `notas/mitma_referencia_filas_por_dia.csv`. Días de viajes descargados: 427 (362 de 2024, 61 de 2025 y 4 de 2022), con 118 818 118 filas de Asturias en total (incluidos los 2 días de la prueba). Ausentes confirmados con 404 en 2024: 2024-04-18, 2024-11-09, 2024-11-10 y 2024-11-26.

### Días sin datos: lo que se sabe y lo que no
- **404 reales** (descargados a 2026-10-15): pernoctaciones y viajes → 2023-10-26, 27, 30, 31, 2023-11-01, 02, 03 (solo comprobado en pernoctaciones; en viajes 2023 está sin descargar), 2024-04-18, 2024-11-09, 2024-11-10, 2024-11-26, 2025-04-28, 2025-04-29 (esta última, comprobada en pernoctaciones; viajes 2025-04 sin descargar aún).
- **Coincide con el RSS oficial** `https://movilidad-opendata.mitma.es/RSS.xml` (leído el 2026-10-15): lo ausente del RSS en el periodo son exactamente estas 13 fechas, en viajes y pernoctaciones.
- **No coincide con la página del MITMA**, que además cita 2024-04-04, 2024-04-19 y 2024-11-11 como sin datos: **esos tres días SÍ están publicados y se descargaron**. Y no cita 2024-11-09 ni 2024-11-26, que **no** están publicados. Causa: **NO VERIFICADO**.
- 2024-10-29..31 (DANA, anomalías en Levante): se descargan normalmente; **hay que marcarlos como anómalos en la limpieza, no excluirlos aquí**.
- **Nunca rellenar un día ausente con 0.**

---

## 6. Estimación de tiempo y rendimiento (medido)
- Por día de viajes en el PC de origen con 4 workers: ~10-20 s (descarga + filtro).
- El cuello de botella es el **ancho de banda del portal**: medido entre ~2-3 MB/s y ~14-20 MB/s según el momento (a las 18:10 muy lento, a las 22:20 y 23:10 rápido). **NO VERIFICADO** si depende de la hora, de la IP o de la carga del servidor.
- Estimaciones (no garantizadas): 120 días de viajes 2025 → 5-10 min si hay ~14 MB/s; viajes 2022+2023 (~715 días) → 25-30 min a esa velocidad y varias horas a ~3 MB/s; todo desde cero → entre ~1 h y ~17 h.

---

## 7. Decisiones pendientes (no tomadas; no las adivines)
1. **¿Se descargan viajes de 2022 y 2023?** El periodo del reto es 2022-2025, pero una instrucción del equipo era parar tras 2024-01..2025-06 y consultar. Ese comando de parada está en §4.
2. **Ficheros por mes** (`data/raw/mitma_viajes/AAAA-MM.csv`, `data/raw/mitma_pernoctaciones/AAAA-MM.csv`): solicitado en un encargo posterior, **no implementado**; el script produce un CSV por año (lo que pide la guía `notas/persona_A_demanda_movilidad`).
3. **`notas/registro_mitma.md`** (una línea por mes y tipo) y **`src/descarga_mitma.*`**: solicitados en ese encargo; **no creados**. Se usan `scripts/descarga_mitma.py` y `notas/registro_descargas.md`.
4. **Fichero origen-destino de «día normal»** (`.../estadisticos/viajes/2024/municipal_estadisticos_diasemana_ods.csv`, 1,08 GB): no descargado.
5. **PDF del cambio de metodología de julio de 2025**: no leído (**NO VERIFICADO** su contenido).
6. Contraste de las URLs diarias con el índice oficial: las URLs son las de la librería `pyspainmobility` 2.1.2 y funcionan (HTTP 200), y el RSS oficial contiene enlaces con esa misma forma; no se contrastó el 100 % de las URLs una a una.

---

## 8. Cosas que han salido mal (para no repetirlas)
- Primera versión con pandas: demasiado lenta y con poca RAM (un filtrado simple tardó 847 s en vez de ~10 s). Sustituida por streaming.
- Con 10 workers el rendimiento total cayó; los workers huérfanos tras parar el proceso seguían consumiendo red.
- `pandas` con la configuración por defecto convierte `NA` en vacío: por eso todo se lee como texto.
- 6 ficheros diarios de viajes de 2022 (`20220104, 05, 07, 08, 09, 11`) en `_mitma_dias` no tienen registro en el estado (los escribieron workers huérfanos): se reescriben al descargar esos días y no se usan hasta entonces.
- Los CSV anuales de pernoctaciones pesan hasta 112 MB: **no se pueden subir a GitHub** (límite 100 MB por fichero). Se estimó mal al principio.

---

## 9. Dónde está cada cosa en la documentación
- Historial y decisiones: `notas/decisiones_y_consideraciones.md` (secciones «Zonificación», «MITMA viajes y pernoctaciones» y «cambio de método»).
- Registro por fichero y hallazgos: `notas/registro_descargas.md` (entradas «Paso 1» y «Paso 2»).
- Uso resumido: `README.md` (sección «Descarga MITMA»).
- Ficheros pesados que no se suben: `data/raw/LEEME_datos_no_versionados.md`.
