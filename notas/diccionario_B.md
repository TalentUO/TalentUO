# Diccionario de datos de la parte B (factores explicativos, limpios)

Fecha: 2026-10-15. Tablas en `data/clean/`, código en `src/limpieza_B/`. Para reproducir todo: `python -X utf8 src/limpieza_B/ejecutar_todo.py` (unos 50 s; se detiene si falla alguna comprobación). El control de calidad está en `notas/control_calidad_B.md`.

Convenciones comunes:
- `fecha` es datetime64 de día (sin hora), en hora local de España.
- **Ausente = NaN, nunca 0.** La única excepción es la precipitación «Ip» de AEMET (0,0 con `prec_inapreciable`).
- Nada se imputa sin una columna indicadora (`*_imputado`, `fila_ausente_en_fuente`, etc.).
- Lo que no se ha podido comprobar va marcado como **[NO VERIFICADO]** o con una columna `*_verificado`.
- `fuente` está en cada tabla o se describe en su apartado.

Uso para el modelo (resumen):

| Tabla | ¿Característica de entrenamiento? | Cuidado |
|---|---|---|
| `openmeteo_diario` | **Sí** (meteorología de entrenamiento) | No evaluar antes del corte (`es_reanalisis`). En producción, la previsión a N días va en `*_prevN`. |
| `aemet_diario` | Solo con retardo (observación) | No existe el día que se predice; sirve para contraste y retardos. |
| `openmeteo_era5_diario` | **No** | Solo referencia. |
| `calendario_diario`, `festivos_locales` | Sí | 2027: escolar desde septiembre y Lagos sin dato (NaN). |
| `eventos_diario`, `partidos_diario` | Sí, con `estado` como calidad | Cruceros: **no** (solo previsión 2025-26). |
| `wikipedia_diario`, `trends_semanal` | Señal adelantada, **solo con retraso** (decisión del equipo) | Wikipedia: `visitas_media7_ant` (media de los 7 días anteriores). Trends: valor semanal de la semana anterior, sin pasar a diario. No se usan las series de `*_no_fiable`. |
| `oapn_anual` | **No** (contexto) | El total anual filtraría información futura si se usara a diario. |

## 1. Meteorología observada (AEMET)

### `data/clean/aemet_diario.parquet`

Script: `src/limpieza_B/limpia_aemet.py`. Fuente: AEMET OpenData, climatologías diarias (`data/raw/aemet_diario_<indicativo>.json`). Hay una fila por `fecha` y `estacion`, en calendario completo desde 2022-01-01 hasta el último día que devuelve cada estación (2026-10-11; Colunga 1203D, 2026-06-04). Son 20 811 filas y 12 estaciones. Los días que la API no devuelve son filas con NaN en todas las variables y `fila_ausente_en_fuente=True` (874 filas). **Ningún hueco está imputado.** Los porcentajes de hueco por estación y variable están en `notas/fuentes/aemet/huecos_aemet.md` y en `data/clean/_qc/aemet_diario.json`.

| Columna | Significado | Unidad | Tratamiento / limitaciones |
|---|---|---|---|
| `fecha` | Día de la observación | datetime64 (día) | Formato de origen AAAA-MM-DD. |
| `estacion` | Indicativo AEMET | texto | Cruce con `estaciones_aemet.csv`. |
| `tmed_c`, `tmin_c`, `tmax_c` | Temperatura media, mínima y máxima del día | °C | Coma decimal convertida a punto. Rango comprobado: -30..50; también se comprueba que tmin ≤ tmax. |
| `prec_mm` | Precipitación diaria | mm | «Ip» (inapreciable, < 0,1 mm) → **0,0** con `prec_inapreciable=True` (regla 2). Si falta el dato, NaN. Rango: 0..500. |
| `prec_inapreciable` | La fuente decía «Ip» | booleano (NaN en filas ausentes) | 331 días (1,6 % de las filas). |
| `viento_medio_ms` | Velocidad media del viento (`velmedia`) | m/s | Unidad según la documentación de AEMET; no recomprobada en la API. |
| `racha_max_ms` | Racha máxima (`racha`) | m/s | Igual que la anterior. |
| `dir_racha_grados` | Dirección de la racha máxima | grados (0-360) | La fuente da decenas de grado (1-36) y se multiplica por 10. Los códigos 99 y 88 → NaN. |
| `dir_racha_codigo` | Código especial de dirección (88 o 99) | entero | 99 = «dirección variable» y 88 = «sin dato/calma», según la convención habitual de AEMET. **[NO VERIFICADO]** en la documentación. |
| `sol_h` | Insolación (`sol`) | horas | Solo la miden 1212E, 1183X, 1249X, 1207U y 5783. En el resto, 100 % NaN, incluida la estación principal 1186P. |
| `pres_max_hpa`, `pres_min_hpa` | Presión máxima y mínima | hPa | Presión a la altitud de la estación (Sotres, a 1236 m, ronda los 887 hPa). No la miden 1179B, 1186P, 1199X, 1203D ni 1210X. |
| `hr_media_pct`, `hr_max_pct`, `hr_min_pct` | Humedad relativa | % | Rango: 0..100. |
| `prec_max_intervalo_mm` | Campo `pintMax` | mm | **Significado [NO VERIFICADO]**: parece la precipitación máxima en un intervalo corto (no es un campo documentado en las notas). Los valores negativos (−0,3; 206 días) → NaN con `prec_max_intervalo_negativo_en_fuente=True`. |
| `prec_max_intervalo_negativo_en_fuente` | `pintMax` venía negativo en la fuente | booleano | |
| `hora_tmin`, `hora_tmax`, `hora_racha`, `hora_hr_max`, `hora_hr_min`, `hora_prec_max_intervalo` | Hora del extremo | texto «HH:MM» | Hora oficial (UTC según AEMET; **[NO VERIFICADO]**). «Varias» → NaN con `<columna>_varias=True`. |
| `hora_pres_max`, `hora_pres_min` | Hora de la presión extrema | texto «HH» o «HH:MM» | La fuente suele dar solo la hora («21»). Se deja tal cual, sin inventar minutos. |
| `*_varias` | La fuente decía «Varias» (más de una hora) | booleano | |
| `hora_racha_invalida_en_fuente` | La hora de la racha era imposible («72:30», etc.) | booleano | 5 casos (1207U ×2, 1179B, 1183X, 1210X) → hora NaN. La racha se conserva. |
| `fila_ausente_en_fuente` | La API no devolvió ese día | booleano | Ese día todas las variables son NaN. |
| `fuente` | «AEMET OpenData climatologías diarias» | texto | |

