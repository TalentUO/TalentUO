# Notas: señales adelantadas (Wikipedia, Google Trends, OAPN)

Descargas del 2026-10-15. Todo lo que no se pudo comprobar con documentación o con una llamada real está marcado **[NO VERIFICADO]**.

## 1. Wikipedia (Wikimedia REST pageviews)

**Endpoint usado:** `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/<proyecto>/all-access/user/<Titulo>/daily/AAAAMMDD/AAAAMMDD`. User-Agent identificable con contacto del proyecto; 1 s entre llamadas. No hubo ningún 429.

**Comprobado en documentación oficial** (doc.wikimedia.org, referencia de page views): "These endpoints serve data starting on July 1, 2015". Nuestro rango (desde 2022-01-01) queda dentro. No he podido leer en la documentación (las páginas consultadas no lo recogen) los límites de peticiones, la definición de `user` ni la política de redirecciones: **[NO VERIFICADO en documentación]**. En la práctica no hubo límites con ~25 llamadas espaciadas 1 s.

**Rango real descargado:** 2022-01-01 a 2026-10-14 = 1748 días esperados.

**Títulos verificados** con `action=query&redirects=1` en cada Wikipedia. Los 11 títulos pedidos existen y **ninguno es redirección**. Redirecciones detectadas en los que probé como extra:
- `es: Santuario de Covadonga` → `Santa Cueva de Covadonga` (usado el título final).
- `es: Arenas de Cabrales` → `Las Arenas (Cabrales)` (no descargado).
- `fr: Picos de Europa` → `Pics d'Europe` (usado el título final).
- No existen: `es: Parque nacional de Covadonga`, `fr: Parc national des Pics d'Europe`.
- Importante: las visitas se cuentan por título. Las visitas que entran por una redirección **no** se suman al artículo de destino (comportamiento general de la API; no lo he medido aquí, **[NO VERIFICADO]**).

