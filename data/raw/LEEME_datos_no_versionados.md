# Datos en `data/raw/` que no están en GitHub

Por tamaño (GitHub rechaza ficheros de más de 100 MB) no se suben; hay que regenerarlos. Cada descarga está detallada (URL, fechas, problemas) en `notas/fuentes/demanda/registro_descargas.md` y, para el MITMA, en `notas/fuentes/mitma/registro_mitma.md`. Cómo descargar el MITMA paso a paso: `notas/fuentes/mitma/descarga_mitma.md`.

**Para entrenar el modelo no hacen falta**: el objetivo ya construido (`data/clean/objetivo_diario.parquet`, 46 zonas) y las tablas limpias de `data/clean/` sí están versionados. Solo se necesitan para reconstruir el objetivo desde cero.

| Fichero o carpeta | Tamaño aprox. | Cómo obtenerlo |
|---|---|---|
| `mitma_viajes_2022..2025.csv`, `mitma_pernoctaciones_2022..2025.csv` (anuales, en bruto filtrados a Asturias) | ≈ 27 GB de viajes en total (313,9 millones de filas) y unos 11,7 millones de filas de pernoctaciones | `python scripts/descarga_mitma.py --workers 4` (reanudable; filtra Asturias). Comprobar con `python scripts/verificar_mitma.py <año>` |
| `mitma_viajes/AAAA-MM.csv`, `mitma_pernoctaciones/AAAA-MM.csv` (mensuales, los que lee `src/modelo/construir_objetivo.py`) | lo mismo, partido por mes (84 ficheros) | `python scripts/dividir_mitma_mensual.py --raw data/raw` a partir de los anuales |
| `ine_moviles_53001.csv`, `ine_moviles_interno_2022..2026.xlsx` | extracto de Asturias / 28–49 MB por año | Paso 3 de `notas/fuentes/demanda/registro_descargas.md` (INE, estadística experimental de turismo con móviles; `scripts/descarga_ine_moviles.py`). No los usa el modelo |
| `ine_viviendas_turisticas.csv` | 31 MB | `https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/39363.csv?nocab=1` (el `.xlsx` equivalente sí está subido) |
| `_mitma_estado_v2.jsonl`, `_mitma_dias/`, `_mitma_viejo/`, `_*_tmp/` | temporales | Los genera el script de descarga: estado por día, ficheros diarios antes de ensamblar y parciales de la primera versión del script |

Sí están subidos: estadísticos de día normal del MITMA (`mitma_estadisticos_dia_normal_2024/`), zonificación (`mitma_zonificacion_v2/`, `zonas_mitma_asturias.csv`), INE (EOH, EOAP, camping, rural), SADEI (`.px`), padrón, COGERSA, `ine_viviendas_turisticas.xlsx`, AEMET, Open-Meteo, calendarios, eventos y señales.

Regla general: los datos que faltan son ausentes, nunca 0.