Limitaciones: AEMET publica con 3 o 4 días de retraso (última fecha, 2026-10-11). Colunga 1203D termina el 2026-06-04. Sotres 1178R tiene un hueco de 537 días (2022-01-16 → 2023-07-06). La estación principal de Picos (1186P, Amieva-Panizales) está a 7-10 km de Cangas, Covadonga y Lagos, y no mide sol ni presión.

### `data/clean/estaciones_aemet.csv`

| Columna | Significado |
|---|---|
| `indicativo` | Código AEMET. |
| `nombre`, `altitud_m`, `provincia` | Tal como vienen en los registros diarios (iguales en todas las filas de cada estación). |
| `lat`, `lon` | Grados decimales, convertidos desde el inventario (`GGMMSS[NSEW]`; W/S negativo). |
| `indsinop` | Indicativo sinóptico (vacío si no tiene). |
| `zona`, `uso` | Papel de la estación según `notas/fuentes/aemet/estaciones_aemet.md` (principal, alternativa, origen…). |
| `fuente` | Inventario de AEMET OpenData. |

## 2. Meteorología para entrenar (Open-Meteo)

Script: `src/limpieza_B/limpia_openmeteo.py`. Las zonas son las 9 de `config/zonas_meteo.csv` (`provisional=si`).

### `data/clean/openmeteo_diario.parquet` (tabla de entrenamiento)

Hay una fila por `fecha` y `zona_meteo`, del 2022-01-01 al 2026-10-15, en calendario continuo: 15 741 filas (9 × 1749). Fuente de las variables base: Historical Forecast API (`best_match`), diaria y en hora local Europe/Madrid.

| Columna | Significado | Unidad | Tratamiento / limitaciones |
|---|---|---|---|
| `fecha` | Día local (Europe/Madrid) | datetime64 (día) | |
| `zona_meteo` | Punto de `config/zonas_meteo.csv` | texto | Las coordenadas son provisionales. Covadonga está verificada por geocodificación y Lagos, solo con Wikipedia. |
| `tmax_c`, `tmin_c` | Temperatura máxima y mínima a 2 m | °C | Sin nulos. |
| `prec_mm` | Precipitación diaria | mm | Sin nulos. |
| `prec_horas` | Horas con precipitación | h | |
| `sol_s` | Duración de la insolación | segundos | Rango: 0..86 400. |
| `viento_max_kmh`, `racha_max_kmh` | Viento y racha máximos a 10 m | km/h | |
| `weather_code` | Código WMO del día (el más severo, según Open-Meteo) | código 0-99 | Es categórico: no se debe tratar como numérico continuo. |
| `*_prev1`, `*_prev2`, `*_prev3` | La misma variable, **prevista 1, 2 o 3 días antes** (Previous Runs API) | igual que la base | Se agrega de horario a diario por día natural local: tmax/tmin son el máximo y el mínimo de `temperature_2m`, `prec_mm` es la suma, `prec_horas` cuenta las horas con ≥ 0,1 mm, viento y racha son el máximo, `sol_s` es la suma y `weather_code` es el máximo horario. Solo hay valor si las 24 horas del día tienen dato. Si no, NaN. **NaN forzado antes de 2024-01-22.** La hora del 2025-06-15 a las 12:00 de `precipitation_previous_day1` venía negativa (−0,2 a −1,0 mm) en covadonga, gijon y oviedo: se anula, y el `*_prev1` de ese día en esas zonas queda NaN. |
| `es_reanalisis` | El día es anterior al corte de la zona (Asturias, < 2022-11-09; Madrid y Sevilla, < 2022-11-16) | booleano | Ese tramo de Historical Forecast es ERA5 (reanálisis), no una previsión: hay riesgo de fuga. **Decisión del equipo:** el entrenamiento base empieza en el corte. El tramo se conserva solo para el análisis de sensibilidad y **no debe usarse para evaluar**. La temperatura del tramo no se puede clasificar: **[NO VERIFICADO]** si es reanálisis ajustado. **Indicio de cambio de régimen en la temperatura** (control de calidad, Covadonga): la Tmax media de julio y agosto es 22,5 °C en 2022 frente a 24,8–25,8 °C en 2023–2026, mientras que en AEMET 1186P el verano de 2022 es el más caluroso (26,5 °C). Es decir, la temperatura del tramo también es más fría, por la celda costera de ERA5. Es otra razón para no mezclar ese tramo sin `es_reanalisis`. |
| `dia_posiblemente_incompleto` | Día de la descarga (2026-10-15) | booleano | El día en curso puede estar parcialmente previsto. |
| `fuente` | Origen de la fila | texto | «Open-Meteo Historical Forecast API (best_match), diario». |

Comprobación de la agregación horaria. El día 0 horario de Previous Runs se agrega con las mismas reglas y se compara con el diario de Historical Forecast desde 2024-01-01. Viento, racha, código WMO y horas de precipitación coinciden casi al 100 %, lo que confirma las reglas de agregación. El sol coincide al 100 % (en Oviedo, al 99,9 %). En temperatura, el error medio absoluto es de 0,02-0,23 °C y la correlación, de 0,998 o más. En precipitación, el error medio absoluto es de 0,08-0,35 mm/día y coincide (±0,05 mm) en el 73-90 % de los días. Las cifras por zona están en `_qc/openmeteo_diario.json` → `sanity_dia0_previous_vs_historical`. Se deduce que el diario de Open-Meteo se calcula con una resolución algo distinta de la horaria (**[NO VERIFICADO]** cómo exactamente), así que `*_prevN` y la base no son idénticas por construcción. Diferencias de ese orden no son error de previsión.

