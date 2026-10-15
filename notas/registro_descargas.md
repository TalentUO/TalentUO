# Registro de descargas

Anotar aquí cada descarga de datos para mantener la trazabilidad.

| Fecha | Fuente | URL / método | Archivo en `data/raw/` o `data/manual/` | Descargado por | Notas |
|-------|--------|--------------|------------------------------------------|----------------|-------|
|       |        |              |                                          |                |       |

## 2026-10-15 · Paso 1 · MITMA: zonificación municipal (v2) – Persona A

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

## 2026-10-15 · Paso 2 · MITMA: viajes y pernoctaciones (estudios básicos, municipios, v2) – Persona A

**Estado: EN CURSO** (descarga lanzada el 2026-10-15 ~17:00, 4 procesos, uno por año). Se actualiza al terminar cada año.

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

## 2026-10-15 · Paso 6 (opcional) · Viviendas turísticas (INE) y residuos (COGERSA) – Persona A

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
