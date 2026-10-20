# Descarga del MITMA (viajes y pernoctaciones, Asturias)

Procedimiento para regenerar los ficheros en bruto del MITMA que no están en el repositorio (`data/raw/LEEME_datos_no_versionados.md`). El resultado de la descarga del 2026-10-15 (filas, días y ausencias por año) está en `notas/fuentes/mitma/registro_mitma.md`, y el detalle por mes en `notas/fuentes/mitma/cobertura_mitma.md`.

**No hace falta para usar el modelo:** `data/clean/objetivo_diario.parquet` (46 zonas) ya está versionado.

## Fuente

Open Data Movilidad del MITMA, estudios básicos, zonificación municipal v2, ficheros diarios (`https://movilidad-opendata.mitma.es/estudios_basicos/por-municipios/...`).

- Rango: 2022-01-01 a 2025-06-30. Desde el 1 de julio de 2025 cambia la metodología: **no se mezcla** con lo anterior.
- Solo cubre residentes en España.
- Zonas: las 46 zonas MITMA de Asturias de `data/raw/zonas_mitma_asturias.csv` (13 son agrupaciones de concejos, con sufijo `_AM`).

## Órdenes

```bash
python scripts/descarga_mitma.py --workers 4        # descarga (reanudable: relanzar el mismo comando)
python scripts/descarga_mitma.py --solo-ensamblar   # junta los ficheros diarios en los CSV anuales
python scripts/verificar_mitma.py 2024              # filas, días, fechas ausentes, destinos fuera de Asturias
python scripts/dividir_mitma_mensual.py --raw data/raw   # ficheros mensuales que lee construir_objetivo.py
python scripts/cobertura_mitma.py --raw data/raw --zonas data/raw/zonas_mitma_asturias.csv --salida notas/fuentes/mitma/cobertura_mitma.md
```

En Windows se puede seguir el progreso con `Get-Content logs\descarga_mitma.log -Tail 10 -Wait` (PowerShell). La carpeta `logs/` es local y no se versiona.

Después, para reconstruir el objetivo y la tabla horaria: `python -X utf8 src/modelo/construir_objetivo.py --mapeo config/mapeo_zonas.csv` y `python -X utf8 src/modelo/construir_llegadas_por_hora.py` (`notas/modelo.md`, «Cómo regenerar el objetivo real»).

## Cómo funciona

- Descarga cada `.csv.gz` en streaming y lo filtra al vuelo, sin guardar el original:
  - viajes, por `destino`;
  - pernoctaciones, por `zona_pernoctacion`;
  - en ambos casos, que la zona esté en `data/raw/zonas_mitma_asturias.csv`.
- Es el único filtro: solo cambia el separador `|` por `,`.
- Escribe un fichero por día en `data/raw/_mitma_dias/` y luego los ensambla en `data/raw/mitma_{viajes,pernoctaciones}_<año>.csv`.
- Guarda el estado de cada día en `data/raw/_mitma_estado_v2.jsonl` (OK, NO_DISPONIBLE o ERROR).
- **Prioridad:** primero las pernoctaciones de todo el periodo, luego los viajes de 2024-25, 2023 y 2022.

## Límites prácticos

- El cuello de botella es el ancho de banda del portal: unos 190 GB de tráfico en total, medidos entre unos 2 y 20 MB/s.
- Conviene usar **4 workers**: con 10 el rendimiento empeoró.
- Al parar el script en Windows, hay que comprobar que no quedan workers huérfanos (procesos `python` con `multiprocessing.spawn`).
- **Días sin datos:** un 404 se deja ausente (nunca 0). El contraste con la lista oficial está en `notas/fuentes/mitma/registro_mitma.md`.
- Mediciones, decisiones y límites de la descarga: `notas/fuentes/demanda/decisiones_demanda.md` (apuntes de los pasos 1 y 2 y «cambio de método»).