Cambio de hora: la serie horaria en Europe/Madrid trae siempre 24 etiquetas por día, también en los días de cambio de hora (comprobado: todos los días tienen 24). Se tratan como completos. Qué hace Open-Meteo con la hora que se repite o se salta está **[NO VERIFICADO]**.

Uso recomendado en producción: lo que se conoce de antemano es la previsión. La variable más fiel a producción es `*_prev1` (desde 2024-01-22). La base de Historical Forecast (desde el corte) es la serie larga de entrenamiento.

### `data/clean/openmeteo_era5_diario.parquet`

Tiene el mismo esquema de variables (`tmax_c` … `weather_code`) y 15 741 filas, más `uso="solo_referencia_no_entrenar"` y `fuente` («Open-Meteo Archive API (ERA5), diario»). **No es una característica de entrenamiento**: es un reanálisis y no existe en producción. La celda ERA5 no coincide con el punto (en Covadonga y Cangas cae a unos 5-6 km). El sesgo medio de Historical Forecast frente a ERA5 tras el corte, por zona, está en `_qc/openmeteo_era5_diario.json`.

### `data/clean/openmeteo_prevision_ejemplo.parquet`

Es la previsión en vivo del 2026-10-15 al 2026-10-21 (7 filas) de la zona **covadonga**. El JSON no dice la zona: se identifica porque las coordenadas devueltas (43,31/−5,06) coinciden con las de Historical Forecast de covadonga. Tiene **exactamente las mismas columnas y dtypes** que `openmeteo_diario`: el script falla si difieren. `*_prevN` es NaN, `es_reanalisis=False`, `dia_posiblemente_incompleto=False` y `fuente` es «Open-Meteo Forecast API (previsión en vivo), diario». En producción, la previsión a N días de un día es lo que corresponde a `*_prevN`. Al montar las características de producción hay que mapear la previsión a la columna `_prevN` que toque según el horizonte: decisión del modelado, que aquí no se aplica.

## 3. Calendario

Script: `src/limpieza_B/limpia_calendario.py` (datos transcritos a mano en `src/limpieza_B/calendario_datos.py`). Validación manual: `notas/fuentes/calendarios/validacion_calendario.md`. Todos los documentos fuente están en `data/raw/calendario/`.

### `data/clean/calendario_diario.parquet`

Una fila por día del 2022-01-01 al 2027-12-31 (2191 filas). Clave: `fecha`.

