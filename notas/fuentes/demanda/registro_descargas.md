# Registro de descargas

Trazabilidad de las descargas de datos de demanda y movilidad (MITMA, INE, SADEI, COGERSA), una sección por paso. Las descargas de factores (AEMET, Open-Meteo, calendarios, eventos y señales) tienen su propio registro en `notas/fuentes/`.

> **Datos del INE de turismo con móviles (paso 3):** se descargaron en el equipo del responsable de demanda, pero no están en el repositorio (`data/raw/ine_moviles_*` está en `.gitignore`) y el modelo no los usa. La validación externa con el INE no se ha hecho (`notas/historico/resultados_reales.md` §8).

## 2026-10-15 · Paso 1 · MITMA: zonificación municipal (v2) – equipo de demanda

**Cangas de Onís es zona propia: SÍ** (id MITMA `33012`, contiene solo el municipio INE 33012; Covadonga y Lagos son núcleos dentro de ese municipio, no tienen zona propia).

### Ficheros descargados (con `pyspainmobility` 2.1.2, `Zones(zones='municipalities', version=2)`)

| Fichero | URL | Descargado | Rango de fechas | Zonas | Problemas |
|---|---|---|---|---|---|
| `data/raw/mitma_zonificacion_v2/zonificacion_municipios.{shp,shx,dbf,prj,qpj,cpg}` | https://movilidad-opendata.mitma.es/zonificacion/zonificacion_municipios/ | 2026-10-15 | n/a (zonificación, sin fechas) | toda España (2735 zonas) | ninguno |
| `.../nombres_municipios.csv`, `.../poblacion_municipios.csv` | ídem | 2026-10-15 | n/a | toda España | separador `\|`, 1.ª columna es un índice sin nombre |
| `.../relacion_ine_zonificacionMitma.csv` | https://movilidad-opendata.mitma.es/zonificacion/ (vía la librería) | 2026-10-15 | n/a | toda España (36 382 secciones censales) | una fila por sección censal; es la fuente de la columna `municipalities` |
| `data/raw/zonas_mitma_asturias.csv` | derivado de los dos anteriores (filtro INE que empieza por 33) | 2026-10-15 | n/a | 46 zonas MITMA de Asturias, 78 municipios INE | derivado, no es descarga directa |

Notas: la librería generó además `municipios_2.geojson` (57 MB, caché); se borró por ser derivado. Import correcto: `pyspainmobility` (minúsculas); la primera ejecución con `python -I` falló por un bloqueo de Windows (Control de aplicaciones) al cargar un DLL de numpy, y sin `-I` funciona.

### Página oficial (Open Data Movilidad, leída 2026-10-15)
https://www.transportes.gob.es/ministerio/proyectos-singulares/estudios-de-movilidad-con-big-data/opendata-movilidad (WebFetch/curl simple dan 403; carga con cabeceras de navegador)

- **Días sin datos** (estudios básicos):
  - No disponibles por incidencia en Orange: 26, 27, 30, 31 oct, 1, 2 y 3 nov 2023; 4, 18, 19 abr y 10, 11 nov 2024.
  - No disponible por el apagón masivo: 28 y 29 abr 2025.
  - Con anomalías (Orange en Levante, DANA): 29 al 31 oct 2024 (disponibles pero con anomalías; ver registro de antenas).
- **Cobertura**: diarios 2022, 2023, 2024 y primer semestre 2025. Para el 2.º semestre de 2025 solo hay **17 días** (una semana tipo de octubre y algunos días singulares de agosto y diciembre). Continuar la serie está "previsto" según la página.
- **Aviso metodológico (cita)**: "Los datos de movilidad referidos a fechas posteriores al 1 de julio de 2025, debido a cambios en ajustes metodológicos, pertenecerán a una nueva versión de la serie de movilidad." **Regla del equipo: no mezclar datos anteriores y posteriores a esa fecha.**
- Documento metodológico del cambio: https://www.transportes.gob.es/recursos_mfom/paginabasica/recursos/leeme_cambiometodologia_indicadoresbigdata_posteriores_a_20250701.pdf — **NO VERIFICADO su contenido** (no leído todavía).
- NO VERIFICADO: que la lista de días sin datos esté completa para 2025 posterior a abril (la página no lista más).

### Resultado de zonas
| Municipio | INE | Zona MITMA | Municipios en la zona | ¿Agrupada? |
|---|---|---|---|---|
| Cangas de Onís | 33012 | `33012` | solo 33012 | **no** |
| Llanes | 33036 | `33036` | solo 33036 | no |
| Oviedo | 33044 | `33044` | solo 33044 | no |
| Gijón | 33024 | `33024` | solo 33024 | no |
| Ribadesella | 33056 | `33056` | solo 33056 | no |
| Cabrales | 33008 | `33008_AM` | 33008 Cabrales; 33043 Onís; 33046 Peñamellera Alta; 33047 Peñamellera Baja; 33055 Ribadedeva | **sí** |
| Onís | 33043 | `33008_AM` | (la misma de Cabrales) | **sí** |
| Amieva | 33003 | `33015_AM` | 33003 Amieva; 33015 Caso; 33050 Ponga; 33067 Sobrescobio | **sí** |

