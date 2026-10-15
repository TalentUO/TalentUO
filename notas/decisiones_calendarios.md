# Decisiones y consideraciones: calendarios (fase 1)

Fecha: 2026-10-15. Complementa `notas/inventario_calendarios.md` (qué hay) y `notas/registro_calendarios.md` (de dónde viene cada fichero). Aquí va el porqué y lo que hay que tener en cuenta al montar la tabla.

## Valoración frente a los objetivos del proyecto

- **Cubre bien** el factor "calendario de origen y destino": festivos laborales 2022-2027 de todas las comunidades (BOE), fiestas locales de todos los concejos de Asturias (BOPA) y vacaciones escolares de Asturias, Madrid y Castilla y León, todo de fuente oficial.
- **Cubre bien** el acceso regulado a los Lagos 2022-2026 con la fuente normativa (resoluciones anuales de la DGT), no con prensa.
- **Cubre mal** los eventos no planificados (cortes o suspensiones): solo hay prensa y sin fechas exactas. El modelo no debe depender de ellos.
- **No hay dato diario de uso de los Lagos** (viajeros o aparcamiento por día). Solo totales anuales. Esto limita la validación del semáforo en esa zona.
- **Límite de esta fase:** se comprobó que cada documento abre, que su año y comunidad son los correctos y que tiene texto. Aún no se ha leído ni validado el contenido fila a fila; eso corresponde al paso de tabla.

## Decisiones tomadas

1. **Solo fuentes oficiales para los datos.** La prensa solo se guardó como contexto y está marcada "NO OFICIAL" (nombre `prensa_*`, columna "Carácter" del registro).
2. **Lagos: fuente = resolución DGT del BOE**, no la web municipal. La web de Cangas de Onís no cita ninguna norma y omite excepciones (6-jun, tarde 24-jul, 25-jul, 8-sep en 2026). Si discrepan, manda el BOE.
3. **Calendario escolar de Asturias desde el BOPA**, no desde Educastur. El PDF que sugería el enunciado (`festivos-locales-25-26`) es de días sustitutivos de fiestas locales, no el calendario escolar. Se conserva como dato secundario.
4. **Orígenes limitados a Madrid y Castilla y León** por ahora. Galicia, Cantabria, País Vasco y Andalucía quedan para cuando el MITMA fije los orígenes reales.
5. **PDF sin modificar** y texto extraído en `.txt` aparte (`pdftotext -layout`). El script `src/descarga_calendarios.py` es reanudable y no repite lo ya descargado.
6. **Hueco 2021-22 de Asturias aceptado** (alternativa: calendario gráfico de Educastur). Como el modelo parte de 2022 y el curso 2021-22 solo afecta a enero-junio de 2022, el impacto es pequeño.

## Consideraciones para montar la tabla

- **Cursos cruzan año.** Convertir cada calendario escolar a fechas explícitas (inicio de curso, Navidad, Semana Santa, días no lectivos, fin de curso) por comunidad y curso.
- **Fiestas del BOE:** la tabla marca sustituciones y traslados a lunes por comunidad. Las notas al pie cuentan. Asturias cambia en 2023/2025 una fiesta nacional por el 8 de septiembre (Día de Asturias, según decretos autonómicos).
- **Fiestas locales:** son por concejo. Para la puerta de los Picos usar Cangas de Onís, Onís, Cabrales, Llanes y Ribadesella; para el resto, Gijón y Oviedo. Las modificaciones posteriores (Vegadeo 2025, corrección 2022) no están descargadas.
- **Variable `lagos_regulado` diaria** a partir de las listas de la DGT:
  - Las excepciones (25-jul, 8-sep, etc.) son parte del dato.
  - Los horarios cambian: 2022 y 2023 eran de 07:30-08:00 a 21:00 (y hasta 19:00 de octubre a diciembre); desde 2024 es de 00:00 a 24:00.
  - El criterio es regulado = carretera cerrada a particulares ese día.
- **Revisar a mano** las tablas de Lagos de 2024 y 2025 contra el PDF antes de cargarlas: el texto extraído separa las fechas de su fila, y en 2025 "12 al 30 de abril" y "26 al 30 de abril" se solapan (posible errata del BOE).
- **Regulado no es lo mismo que menos visitantes.** Un día regulado concentra visitas en el autobús (tope de 3.000 viajeros diarios según la web municipal) y puede desplazar presión a Covadonga y Cangas. Tratarlo como factor explicativo, no como corrección automática.
- **Agosto 2025:** los incendios suspendieron el transporte público a los Lagos (fuente solo prensa, ~16-ago) en días que ya eran regulados. Es un valor atípico: se sugiere marcarlo como evento aparte para no sesgar la comparación con un "día normal".
- **Datos anuales del Parque** (MITECO: 1,80 M en 2022, 1,70 M en 2023, 1,63 M en 2024) sirven de contexto, no de variable diaria.

## Incidencia de proceso (lección)

Para localizar el código del BOPA de 1-jun-2021 se lanzó un barrido de URLs que, por error, corrió dos veces en paralelo. `miprincipado.asturias.es` dejó de responder a partir de ahí. Se detuvo, no se encontró nada y no se reintentó contra ese host. **No hacer barridos de URLs contra servidores oficiales**; buscar el código en el buscador del BOPA (sede.asturias.es/bopa) o pedir el fichero a mano.

## Pendiente (para quien continúe)

- Bajar a mano el BOPA de 1-jun-2021 (calendario escolar 2021-22) y, si interesa, las correcciones de fiestas locales (2021-11-30 y 2025 Vegadeo) y la modificación del calendario escolar 2025-26 (12-jun-2025).
- Buscar fuente oficial del corte de agosto de 2025 (Principado, SEPA, Parque Nacional) y cualquier dato diario de viajeros a los Lagos (Consorcio de Transportes de Asturias).
- OCR o transcripción del folleto `turismocangasdeonis_folleto_acceso_lagos.pdf` (única imagen).
- Ampliar a otras comunidades de origen cuando el MITMA los fije.
