# Eventos 2022-2026: fuentes, estado y candidatos

Recopilación a 2026-10-15. Tabla: `data/manual/eventos_recopilado.csv` (378 filas). Fuentes en bruto: `data/raw/eventos/` (ver `notas/registro_eventos.md`). Referencia espacial: concejo. No es la tabla final.

Estados: `verificado` = fuente oficial/organizador para esa edición; `probable` = solo prensa/secundaria, o previsión oficial sin confirmar que se realizó; `no_encontrado`.

## 1. Cruceros en Gijón (concejo Gijón)
| Año | Estado | Fuente | Qué falta |
|---|---|---|---|
| 2022, 2023, 2024 | `no_encontrado` (3 filas sin fecha) | Solo cifras agregadas en prensa (≈28 buques previstos 2023; 21 llegados 2024 según PortsEurope) | Pedir a la Autoridad Portuaria de Gijón las escalas realizadas por fecha y buque |
| 2025 | `probable` (39 escalas) | PDF "Previsión de escalas 2025, actualización 01/2025", Gijón Turismo Profesional | Escalas realmente hechas. Indicio de que no coincide: PortsEurope habla de 15 buques entre enero y julio, y el PDF tiene 17 entre abril y julio |
| 2026 | `probable` (50 escalas) | PDF puertogijon.es "versión abril 2026" | Escalas realizadas (hasta hoy) y versión posterior; PortsEurope hablaba de 39 escalas en enero, el PDF de abril tiene 50 |

Notas: la columna de pasajeros es la capacidad declarada, no pasajeros reales. El PDF 2025 tiene dos erratas de fecha (`30/5/05`, `1/10/29`), corregidas con el día de la semana del propio PDF. Algunas escalas de 2026 no tienen horario. Una escala de 2 días (Europa 2, 4-5 mayo 2026) va con rango.

## 2. Partidos en casa (Real Oviedo, Sporting de Gijón)
Fuente de partidos jugados 2021-22 a 2025-26: football-data.co.uk (secundaria; fecha del partido jugado; hora en UK, se suma 1 h para hora de España, comprobado contra LaLiga). Temporada 2026-27: LaLiga (oficial), calendario completo de 42 jornadas descargado el 2026-10-15; los 10 partidos ya jugados son `verificado` y coinciden en fecha y hora con football-data; los 32 restantes son `probable` (calendario no confirmado, muchos sin día/hora fijados).

Categoría por temporada (comprobada con la división de cada CSV, no supuesta):
| Temporada | Real Oviedo | Sporting |
|---|---|---|
| 2021-22 | Segunda | Segunda |
| 2022-23 | Segunda | Segunda |
| 2023-24 | Segunda | Segunda |
| 2024-25 | Segunda | Segunda |
| 2025-26 | **Primera** (19 partidos en casa) | Segunda |
| 2026-27 | Segunda | Segunda |

Pendiente: Copa del Rey (1 fila `no_encontrado`), promociones de ascenso/play-off (no incluidas; la liga regular sí) y verificación oficial de temporadas pasadas (probable por ser fuente secundaria). Para hacerlo: LaLiga con crawl-delay de 30 s (~200 páginas) o RFEF.

## 3. Eventos locales
| Evento (concejo) | 2022 | 2023 | 2024 | 2025 | 2026 | Observaciones |
|---|---|---|---|---|---|---|
| Descenso del Sella (Parres y Ribadesella) | V | V | V | V | V | Fuente: organizador CODIS. Rango = semana de actos, prueba el sábado. Hora de salida solo 2025-2026 (12:00) |
| Fiesta del Pastor (Cangas de Onís) | P | P | P | P | V | 2022-2025 solo prensa; falta nota del Ayuntamiento/cartel. Fecha fija 25 jul. En 2024-2026 hay acampada la víspera; en 2025 actos hasta el 27 |
| San Mateo (Oviedo) | V | V | V | V | V | Fuente oviedo.es. `fecha_fin` = último acto del programa (incluye la Romería, 2025-09-28), no el cierre de las fiestas principales (22) |
| Festival de la Sidra (Nava) | P | V | V | V | V | 2022 solo secundaria (hay discrepancia 8-10 vs 7-11 jul). 2023 es copia Wayback del PDF oficial |
| Semana Negra (Gijón) | V | P | V | P | V | 2023: falta fecha oficial (web oficial no la da). 2025: fin 13 vs 14 jul. Lugar: Naval Gijón hasta 2025; L'Arbeyal en 2026 (fuente secundaria) |
| FICX, festival de cine (Gijón) | V | V | V | V | P | 2026 aún sin celebrar, 13-21 nov por prensa/festivales; falta reglamento |
| FIDMA, feria de muestras (Gijón) | V | P | V | P | V | **FIDMA no es el festival de cine**, es la Feria Internacional de Muestras de Asturias (Recinto Luis Adaro, agosto). 2023 solo por una web de la Universidad de Oviedo (no guardada); 2025 hay 1-17 vs 2-17 ago |

