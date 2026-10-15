# Registro Open-Meteo

Script: `src/descarga_openmeteo.py` (reanudable; zonas en `config/zonas_meteo.csv`).
Estado a 2026-10-15: descarga **parcial** (ver tabla). La tabla se regenera sola al terminar el script.

## Condiciones de uso (fuente: open-meteo.com/en/pricing y /en/docs, consultadas 2026-10-15)

- Uso gratuito **solo no comercial**. El uso comercial exige plan de pago y clave. Para un hackathon es válido; si la app pasase a un uso comercial real habría que contratar plan o autoalojar.
- Licencia de los datos CC BY 4.0: hay que citar a Open-Meteo (y ERA5/Copernicus y los modelos de origen) e indicar si se modifican.
- Límites gratuitos publicados: 600 llamadas/min, 5.000/hora, 10.000/día, 300.000/mes. Una petición con más de 10 variables o más de 2 semanas cuenta como varias llamadas (ej.: 4 semanas = 3,0 llamadas). Sin garantía de disponibilidad.
- **Observado:** una petición de un año con 24 variables horarias (Previous Runs) pesa mucho y agotó la cuota *horaria* a mitad de la descarga (`Hourly API request limit exceeded`). El script espera 6 s entre llamadas y, ante un 429 horario, 30 min.

## Qué es cada serie

| Serie | Qué contiene | Desde |
|---|---|---|
| Historical Forecast (`historical-forecast-api`) | Serie continua con las primeras horas de cada ejecución del modelo. Diaria disponible. | 2022-01-01 (Covadonga, sin nulos) |
| Previous Runs (`previous-runs-api`) | Valor previsto N días antes (`_previous_dayN`, N=1..7). **Solo horaria** (pedir `daily=..._previous_day1` da error); hay que agregar a diario después. | Ver abajo |
| Archive (`archive-api`, ERA5) | Meteorología realmente ocurrida (reanálisis). Solo contraste. | ≥ 2022-01-01 |

Previous Runs: la doc dice «la mayoría de modelos desde enero de 2024». En Covadonga el día 0 (`temperature_2m`, etc.) existe desde 2024-01-01 00:00, pero `_previous_day1` solo desde **2024-01-19 14:00**, `_day2` desde 01-20 14:00 y `_day3` desde 01-21 14:00 (todas las variables). **Útil sin huecos desde 2024-01-22.** Después de esa fecha no hay nulos en las variables de Covadonga.

## Hallazgos (Covadonga, 43.31 N, -5.05 E)

1. **Cambio de modelo en `best_match`.** Comparando día a día con modelos concretos (`models=`):
   - Desde **2022-11-10** `best_match` coincide exactamente con `meteofrance_seamless` (ARPEGE/AROME) en temperatura máxima y precipitación (100 % de días hasta 2025-06-30).
   - Antes de esa fecha no coincide con Météo-France, ICON ni ECMWF; solo con GFS en ~35 % de los días. El modelo de ese tramo **no está identificado** (no verificado).
   - La API no devuelve qué modelo se usó: esto es una inferencia por coincidencia de valores, no un dato oficial.
