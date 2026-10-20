# Validación manual del calendario (tabla 3 de la limpieza B)

Fecha: 2026-10-15. Tablas: `data/clean/calendario_diario.parquet` y `data/clean/festivos_locales.parquet`, generadas por `python -X utf8 src/limpieza_B/limpia_calendario.py`.

## 1. Muestra aleatoria (16 fechas)

Muestra con `numpy.random.RandomState(20261015)`: 4 festivos de comunidad (filas con `festivo_ast|mad|cyl`), 4 fiestas locales (filas de `festivos_locales`), 4 días del calendario escolar y 4 días de 2022-2026 para los Lagos. Cada valor se contrastó con el documento original: los festivos y las fiestas locales **sobre la imagen renderizada de la página del PDF** (no sobre el texto que usa el script, para que la comprobación sea independiente del extractor), y el calendario escolar y los Lagos sobre el texto del boletín.

| # | Fecha | Campo | Valor en la tabla | Documento original (cita) | ¿Coincide? |
|---|---|---|---|---|---|
| 1 | 2025-01-06 (lun) | festivo_ast / mad / cyl | True / True / True, "Epifanía del Señor" | BOE-A-2024-21316, anexo: fila "6 Epifanía del Señor." con `**` en las 19 columnas | Sí |
| 2 | 2024-12-09 (lun) | festivo_ast / mad / cyl | True / **False** / True, "Lunes siguiente a la Inmaculada Concepción" | BOE-A-2023-22014: fila "9 Lunes siguiente a la Inmaculada Concepción." con `**` en Andalucía, Aragón, Asturias, Castilla y León, Extremadura, Murcia y Melilla; columna "Com. Madrid" vacía | Sí |
| 3 | 2025-11-01 (sáb) | festivo_ast / mad / cyl | True / True / True, "Todos los Santos" | BOE-A-2024-21316: fila "1 Todos los Santos." con `*` en las 19 columnas | Sí |
| 4 | 2022-12-08 (jue) | festivo_ast / mad / cyl | True / True / True, "Inmaculada Concepción" | BOE-A-2021-17113: fila "8 Inmaculada Concepción." con `*` en las 19 columnas | Sí |
| 5 | 2023-07-03 | festivo local Salas | "Festividad de San Vicente -La Festona en La Espina" | BOPA 2022-03495, p. 3: Salas, "3 de julio — Festividad de San Vicente -La Festona en La Espina" (Salas tiene 4 fechas) | Sí |
| 6 | 2023-11-11 | festivo local Aller | "San Martín de Moreda" | BOPA 2022-03495, p. 1: Aller, "11 de noviembre — San Martín de Moreda" | Sí |
| 7 | 2024-06-24 | festivo local San Tirso de Abres | "Festividad de San Juan" | BOPA 2023-03229, p. 4: SAN TIRSO DE ABRES, "15 de Mayo — Festividad de San Isidro Labrador; 24 de junio — Festividad de San Juan" | Sí |
| 8 | 2027-08-23 | festivo local Nava | "San Bartolomé" | BOPA 2026-04656, p. 3: NAVA, "12 de julio — Festival de la Sidra; 23 de agosto — San Bartolomé" | Sí |
| 9 | 2024-02-10 (sáb) | periodo_escolar_ast | fin_de_semana | BOPA 2023-03661: lectivo 11-sep-2023 a 21-jun-2024; vacaciones 26-dic a 5-ene y 25-mar a 1-abr; no lectivos 12 y 13-feb-2024 (no el 10) | Sí |
| 10 | 2023-01-20 (vie) | periodo_escolar_mad | lectivo | Orden 1210/2022 (BOCM): lectivo 7-sep-2022 a 22-jun-2023; Navidad hasta el 8-ene-2023; no lectivos 31-oct, 5 y 7-dic, 24 y 27-feb, 31-mar, 10-abr | Sí |
| 11 | 2027-03-17 (mié) | periodo_escolar_cyl | lectivo | Orden EDU/478/2026 (BOCYL): Semana Santa "al término de las actividades del viernes 19 de marzo de 2027"; no lectivos 30-oct, 8 y 9-feb | Sí |
| 12 | 2025-08-20 (mié) | periodo_escolar_ast | verano | BOPA 2024-04412: fin lectivo 20-jun-2025; BOPA 2025-03852: inicio 9-sep-2025 | Sí |
| 13 | 2022-05-15 (dom) | lagos_regulado / horario | True / 08:00-21:00 | BOE-A-2022-1125, CO-04: "1,2 y fines de semana de mayo"; "Del 9 de abril al 30 de septiembre de 08:00 a 21:00" | Sí |
| 14 | 2023-04-20 (jue) | lagos_regulado | False | BOE-A-2023-2159: abril "1 al 9" y "15, 16, 22, 23, 29 y 30" (no el 20) | Sí |
| 15 | 2026-01-06 (mar) | lagos_regulado | False | BOE-A-2026-1255: la lista empieza en "28 a 31 de marzo" (nada en enero) | Sí |
| 16 | 2022-09-03 (sáb) | lagos_regulado / horario | True / 08:00-21:00 | BOE-A-2022-1125: "1/VI al 16/X, excepto el 25/VII y el 8/IX" | Sí |