| Columna | Significado | Unidad / tipo | Fuente | Tratamiento | Limitaciones |
|---|---|---|---|---|---|
| fecha | Día | datetime64, sin hora | — | Rango completo y continuo (comprobado) | — |
| anio, mes | Año y mes de `fecha` | entero | derivado | — | — |
| dia_semana | Día de la semana | entero, 0 = lunes … 6 = domingo | derivado | — | — |
| nombre_dia | Nombre del día | texto ("lunes"…) | derivado | — | — |
| es_fin_de_semana | Sábado o domingo | bool | derivado | — | — |
| festivo_nacional | Fiesta marcada en las 19 columnas del BOE (17 CCAA + Ceuta + Melilla) | bool | BOE (resolución anual de fiestas laborales, `boe_fiestas_<año>.pdf`) | Extraída de la tabla del anexo por posición de las marcas | Incluye las "nacionales no sustituidas" (`**`) solo si ninguna comunidad las sustituye; un festivo nacional sustituido en alguna comunidad no cuenta aquí |
| nombre_festivo_nacional | Nombre de esa fiesta | texto; NaN si no es festivo | BOE | Texto de la fila | — |
| festivo_ast / festivo_mad / festivo_cyl | Fiesta laboral en Asturias / Comunidad de Madrid / Castilla y León (nacional o autonómica), con traslados y sustituciones ya aplicados por el BOE | bool | BOE del año (`festivos_fuente`) | Marca `*`, `**` o `***` en la columna de esa comunidad | No incluye fiestas locales (ver `festivos_locales.parquet`). Sin notas al pie para estas tres comunidades en 2022-2027 (comprobado) |
| nombre_festivo_ast / _mad / _cyl | Nombre de la fiesta | texto; NaN si no es festivo | BOE | Si hay dos filas el mismo día, unidas con " / " | — |
| tipo_festivo_ast / _mad / _cyl | `nacional_no_sustituible` (*), `nacional_no_sustituida` (**), `autonomica` (***) | categoría; NaN si no es festivo | BOE (leyenda "Códigos de las fiestas") | — | — |
| festivos_fuente | Código BOE de la resolución del año | texto | BOE | — | — |
| puente_ast / _mad / _cyl | **Puente**: día laborable (lunes a viernes y no festivo en esa comunidad) con un día no laborable (fin de semana o festivo de la comunidad) inmediatamente antes **y** inmediatamente después. Ej.: martes festivo → el lunes es puente; jueves festivo → el viernes es puente | bool | derivado de `festivo_*` | Fuera del rango solo se conocen los fines de semana | Ignora fiestas locales y días no lectivos escolares; no es un día libre oficial, sino una oportunidad de puente |
| finde_largo_ast / _mad / _cyl | Día que forma parte de un tramo de ≥ 3 días no laborables seguidos (fin de semana + festivos de la comunidad) | bool | derivado | — | Sin puentes |
| finde_largo_con_puente_ast / _mad / _cyl | Igual, pero contando también los días de puente como libres (tramos ≥ 3 días) | bool | derivado | — | Supone que el puente se toma |
| semana_santa | Jueves Santo a Domingo de Resurrección (4 días) | bool | Domingo de Pascua calculado (algoritmo gregoriano anónimo) | Verificado contra las filas Jueves/Viernes Santo y Lunes de Pascua del BOE de 2022-2027 (6/6) | — |
| semana_santa_ampliada | Domingo de Ramos a Lunes de Pascua (9 días) | bool | idem | — | Definición propia |
| domingo_pascua | Domingo de Resurrección | bool | idem | — | — |
| periodo_escolar_ast / _mad / _cyl | Situación escolar del día para **Infantil (2.º ciclo) y Primaria**: `lectivo`, `fin_de_semana`, `festivo` (festivo laboral de la comunidad en periodo lectivo), `no_lectivo_puntual` ("otros días no lectivos" de la norma), `vacaciones_navidad`, `vacaciones_semana_santa`, `verano` (del día siguiente al último lectivo al día anterior al primero del curso siguiente) | categoría; NaN desde 2027-09-01 | Calendarios escolares oficiales: BOPA (Asturias), BOCM (Madrid), BOCYL (CyL); ver `escolar_fuente_*` | Transcrito a mano del texto de cada norma; las vacaciones de CyL ("al término de las actividades del día X … comenzarán el día Y") se pasan a (X+1, Y-1). Prioridad: vacaciones > fin de semana > festivo > no lectivo puntual > lectivo | No incluye fiestas locales de cada municipio ni los días sustitutivos que fija cada centro. En Asturias 2021-22 ESO/Bach empezaba y terminaba en otras fechas (no se usan). El curso 2027-28 no está publicado: NaN desde el 2027-09-01 |
| vacaciones_escolares_ast / _mad / _cyl | `periodo_escolar_*` ∈ {vacaciones_navidad, vacaciones_semana_santa, verano} | bool (nullable); NaN desde 2027-09-01 | idem | — | Los fines de semana dentro de las vacaciones cuentan como vacaciones |
| no_lectivo_ast / _mad / _cyl | Cualquier día sin clase (`periodo_escolar_*` ≠ lectivo) | bool (nullable) | idem | — | idem |
| escolar_verificado_ast / _mad / _cyl | False si el dato no sale de la norma publicada en boletín | bool | — | **False** en Asturias del 2022-01-01 al 2022-09-11 (curso 2021-22 tomado del calendario gráfico de Educastur, porque el BOPA de 1-jun-2021 no se obtuvo, y verano 2022 que depende de él) y en las tres comunidades del 2027-07-01 al 2027-08-31 (se supone que el curso 2027-28 no empieza antes del 1-sep) | — |
| escolar_fuente_ast / _mad / _cyl | Documento y apartados usados | texto | — | — | — |
| lagos_regulado | Día con acceso regulado a los Lagos de Covadonga (carretera CO-04 cerrada a vehículos particulares) según lo **planificado** | bool (nullable); NaN en 2027 | Resolución anual de la DGT en el BOE (anexo, fila "Covadonga CO-04"): BOE-A-2022-1125, 2023-2159, 2024-1773, 2025-1329, 2026-1255 | Transcrito a mano; "fines de semana del mes" expandido a sábados y domingos; excepciones (25-VII, 8-IX, 6-VI-2026) aplicadas; 2025 "12-30 abr" y "26-30 abr" se solapan en el propio BOE (unión). 2024 y 2025 revisados sobre la imagen del PDF | No recoge cortes ni suspensiones excepcionales; 2027 sin resolución publicada |
| lagos_regulado_fuente | "oficial: BOE-A-…" | texto; NaN en 2027 | — | Rellena también los días no regulados de 2022-2026 (la lista del BOE es completa para el año) | — |
| lagos_horario | Horario de la restricción | texto ("08:00-21:00", "00:00-24:00"…); NaN si no regulado | BOE | 2022: 08:00-21:00 (9-abr a 30-sep) y 08:00-19:00 (oct-dic); 2023: 07:30-21:00 / 07:30-19:00; 2024-2026: 00:00-24:00. 24-VII-2025 y 24-VII-2026: "salvo la tarde" | — |
| lagos_incidencia | Incidencia excepcional: `cierre_co4_particulares_ampliado` (2023-08-03 a 2023-08-31) o `suspension_transporte_publico_incendio` (2025-08-16 a 2025-08-18) | texto; NaN si no hay | **Solo prensa** (NO OFICIAL) | — | Fechas de fin aproximadas: 2023 "hasta el mes de septiembre"; 2025 "hasta el próximo lunes, día 18" (no consta si el 18 se incluye). No usar sin revisar |
| lagos_incidencia_fuente | Medio, fecha y cita | texto | prensa | — | — |
| lagos_incidencia_verificado | Siempre False donde hay incidencia | bool (nullable) | — | — | — |
| n_concejos_fiesta_local | Nº de concejos de Asturias con fiesta local ese día | entero (0 si ninguno) | BOPA (`festivos_locales.parquet`) | 0 = ningún concejo (no es un valor ausente) | Las fiestas locales con ámbito parcial (parroquias) cuentan igual |

### `data/clean/festivos_locales.parquet`

Fiestas locales de los 78 concejos de Asturias, 2022-2027 (1024 filas). Clave: `fecha`, `concejo`, `nombre`.

| Columna | Significado | Unidad / tipo | Fuente | Tratamiento | Limitaciones |
|---|---|---|---|---|---|
| fecha | Día de la fiesta local | datetime64 | BOPA, calendario anual de fiestas locales | Extraída del PDF: tabla (`find_tables`) en 2023 y 2025-2027, posición del texto en 2022 y 2024 | Correcciones posteriores no descargadas: BOPA 30-nov-2021 (corrección de 2022) y Res. 4-abr-2025 (Vegadeo 6-jun → 9-jun en 2025) — **no aplicadas** |
| anio | Año | entero | — | — | — |
| concejo | Concejo, con el nombre de la resolución de 2022 (mayúsculas/minúsculas y tildes; p. ej. "Cangas de Onís") | texto | BOPA | Años en mayúsculas emparejados sin tildes ni espacios; 78 por año (comprobado) | — |
| nombre | Denominación de la fiesta, tal cual el BOPA (incluye el ámbito: "… en La Espina", "excepto Posada y Nueva") | texto; NaN si la celda del BOPA está vacía (60 filas, ≈ 6 %) | BOPA | Espacios normalizados | Algunos concejos tienen 3-6 fechas porque cada parroquia tiene las suyas; no hay columna de ámbito estructurada |
| fuente | Código BOPA | texto | — | — | — |
| pagina | Página del PDF | entero | — | — | — |
| metodo_extraccion | `tabla_pdf` o `posicion_texto` | texto | — | — | — |
| dia_semana_coherente | Si el nombre empieza por un día de la semana ("Lunes, …"), ¿coincide con la fecha? | bool (nullable; NaN si el nombre no nombra un día) | derivado | **No se corrige el dato** | 2 erratas del BOPA: Grado 2022-07-26 ("Lunes", fue martes) y Pravia 2024-09-06 ("Miércoles", fue viernes) |