**Artículos (20 ficheros):** 15 en es (los 11 pedidos + Santa Cueva de Covadonga, Cabrales, Potes, Fuente Dé), 3 en en (Picos de Europa, Covadonga, Picos de Europa National Park) y 2 en fr (Pics d'Europe, Covadonga). Los ficheros en/fr llevan sufijo `_en`/`_fr`. Cada JSON es `{"meta": {...}, "respuesta": <JSON tal cual de la API>}`; `meta` añade parámetros y fecha de descarga (única desviación del "tal como llega", para no perder la trazabilidad).

**Comportamiento de días sin visitas (medido con llamadas reales, ver `data/raw/wikipedia_sonda_dias_ausentes.json`):**
- Un título sin datos en todo el rango da **HTTP 404** (`Mirador_de_Entrelagos` en 2022; un título inexistente; también `Lagos_de_Covadonga` pedido para 2015-01 a 2015-06, antes de que existan datos en la API).
- Con datos parciales, la API **omite los días sin registro**: `Lago_de_la_Ercina` devolvió 296 de 365 días de 2022.
- Además, en los ficheros descargados aparecen **días con `views: 0` explícito** (`covadonga_fr`: 405 ceros y 630 días omitidos de 1748; `parque_nacional_de_los_picos_de_europa`: 7 ceros y 1 día omitido, 2022-03-17; `descenso_internacional_del_sella`: 1 cero). No sé por qué coexisten ceros explícitos y días omitidos **[NO VERIFICADO]**.
- Consecuencia: al limpiar hay que reindexar a calendario completo y decidir el valor de los días ausentes. Hipótesis razonable: ausente = 0 visitas (el artículo existe y se consulta pocas veces), pero hay que decidirlo. Los artículos grandes (todos los de es salvo uno) están completos y sin ceros, así que el problema afecta solo a artículos pequeños y a `covadonga_fr`.
- Otros 17 ficheros: 1748 registros sin huecos.

**Observaciones útiles:** `picos_de_europa` (es) tiene un máximo de 61.525 visitas/día frente a mínimos de 55: hay al menos un pico muy anómalo (p. ej. un evento mediático o tráfico automatizado que la clasificación `user` no filtró; causa **[NO VERIFICADA]**). Revisar antes de usar como señal.

## 2. Google Trends

**Descargado con pytrends (no oficial)**, pausa de 60 s entre consultas, serie semanal 2022-01-01 → 2026-10-15 (251 filas; la primera fila es la semana que empieza el 2021-12-26 y la última, 2026-10-11, está marcada `isPartial=True`):
- ES: lagos de covadonga, llanes, cangas de onís, ruta del cares, covadonga (5 ficheros).
- ES-MD: lagos de covadonga, llanes, cangas de onís, ruta del cares (4 ficheros).
- Cada consulta incluye el ancla "picos de europa" más un término.

**Bloqueo:** al pedir `ES-MD / covadonga` Google devolvió **HTTP 429 (TooManyRequestsError)** tras 9 consultas (≈10 minutos con 60 s de pausa). Paré, sin proxies ni reintentos. No se han descargado: ES-MD covadonga, todo ES-CL, todo ES-AS, y **ninguna ventana diaria**.

**Problema grave del ancla elegida:** "picos de europa" tiene **un único pico de 100 en la semana del 2023-09-17** y su mediana semanal es 3. Al escalar cada consulta al máximo, los demás términos quedan aplastados: "cangas de onís" máx. 2–3, "ruta del cares" máx. 4, "lagos de covadonga" máx. 16–17, "llanes" máx. 38. Son valores enteros con muy poca resolución (0, 1, 2…), inservibles para series. Esto es medido en los ficheros. Antes de seguir hay que cambiar de ancla (ver decisiones).

**Datos a tener en cuenta (conocimiento general, no comprobado en documentación oficial en esta sesión, **[NO VERIFICADO]**):** índice relativo 0–100 dentro de cada consulta; granularidad diaria solo para ventanas cortas (en torno a 9 meses o menos; confirmar el límite actual), semanal o mensual para periodos largos; la muestra cambia entre descargas, por lo que conviene repetir y promediar. Confirmado empíricamente: para 2022-2026 la granularidad devuelta fue semanal.

### Exportación manual que te toca (trends.google.es)
Hazlo en una ventana normal del navegador, sin prisa (unos 20 s entre exportaciones). Para cada consulta: https://trends.google.es/trends/explore → región, periodo, hasta 5 términos separados (botón "+ Añadir término") → icono ↓ "Descargar CSV" en el gráfico "Interés a lo largo del tiempo". Nombra el CSV como `trends_<geo>_<periodo>_<terminos>.csv` y súbelo a `data/raw/trends/`.

Qué falta, en orden de prioridad (usa **ancla nueva**, ver decisión 1; si la aceptas, la propuesta es "covadonga" o "lagos de covadonga" como ancla porque tienen más volumen estable):
1. **España, 01/01/2022 – hoy, todas las categorías, Búsqueda web**, términos: `covadonga`, `lagos de covadonga`, `llanes`, `cangas de onís`, `ruta del cares` (5 términos en una sola consulta; el ancla ya va incluida entre ellos). Es la serie semanal comparable. Repite con `picos de europa` en una consulta aparte con `covadonga` como enlace.
2. Lo mismo con región **Comunidad de Madrid**, **Castilla y León** y **Principado de Asturias**.
3. **Ventanas diarias solapadas** (para encadenar): para España, periodos de 8 meses con solape de 1 mes, por ejemplo 01/01/2022–31/08/2022, 01/08/2022–31/03/2023, 01/03/2023–31/10/2023… hasta hoy, con los mismos términos y la misma ancla. Comprueba en el CSV que las filas sean diarias; si salen semanales, acorta la ventana.
4. Opcional: Madrid y Castilla y León en diario solo para `covadonga` y `lagos de covadonga`.

## 3. OAPN: visitantes del Parque Nacional de los Picos de Europa

**Descargados (todos con texto extraíble, no son imágenes escaneadas; probado con pypdf):**
- `oapn_visitantes_2022..2025.pdf`: informes "Visitantes en la Red de Parques Nacionales" (9, 10, 13 y 18 páginas).
- `oapn_memoria_red_2018..2021.pdf`: memorias anuales de la Red (501, 214, 205 y 205 páginas). El de 2018 pesa 17 MB y su extracción es lenta.
- Todo desde miteco.gob.es. URLs en `OAPN_PDFS` de `src/descarga_senales.py`. No hay informe de visitantes separado para 2018–2021; esos años van dentro de las memorias. No existe memoria de la Red para 2022-2025 en lo que he encontrado (no buscado a fondo, **[NO VERIFICADO]**).
- Nota: en la URL 2024 hay un nombre alternativo (`Visitantes_RedPPNN_2024.pdf`) que devuelve una página HTML de error; la buena es la que sigue el patrón del informe 2023.

**Cifras de Picos de Europa según el documento oficial:**

| Año | Visitantes | Documento y página (PDF) | Coincide con la referencia previa |
|---|---|---|---|
| 2015 | 1.913.858 | memoria 2021, p. 129 (tabla "Visitas anuales") | n/a |
| 2016 | 2.101.293 | idem | n/a |
| 2017 | 2.047.956 | idem | n/a |
| 2018 | 1.958.240 | idem (también memoria 2019, p. 147 y memoria 2020, p. 142; no localizado en el texto de la memoria 2018) | n/a |
| 2019 | 1.791.410 | idem | n/a |
| 2020 | 1.383.338 | idem | n/a |
| 2021 | 1.620.739 | idem | n/a |
| 2022 | 1.798.533 | informe visitantes 2022, p. 4 | **Sí** (1.798.533) |
| 2023 | 1.698.780 | informe visitantes 2023, p. 5 | **Sí** (1.698.780) |
| 2024 | 1.632.805 | informe visitantes 2024, p. 5 | **Sí** (1.632.805) |
| 2025 | 1.565.899 | informe visitantes 2025, p. 7 | n/a (dato nuevo) |

(2022–2025 localizados en el texto del informe; 2015–2021 en una tabla de texto de la memoria 2021. No comparé 2022-2025 contra la tabla del informe anual, por si hubiera revisiones: solo he leído la frase del texto.)

**Metodología:** según los informes, las cifras son una mezcla de conteos directos y estimaciones modeladas de visitas independientes, aportadas por cada parque al Sistema de Información de la Red (SIR). Cada parque usa metodologías distintas, así que las cifras son comparables en el tiempo dentro de un parque, no tanto entre parques.

**Datos mensuales o por punto de acceso:**
- Mensuales: los informes 2022–2025 solo publican **gráficos con el porcentaje mensual** de visitas por parque (informe 2023 p. 5–7, informe 2024 p. 5–9, informe 2025 p. 8–13), no tablas numéricas. Los valores del gráfico no se extraen como texto. Los informes 2024 (p. 12) y 2025 (p. 18) dicen que **los datos mensuales brutos por parque se piden a `seguimiento@oapn.es`**.
- Por punto de acceso (centros de visitantes, Lagos): **no los he encontrado**. En la memoria 2021 solo vi menciones a los centros Pedro Pidal y Sotama en venta de publicaciones. Búsqueda no exhaustiva: **[NO VERIFICADO]** que no existan en otras secciones de la ficha de Picos.

## Dificultades y avisos
- pytrends es no oficial y bloquea pronto (429 a la décima consulta con 60 s de pausa). `pip install pytrends` fue lo único instalado (además de `pypdf` para leer los PDF).
- Los ficheros de Wikipedia y Trends tienen la fecha de descarga dentro de `meta`.