- Códigos INE de los 78 municipios cotejados con Wikidata (propiedad P772, consulta SPARQL 2026-10-15), fuente secundaria: coinciden los 78 y los de las tablas anteriores. Los códigos de Cangas de Onís, Llanes, Oviedo y Gijón coinciden además con los dados por el equipo. **No** contrastados contra la tabla oficial del INE (NO VERIFICADO frente al INE directo).
- Implicación: Cabrales (acceso a Picos por Arenas/Poncebos) y Onís no se pueden medir por separado en MITMA, ni Amieva (se agrupa con Caso/Ponga/Sobrescobio).
- Zonas agrupadas en Asturias: 13 de 46 (las que acaban en `_AM`, "agregacion de municipios").

## 2026-10-15 · Paso 2 · MITMA: viajes y pernoctaciones (estudios básicos, municipios, v2) – equipo de demanda

**Estado al escribir esta sección: en curso** (descarga lanzada el 2026-10-15 ~17:00). Terminó a las 00:19; filas, días y ausencias por año en `notas/fuentes/mitma/registro_mitma.md`.

### Prueba 2024-08-15: OK (sin errores de red; no hizo falta probar otro día)
- URL viajes: `https://movilidad-opendata.mitma.es/estudios_basicos/por-municipios/viajes/ficheros-diarios/2024-08/20240815_Viajes_municipios.csv.gz` (147 MB, 13 156 431 filas, separador `|`).
- URL pernoctaciones: `.../por-municipios/pernoctaciones/ficheros-diarios/2024-08/20240815_Pernoctaciones_municipios.csv.gz` (4,2 MB, 772 285 filas).
- Tras filtrar a Asturias (46 zonas): viajes 346 877 filas (24 periodos horarios, 46 destinos); pernoctaciones 24 334 filas (46 zonas).
- **Hallazgo (columnas)**: viajes trae **15** columnas, 2 más de las esperadas: `estudio_origen_posible`, `estudio_destino_posible` (en las filas vistas solo `no`; resto de valores NO VERIFICADO). Orden: fecha, periodo, origen, destino, distancia, actividad_origen, actividad_destino, estudio_origen_posible, estudio_destino_posible, residencia, renta, edad, sexo, viajes, viajes_km. Pernoctaciones: exactamente las esperadas (fecha, zona_residencia, zona_pernoctacion, personas). Se conservan todas.
- **Hallazgo (formato)**: `fecha` es `AAAAMMDD`; `periodo` es `00`..`23`; `edad`/`sexo` traen el texto `NA` (dato no disponible en origen, ~45 % de filas de ese día) → se conserva como texto `NA`, no se rellena. Ids de zona con ceros a la izquierda y sufijo `_AM` → los CSV se leen/escriben como texto.
- Los CSV de salida usan `,` como separador (el original usa `|`), mismas columnas y mismos valores.

### Método
`scripts/descarga_mitma.py`: descarga día a día (reintentos, comprueba Content-Length), filtra (`destino` / `zona_pernoctacion` ∈ `zonas_mitma_asturias.csv`), anexa al CSV anual y **borra el .csv.gz**. Estado en `data/raw/_mitma_estado.jsonl` (un registro por día/tipo: OK / NO_DISPONIBLE (404) / ERROR, con filas leídas y guardadas); log en `logs/descarga_mitma.log`. Reanudable (relanzar el mismo comando; trunca el CSV al último día completo). Un 404 se deja **ausente**, nunca 0. `scripts/verificar_mitma.py <año>` hace las comprobaciones.

### Días que el MITMA no publica (contraste con el RSS oficial `https://movilidad-opendata.mitma.es/RSS.xml`, leído 2026-10-15)
Ausentes del RSS en 2022-01-01..2025-06-30 (viajes y pernoctaciones, idénticos): 2023-10-26, 27, 30, 31, 2023-11-01, 02, 03; 2024-04-18; 2024-11-09, 10, 26; 2025-04-28, 29.
- Difiere de la lista de la página: la página dice también 2024-04-04 y 2024-04-19 (el RSS sí los lista) y 2024-11-11 (RSS sí lo lista; el RSS no lista 2024-11-09 ni 2024-11-26). **NO VERIFICADO** cuál es correcta; el resultado real (404 o fichero) está en el estado de la descarga.

