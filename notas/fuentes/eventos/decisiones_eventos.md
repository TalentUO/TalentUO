# Eventos: decisiones, límites y consideraciones (fase 1)

Fecha: 2026-10-15. Complementa `notas/fuentes/eventos/eventos_fuentes.md` (fuentes y estado por evento) y `notas/fuentes/eventos/registro_eventos.md` (ficheros). Tabla: `data/manual/eventos_recopilado.csv`.

## Valoración honesta frente a los objetivos del proyecto
El objetivo de la fase 1 era dejar los eventos recopilados con fuente y estado, sin inventar. Eso se cumple: 378 filas, ninguna sin fuente ni estado, y lo no hallado figura como `no_encontrado`. Pero la cobertura útil para el modelo es desigual:

- **Buena:** Sella, San Mateo, Nava (2023-2026), FICX 2022-2025, Semana Negra y FIDMA en la mayoría de años. Fechas con fuente oficial.
- **Débil:** el 87 % de las filas son `probable`. La mayoría son partidos de liga, cuya fuente es secundaria; los partidos jugados 2021-22 a 2025-26 no se contrastaron con LaLiga (solo una comprobación puntual de la hora).
- **Hueco importante:** cruceros de Gijón 2022-2024 (`no_encontrado`). Los datos de movilidad a predecir cubren 2022 a junio de 2025, así que el factor "cruceros" solo tiene calendario en 2025 (y como previsión). Sin las escalas realizadas, el modelo no puede aprender su efecto.
- **Sin recopilar:** Copa del Rey, promociones de ascenso, aforo de estadios y de eventos (la columna `aforo_o_pasajeros` solo se rellenó en cruceros, con capacidad declarada).
- **Revisión pendiente:** las fechas de Sella, Pastor, San Mateo, Nava, Semana Negra, FICX y FIDMA las recopilaron en tareas de búsqueda separadas. Se comprobó que cada fila tuviera fuente y estado, pero no se contrastó cada fecha contra su fuente en bruto. Hay que repasarlas antes de darlas por buenas, empezando por las `verificado`.

## Decisiones tomadas
1. **Estados.** `verificado` solo con fuente oficial o del organizador para esa edición. Prensa, agregadores y previsiones sin confirmación de que se realizaron son `probable`. Las previsiones de cruceros 2025 y 2026 son `probable` aunque el PDF sea oficial: es una previsión, no una escala realizada.
2. **Fechas reales, no calculadas.** No se usaron reglas como "primer sábado de agosto" para el Sella, aunque Wikipedia las da calculadas; solo cuentan fechas respaldadas por una fuente de esa edición.
3. **Partidos.** Fecha del partido jugado. Hora local de España = hora de football-data (UK) + 1 h (comprobado con LaLiga: 17:00 UTC = 19:00 local). Temporada 2026-27: LaLiga como fuente oficial; los partidos aún sin día/hora fijados llevan la fecha de la jornada y la nota "calendario no confirmado".
4. **LaLiga solo para 2026-27.** Se respetó el `Crawl-delay: 30` de su `robots.txt` (42 jornadas, ~21 min). No se descargaron temporadas pasadas (~200 páginas) por coste; queda como mejora.
5. **Categoría por temporada**, deducida de la división en la que aparece cada club en los CSV, no supuesta: Primera solo para el Oviedo en 2025-26; el resto, Segunda.
6. **FIDMA es la Feria Internacional de Muestras de Asturias, no el festival de cine.** Se recopilan ambos (FIDMA y FICX) como eventos distintos. Conviene confirmar con el reto si se quería el cine.
7. **Referencia espacial: concejo**, como se pidió. Sella: `Parres;Ribadesella`; partidos: `Oviedo` o `Gijón`. La asignación a zonas MITMA queda para después.
8. **Convención de rangos.** `fecha_ini` = inicio oficial, `fecha_fin` = último acto del programa oficial. Consecuencia: San Mateo 2025 termina el 28 de septiembre (Romería), no el 22 (fin de las fiestas principales).
9. **Fuentes en bruto en el repo** (~32 MB). No se añadieron a `.gitignore`; decidir si se versionan.

## Discrepancias y avisos conocidos
- Cruceros 2025: PDF con erratas de fecha (`30/5/05`, `1/10/29`), corregidas con el día de la semana del propio PDF. Indicio de previsión ≠ realidad: la prensa cuenta 15 buques de enero a julio y el PDF lista 17 hasta el 24 de julio.
- Cruceros 2026: PortsEurope (enero) hablaba de 39 escalas; el PDF de abril lista 50.
- Nava 2022: 8-10 jul (Comarca de la Sidra) frente a 7-11 jul (blog). FIDMA 2025: 1-17 frente a 2-17 ago. Semana Negra 2025: fin 13 o 14 jul.
- Semana Negra cambia de sede en 2026 (Naval Gijón → L'Arbeyal, La Calzada), según fuentes secundarias.
- Fiesta del Pastor: no se halló nota oficial del Ayuntamiento para 2022-2025.
- Nava 2023 se apoya en una copia de Wayback del PDF oficial; en 2025 y 2026 el PDF es una imagen y las fechas se leyeron a ojo.

## Qué hace falta para cerrar los huecos
| Hueco | Acción |
|---|---|
| Cruceros 2022-2024 y escalas realizadas 2025-2026 | Solicitar a la Autoridad Portuaria de Gijón (escalas realizadas por fecha y buque) |
| Partidos 2021-22 a 2025-26 en `probable` | Descargar LaLiga por jornada (30 s entre peticiones) o RFEF y contrastar |
| Pastor 2022-2025, Nava 2022, Semana Negra 2023/2025, FIDMA 2023/2025 | Notas oficiales del Ayuntamiento/organizador, o el cartel de cada edición |
| FICX 2026 | Reglamento oficial cuando se publique |
| Copa del Rey | RFEF o fuente de temporada; baja prioridad |
| Aforo de estadios y eventos | Fuente por determinar; hoy vacío |

## Decisiones pendientes para la tabla final
1. Eventos de varios días: una fila por día (con marca de día grande) o rango más día principal.
2. `fecha_fin` de San Mateo: último acto del programa o fin de las fiestas principales.
3. Cruceros: usar la previsión o esperar a las escalas realizadas; la capacidad declarada no es el número real de pasajeros.
4. Partidos: variables de peso propias (categoría, rival, derbi); el Oviedo solo jugó en Primera en 2025-26.
5. Entrada al modelo de los `probable`: incluirlos con una columna de calidad de fuente o usar solo `verificado`.
6. Qué candidatos adicionales (ver `notas/fuentes/eventos/eventos_fuentes.md`, sección 4) pasan a la tabla.