### Ficheros auxiliares

- `data/clean/festivos_autonomicos.csv`: filas del BOE con marca en AST, MAD o CYL antes de expandir (fecha, nombre, nº de comunidades con marca, marca por comunidad, fuente).
- `data/clean/vacaciones_escolares_periodos.csv`: periodos fuente por comunidad y curso (inicio y fin lectivo, Navidad, Semana Santa, no lectivos puntuales) con su referencia y `verificado`.
- `data/clean/lagos_folleto_transcripcion.csv`: transcripción manual del folleto de imagen de Turismo Cangas de Onís (año inferido 2024, `verificado=False`). No se usa en `lagos_regulado`.
- `data/clean/_qc/semana_santa_comprobacion.csv`: cálculo de Pascua frente al BOE.


**Fiestas parciales (decisión del equipo: cuentan como fiesta de todo el concejo, pero se marcan).** Algunas fiestas solo afectan a parte del concejo: en Llanes, «San Jorge en Nueva y Valle de San Jorge» o «La Magdalena (excepto Posada y Nueva)»; en Candamo, «sólo en San Román». Por eso Llanes tiene unas 6 fiestas al año. Hay dos columnas, que calcula `ambito_festivo()` en `limpia_calendario.py` a partir del texto del BOPA:

| Columna | Significado | Tipo | Regla |
|---|---|---|---|
| `ambito` | Ámbito de la fiesta según el texto | texto: `concejo` (798), `parcial` (157), `dudoso_villa_o_concejo` (9), `sin_nombre` (60) | `parcial`: «excepto/salvo», «sólo/solamente/exclusivamente», «parroquia(s)» o «en <lugar>». `concejo`: sin lugar, o «en todo el concejo/municipio», «y (resto del) Concejo», «para todo el Término» (sin «excepto»). `dudoso_villa_o_concejo`: «en <el propio concejo>» («Festividad del Bollo en Salas», «San Roque en Navia», «Virgen de Loreto en Colunga»), que puede ser la villa o todo el concejo. |
| `festivo_parcial` | La fiesta es solo de una parte del concejo | bool nullable | True si `parcial`; False si `concejo`; NA si dudosa o sin nombre. Revisada a mano sobre la lista completa de nombres; la regla es textual y no está contrastada parroquia a parroquia. |

## 4. Eventos

Script: `python -X utf8 src/limpieza_B/limpia_eventos.py`. Entrada: `data/manual/eventos_recopilado.csv` (378 filas, sin modificar). Comprobaciones automáticas: 378 filas de entrada; estados ∈ {verificado, probable, no_encontrado}; `fuente_tipo` ∈ {oficial, secundaria, prensa}; ninguna fila sin `fuente_url`; `fecha_fin ≥ fecha_ini`; solo las `no_encontrado` carecen de fecha; sin duplicados por (fecha, concejo, evento); nº de filas expandidas = Σ(duración × nº de concejos); cruceros solo en 2025-2026 y todos previsión; horas en formato HH:MM; capacidad de crucero en 1-10 000.

### 4.1 `data/clean/eventos_diario.parquet`: una fila por `fecha`, `concejo` y `evento`

674 filas, 2021-08-15 → 2027-06-06. Las 4 filas `no_encontrado` (cruceros 2022, 2023, 2024 y Copa del Rey) **no se expanden** porque no tienen fecha y no se inventa ninguna: van a `data/clean/eventos_sin_fecha.csv`.