2. **Antes de 2022-11-10 la «previsión» no parece una previsión.** En esos 313 días, `precipitation_sum`, `precipitation_hours`, `weather_code`, viento y rachas son prácticamente idénticos a ERA5 (312-313 de 313 días exactos). La temperatura y las horas de sol sí difieren (error medio absoluto 1,4 °C en Tmax). Es decir, ese tramo se parece a la meteorología ocurrida, no a lo que se sabía de antemano → riesgo de fuga de información y de distribución distinta a producción. Causa no verificada (hipótesis: relleno con reanálisis donde no hay archivo de previsiones).
3. **Resolución y elevación.** Covadonga: `elevation` 278 m (Covadonga real ≈ 260 m, ok). Lagos de Enol: `elevation` 1070 m en el JSON (coherente con el lago, ≈1.070 m). Ese valor es la elevación del punto que usa Open-Meteo para ajustar la temperatura; la orografía real del modelo (celda de varios km) es más suave y no representa bien los Picos (>2.000 m cerca). Se espera sesgo en temperatura y sobre todo en precipitación y viento en los Lagos (no cuantificado: falta comparar con AEMET).
4. **Contraste con ERA5** (Covadonga, 2022-01-01 → 2026-10-15, 1.749 días, previsión − ERA5):
   - Tmax: sesgo medio **+0,09 °C**, error absoluto medio 1,27 °C. Solo tramo ≥ 2022-11-10: +0,37 °C / 1,24 °C. Tramo anterior: −1,17 °C / 1,41 °C.
   - Precipitación diaria: sesgo medio **−0,79 mm/día** (media prev. 3,5 vs ERA5 4,29 mm), error absoluto medio 2,0 mm, correlación 0,81. Solo ≥ 2022-11-10: −0,96 mm / 2,43 mm. La previsión sub-estima la lluvia respecto al reanálisis.
   - La rejilla ERA5 que devuelve la Archive API para el punto es 43,339 / -5,120 (no coincide con la pedida; ~0,03° de diferencia). Comparación con AEMET pendiente.
5. Sin nulos en Historical Forecast ni en ERA5 en Covadonga (2022-01-01 → 2026-10-15). Esa última fecha es el día de la descarga: el valor del día en curso puede estar incompleto/provisional (no verificado).
6. `utc_offset_seconds` y `timezone_abbreviation` del JSON reflejan el horario actual (GMT+2, verano), no el de cada fecha; las fechas diarias sí están en hora local de Madrid.

## Recomendación provisional para entrenar (a confirmar antes de limpiar)

- **Previous Runs día 1 (y 2-3 como alternativa), desde 2024-01-22**: es lo más fiel a producción (lo que se sabía 1-3 días antes) y no tiene fuga. Inconveniente: solo ~2,7 años y requiere agregar horario → diario.
- **Historical Forecast desde 2022-11-10** como serie larga, aceptando que son las primeras horas de cada pasada (más precisa que una previsión a 1-3 días, por tanto algo optimista).
- **Descartar o marcar** el tramo 2022-01-01 → 2022-11-09 de Historical Forecast (parece reanálisis y modelo distinto).
- ERA5 solo como contraste, nunca como entrada de entrenamiento.
- Variable de modelo: considerar una variable indicadora del tramo (cambio de modelo) si se usa antes de 2023.

## Decisiones pendientes

1. ¿Entrenar con Previous Runs (2024-01-22 →) o con Historical Forecast (2022-11-10 →) o con ambas (validación cruzada de la diferencia)?
2. ¿Cómo agregar horario → diario en Previous Runs (suma de precipitación, máx. de temperatura y rachas, suma de sol) y con qué zona horaria (hoy se pide `Europe/Madrid`)?
3. Lista definitiva de zonas (el CSV es provisional, ver abajo).
4. Para los Lagos: aceptar el sesgo orográfico o corregirlo con estaciones AEMET.

## Coordenadas (`config/zonas_meteo.csv`, todas `provisional=si`)

Contraste con la API de geocodificación de Open-Meteo (2026-10-15):

| Zona | Pedida | Geocodificación | Estado |
|---|---|---|---|
| cangas_de_onis | 43,35 / -5,13 | 43,3514 / -5,1292 | verificada |
| llanes | 43,42 / -4,75 | 43,4198 / -4,7549 | verificada |
| ribadesella | 43,46 / -5,06 | 43,4615 / -5,0596 | verificada |
| gijon | 43,53 / -5,66 | 43,5357 / -5,6615 | verificada |
| oviedo | 43,36 / -5,86 | 43,3603 / -5,8448 | verificada (≈0,015° de diferencia) |
| madrid | 40,42 / -3,70 | 40,4165 / -3,7026 | verificada |
| sevilla | 37,39 / -5,98 | 37,3828 / -5,9732 | verificada |
| covadonga | 43,31 / -5,05 | sin resultado en Asturias (devuelve Covadonga de México) | **no verificada por API** |
| lagos_enol | 43,27 / -4,99 | sin resultado ("Lago Enol", "Lagos de Covadonga") | **no verificada por API**; elevación 1070 m coherente con los Lagos |