### Estadísticos de "día normal" — ENCONTRADOS
Carpeta `https://movilidad-opendata.mitma.es/estudios_basicos/estadisticos/` (año 2024). Columnas: `dia_semana`, código de zona, `promedio`, `desviacion_estandar`, `q1`, `q3`, `q3-q1`, `umbral_extremo_bajo/alto`, `umbral_atipico_bajo/alto`. Descargados hoy (nacionales, sin filtrar) en `data/raw/mitma_estadisticos_dia_normal_2024/`:
| Fichero local | Origen (bajo `.../estadisticos/`) | Contenido |
|---|---|---|
| `viajes_municipal_intra.csv` | `viajes/2024/municipal_estadisticos_diasemana_intra.csv` | viajes dentro de la zona, por zona y día de la semana |
| `viajes_municipal_inter.csv` | `viajes/2024/municipal_estadisticos_diasemana_inter.csv` | viajes entre zonas (por zona) |
| `pernoctaciones_municipal_pernoctacion.csv` | `pernoctaciones/2024/estadisticos_diasemana_municipal_pernoctacion.csv` | por zona de pernoctación y residentes/no residentes |
| `pernoctaciones_municipal_residencia.csv` | `pernoctaciones/2024/estadisticos_diasemana_municipal_residencia.csv` | por zona de residencia |
- NO descargado: `viajes/2024/municipal_estadisticos_diasemana_ods.csv` (origen-destino, **1,08 GB**; el único con detalle por pareja origen-destino). También existen versiones provinciales. "Sin julio ni agosto" y "2024" salen de la página oficial; **NO VERIFICADO** en los propios ficheros.

## 2026-10-15 · Paso 6 (opcional) · Viviendas turísticas (INE) y residuos (COGERSA) – equipo de demanda

### 6a. INE · Viviendas turísticas por municipio — DESCARGADO
- Página: `https://www.ine.es/experimental/viv_turistica/exp_viv_turistica_tablas.htm`. Tabla municipal: **Tabla 2 "Viviendas turísticas, plazas y plazas por vivienda turística. Municipios"** (id INE 39363). Hay otra municipal, Tabla 4 (% de viviendas turísticas sobre total censado, id 39366), **no descargada**.
- URLs: `https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/39363.csv?nocab=1` → `data/raw/ine_viviendas_turisticas.csv` (30,9 MB, separador `;`, UTF-8 con BOM, toda España); `https://www.ine.es/jaxiT3/files/t/es/xlsx/39363.xlsx?nocab=1` → `data/raw/ine_viviendas_turisticas.xlsx` (1,3 MB). Las URLs de exportación se dedujeron del id de tabla, no aparecen en la página; funcionaron (HTTP 200). **NO VERIFICADO** que el xlsx tenga el mismo contenido que el csv (solo se abrió el csv).
- Columnas csv: Total Nacional; Comunidades y CCAA; Provincias; Municipios; Viviendas y plazas (Viviendas turísticas / Plazas / Plazas por vivienda turística); Periodo; Total.
- **Frecuencia: semestral, no mensual.** Periodos de Cangas de Onís (13): 2020M08, 2021M02, 2021M08, 2022M02, 2022M08, 2023M02, 2023M08, 2024M02, 2024M08, 2024M11, 2025M05, 2025M11, 2026M05 (cortes irregulares: M02/M08 hasta 2024 y M05/M11 desde 2024-11). La web avisa de que ago y nov 2024 se actualizaron para incluir licencias de Andalucía.
- Comprobado: aparecen **33012 Cangas de Onís** y **33036 Llanes** (viviendas, plazas y plazas/vivienda). Cangas de Onís: 252 (2020M08) → 410 (2024M08) → 378 (2026M05). Llanes: 769 (2020M08), 747 (2022M02)… Asturias tiene 78 municipios en la tabla.
- Problemas: hay celdas vacías/con punto en el original (16 847 líneas acabadas en `.` o `..`; **no se ha investigado** qué significan: tratar como ausente, nunca 0). Separador de miles `.` en los números (p. ej. `341.001`). Solo incluye lo registrado en ventanas de datos del INE (experimental, a partir de registros/plataformas): cobertura de oferta turística **NO VERIFICADA**. Covadonga y Lagos no son municipios (pertenecen a Cangas de Onís): no hay detalle por zona.