V = verificado, P = probable. Si el reto quiso decir el cine al decir FIDMA, el evento correcto es FICX; se recopilan los dos.

## 4. Candidatos adicionales (NO incluidos en el CSV)
Todos con fuente secundaria/prensa; sin confirmar en fuente oficial.
1. **Día de Asturias / Santina, 8 sep (Covadonga, Cangas de Onís)**: romería masiva en el mismo punto que el reto, y coincide con el pico de afluencia a los Lagos. https://www.festivalesdeespana.com/festival/d-ia-de-asturias-covadonga-covadonga-cangas-de-on-is
2. **Día de América en Asturias (Oviedo, 19 sep 2026, 17:00)**: desfile de gran asistencia dentro de San Mateo, de interés turístico nacional (confirmado en oviedo.es para 2023-2026). https://www.turismoasturias.es/agenda-de-asturias/-/calendarsuite/event/dia-de-america-en-asturias-en-oviedo/4777154/JXvXAPSD7JC0
3. **Semana Grande de Gijón (7-15/16 ago 2026)**: solapa con FIDMA; las fuentes difieren en un día. https://www.turismoasturias.es/agenda-de-asturias/fiestas/-/calendarsuite/event/semana-grande-de-gijon/17146030/jr0cMeS144cd
4. **Festival de la Sidra Natural de Gijón (finales de agosto)**: fechas distintas según fuente (22-31 vs 20-30). https://www.festivalesdeespana.com/festival/festival-de-la-sidra-natural-de-gij-on-gij-on
5. **La Guía (Llanes), 7-9 sep, día grande el 8**: pico en Llanes la misma semana que Covadonga. https://www.festivalesdeespana.com/festival/romer-ia-de-la-virgen-de-la-gu-ia-de-llanes-llanes
6. **San Roque (Llanes), 14-16 ago**: fiestas principales de Llanes en agosto. https://www.festivalesdeespana.com/festival/fiestas-de-san-roque-de-llanes-jornadas-agosto-llanes
7. **Semana Santa de Oviedo (29 mar-5 abr 2026)**: fecha móvil, que el modelo captura mal con solo un calendario de festivos nacionales. https://www.festivalesdeespana.com/festival/semana-santa-de-oviedo-oviedo
8. **Vuelta a España en los Lagos de Covadonga (3 sep 2024, etapa 16)**: evento puntual con pico en la subida; hay que revisar año por año (no hallada en 2025 ni 2026). https://www.lafm.com.co/deportes/vuelta-a-espana-2024-marc-soler-gano-la-etapa-16-en-lagos-de-covadonga
9. **Fiestas de San Antonio (Cangas de Onís), 5-21 jun 2026, día grande 13 jun**: interés turístico regional en el concejo central del reto. https://asturias.com/fiestas-de-san-antonio-cangas-de-onis/
10. **Noche Blanca de Oviedo (3 oct 2026)** y **Concurso de Quesos de los Picos (12 oct 2026)**: de menor impacto, solo si se quiere ampliar. https://www.festivalesdeespana.com/festival/noche-blanca-de-oviedo-oviedo
Además: el calendario de cierres de acceso a los Lagos de Covadonga (loscauces.com, 2026) es un indicador directo de presión en esa zona y merece un vistazo.

No se encontró nada sobre Festival Intercéltico, Prestosu ni Vaqueirada.
