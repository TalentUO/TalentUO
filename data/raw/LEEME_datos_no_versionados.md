# Datos en `data/raw/` que no están en GitHub

Hay dos motivos para no subir un fichero: **el tamaño** (GitHub rechaza ficheros de más de 100 MB) y **la licencia** (copias de terceros o datos sin permiso de redistribución). Cada descarga está detallada (URL, fechas, problemas) en `notas/fuentes/demanda/registro_descargas.md` y, para el MITMA, en `notas/fuentes/mitma/registro_mitma.md`. Cómo descargar el MITMA paso a paso: `notas/fuentes/mitma/descarga_mitma.md`. Condiciones de cada fuente: `FUENTES_Y_LICENCIAS.md`.

**Para entrenar el modelo no hace falta ninguno**: el objetivo ya construido (`data/clean/objetivo_diario.parquet`, 46 zonas) y las tablas limpias de `data/clean/` sí están versionados. **Para rehacer la limpieza de los factores tampoco**: `src/limpieza_B/` solo lee ficheros que siguen en el repositorio (AEMET, Open-Meteo, PDF del BOE y del BOPA, OAPN, Wikipedia, Trends y `data/manual/eventos_recopilado.csv`).

## No se suben por tamaño

Solo se necesitan para reconstruir el objetivo desde cero.

| Fichero o carpeta | Tamaño aprox. | Cómo obtenerlo |
|---|---|---|
| `mitma_viajes_2022..2025.csv`, `mitma_pernoctaciones_2022..2025.csv` (anuales, en bruto filtrados a Asturias) | ≈ 27 GB de viajes en total (313,9 millones de filas) y unos 11,7 millones de filas de pernoctaciones | `python scripts/descarga_mitma.py --workers 4` (reanudable; filtra Asturias). Comprobar con `python scripts/verificar_mitma.py <año>` |
| `mitma_viajes/AAAA-MM.csv`, `mitma_pernoctaciones/AAAA-MM.csv` (mensuales, los que lee `src/modelo/construir_objetivo.py`) | lo mismo, partido por mes (84 ficheros) | `python scripts/dividir_mitma_mensual.py --raw data/raw` a partir de los anuales |
| `ine_moviles_53001.csv`, `ine_moviles_interno_2022..2026.xlsx` | extracto de Asturias / 28–49 MB por año | Paso 3 de `notas/fuentes/demanda/registro_descargas.md` (INE, estadística experimental de turismo con móviles; `scripts/descarga_ine_moviles.py`). No los usa el modelo |
| `ine_viviendas_turisticas.csv` | 31 MB | `https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/39363.csv?nocab=1` (el `.xlsx` equivalente sí está subido) |
| `_mitma_estado_v2.jsonl`, `_mitma_dias/`, `_mitma_viejo/`, `_*_tmp/` | temporales | Los genera el script de descarga: estado por día, ficheros diarios antes de ensamblar y parciales de la primera versión del script |

## No se suben por licencia

Se retiraron del árbol del repositorio el 2026-10-25 (siguen en el historial de git; ver el pendiente 7 de `FUENTES_Y_LICENCIAS.md`). Ninguno lo lee el modelo ni la limpieza: los datos que se sacaron de ellos ya están transcritos en el código o en `data/manual/`.

| Fichero o carpeta | Qué es | Cómo obtenerlo |
|---|---|---|
| `sadei_*.px`, `padron_concejos.px` | Estadísticas de SADEI y padrón por concejo (contexto) | `python scripts/descarga_sadei.py`; se comprueba con `python scripts/verificar_sadei.py` |
| `cogersa_residuos.xlsx` | Residuos por concejo (contexto, 53 KB) | `https://recursos.cogersa.es/gestion%20residuos/Residuos-COGERSA-Ayuntamientos-2021.xlsx`. COGERSA exige autorización escrita para distribuirlo |
| `eventos/` | Copias de las páginas de donde se tomó cada fecha de evento (webs de festivales, ayuntamientos, prensa, LaLiga) | No se redistribuyen. La URL y la fecha de consulta de cada una están en `notas/fuentes/` y en la columna de fuente de `data/manual/eventos_recopilado.csv` |
| `calendario/prensa_*`, `calendario/pnpe_*`, `calendario/turismocangasdeonis_*`, `calendario/juridicas_*`, `calendario/_descartados/` | Copias de prensa, del Parque Nacional y de Turismo de Cangas de Onís sobre el acceso a los Lagos | No se redistribuyen. Su contenido está transcrito, con la cita, en `src/limpieza_B/calendario_datos.py`; URL y fecha en `notas/fuentes/` |

## Sí están subidos

Estadísticos de día normal del MITMA (`mitma_estadisticos_dia_normal_2024/`), zonificación (`mitma_zonificacion_v2/`), INE (EOH, EOAP, camping, rural y `ine_viviendas_turisticas.xlsx`), AEMET, Open-Meteo, los boletines oficiales de `calendario/` (BOE, BOPA, BOCYL, BOCM, Educastur), OAPN, Wikipedia y Trends.

Regla general: los datos que faltan son ausentes, nunca 0.