### 6b. COGERSA · Residuos por concejo — PARCIAL: solo ANUAL, sin detalle mensual
- Página: `https://cogersa.es/datos_residuos/`. **Granularidad real: anual** (concejo × año × tipo de residuo). No se ofrece desglose mensual en ningún fichero descargable.
- Descargado: `https://recursos.cogersa.es/gestion%20residuos/Residuos-COGERSA-Ayuntamientos-2021.xlsx` → `data/raw/cogersa_residuos.xlsx` (53 KB). Una hoja ("Ayuntamientos"), 83 ayuntamientos + "Total general"; comparativa **2020 vs 2021** (toneladas, presumiblemente; **unidad NO VERIFICADA**) para: residuos urbanos mezclados, fracción orgánica, envases, papel y cartón, vidrio, vegetales, muebles, RCD, otros, separados, total gestionado, % separados. Aparecen CANGAS DE ONIS y LLANES (también CABRALES, ONIS, etc.; Covadonga y Lagos no, al ser municipales).
- Problemas: nombres en mayúsculas sin tildes y con caracteres corruptos (`CARRE�O`, `COA�A`: codificación de origen); sin código INE (hay que cruzar por nombre); cabecera en varias filas.
- **NO DISPONIBLE (descargable)**: 2022–2025. Solo existen como paneles Power BI (en línea, sin descarga según la página) y folletos PDF resumen 2024 y 2025 (no descargados; **NO VERIFICADO** si traen datos por concejo). **NO VERIFICADO** si los paneles Power BI muestran detalle mensual (no se abrieron). Anteriores: XLSX 2020 (incluido en el de 2021), XLS 2019/2018, PDF 2011–2017 (no descargados).
- Utilidad: con datos anuales y solo hasta 2021 no sirve para entrenar la serie diaria; solo como indicador estructural/anual. El rango temporal descargable (2020–2021) no solapa con MITMA (2022–2025).

## 2026-10-15 · Paso 5 · SADEI: tablas PC-Axis por concejo – equipo de demanda

**Estado: HECHO** (6 tablas + padrón). Los 7 ficheros se abren con pyaxis y contienen Cangas de Onís y Llanes (salvo las 2 tablas de Asturias, que no son por concejo; ver abajo).

### Cómo se descargó (el método de la guía NO funcionó)
- Los enlaces "Ver fichero .px" (`...html?f=<código>`) **devuelven la página HTML**, no el .px. El enlace directo del iframe (`http://sadei.sentidocomun.es/sadei/pxweb/...px`) redirige (301) a `www.sadei.sentidocomun.es`, que **no resuelve**.
- Método que sí funciona: el visor PxWeb de SADEI `https://www.sadei.es/sadei/pxweb/es/01/<carpeta>/<código>.px`: seleccionar todos los valores de cada variable → "Continuar" → botón "Archivo de PC-Axis" (POST de formulario ASP.NET). Sin API REST (`/api/v1` da error). Script: `scripts/descarga_sadei.py` (reanudable por fichero: `python scripts/descarga_sadei.py <nombre.px>`); comprobación: `scripts/verificar_sadei.py`.
- **Límite del PxWeb: 100 000 celdas por consulta.** El turismo receptor nacional (79 concejos × 52 provincias × 80 meses) lo excede → se bajó en **4 partes por fecha**, sin tocar: `sadei_receptor_nacional_concejos_parte1..4.px` (partes 1–3: 24 meses cada una; parte 4: 8). No hay un único fichero; hay que concatenarlas (Fase 2).
- Los .px bajados son una **consulta con todos los valores** de cada variable, no el fichero original del servidor (cabecera con fecha de la descarga), pero con el mismo contenido seleccionable.
- `pyaxis.parse` solo existe como `from pyaxis import pyaxis; pyaxis.parse(...)` (no `import pyaxis`). Todos abren con `encoding="ISO-8859-1"`; las cabeceras declaran `Windows-1252` o `iso-8859-15` (equivalentes para los acentos).

### Ficheros
Códigos de la guía: todos **verificados por el título** de la tabla (columna "Título"), salvo la discrepancia de nombre indicada.

