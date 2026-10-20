# Contrato del objetivo: `data/clean/objetivo_diario.parquet`

Fecha: 2026-10-15. Lo genera `python -X utf8 src/modelo/construir_objetivo.py` a partir de los ficheros mensuales del MITMA. Lo consume `src/modelo/ejecutar.py --objetivo real`.

## Entradas (las prepara el equipo de demanda)

| Qué | Dónde | Formato |
|---|---|---|
| Lista de zonas MITMA de Asturias | `data/raw/zonas_mitma_asturias.csv` | CSV con `id_zona_mitma` (también se aceptan `zona_mitma_id` o `id`) y `nombre`; el resto de columnas es libre (p. ej. municipios INE que agrupa). |
| `zona_mitma_id` de cada zona del proyecto | `config/mapeo_zonas.csv` (46 zonas, rellenas) | El identificador exacto tal y como aparece en `origen`/`destino` de los ficheros. El mapeo es 1 a 1: cada zona del proyecto es una zona MITMA. |
| Viajes, 2022-01-01 → 2025-06-30 | `data/raw/mitma_viajes/AAAA-MM.csv` | Ver columnas abajo. |
| Pernoctaciones, mismo periodo | `data/raw/mitma_pernoctaciones/AAAA-MM.csv` | Ver columnas abajo. |

Formatos aceptados (se detectan por fichero; separador `|`, `,` o `;`):

| Fichero | MITMA original | spanishoddata |
|---|---|---|
| Viajes | `fecha, periodo, origen, destino, actividad_origen, actividad_destino, residencia, viajes` | `date, hour, id_origin, id_destination, activity_destination, residence_province_ine_code, n_trips` |
| Pernoctaciones | `fecha, zona_residencia, zona_pernoctacion, personas` | `date, id_residence, id_overnight_stay, n_persons` |

- `fecha`: `AAAAMMDD` o `AAAA-MM-DD`.
- `actividad_destino`: `casa`, `frecuente`, `no_frecuente`, `trabajo_estudio` (MITMA) o `home`, `frequent_activity`, `infrequent_activity`, `work_or_study` (spanishoddata). Cualquier otro valor detiene el proceso, para no clasificarlo mal sin avisar.
- `residencia`: código INE de provincia (`33` = Asturias). Un número de una cifra se completa con cero a la izquierda.
- Otras columnas (`distancia`, `renta`, `edad`…) se ignoran.

## Tabla resultante

Una fila por `fecha` × `zona_mitma_id` del mapeo, del 2022-01-01 al 2025-06-30, sin huecos de fecha.

| Columna | Tipo | Definición |
|---|---|---|
| `fecha` | datetime (día) | Día del viaje o de la pernoctación. |
| `zona_mitma_id` | texto | Zona de destino o de pernoctación. |
| `llegadas_total` | float | Suma de viajes con `destino` = zona y `origen` ≠ zona (todas las horas y actividades). |
| `llegadas_ocio` | float | Las mismas, con actividad de destino `frequent_activity` o `infrequent_activity` (sin trabajo, estudio ni casa). **Variable que predice el modelo por defecto.** |
| `llegadas_desde_asturias` | float | Llegadas de **ocio** con provincia de residencia 33. |
| `llegadas_resto_espana` | float | Llegadas de **ocio** con provincia de residencia distinta de 33 (código de dos cifras). Los no residentes en España no aparecen en el MITMA. |
| `llegadas_total_desde_asturias` | float | El mismo reparto, sobre **todas** las llegadas (`llegadas_total`): provincia de residencia 33. |
| `llegadas_total_resto_espana` | float | Todas las llegadas con provincia de residencia distinta de 33 (código de dos cifras). |
| `pernoctaciones_no_residentes` | float | Personas que pernoctan en la zona y residen fuera de ella (`zona_residencia` ≠ `zona_pernoctacion`). |
| `calidad` | texto | `completa`, `sin_dato_mitma` o `anomalia_mitma`. |

Reglas de calidad (`config/mitma_calidad.yaml`):
- `sin_dato_mitma`: 26, 27, 30 y 31-oct y 1-3-nov-2023; 4, 18 y 19-abr y 10-11-nov-2024; 28-29-abr-2025. **Además**, cualquier día que no esté en ningún fichero de viajes. Todos los valores quedan NaN (nunca 0).
- `anomalia_mitma`: 29-31-oct-2024. Se conservan los valores, pero el modelo no los usa para entrenar ni evaluar.
- En un día con fichero, una zona sin filas tiene 0 llegadas: es un dato real, no un ausente.

**Decisión del equipo (2026-10-15).** El reparto Asturias / resto de España del perfil del visitante se calcula sobre las llegadas de **ocio**. Además se guarda sobre `llegadas_total` en columnas aparte (`llegadas_total_*`), que la web recibe como `pct_total_*` en `perfil.json`.

## Prueba

`pytest src/modelo/tests/test_construir_objetivo.py` construye la tabla con ficheros pequeños inventados en los dos formatos y comprueba que:
- los dos formatos dan exactamente el mismo resultado;
- los viajes internos y los de trabajo quedan fuera;
- el reparto por residencia es correcto, sobre ocio y sobre el total;
- las pernoctaciones de residentes no cuentan;
- los días sin dato quedan como NaN y los ceros reales, como 0.