## Pendiente / no verificado

- Descarga completa de las 9 zonas, Previous Runs y ERA5 de Cangas de Onís, previsión en vivo (`openmeteo_prevision_ejemplo.json`): ver tabla.
- Modelo usado antes de 2022-11-10; si hay más cambios de modelo posteriores a 2025-06-30 (solo se comparó hasta esa fecha).
- Si Previous Runs también cambia de modelo entre 2024 y 2026.
- Nota: `data/raw/_chunks/` (respuestas por tramo) no se sube al repo (duplica los JSON finales); solo su `manifest.json`.

## Ficheros descargados

<!-- TABLA:INICIO -->
| Fichero | Endpoint | Descargado | Rango real | N reg. | Nulos por variable | Incidencias |
|---|---|---|---|---|---|---|
| `openmeteo_archive_covadonga.json` | archive-api.open-meteo.com | 2026-10-15 | 2022-01-01 → 2026-10-15 | 1749 | temperature_2m_max=0, temperature_2m_min=0, precipitation_sum=0, precipitation_hours=0, sunshine_duration=0, wind_speed_10m_max=0, wind_gusts_10m_max=0, weather_code=0 | ver notas |
| `openmeteo_covadonga.json` | historical-forecast-api.open-meteo.com | 2026-10-15 | 2022-01-01 → 2026-10-15 | 1749 | temperature_2m_max=0, temperature_2m_min=0, precipitation_sum=0, precipitation_hours=0, sunshine_duration=0, wind_speed_10m_max=0, wind_gusts_10m_max=0, weather_code=0 | ver notas |
| `openmeteo_lagos_enol.json` | historical-forecast-api.open-meteo.com | 2026-10-15 | 2022-01-01 → 2026-10-15 | 1749 | temperature_2m_max=0, temperature_2m_min=0, precipitation_sum=0, precipitation_hours=0, sunshine_duration=0, wind_speed_10m_max=0, wind_gusts_10m_max=0, weather_code=0 | ver notas |
| `openmeteo_previous_covadonga.json` | previous-runs-api.open-meteo.com | 2026-10-15 | 2024-01-01 → 2026-10-15 | 24456 | temperature_2m=0, temperature_2m_previous_day1=446, temperature_2m_previous_day2=470, temperature_2m_previous_day3=494, precipitation=0, precipitation_previous_day1=446, precipitation_previous_day2=470, precipitation_previous_day3=494, wind_speed_10m=0, wind_speed_10m_previous_day1=446, wind_speed_10m_previous_day2=470, wind_speed_10m_previous_day3=494, wind_gusts_10m=0, wind_gusts_10m_previous_day1=446, wind_gusts_10m_previous_day2=470, wind_gusts_10m_previous_day3=494, weather_code=0, weather_code_previous_day1=446, weather_code_previous_day2=470, weather_code_previous_day3=494, sunshine_duration=0, sunshine_duration_previous_day1=446, sunshine_duration_previous_day2=470, sunshine_duration_previous_day3=494 | ver notas |
| `openmeteo_previous_lagos_enol.json` | previous-runs-api.open-meteo.com | 2026-10-15 | 2024-01-01 → 2026-10-15 | 24456 | temperature_2m=0, temperature_2m_previous_day1=446, temperature_2m_previous_day2=470, temperature_2m_previous_day3=494, precipitation=0, precipitation_previous_day1=446, precipitation_previous_day2=470, precipitation_previous_day3=494, wind_speed_10m=0, wind_speed_10m_previous_day1=446, wind_speed_10m_previous_day2=470, wind_speed_10m_previous_day3=494, wind_gusts_10m=0, wind_gusts_10m_previous_day1=446, wind_gusts_10m_previous_day2=470, wind_gusts_10m_previous_day3=494, weather_code=0, weather_code_previous_day1=446, weather_code_previous_day2=470, weather_code_previous_day3=494, sunshine_duration=0, sunshine_duration_previous_day1=446, sunshine_duration_previous_day2=470, sunshine_duration_previous_day3=494 | ver notas |
<!-- TABLA:FIN -->