| Fichero en `data/raw/` | Código PxWeb | Título real (TITLE del .px) | Dimensiones | Filas | Cobertura (último dato NO vacío) | Cangas de Onís / Llanes |
|---|---|---|---|---|---|---|
| `sadei_receptor_nacional_concejos_parte{1-4}.px` | `11__04__07/11040706` | Número de turistas nacionales por Municipio, Provincia de origen y Fecha (fuente INE, estadística experimental de teléfonos móviles) | Municipio (79) × Provincia de origen (52) × Fecha mensual | 98 592 ×3 + 32 864 | **2019-07 a 2026-02** (80 meses) | sí / sí |
| `sadei_receptor_extranjero_concejos.px` | `11__04__07/11040704` | Número de turistas extranjeros por Municipio y Fecha | Municipio (78) × Fecha mensual | 6 162 | **2019-07 a 2025-12** (78 meses) | sí / sí |
| `sadei_rentabilidad.px` | `99__04__08__04/9904080406` | Indicadores de rentabilidad del sector hotelero por Periodo y Indicador | Periodo mensual × 2 indicadores (tarifa media diaria, ingresos por habitación disponible) | 480 | **2008-01 a 2026-08** | **no aplica**: solo Asturias, sin concejos |
| `sadei_eoh_viajeros.px` | `99__04__08__04/9904080402` | Viajeros y pernoctaciones según origen del viajero y tipo de establecimiento por Periodo, Tipo de alojamiento, Indicador y Origen del viajero | Periodo (años 1995+ y meses) × 5 tipos × 2 indicadores × origen | 12 330 | **1995 a 2026-08** (mezcla años y meses en `Periodo`) | **no aplica**: solo Asturias, sin concejos |
| `sadei_plazas_concejos.px` | `11__02__02/11020202` | Alojamientos y plazas según tipo. Concejos | Ámbito territorial × Establecimientos/plazas × Tipo × Periodo anual | 50 560 | **2006 a 2025** (anual) | sí / sí |
| `sadei_apartamentos_concejos.px` | `11__02__04/11020418` | Apartamentos turísticos. Establecimientos y plazas según categoría. Concejos | Ámbito × Categoría × Estab./plazas × Periodo anual | 18 960 | **2006 a 2025** (anual) | sí / sí |
| `padron_concejos.px` | `02__02__02/02020202` | Evolución de la población. Censo, oficial padronal, residente de referencia y provisional. Concejos | Ámbito territorial (79) × Periodo (60, 1900 (Censo) … 2026 (Provisional 1-jul)) | 4 740 | último con dato: 2026 (Provisional 1-jul) | sí / sí (Cangas: 1900 = 8 559) |

- **Discrepancias de nombre** (no de contenido): la guía llama "Turismo receptor nacional/extranjero. Concejos" a lo que el fichero titula "Número de turistas nacionales/extranjeros"; y "Otros alojamientos. Apartamentos turísticos" a lo que titula "Apartamentos turísticos…". Mismo código, tabla coherente.
- **Plazas llegan hasta 2025**, no 2023 (hipótesis de la guía desmentida para estas dos tablas).
- Los dos ficheros de **Asturias en conjunto** (rentabilidad, EOH) no tienen concejos: valen como contexto regional/estacionalidad, no para Cangas de Onís. En EOH el nombre de la guía sugiere detalle por origen de viajero, no por concejo.
- Páginas de origen: `.../turismo/viajeros--pernoctaciones--gasto-e-indicadores-de-rentabilidad_212_1_ap.html` (en ella están también los códigos de receptor nacional/extranjero, no en la de establecimientos) y `.../establecimientos-y-plazas_211_1_ap.html`.

### Valores ausentes (regla 1)
Los .px traen celdas vacías (`NaN` al abrirlas): **no se rellenan con 0**. En los receptores la propia página indica "las celdas vacías corresponden a valores inferiores a 30 personas, omitidos por secreto estadístico" (el INE los suprime) → ausentes, no cero. Proporción de celdas vacías en bruto: receptor nacional 72–80 % por parte, extranjero 19 %, EOH 23 %, plazas 3 %, apartamentos 0 %, rentabilidad 1 %, padrón 10 % (periodos futuros/provisionales). No analizado en qué concejos/meses (Fase 2).
- Las celdas de turistas de Cangas de Onís **no se han inspeccionado** (¿cuántas vacías?): NO VERIFICADO.

### Padrón
**Encontrado** en https://www.sadei.es/sadei/poblacion/evolucion-e-indicadores_166_1_ap.html (Población → Evolución e indicadores). Se eligió `02020202` por ser una sola tabla compacta concejo × periodo. Alternativas en la página "Padrones de habitantes" (`.../padrones-de-habitantes_167_1_ap.html`), no descargadas: `02__04__02/02040202` (población por nacionalidad, sexo y edad, concejos) y `02__04__01/02040102` (Población. Concejos). **NO VERIFICADO**: qué filas del periodo 2021–2026 son padrón definitivo, residente de referencia o provisional (la columna `Periodo` mezcla etiquetas "(Censo)", "(Provisional…)" etc.; mirar las etiquetas completas antes de usarla).

## 2026-10-15 · Paso 4 · INE: encuestas de ocupación por punto turístico – equipo de demanda

**Estado: DESCARGADO y abierto (8 CSV). Sin limpiar.** URL patrón (funciona, HTTP 200): `https://www.ine.es/jaxiT3/files/t/csv_bdsc/<tabla>.csv`. Formato: separador `;`, UTF-8 con BOM (la cabecera HTTP dice ISO-8859-15 pero el contenido es UTF-8), decimal/millar con `.` (p. ej. `25.874` = 25 874 viajeros; **NO VERIFICADO** si algún valor lleva decimales). Formato largo: punto turístico; variable; [residencia]; `Periodo` (`2026M08`); `Total`.