| Columna | Significado | Unidad / tipo | Fuente | Tratamiento | Limitaciones |
|---|---|---|---|---|---|
| `fecha` | Día del evento | fecha | CSV manual | Expansión de `fecha_ini..fecha_fin` (ambos incluidos) | Rango según la convención de la fase 1: inicio oficial → último acto del programa (San Mateo 2025 termina el 28-sep) |
| `concejo` | Concejo donde se celebra | texto | CSV manual | "Cangas de Onis" → "Cangas de Onís". Los eventos con varios concejos (`Parres;Ribadesella`, Sella) se duplican: una fila por concejo | La zona MITMA se asigna después (`config/mapeo_zonas.csv`) |
| `evento` | Nombre del evento | texto | CSV manual | Partidos: "club local - rival" con nombres de club normalizados (ver `club_local`/`rival`) | — |
| `tipo` | partido_futbol, crucero_gijon, fiesta, festival, deportivo, romeria, feria | categoría | CSV manual | Sin cambios | — |
| `dia_evento` / `n_dias_evento` | Día ordinal dentro del evento (1..n) y duración total | entero (días) | Derivado | — | No marca el "día grande" (p. ej. la prueba del Sella es el último día; está en `notas`) |
| `fecha_ini`, `fecha_fin`, `hora_ini`, `lugar` | Los del CSV de origen | fecha / HH:MM / texto | CSV manual | Sin cambios | `hora_ini` solo en partidos y algunos cruceros |
| `evento_multiconcejo`, `concejos_evento` | Si el evento abarca varios concejos y la lista original | bool / texto | Derivado | — | Al agregar por zona, no sumar el mismo evento dos veces si los dos concejos caen en la misma zona |
| `estado` | verificado / probable | categoría | CSV manual | Sin cambios. **Calidad de la fecha**: usar como columna de calidad, no para filtrar sin decidirlo | 89,7 % de las filas del CSV son `probable` (la mayoría partidos y cruceros) |
| `fuente_tipo`, `fuente_url` | Tipo de fuente (oficial/secundaria/prensa) y URL | texto | CSV manual | Sin cambios | ≈100 ficheros en bruto sin URL exacta en el registro (auditoría) |
| `aforo` | Aforo del evento | personas | CSV manual (`aforo_o_pasajeros`) | Separado de la capacidad de crucero | **Vacío en todos los eventos**: no se recopiló |
| `pasajeros_capacidad` | Capacidad máxima declarada del buque | pasajeros | PDF de previsión de escalas (Autoridad Portuaria / Gijón Turismo) | Separada de `aforo` | Es la capacidad, **no** los pasajeros reales |
| `es_prevision` | La escala es una previsión, no una escala realizada | bool (NA fuera de cruceros) | Notas del CSV ("Previsión de escalas…") | True en las 89 escalas (2025: 39, 2026: 50); el script falla si alguna no lo es | Ver nota de cruceros |
| `competicion`, `temporada` | Competición y temporada (AAAA-AA) | texto | CSV manual | `temporada` extraída de `competicion` | — |
| `club_local`, `rival` | Clubes normalizados (Real Oviedo, Real Sporting de Gijón; rivales sin "SAD"/"Club de Fútbol" y con tildes) | texto | Derivado de `evento` | Diccionario `CLUBS` del script | — |
| `partido_oviedo`, `partido_sporting` | Partido en casa de ese club ese día | bool | Derivado | False en filas que no son partidos | Solo liga; **Copa del Rey y promociones no recopiladas** |
| `derbi_asturiano` | Real Oviedo – Real Sporting de Gijón | bool | Derivado | — | — |
| `hora_partido` | Hora de inicio (hora de Madrid) | HH:MM o NaN | football-data (+1 h) / laliga.com | NaN si no hay hora: son los 29 partidos de 2026-27 sin día/hora fijados | Partidos 2021-22..2025-26 contrastados solo por muestra (7/7 + 1) con LaLiga |
| `categoria_temporada` | Primera / Segunda | categoría | Derivado de `competicion` | — | Primera solo para el Real Oviedo en 2025-26 |
| `calendario_confirmado` | False si la nota dice "calendario no confirmado" (LaLiga solo da la jornada) | bool (NA fuera de partidos) | Notas del CSV | — | 29 partidos 2026-27: la fecha es la de la jornada y puede cambiar |
| `nota_calidad` | Aviso de calidad añadido en la limpieza | texto | Notas de la fase B | Solo FIDMA 2025: discrepancia 1-ago (festivalesdeespana) frente a 2-ago (Diario de León, asturias.com). **La fecha no se cambia** (queda `probable`, 1-17 ago) | — |
| `notas` | Notas del CSV de origen | texto | CSV manual | Sin cambios | Texto libre |
| `id_evento_original` | Nº de línea en el CSV manual (cabecera = 1) | entero | Derivado | Para trazar cada fila a su origen | — |

**Cruceros (importante).** Solo hay escalas con fecha para **2025 (39) y 2026 (50)**, y **todas son previsiones** de los PDF oficiales (`es_prevision=True`), no escalas realizadas. `pasajeros_capacidad` es la capacidad declarada del buque, no los pasajeros reales. **2022, 2023 y 2024: no hay datos** (filas `no_encontrado` en `eventos_sin_fecha.csv`; solicitud a la Autoridad Portuaria redactada en `notas/fuentes/eventos/solicitud_cruceros.md`, sin enviar). Como el objetivo de movilidad cubre 2022 a jun-2025, **las columnas de cruceros no se deben usar para entrenar**: en ese periodo serían cero por falta de dato, no por ausencia de cruceros. Solo sirven como contexto o en producción, una vez existan escalas realizadas para entrenar. Además, la previsión no coincide con la realidad: la prensa cuenta 15 buques de enero a julio de 2025 y el PDF lista 17.

### 4.2 `data/clean/partidos_diario.parquet`: una fila por `fecha` (2021-08-15 → 2027-06-06, 2122 días)

Tabla derivada, sin huecos de fecha, para unir por día. Fuera de ese rango no hay dato (NaN al unir). Dentro del rango, un día sin partido es `False` (el calendario de liga está completo: 124 partidos en casa del Oviedo y 126 del Sporting; 10 derbis).

| Columna | Significado | Tratamiento / limitaciones |
|---|---|---|
| `fecha`, `temporada` | Día y temporada (julio-junio) | — |
| `partido_oviedo` / `partido_sporting` | Partido de liga en casa ese día | Copa del Rey no recopilada |
| `hora_partido_<club>`, `rival_<club>`, `estado_partido_<club>`, `calendario_confirmado_<club>` | Datos del partido ese día | NaN si no hay partido |
| `categoria_temporada_<club>` | Categoría del club en la temporada del día (también en días sin partido) | Deducida de la competición en la que juega el club ese año |
| `derbi_asturiano` | Hay derbi ese día | — |
| `fuente` | football-data.co.uk (2021-22..2025-26), laliga.com (2026-27) | — |

## 5. Señales de interés

Script: `python -X utf8 src/limpieza_B/limpia_senales.py`.

### 5.1 `data/clean/wikipedia_diario.parquet`: una fila por `fecha` y `articulo`

20 artículos × 1748 días (2022-01-01 → 2026-10-14) = 34 960 filas, sin huecos.

**Regla de días ausentes.** La sonda (`data/raw/wikipedia_sonda_dias_ausentes.json`, comprobada por el script) muestra que la API (a) da 404 si un título no tiene datos en todo el rango y (b) **omite los días sin registro** cuando hay datos parciales (Lago de la Ercina: 296 de 365 días en 2022). Los días omitidos de un artículo que existe se rellenan con **0 visitas** y se marcan `visitas_imputado=True`: 631 días (630 en `covadonga_fr`, 1 en `parque_nacional_de_los_picos_de_europa`, el 2022-03-17); los otros 18 artículos están completos. El cero explícito de la API (`visitas_api == 0`: 405 días en `covadonga_fr`, 7 en el parque nacional) **no** es imputado. **[NO VERIFICADO]** que un día omitido signifique exactamente 0 visitas de usuario (hipótesis razonable: el artículo existe y se consulta poco; la documentación no lo aclara). Si se prefiere tratarlo como desconocido, basta con usar `visitas_api` (NaN en esos días).

