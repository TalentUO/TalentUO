# Registro de la descarga MITMA (viajes y pernoctaciones, Asturias)

Equipo de demanda. Descarga hecha el 2026-10-15 (de 17:00 a 00:19, hora de España) con `scripts/descarga_mitma.py`. Resumen por mes y tipo: `notas/fuentes/mitma/cobertura_mitma.md`. Lo que no se pudo comprobar figura como **NO VERIFICADO**.

## Fuente
- Portal Open Data Movilidad del MITMA, estudios básicos, zonificación municipal v2, ficheros diarios:
  `https://movilidad-opendata.mitma.es/estudios_basicos/por-municipios/{viajes|pernoctaciones}/ficheros-diarios/AAAA-MM/AAAAMMDD_{Viajes|Pernoctaciones}_municipios.csv.gz`
- El patrón de URL es el de la librería `pyspainmobility` 2.1.2 y el índice oficial (`https://movilidad-opendata.mitma.es/RSS.xml`, leído el 2026-10-15) lista enlaces con esa forma. No se contrastó el 100 % de las URLs una a una.
- Periodo: 2022-01-01 a 2025-06-30. **No se descarga nada posterior** (desde 2025-07-01 cambia la metodología). Solo residentes en España.

## Filtro exacto (el único que se aplica)
- Viajes: se conservan las filas cuyo campo `destino` es una de las 46 zonas de `data/raw/zonas_mitma_asturias.csv`.
- Pernoctaciones: se conservan las filas cuya `zona_pernoctacion` es una de esas 46 zonas.
- Las líneas se copian tal cual: no se agrega, no se recodifica y no se renombra ninguna columna. **Única transformación: el separador `|` pasa a `,`** (el script aborta si algún valor ya contiene una coma).
- El `.csv.gz` nacional se descomprime al vuelo y **no se guarda**.

## Qué se guarda
- En bruto, un fichero por año: `data/raw/mitma_viajes_<año>.csv` y `data/raw/mitma_pernoctaciones_<año>.csv`.
- Derivado, un fichero por mes (las mismas líneas, byte a byte): `data/raw/mitma_viajes/AAAA-MM.csv` y `data/raw/mitma_pernoctaciones/AAAA-MM.csv`, con `scripts/dividir_mitma_mensual.py` (comprueba que las filas cuadran con el anual).
- **Nada de esto se sube a GitHub** (≈ 27 GB de viajes). Se regenera con el script. Ver `.gitignore`.

| Año | Viajes: filas | Días | Pernoctaciones: filas | Días |
|---|---|---|---|---|
| 2022 | 74 286 618 | 365 | 2 964 041 | 365 |
| 2023 | 83 792 269 | 358 | 3 244 975 | 358 |
| 2024 | 100 500 025 | 362 | 3 834 878 | 362 |
| 2025 (hasta 30-06) | 55 291 351 | 179 | 1 653 463 | 179 |
| Total | 313 870 263 | 1 264 | 11 697 357 | 1 264 |

Comprobado (`scripts/verificar_mitma.py` y `scripts/cobertura_mitma.py`): los 84 ficheros mensuales existen y abren; 0 filas con destino o zona de pernoctación fuera de Asturias; ninguna fecha posterior al 2025-06-30.

## Columnas (cabecera original del MITMA)
- Viajes (**15**): `fecha, periodo, origen, destino, distancia, actividad_origen, actividad_destino, estudio_origen_posible, estudio_destino_posible, residencia, renta, edad, sexo, viajes, viajes_km`. Hallazgo: la guía esperaba 13; `estudio_origen_posible` y `estudio_destino_posible` son extra.
- Pernoctaciones (4): `fecha, zona_residencia, zona_pernoctacion, personas`.
- `fecha` es `AAAAMMDD`; `periodo` es `00`..`23`; `edad` y `sexo` traen el texto `NA` (dato no disponible en origen, no relleno nuestro); los ids de zona llevan ceros a la izquierda y sufijo `_AM` en las zonas agrupadas.

## Días sin datos
- **Ausentes del portal (404) y del RSS oficial, en viajes y en pernoctaciones: 13 días por tipo** (26 en total): 2023-10-26, 27, 30, 31; 2023-11-01, 02, 03; 2024-04-18; 2024-11-09, 10, 26; 2025-04-28, 29. Quedan **ausentes, nunca 0**.
- **No coincide con la lista de la página del MITMA** (2023-10-26..2023-11-03, 2024-04-04, 18 y 19, 2024-11-10 y 11, 2025-04-28 y 29):
  - **Publicados aunque la página los da por sin datos:** 2024-04-04, 2024-04-19 y 2024-11-11 (están descargados).
  - **No publicados y no están en esa lista:** 2024-11-09 y 2024-11-26.
  - Causa de la discrepancia: no verificada.
  - **Decisión:** el objetivo deja en NaN los 16 días (la lista oficial más los dos no publicados). Los tres publicados se excluyen porque el MITMA los declara sin datos válidos; se respeta su criterio en lugar de usar ficheros que la fuente no avala (`config/mitma_calidad.yaml`).
- 2024-10-29, 30 y 31 (DANA, anomalías en Levante): publicados y descargados con normalidad; hay que tratarlos como anómalos aguas abajo (`calidad = anomalia_mitma` en el objetivo).

## Zonas
- 46 zonas MITMA de Asturias (13 agrupadas). **Cangas de Onís (INE 33012) es zona propia (`33012`)**; Covadonga y Lagos están dentro y MITMA no los separa.
- Llanes `33036`, Ribadesella `33056`, Gijón `33024` y Oviedo `33044` también son zonas propias.
- Cabrales y Onís comparten zona (`33008_AM`, con Peñamellera Alta, Peñamellera Baja y Ribadedeva); Amieva va en `33015_AM` (con Caso, Ponga y Sobrescobio).

## Incidencias de la descarga
- Dos reintentos que se recuperaron solos (2022-05-31: respuesta no gzip del servidor; 2022-06-01: conexión cerrada). Ambos días constan como correctos.
- Rendimiento limitado por el ancho de banda del portal (≈ 2–20 MB/s según el momento); se usaron 4 conexiones. Con 10 el rendimiento empeoró.
- Referencia de filas por día y tipo (2 554 días-tipo, incluidos los 26 sin publicar): `notas/fuentes/mitma/mitma_referencia_filas_por_dia.csv`; comparar una descarga propia con `scripts/comparar_con_referencia.py` (solo se probó contra el propio estado: **NO VERIFICADO** que detecte diferencias reales).

## Cómo reproducir
```
python scripts/descarga_mitma.py --workers 4                                  # descarga (reanudable) y ensamblado anual
python scripts/dividir_mitma_mensual.py --raw data/raw                       # ficheros mensuales
python scripts/cobertura_mitma.py --raw data/raw --zonas data/raw/zonas_mitma_asturias.csv --salida notas/fuentes/mitma/cobertura_mitma.md
```