### Verificación de números de tabla (API INE `servicios.ine.es/wstempus`, TABLAS_OPERACION)
- **2078 = EOH, Viajeros y pernoctaciones por puntos turísticos** (hoteles) → CORRECTA.
- **2076 = EOH, Establecimientos, plazas estimadas, grados de ocupación y personal empleado por puntos turísticos** → CORRECTA.
- **2082 = EOAP (apartamentos), Viajeros y pernoctaciones por puntos turísticos** → CORRECTA, pero **solo cubre Llanes y Cudillero** en Asturias (no hay Cangas de Onís ni Covadonga).
- Las tres supuestas eran correctas; ninguna era provincial/CCAA.

### Ficheros
| Fichero | Tabla | Contenido | Hasta | Puntos asturianos |
|---|---|---|---|---|
| `ine_eoh_2078.csv` | 2078 | Hoteles: viajeros y pernoctaciones, residentes España / extranjero | 2026M08 (desde 2005M01) | Cangas de Onís (33012), Gijón (33024), Llanes (33036), Oviedo (33044), Villaviciosa (33076) |
| `ine_eoh_2076.csv` | 2076 | Hoteles: establecimientos, habitaciones, plazas, grado de ocupación (habitaciones, plazas, plazas fin de semana), personal | 2026M08 | los mismos 5 |
| `ine_eoap_2082.csv` | 2082 | Apartamentos: viajeros y pernoctaciones | 2026M08 | Llanes, Cudillero (33021) |
| `ine_eoap_2083.csv` | 2083 (extra) | Apartamentos: apartamentos, plazas, ocupación, personal | 2026M08 | Llanes, Cudillero |
| `ine_camping_2084.csv` | 2084 | Campings: viajeros y pernoctaciones | 2026M08 | solo Llanes |
| `ine_camping_2085.csv` | 2085 (extra) | Campings: establecimientos, parcelas, plazas, ocupación | 2026M08 | solo Llanes |
| `ine_rural_1999.csv` | 1999 | Turismo rural: viajeros y pernoctaciones | 2026M08 | **no hay puntos**: solo zona turística "Asturias (Principado De): Costa Verde" |
| `ine_rural_2005.csv` | 2005 (extra) | Turismo rural: establecimientos, plazas, ocupación, personal | 2026M08 | solo zona "Costa Verde" |

- **Turismo rural: el INE no publica puntos turísticos** (la operación EOTR 241 solo tiene tablas por CCAA, zonas turísticas y provincias). Se usa zona Costa Verde (todo Asturias costero; **NO VERIFICADO** qué municipios incluye) → no sirve para Cangas de Onís/Covadonga. Alternativa para rural/vivienda: `ine_viviendas_turisticas.csv`.
- **Ninguna tabla trae Covadonga ni Lagos** (no son municipio; Covadonga y Lagos están dentro de Cangas de Onís). 2078/2076 contienen 139 puntos en toda España.
- Existen tablas `751xx` (75191–75198) con las mismas variables pero solo desde 2025M01 (probable serie nueva; **NO VERIFICADO** el motivo). No descargadas; las 20xx llegan igualmente a 2026M08 y tienen histórico desde 2005.

### Datos ausentes (secreto estadístico) – NO convertir en 0
Cada serie tiene 260 filas (2005M01–2026M08 × variable); el valor puede ser `.`, `..` o vacío. Cangas (viajeros, España) tiene 202 `.`, 60 `..`, 30 vacíos y solo 4 `0` entre sus series; **NO VERIFICADO** si `.` y `..` significan lo mismo para el INE (se asume ausente en ambos; los `0` reales se conservan). Filas ausentes por serie (de 260):
- Hoteles 2078: Cangas de Onís ~66, Llanes ~56 (viaj. España 56, extranj. 50), Villaviciosa ~111–118, Gijón 2, Oviedo 2. Cangas tiene dato real en 2026M05–08 (p. ej. 2026M08 viajeros españoles = 25 874). **Villaviciosa: último dato real 2025M08** (después, ausente).
- Hoteles 2076: Cangas 66 (habitaciones 46), Llanes 56, Villaviciosa 118, Gijón/Oviedo 2.
- Apartamentos: Llanes 7 ausentes; **Cudillero ~155 ausentes, último dato real 2024M10**.
- Camping Llanes: **120 de 260 ausentes** (campings abren solo parte del año o por secreto; causa **NO VERIFICADO**).
- Rural Costa Verde: 7 ausentes (personal empleado 19).

### Pendiente / siguiente
- Confirmar con muestra que `.` y vacío corresponden a meses cerrados/secreto (comparar con el PDF/nota metodológica EOH).
- Cangas de Onís solo tiene hoteles; para presión turística local no hay apartamentos, campings ni rural por punto.

## 2026-10-15 · Paso 3 · INE: turismo con móviles, interno (estadística experimental) – equipo de demanda