**Resultado: 16/16 coinciden.**

## 2. Semana Santa (cálculo frente al BOE)

Domingo de Resurrección calculado con el algoritmo gregoriano anónimo (Meeus/Jones/Butcher) y comparado con las filas "Jueves Santo", "Viernes Santo" y "Lunes de Pascua" del BOE de cada año. El script falla si no coinciden. Además, comprueba que cada periodo de vacaciones de Semana Santa de los tres calendarios escolares contiene el Viernes Santo calculado (18/18 cursos).

| Año | Domingo de Pascua (calc.) | Jueves Santo calc. / BOE | Viernes Santo calc. / BOE | Lunes de Pascua calc. / BOE | ¿Coincide? |
|---|---|---|---|---|---|
| 2022 | 2022-04-17 | 04-14 / 04-14 | 04-15 / 04-15 | 04-18 / 04-18 | Sí |
| 2023 | 2023-04-09 | 04-06 / 04-06 | 04-07 / 04-07 | 04-10 / 04-10 | Sí |
| 2024 | 2024-03-31 | 03-28 / 03-28 | 03-29 / 03-29 | 04-01 / 04-01 | Sí |
| 2025 | 2025-04-20 | 04-17 / 04-17 | 04-18 / 04-18 | 04-21 / 04-21 | Sí |
| 2026 | 2026-04-05 | 04-02 / 04-02 | 04-03 / 04-03 | 04-06 / 04-06 | Sí |
| 2027 | 2027-03-28 | 03-25 / 03-25 | 03-26 / 03-26 | 03-29 / 03-29 | Sí |

(Tabla completa en `data/clean/_qc/semana_santa_comprobacion.csv`.)

## 3. Lagos 2024 y 2025 revisados sobre el PDF

Se renderizó la página de la fila "ASTURIAS. Covadonga. CO-04" (BOE-A-2024-1773 p. 60 y BOE-A-2025-1329 p. 59) y se leyó sobre la imagen:

- **2024**: "23 al 31 de marzo; 29 y 30 de abril; fines de semana del mes de abril; 1 al 3 de mayo; fines de semana del mes de mayo; 1/VI al 13/X (excepto el 25/VII y el 8/IX); 19, 20, 26 y 27 de octubre; 1 al 3 de noviembre; 30 de noviembre; 1 al 9 de diciembre; horario 00:00 a 24:00". La duda del inventario (texto separado de su fila) queda resuelta: es la fila de Covadonga. Igual que lo transcrito.
- **2025**: "5 y 6 de abril; 12 al 30 de abril; 26 al 30 de abril; 1 y 4 de mayo; fines de semana del mes de mayo; 1/VI al 19/X (excepto la tarde del 24/VII, el 25/VII y el 8/IX); 25 y 26 de octubre; 1 y 2 de noviembre; 29 y 30 de noviembre; 1 al 8 de diciembre". **El solapamiento "12 al 30" / "26 al 30" está en el propio BOE**; se toma la unión (no cambia nada). La tarde del 24-VII se deja como regulado con la nota "salvo la tarde" en `lagos_horario`.