| Columna | Significado | Unidad | Fuente | Tratamiento | Limitaciones |
|---|---|---|---|---|---|
| `fecha` | Día (UTC según la API) | fecha | API Wikimedia | `timestamp[:8]` | Día en UTC, no en hora local **[NO VERIFICADO]** |
| `articulo` | Identificador estable = nombre de fichero sin `wikipedia_` (p. ej. `covadonga_fr`) | texto | — | — | — |
| `proyecto`, `titulo` | Wikipedia (es/en/fr) y título exacto consultado | texto | `meta` | — | Las visitas por redirecciones no se suman **[NO VERIFICADO]** |
| `visitas` | Visitas de usuarios (agent=user, all-access) | visitas/día | API | Días omitidos = 0 (imputado) | Incluye tráfico automático no filtrado (ver anomalía) |
| `visitas_api` | Valor tal cual de la API (NaN si el día se omitió) | visitas/día | API | — | — |
| `visitas_imputado` | El valor de `visitas` es un 0 imputado | bool | Derivado | — | — |
| `visitas_media7_ant` | **Variable para el modelo** (decisión del equipo): media de `visitas` de los 7 días anteriores (d-7…d-1), **sin el propio día** | visitas/día | Derivado | NaN los primeros 7 días (ventana incompleta). Los 0 imputados cuentan como 0 | Comprobado en el script: no usa el día d. Incluye el pico anómalo del 2023-09-17 en los 7 días siguientes |
| `media7_ant_n_imputados` | Cuántos de esos 7 días son 0 imputados | 0–7 | Derivado | — | Útil para descartar la media en artículos pequeños (`covadonga_fr`) |
| `mediana_movil_29d` | Mediana móvil centrada de 29 días (mín. 15) | visitas/día | Derivado | Recortada a ≥1 | Usa días futuros (centrada): **solo para marcar, no como característica** |
| `pico` | visitas > 10 × mediana móvil y ≥ 500 | bool | Derivado | 14 días | Muchos picos son reales (días del Sella, 2024-09-03 en varios artículos): son señal, no error |
| `posible_anomalia` | visitas > 50 × mediana móvil y ≥ 500 | bool | Derivado | 1 día: `picos_de_europa` 2023-09-17 (61 525 visitas, mediana ≈259) | Causa **[NO VERIFICADA]** (mismo día que el 100 de Trends "picos de europa"). No se borra; conviene excluirlo o recortarlo antes de usarlo |
| `fuente` | "Wikimedia REST API pageviews per-article (agent=user, all-access)" | texto | — | — | — |

### 5.2 `data/clean/oapn_anual.csv`: visitantes anuales del Parque Nacional de los Picos de Europa (solo contexto)

11 filas (2015-2025). **No es variable diaria: solo sirve de contexto o para comprobar el orden de magnitud.**

| Columna | Significado | Tratamiento / limitaciones |
|---|---|---|
| `anio`, `parque` | Año y parque (Picos de Europa) | — |
| `visitantes` | Visitantes anuales (personas) | Extraídos por el script del texto del PDF: 2022-2025 de la frase del informe de visitantes (págs. 4, 5, 5 y 7); 2015-2021 de la tabla "Visitas anuales" (Ilustración 27) de la memoria 2021, pág. 129. Mezcla de conteos y estimaciones, con metodología propia de cada parque |
| `documento`, `pagina`, `localizacion` | PDF de `data/raw/oapn/`, página (1 = primera) y dónde está la cifra | — |
| `referencia_notas` | Cifra de `notas/fuentes/senales/notas_senales.md` | — |
| `verificado` | Lo extraído coincide con la referencia | **11/11 True**. 2022-2025 no se compararon con la tabla del informe (solo la frase) |
| `fuente`, `uso` | OAPN/MITECO; `solo_contexto` | Datos mensuales solo en gráficos de porcentaje (no extraídos); se piden a seguimiento@oapn.es |

### 5.3 Google Trends: `trends_semanal.parquet` (fiables) y `trends_semanal_no_fiable.parquet`

Series semanales (251 semanas, 2021-12-26 → 2026-10-11, con la semana que empieza en domingo). Cada fila es una semana de un término en una consulta de dos términos (ancla + término). **No se tocó el ancla ni se repitió ninguna consulta.** No hay CSV manuales en `data/raw/trends/ancla_cabrales/manual/` (el script los incluiría si aparecen).

- `trends_semanal.parquet`: 3 series, 753 filas, ancla **"cabrales"**, España (lagos de covadonga, llanes, cangas de onís), sin semanas a cero. `fiable=True`, con salvedades.
- `trends_semanal_no_fiable.parquet`: 9 series, 2259 filas, ancla **"picos de europa"** (ES y ES-MD). `fiable=False`: el ancla tiene un único 100 (semana del 2023-09-17) y mediana 3, y aplasta el otro término a 0-4 (cangas de onís ES-MD con 137 semanas a cero, ruta del cares con 76-84). **No usar.**

| Columna | Significado | Tratamiento / limitaciones |
|---|---|---|
| `semana_inicio` | Domingo de inicio de la semana | — |
| `termino`, `geo`, `ancla` | Término consultado, región (ES, ES-MD) y término de anclaje | — |
| `valor`, `valor_ancla` | Índice relativo 0-100 del término y del ancla **dentro de esa consulta** | Solo comparable dentro de la misma consulta. La muestra de Google cambia entre descargas **[NO VERIFICADO el tamaño del efecto]** |
| `termino_sobre_ancla` | `valor / valor_ancla` (NaN si el ancla vale 0) | Permite comparar términos de consultas distintas que comparten ancla; ruidoso cuando el ancla es baja |
| `is_partial` | Semana incompleta (la última, 2026-10-11) | No usar esa semana como dato definitivo |
| `fichero`, `origen`, `timeframe`, `descargado_utc` | Trazabilidad (pytrends o csv_manual) | — |
| `fiable`, `motivo` | Fiabilidad de la serie y por qué | "cabrales" es también un queso: sirve solo de escala, no como señal turística |
| `fuente` | Google Trends vía pytrends (no oficial) | Faltan 17 consultas con ancla cabrales (ES ruta del cares y covadonga, y ES-MD/ES-CL/ES-AS) y todas las ventanas diarias. Granularidad semanal. **Decisión del equipo:** no se pasa a diario ni se hacen las 17 consultas que faltan; se usa como variable semanal con una semana de retraso (ver `factores_B`). |