**ALCANCE: turismo interno interprovincial.** Solo cuenta turistas residentes en España que viajan a una provincia **distinta** de la de residencia. **NO incluye a los asturianos que viajan dentro de Asturias** (eso lo cubre MITMA). Las cifras de destino asturiano son visitantes de fuera de Asturias; no son el total de visitantes. Tampoco incluye extranjeros (según la nota del propio Excel; la tabla 53001 NO VERIFICADO que use la misma definición, aunque su concepto es "Turistas").

### 3.1 Excel anuales (sin 404 en ningún año)
URL: `https://www.ine.es/experimental/turismo_moviles/exp_tmov_interno_mun_<año>.xlsx`, descargados 2026-10-15.

| Fichero | Tamaño | Hojas de datos | Último mes |
|---|---|---|---|
| `data/raw/ine_moviles_interno_2022.xlsx` | 39,5 MB | 2022-01 … 2022-12 | 2022-12 |
| `data/raw/ine_moviles_interno_2023.xlsx` | 46,0 MB | 2023-01 … 2023-12 | 2023-12 |
| `data/raw/ine_moviles_interno_2024.xlsx` | 48,8 MB | 2024-01 … 2024-12 | 2024-12 (las hojas de sept–dic se llaman `2024_09`… con guion bajo) |
| `data/raw/ine_moviles_interno_2025.xlsx` | 37,7 MB | 2025-01 … 2025-12 | 2025-12 |
| `data/raw/ine_moviles_interno_2026.xlsx` | 28,4 MB | 2026-01 … 2026-08 | **2026-08** (8 hojas) |

- Estructura: una hoja `Notas`/`Hoja1` + una hoja por mes. Columnas: `mes, mun_orig_cod, mun_orig, dest_cod, dest, turistas, prov_orig_cod, prov_orig, prov_dest_cod, prov_dest`. Una fila = par municipio de origen → municipio de destino. Códigos como texto con ceros (`'01001'`). Los textos se leen bien con openpyxl (`Alegría-Dulantzi`, `Araba/Álava`); el `�` que se ve en la consola de Windows es solo de la consola.
- **Secreto estadístico (nota 2 del propio fichero): solo se dan los cruces con más de 30 turistas.** Un cruce que no aparece es "no publicado" (menos de ~30), **nunca 0**. Mínimo observado: 30. Sumar las filas de un destino da una **cota inferior**, no el total. Ejemplo 2025-08, Cangas de Onís: Excel suma 21.675 frente a 34.979 en la tabla 53001.
- No hay celdas vacías ni "." en `turistas` en ninguna hoja para destinos asturianos (comprobado en las 56 hojas mensuales; la ausencia se expresa quitando la fila).
- La hoja `2026-05` tiene 1.048.576 filas (el límite de Excel), pero ~974.000 son filas vacías de formato; los datos reales son ~74.000 filas. **No está truncada.**
- **Cangas de Onís (33012) y Llanes (33036) aparecen como destino en los 56 meses (2022-01 a 2026-08).** Cangas de Onís: 16–229 orígenes por mes; Llanes: 38–334.
- Comprobado: 62–75 municipios asturianos distintos como destino por hoja (de 78).

### 3.2 Tabla mensual 53001
- `https://www.ine.es/jaxiT3/files/t/csv_bdsc/53001.csv` **sí funciona** (HTTP 200, cabecera HTTP `charset=ISO-8859-15`, pero los bytes son UTF-8 con BOM; separador `;`). Patrón verificado.
- **Pero el CSV completo es enorme**: más de 2,3 GB (todos los municipios de España × todos los orígenes por CCAA/provincia × 86 meses; las dos descargas completas que probé se interrumpieron o se colgaron antes del final). No se descargó entero.
- **`data/raw/ine_moviles_53001.csv` NO es el fichero íntegro**: es un extracto que hice filtrando el flujo del INE por **destino = municipios de Asturias (código 33xxx)** y **origen = "Total Nacional"** (sin desglose por CCAA/provincia de origen). 6.708 filas = 78 municipios × 86 meses (2019M07 – 2026M08). Mismas columnas y formato que el original, no limpiado. El desglose por origen se puede pedir por la web (`Tabla.htm?t=53001&L=0`) si hace falta; no se automatizó.
- Reproducible con `scripts/descarga_ine_moviles.py` (lee en streaming y corta al acabar el bloque "Total Nacional"). **NO VERIFICADO de principio a fin**: el INE cortó la conexión a los 14 min en la prueba; lo descargado coincidió byte a byte con el extracto manual.
- Los ficheros temporales (descarga parcial filtrada) quedaron en el scratchpad, no en el repo. `data/raw/ine_moviles_*` está en `.gitignore`.
- **Último mes de la 53001: 2026M08** (Cangas de Onís 24.430, Llanes 51.592 turistas). Coincide con el último mes del Excel de 2026. La "última modificación 07/10/2026" de la web NO VERIFICADO que corresponda a otro mes; los datos llegan hasta 2026M08.
- **Cangas de Onís (`33012 Cangas de Onís`) y Llanes (`33036 Llanes`) están completos: 86 meses con dato numérico, sin celdas vacías.**
- **TRAMPA DE FORMATO: el punto es separador de miles Y marca de dato ausente.** `"1.179"` = 1179; `"."` solo = ausente. Además `""` (comillas vacías) = ausente. Hay que parsear con regex (`^\d{1,3}(\.\d{3})*$`), no con `float()`. Hay 6.434 celdas numéricas, 42 con `.` y 232 vacías. Todas se tratan como **ausentes, nunca 0** (secreto estadístico o no disponible).
- Municipios con celdas ausentes (`.` / vacía, de 86 meses):