## 4. Folleto de imagen (transcripción, sin verificar)

`turismocangasdeonis_folleto_acceso_lagos.pdf` es imagen (0 letras). Se renderizó a PNG y se transcribió a mano el recuadro "Fechas del Plan" a `data/clean/lagos_folleto_transcripcion.csv` (`verificado=False`). No indica año; por los metadatos (mayo de 2024) y las fechas se infiere 2024. Coincide con el BOE 2024 (Semana Santa 23-31 mar, verano 1-jun a 13-oct salvo 25-jul y 8-sep, Todos los Santos 1-3 nov, Constitución 30-nov a 9-dic). Discrepancia de redacción: el folleto dice "abril y mayo: sábados, domingos y puentes" y "fines de semana de octubre", el BOE da días concretos. **No alimenta `lagos_regulado`** (la fuente es el BOE); queda como contraste.

## 5. Hallazgos durante la validación

1. **La auditoría de la fase B tenía fechas erróneas de Cangas de Onís.** `notas/historico/auditoria_fase_B.md` §3.3 da como fiestas locales de Cangas de Onís 2022-05-16, 2023-05-29, 2024-06-13 y 2026-08-31 y dice que "coinciden con el texto de los PDF". Sobre la imagen de los PDF, Cangas de Onís tiene: 2022 → 13-jun y 25-jul; 2023 → 13-jun y 25-jul; 2024 → 13-jun y 25-jul; 2026 → 13-jun y 24-sep. Solo 2024-06-13 es correcta; las otras tres parecen leídas de filas vecinas del `.txt` (pdftotext desordena la tabla; p. ej. 2022-05-16 es de Belmonte de Miranda). La tabla limpia usa la extracción por posición/tablas del PDF, contrastada con la imagen.
2. **Dos erratas en el BOPA** (señaladas con `dia_semana_coherente=False`, sin corregir): Grado 2022-07-26 "Lunes, Festividad de Santa Ana" (el 26-jul-2022 fue martes) y Pravia 2024-09-06 "Miércoles, Festividad del Santísimo Cristo…" (el 6-sep-2024 fue viernes; parece copiado del año anterior). Se conserva la fecha publicada.
3. Nombres de fiesta del BOPA con el orden de palabras alterado en el propio texto del PDF (p. ej. Llanes "Santa en Lucía Posada y Parroquia" en 2022-2024): se dejan tal cual.

## 6. Comprobaciones automáticas del script (todas pasan)

- BOE: 19 columnas de comunidad por página; cada marca asignada a una sola comunidad; 12 festivos por comunidad y año (AST, MAD y CYL, 2022-2027); todos los "Lunes …" caen en lunes.
- BOPA: 78 concejos por año (2022-2027), ninguna fecha sin concejo; nombres de concejo normalizados al de 2022.
- Calendario escolar: inicio < Navidad < Semana Santa < fin; ningún "no lectivo" cae en fin de semana ni fuera del curso; las vacaciones de primavera contienen el Viernes Santo; sin huecos hasta el 2027-08-31 y NaN desde el 2027-09-01.
- Lagos: 2022-2026 sin NaN, 2027 todo NaN; entre 150 y 200 días regulados por año (173, 175, 180, 184, 185); cada día regulado tiene horario.
- Calendario diario: 2191 filas, sin fechas duplicadas ni ausentes; ningún puente cae en fin de semana o festivo.