## 6. Cruce con las zonas del MITMA

### `config/mapeo_zonas.csv`

Hay una fila por zona MITMA de Asturias: **46 zonas** que cubren los 78 concejos (13 son agrupaciones de concejos, con sufijo `_AM`). `zona_mitma_id` está relleno desde `data/raw/zonas_mitma_asturias.csv`; `unir_B.py` se niega a ejecutarse si alguna fila no lo tiene. La ampliación de 5 a 46 zonas se explica en `notas/ampliacion_zonas.md`.

| Columna | Significado | Estado |
|---|---|---|
| `zona_mitma_id` | Identificador de zona MITMA | Relleno (46 zonas). |
| `nombre` | Nombre legible | Las zonas de 3 o más concejos se llaman «<concejo de más superficie> y N más». |
| `concejos_ine` | Código(s) INE de los concejos de la zona, separados por `;` | Salen de `data/raw/zonas_mitma_asturias.csv` (relación oficial INE-MITMA). |
| `zona_meteo` | Punto principal de `openmeteo_diario` (en Cangas de Onís, el **valle**: `cangas_de_onis`) | Las 41 zonas añadidas usan el punto de valle o ciudad más cercano (aproximación; hasta unos 90 km en el occidente). |
| `zona_meteo_montana` | Segundo punto, opcional: **montaña** (`lagos_enol`). Decisión del equipo, solo para la zona de Cangas de Onís, que ahora incluye Covadonga y Lagos | Vacío en el resto. |
| `estacion_aemet` | Indicativo de `aemet_diario` (solo las 5 zonas iniciales; el modelo no usa AEMET como variable) | Regla del equipo: la más cercana con mejor cobertura y, en empate, la preferida (Ribadesella → 1183X, Gijón → 1207U). La aplica `src/limpieza_B/elige_estaciones.py`; el detalle está en `notas/fuentes/aemet/eleccion_estaciones.md`. |
| `concejo_eventos` | Concejo(s), separados por `;`, para los eventos y las fiestas locales | Se cruza sin tildes ni mayúsculas y solo con la parte en castellano («Gijón/Xixón» → «gijon»). |
| `notas` | Observaciones por zona | |

| `lat`, `lon` | Centroide de los concejos de la zona, ponderado por área | Lo usa `src/modelo/web_salidas.py` para las distancias entre zonas. |

`config/mapeo_zonas_ejemplo.csv` usa IDs **ficticios** (`EJEMPLO_*`) y solo sirve para probar la unión.

### `data/clean/factores_B_diario.parquet` (lo genera `src/limpieza_B/unir_B.py`)

Hay una fila por `fecha` y `zona_mitma_id`. El rango por defecto va del 2022-01-01 al último día de Open-Meteo; se cambia con `--desde` y `--hasta`. Con el mapeo actual tiene 80 454 filas (46 zonas). La prueba con el mapeo de ejemplo se guarda en `data/clean/_prueba/factores_B_ejemplo.parquet`.

| Grupo de columnas | Origen | Regla de unión |
|---|---|---|
| `zona_meteo`, `zona_meteo_montana`, `estacion_aemet` | mapeo | |
| Columnas del calendario (sin prefijo) | `calendario_diario` | Por `fecha`. |
| `festivo_local`, `festivo_local_nombre` | `festivos_locales` | Hay fiesta en algún concejo de `concejo_eventos`; las parciales cuentan. Si no hay fila, vale False. |
| `festivo_local_parcial` | `festivos_locales` | True si todas las fiestas del día en la zona son parciales; False si alguna es de todo el concejo o si no hay fiesta; NA si solo hay fiestas de ámbito dudoso o sin nombre. |
| `om_*` | `openmeteo_diario` | Por (`fecha`, `zona_meteo`). Incluye `om_es_reanalisis` y `om_*_prevN`. |
| `aemet_*` | `aemet_diario` | Por (`fecha`, `estacion_aemet`). No incluye las horas de los extremos ni los códigos crudos. Si la zona no tiene estación, todo es NaN. |
| `ev_n`, `ev_n_verificado`, `ev_<tipo>` | `eventos_diario` | Eventos en los concejos de la zona. Un evento presente en dos concejos de la misma zona cuenta una vez. Sin evento: 0 o False (no es un dato ausente). |
| `crucero_pasajeros_prevision` | `eventos_diario` (cruceros) | Suma de la capacidad de los buques. **Es previsión: no usar para entrenar.** |
| `futbol_*` | `partidos_diario` | Por `fecha`, igual para todas las zonas (los partidos atraen público de toda Asturias). Fuera del rango de temporadas, NaN. |
| `om_montana_*` | `openmeteo_diario` | Por (`fecha`, `zona_meteo_montana`): las mismas variables que `om_*`, del punto de montaña. NaN en las zonas sin él. |
| `wiki_<articulo>_media7_ant` | `wikipedia_diario` | Por `fecha`, igual para todas las zonas: `visitas_media7_ant`. **No entran las visitas del mismo día**, que siguen en `wikipedia_diario` para análisis. |
| `trends_<termino>_<geo>_sem_ant` | `trends_semanal` (solo `fiable`) | Valor de la **semana completa anterior** a la del día. Las semanas de Trends empiezan en domingo y la anterior se conoce el sábado previo. Se excluyen las semanas parciales. NaN el 2022-01-01, porque no hay una semana anterior descargada. |

No entran en la unión: ERA5, la previsión de ejemplo, OAPN anual y Trends no fiable.

Comprobaciones automáticas de `unir_B`:
- filas = n_fechas × n_zonas;
- sin duplicados de (`fecha`, `zona_mitma_id`);
- todas las fechas presentes en cada zona;
- uniones `many_to_one` o `one_to_one` validadas por pandas;
- cada `zona_meteo` y `estacion_aemet` del mapeo existe en las tablas.

Pruebas: `src/limpieza_B/test_unir_B.py` (datos sintéticos) y la prueba real con el mapeo de ejemplo dentro de `ejecutar_todo.py`.
