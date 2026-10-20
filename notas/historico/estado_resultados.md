# Estado de partida para los resultados con datos reales

> **Documento histórico.** Estado de partida (2026-10-16) antes de entrenar con datos reales: ramas, ficheros y validación del objetivo de **5 zonas**. Superado por la ampliación a 46 zonas (`notas/ampliacion_zonas.md`).

Fecha: 2026-10-16. Rama de trabajo: `resultados-reales`, creada desde `origin/modelo` (`a19b727`) e integrada con `origin/fase-A-objetivo` (`e99268d`). La integración fue un avance rápido (fast-forward): `fase-A-objetivo` es `modelo` más un commit, así que no hubo conflictos.

## Ramas remotas (tras `git fetch --all`)

| rama | último commit | fecha | autor | mensaje |
|---|---|---|---|---|
| main | 0f8f6a0 | 2026-10-16 01:09 | hugoomez | Merge pull request #9 from hugoomez/web |
| calendarios | de48238 | 2026-10-15 18:01 | Hugo Gómez | Open-Meteo: descarga completa (9 zonas), ERA5 de 3 zonas, prevision en vivo y analisis |
| fase-A-objetivo | e99268d | 2026-10-16 01:06 | Adrián | Parte A: objetivo real (MITMA) y tabla horaria para la web |
| fase-B-limpieza | a74db11 | 2026-10-15 21:32 | Hugo Gómez | Limpieza de la parte B: tablas limpias, diccionario y control de calidad |
| modelo | a19b727 | 2026-10-15 23:31 | Hugo Gómez | Fusiona main (PR #1 y #2, parte A) en modelo |
| paso1-zonas-mitma | bcf92a2 | 2026-10-15 23:24 | Adrián | MITMA: documenta viajes 2024 y 2025 completados y verificados |
| web | 6fba3b5 | 2026-10-16 01:07 | Hugo Gómez | Web: revisión de usabilidad |
| web-frontend | b0aba54 | 2026-10-15 23:46 | sggg6 | Web: añade el piloto de interfaz (frontend) con datos ficticios |
| web-gestion | bd39e83 | 2026-10-16 00:48 | Adrián | Merge remote-tracking branch 'origin/web' into web-gestion |

Las ramas `web` y `web-gestion` no se han tocado. El trabajo se hace en un worktree aparte para no alterar la copia local de `web`.

## Ficheros comprobados

`origin/fase-A-objetivo` (todos presentes):

| fichero | bytes |
|---|---|
| data/clean/objetivo_diario.parquet | 368 806 |
| data/clean/llegadas_por_hora.parquet | 31 887 |
| data/raw/zonas_mitma_asturias.csv | 1 741 |
| config/mapeo_zonas.csv | 1 061 |
| notas/fuentes/mitma/registro_mitma.md | 5 402 |
| notas/fuentes/mitma/cobertura_mitma.md | 6 794 |
| notas/historico/revision_objetivo.md | 7 840 |

`origin/modelo` (todos presentes): src/modelo/ejecutar.py, notas/contrato_objetivo.md, notas/contrato_web.md, notas/modelo.md, notas/guion_modelo.md, src/limpieza_B/unir_B.py.

Ausentes, como se esperaba: los ficheros mensuales del MITMA (`data/raw/mitma_viajes/`, `data/raw/mitma_pernoctaciones/`). No se ejecuta `construir_objetivo.py`.

Datos del INE en el repositorio: no hay `data/raw/ine_moviles_*`. Sí hay otros ficheros del INE (`ine_eoh_*`, `ine_camping_*`, `ine_eoap_*`, `ine_rural_*`, `ine_viviendas_turisticas.xlsx`) y del SADEI (`sadei_*.px`). Se revisará en el paso 5.

## Validación de `data/clean/objetivo_diario.parquet` (paso 1)

Comprobado con el propio parquet:

- 6 385 filas = 5 zonas × 1 277 días (2022-01-01 a 2025-06-30), sin huecos de fecha y sin duplicados fecha × zona. 42 meses por zona.
- Columnas y tipos según el contrato: `fecha` datetime; `zona_mitma_id` texto; las 7 columnas de valores, float; `calidad` texto.
- Zonas: 33012 (Cangas de Onís), 33024 (Gijón), 33036 (Llanes), 33044 (Oviedo), 33056 (Ribadesella). Las 5 están en `config/mapeo_zonas.csv` y en `data/raw/zonas_mitma_asturias.csv` (46 zonas), y las 5 del mapeo están en el objetivo. Ninguna de las 5 es una agregación de municipios.
- `calidad`: completa 6 290, sin_dato_mitma 80 (16 días × 5 zonas), anomalia_mitma 15 (3 días × 5 zonas).
- Los 14 días oficiales sin dato están todos marcados `sin_dato_mitma`, con NaN en las 7 columnas y ningún 0. Hay **dos días más** marcados igual: 2024-11-09 y 2024-11-26, que no están en ningún fichero descargado del portal (regla del contrato: «cualquier día que no esté en ningún fichero de viajes»).
- 2024-10-29 a 2024-10-31: `anomalia_mitma`, con los valores conservados.
- Días `completa`: ningún NaN y ningún 0.
- `zonas_mitma_asturias.csv` llama a la columna `id_zona_mitma`, no `zona_mitma_id` ni `id` como dice el contrato. El código ya lo acepta (`construir_objetivo.py`, línea 188) y hay una prueba para ello (`test_zonas_con_columna_id_zona_mitma`).
