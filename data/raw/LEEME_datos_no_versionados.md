# Datos en `data/raw/` que NO están en GitHub

Por tamaño (GitHub rechaza ficheros >100 MB) no se suben; hay que regenerarlos. Cada descarga está detallada (URL, fechas, problemas) en `notas/registro_descargas.md`.

| Fichero | Tamaño aprox. | Cómo obtenerlo |
|---|---|---|
| `mitma_viajes_2022..2025.csv`, `mitma_pernoctaciones_2022..2025.csv` | unos 14 GB/año de viajes y 20–50 MB/año de pernoctaciones al completarse (estimación; en construcción mientras corre la descarga) | `python scripts/descarga_mitma.py` (reanudable; filtra Asturias). Comprobar con `scripts/verificar_mitma.py <año>` |
| `ine_moviles_53001.csv`, `ine_moviles_interno_2022..2026.xlsx` | 1,8 GB / 28–47 MB | Paso 3 del registro (INE Estadística Experimental, móviles) |
| `ine_viviendas_turisticas.csv` | 30 MB | `https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/39363.csv?nocab=1` (el `.xlsx` equivalente sí está subido) |
| `_mitma_estado_v2.jsonl`, `_mitma_dias/`, `_mitma_viejo/`, `_*_tmp/` | temporales | los genera el script de descarga (estado por día, ficheros diarios antes de ensamblar, y parciales de la primera versión con pandas, ya sustituidos) |

Sí están subidos: estadísticos de día normal, zonificación, INE (EOH, EOAP, camping, rural), SADEI, COGERSA, `ine_viviendas_turisticas.xlsx`.
Regla general: datos que faltan = ausentes, nunca 0.