| Municipio | `.` | vacía | Total ausentes | Primer–último mes ausente |
|---|---|---|---|---|
| 33078 Yernes y Tameza | 6 | 70 | **76** | 2019M07–2026M08 (último dato numérico: **2026M03**) |
| 33048 Pesoz | 6 | 51 | 57 | 2020M02–2026M06 |
| 33064 Santo Adriano | 6 | 37 | 43 | 2020M03–2026M03 |
| 33030 Illas | 4 | 22 | 26 | 2020M05–2024M10 |
| 33029 Illano | 4 | 12 | 16 | 2020M04–2026M03 |
| 33065 Sariego | 0 | 9 | 9 | 2023M11–2024M07 |
| 33067 Sobrescobio | 3 | 4 | 7 | 2020M04–2021M04 |
| 33052 Proaza | 1 | 5 | 6 | 2020M03–2024M06 |
| 33054 Regueras, Las | 0 | 5 | 5 | 2023M11–2024M05 |
| 33003 Amieva | 2 | 2 | 4 | 2020M04–2021M02 |
| 33043 Onís | 1 | 3 | 4 | 2020M04–2020M12 |
| 33077 Villayón | 1 | 3 | 4 | 2020M03–2026M02 |
| 33050 Ponga | 2 | 1 | 3 | 2020M04–2021M02 |
| 33072 Teverga | 3 | 0 | 3 | 2020M04–2021M02 |
| 33038 Morcín | 2 | 0 | 2 | 2020M04–2020M05 |
| 33042 Noreña | 0 | 2 | 2 | 2024M04–2025M02 |
| 33053 Quirós | 0 | 2 | 2 | 2020M11–2021M03 |
| 33062 Santa Eulalia de Oscos | 0 | 2 | 2 | 2024M04–2025M02 |
| 33006 Bimenes, 33009 Cabranes, 33058 Riosa | – | – | 1 cada uno | 2020M11, 2021M03, 2020M04 |

  Los 78 municipios aparecen; 21 tienen ausentes; el resto (incl. Cangas de Onís, Llanes, Cabrales, Ribadesella, Oviedo, Gijón) está completo. Las ausencias se concentran en 2020 (COVID) y en municipios pequeños (secreto estadístico).

### Coherencia y límites
- Cotejo Excel vs 53001 (mismo mes y destino): el Excel queda siempre por debajo (p. ej. 2026-08 Llanes 41.172 vs 51.592), coherente con que el Excel omite cruces <30. No se cotejó la causa exacta de la diferencia: NO VERIFICADO.
- 53001 empieza en 2019M07; los Excel solo desde 2022. No se comprobó si las series de ambos usan el mismo criterio de "turista".
- NO VERIFICADO: si "Turistas" de la 53001 incluye o excluye los viajes dentro de la misma provincia/comunidad (la nota del Excel dice provincia distinta).

### 2026-10-15 18:16 · Paso 2: cambio de script (v2, streaming) — registro de la reanudación
- Se descartó la tanda inicial (pandas); sus CSV parciales (≈68 días por año) están en `data/raw/_mitma_viejo/`. El script actual `scripts/descarga_mitma.py` rehace la descarga entera con el método de streaming; salida y columnas idénticas (comprobado en 4 casos). Estado en `data/raw/_mitma_estado_v2.jsonl` (el antiguo `_mitma_estado.jsonl` quedó en `_mitma_viejo/`).
- Orden: pernoctaciones de todo el periodo → viajes 2024-01..2025-06 → 2023 → 2022. Los CSV anuales se ensamblan al terminar la tanda (o con `--solo-ensamblar`). Ver `notas/fuentes/demanda/decisiones_demanda.md` para las mediciones.
- Resultados finales por año (filas, días, fechas ausentes): en `notas/fuentes/mitma/registro_mitma.md`.
