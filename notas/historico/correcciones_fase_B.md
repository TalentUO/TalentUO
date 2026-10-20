# Correcciones de la fase B (tras la auditoría)

> **Documento histórico.** Correcciones aplicadas el 2026-10-15 tras la auditoría de la fase B. Se conserva como registro; el estado final de los datos está en `notas/diccionario_B.md` y `notas/control_calidad_B.md`.

Fecha: 2026-10-15. Orden y numeración de la tarea. Regla general: nada borrado en `data/raw/`; lo inválido va a `_descartados/`; ningún dato en bruto transformado. Parte A (MITMA, INE, SADEI) no tocada.

## 1. Open-Meteo

### 1a. Procesos duplicados
- **Qué había:** a las 17:40 no había **ningún** proceso `python … descarga_openmeteo.py` en marcha (`Get-CimInstance Win32_Process`). Los dos procesos que ve el informe y que aún aparecían eran dos `bash.exe` (padre PID 25016 e hijo PID 2820, iniciados 16:12) que ejecutan un bucle de espera `until ! pgrep -f descarga_openmeteo … tail /tmp/p/run.log`: es un vigilante de otra sesión, no una descarga; no escribe ficheros. No lo he tocado.
- **Resultado:** quedan 0 descargas activas (la descarga había terminado a las 17:38: último fichero `openmeteo_prevision_ejemplo.json`). Después lancé yo una sola ejecución (`--solo archive`) para el ERA5 que faltaba (ver 1d); terminó a las 18:04 y no hay otra en marcha.
- **Riesgo de ficheros a medias:** descartado. Validé los 28 JSON (9 hist + 9 previous + 9 ERA5 + previsión): todos abren; Historical Forecast y ERA5 tienen exactamente los 1749 días 2022-01-01 → 2026-10-15 contiguos; Previous Runs las 24 456 horas 2024-01-01 00:00 → 2026-10-15 23:00 contiguas; el contenido de cada JSON final es idéntico a la concatenación de sus tramos en `_chunks/` (comparación de listas). No ha hecho falta redescargar nada.

### 1b. Descarga completa
- 9/9 zonas de `config/zonas_meteo.csv` con Historical Forecast, Previous Runs y (ahora) ERA5, más `openmeteo_prevision_ejemplo.json` (7 días, 2026-10-15 → 10-21).
- **Nulos:** Historical Forecast y ERA5: 0 en todas las variables y zonas. Previous Runs: solo en `*_previous_dayN` (446, 470 y 494 horas por variable en day1/day2/day3, las horas anteriores al 2024-01-19 14:00, 01-20 14:00 y 01-21 14:00; 8460 nulos por fichero, igual en las 9 zonas); el día 0 no tiene nulos. Previsión de ejemplo: 0.
- **Rango temporal** documentado arriba y en la tabla de `notas/fuentes/openmeteo/registro_openmeteo.md` (regenerada por el script). El último día (2026-10-15) es el de la descarga: puede estar incompleto (no verificado).
- Cambio en `src/descarga_openmeteo.py`: `ZONAS_ARCHIVE` ahora incluye las 9 zonas (antes solo Covadonga y Cangas) para poder comparar por zona (1d).
- `notas/fuentes/openmeteo/registro_openmeteo.md`: estado, tabla de coordenadas, pendientes y nota sobre el corte actualizados.
- **Abierto:** `aud_openmeteo_resumen.py` imprime mal los nombres de zona de los ficheros archive en su última línea (`lstrip` de caracteres); es cosmético del script de auditoría, los ficheros están bien.

### 1c. Coordenadas
- Geocodificación Open-Meteo (`geocoding-api.open-meteo.com`): "Basílica de Covadonga" → 43,3082 / −5,0549 (258 m) = ~0,4 km de nuestro punto (43,31 / −5,05). **Covadonga verificada.** Wikipedia (es): Covadonga 43,3121 / −5,0589.
- **Lagos:** la API de geocodificación no tiene "Lago Enol", "Lagos de Covadonga", "Ercina" (probados). Verificación alternativa con Wikipedia: Lago Enol 43,2721 / −4,9911; Lago Ercina 43,2679 / −4,9809; Lagos de Covadonga 43,2683 / −4,9859 → nuestro punto (43,27 / −4,99) a ~0,25 km del Enol. API de elevación de Open-Meteo (DEM): 1070 m en el punto (1075 m en 43,2705 / -4,9926, cerca del Enol), coherente con el lago (~1070 m). **Verificada con Wikipedia, no con la API de geocodificación.**
- Elevación del punto devuelta en las respuestas: Covadonga 278 m (basílica 258–260 m), Lagos 1070 m, Cangas 70, Llanes 4, Ribadesella 11, Gijón 30, Oviedo 249, Madrid 667, Sevilla 16. Ningún punto cae en un valle/costa de forma que se desvíe de lo esperado. **Salvedad:** esa es la elevación del DEM del punto, no la de la celda del modelo (que es lo que condiciona lluvia y viento y no se conoce); los Lagos tendrán sesgo orográfico (>2000 m cercanos).
- Rejilla devuelta: para Historical Forecast/Previous Runs el punto cae a ≤ 0,01° salvo Madrid (~3 km) y Sevilla (~3 km); el ERA5 de Covadonga y Cangas cae ~5–6 km al norte/oeste. No hay nada que corregir ni redescargar. `config/zonas_meteo.csv` **sin cambios**; `provisional=si` se mantiene (la lista final de zonas es decisión del equipo).

### 1d. Tramo 2022 (fuga)
- Descargado el ERA5 de las 7 zonas que faltaban. Resultado y opciones en `notas/fuentes/openmeteo/openmeteo_tramo_2022.md` (script: `src/auditoria/tramo_2022_openmeteo.py`).
- Cortes: 7 zonas asturianas, último día idéntico a ERA5 = 2022-11-08 (primer día de previsión 2022-11-09); Madrid y Sevilla: 2022-11-15 / 2022-11-16. Previous Runs **no** cubre el tramo (day1 nulo en todo 2022–2023).
- **Abierto (decisión vuestra):** qué hacer con el tramo; la temperatura del tramo no se puede clasificar con este método.

## 2. Calendarios

- **2a:** `juridicas_res_calendario_escolar_asturias_2021-22.html` (25 bytes, "ERROR Host NO CONFIGURADO") movido a `data/raw/calendario/_descartados/`. Corregidos `notas/fuentes/calendarios/registro_calendarios.md` (celda marcada NO OBTENIDO), `notas/fuentes/calendarios/inventario_calendarios.md` (dos frases) y la fila de `data/raw/calendario/_verificacion.csv` (`no_obtenido_error_pagina`). Reintento de la URL el mismo día: sigue dando el mismo error; sin copia en Internet Archive (API de disponibilidad: sin snapshots).
- **2b:** `src/descarga_calendarios.py` ahora valida los HTML (≥ 1000 bytes y sin mensaje de error en los primeros 1500 bytes: "host no configurado", "access denied", "forbidden", "page not found", "404 not found", "service unavailable", "bad gateway", "error 404", "no encontrada"). Probado: rechaza el contenido de 25 bytes (`error_html_demasiado_corto`) y una página "404 Not Found" (`error_html_mensaje_de_error`) y acepta los 9 HTML reales guardados. Comprobado con el manifiesto: 54/55 ficheros presentes y válidos; falta solo el de Noticias Jurídicas.
- **2c:** una búsqueda (web + Internet Archive + prueba de URL del BOPA) del BOPA nº 104 de 1-jun-2021 (Res. 5-may-2021, calendario escolar 2021-22) sin resultado. **Hueco conocido**, no se insiste. Queda como alternativa oficial el calendario gráfico de Educastur (`educastur_calendario_escolar_2021-22_grafico.pdf`) y el BOPA 2021-08142 (modificación para FP).
- Abierto: el correo personal sigue en el `User-Agent` de `descarga_calendarios.py` (hallazgo menor del informe; no estaba en esta tarea, no lo he cambiado).

## 3. Menores

- README línea 16: el carácter BEL (0x07) sustituido por `\a` → `.venv\Scripts\activate`. Verificado con `sed -n 16p`.
- `requirements.txt`: añadidos `pytrends==4.9.2` y `pypdf==6.20.1` (las versiones instaladas/disponibles; pytrends instalado en `.venv` el 2026-10-15). Añadidos también a `requirements-lock.txt` (con `lxml==6.1.3`, dependencia de pytrends). Falta documentar la dependencia externa de poppler (`pdftotext`/`pdfinfo`) que usa `descarga_calendarios.py`: **abierto**, no lo he añadido al README.
- `data/manual/eventos_recopilado.csv`: "Cangas de Onis" → "Cangas de Onís" en las 5 filas de la Fiesta del Pastor (solo la columna `concejo`; bytes de las demás columnas sin cambios; el BOM y los saltos de línea se conservan). Queda "Onis" solo dentro de una nota de texto libre.

## 4. Eventos

- **4a (verificación):** intento de verificar contra fuente oficial o del organizador: **no he conseguido verificar ninguna edición nueva**; el estado de las filas no ha cambiado (35 verificado / 339 probable / 4 no_encontrado).
  - Sella (5/5), San Mateo (5/5), Nava 2023–2026 y Semana Negra 2022/2024/2026 ya estaban verificados. Fiesta del Pastor 2022–2025: solo hay previas de prensa (El Fielato, Cope Ribadesella, El 21 Asturias) y la web oficial de Turismo Asturias da una descripción genérica (se celebra siempre el 25 de julio) sin cartel por año; el Ayuntamiento de Cangas de Onís no aparece en el buscador. Siguen `probable`.
  - Semana Negra 2023 y 2025: las URL oficiales (`semananegra.org/?p=…`, `agenda_xxxvi`, `agenda_xxxviii`) devuelven 404 o son de otra edición; los 7–16 julio 2023 y 4–13 julio 2025 solo constan en terceros. Nava 2022: no localizada fuente oficial. Siguen `probable`.
  - **FIDMA 2025: discrepancia no resuelta.** El CSV dice 1–17 agosto. Diario de León y asturias.com dan **2–17 agosto** (68.ª edición; el 1 de agosto de 2025 fue viernes y las demás ediciones empiezan en sábado: 2022-08-06, 2023-08-05, 2024-08-03, 2026-08-01). No he cambiado la fecha porque no tengo la fuente oficial de la Cámara de Comercio: **posible error de un día en `fecha_ini` de FIDMA 2025**, a decidir/confirmar.
- **4b (FIDMA 2023):** la URL de la Universidad de Oviedo (`…/motostudent/en/wolfast-at-fidma-2023/` y la variante `?p=2326` que devuelve el buscador) sigue dando 404. No se encuentra fuente alternativa: marcada en el campo `notas` como NO ENCONTRADA / fecha no verificada (sigue `probable`).
- **4c (partidos):** contrastados con las páginas de resultados de laliga.com (jornadas, hora en UTC) 7 partidos en casa de Oviedo/Sporting: Oviedo–Valladolid 2022-03-13 18:15, Sporting–Tenerife 2022-03-13 16:00, Oviedo–Ibiza 2022-09-17 16:15, Oviedo–Huesca 2022-10-12 18:30, Sporting–Almería 2025-02-22 21:00, Sporting–Tenerife 2025-04-05 21:00, Oviedo–Betis 2026-01-10 14:00 (Primera). **7/7 coinciden en fecha y hora** (CSV en hora de Madrid = hora de LaLiga + 1 h en invierno, + 2 h en verano). Es una muestra (temporadas 2021-22, 2022-23, 2024-25, 2025-26; ninguna de 2023-24 ni partido aplazado), no una verificación completa.
- **4d (cruceros):** una búsqueda (web de la Autoridad Portuaria y prensa/turismo profesional): solo cifras agregadas de prensa (≈21 buques en 2024, sin fechas) y previsiones. No hay escalas realizadas por fecha. Borrador de correo en `notas/fuentes/eventos/solicitud_cruceros.md`; factor documentado como **no disponible 2022–2024**.

## 5. Google Trends

- **Ancla nueva: "cabrales"** (antes "picos de europa"). Elegida midiendo el volumen relativo de candidatas en España 2022-2026 (pytrends, pruebas pequeñas): covadonga media 17, ribadesella 16, llanes 31, lagos de covadonga 5, cangas de onís 2,7, ruta del cares 2,3, **cabrales 6,3 (máx. 18, sin picos)**, fuente dé 0,4, descenso del sella 3,2. Es estacional y estable (a diferencia de "picos de europa", con un único 100 y mediana 3) y está a ≤ 6× de los términos grandes y pequeños. Salvedad: "cabrales" también es un queso, así que solo sirve como ancla de escala, no como señal turística.
- `src/descarga_senales.py`: `TRENDS_ANCLA = "cabrales"`; los ficheros nuevos van a `data/raw/trends/ancla_cabrales/` (los 9 anteriores con ancla "picos de europa" se conservan intactos).
- **Descargado** (ES, semanal, 251 filas, pausa de 90 s): `lagos de covadonga`, `llanes`, `cangas de onís`. Mediana semanal del término / del ancla: lagos 9 (máx. 100) / 13; llanes 24 / 5; cangas 13 / 31; **0 semanas a cero en todos** (antes: cangas máx. 3, mediana 1, 22 ceros). No se cumple estrictamente "20–80" en la mediana (lagos 9, cangas 13): los términos tienen volúmenes muy distintos y un solo ancla no los deja a todos en ese rango; la resolución es, con todo, claramente utilizable.
- **429 (TooManyRequestsError) en la 4.ª consulta** (`ES / ruta del cares`). Paro, sin proxies ni reintentos. **Faltan 17 consultas**: ES `ruta del cares`, `covadonga`; y los 5 términos en `ES-MD`, `ES-CL`, `ES-AS`.
- (Una vez parada, no se relanzó: varias esperas en segundo plano se cerraron además por falta de memoria del sistema.)

### Exportación manual exacta para las consultas que faltan
En una ventana normal del navegador (sesión de Google iniciada si es posible), con ~30 s entre exportaciones, en https://trends.google.es/trends/explore:
1. Periodo: **personalizado 01/01/2022 – 15/10/2026** (todo el rango, para que sea semanal). Categoría: todas las categorías. Búsqueda web.
2. Para cada región (**España**, **Comunidad de Madrid**, **Castilla y León**, **Principado de Asturias**) y cada término **T** de la lista [`ruta del cares`, `covadonga` en España; `lagos de covadonga`, `llanes`, `cangas de onís`, `ruta del cares`, `covadonga` en las otras tres], escribe **dos términos**: `cabrales` y **T** (exactamente en ese orden y con esas grafías). Descarga con el icono ↓ "Descargar CSV" de "Interés a lo largo del tiempo".
3. Nombra cada CSV `trends_semanal_<T sin tildes ni espacios, con _>_<geo>.csv` (geo = ES, ES-MD, ES-CL o ES-AS; ejemplo `trends_semanal_ruta_del_cares_ES.csv`) y guárdalo en `data/raw/trends/ancla_cabrales/manual/`. No edites el CSV.
4. Comprueba que las filas son semanales (251 filas) y que la columna `cabrales` no sale en cero; si el término sale en 0–4 con "cabrales" en 100, avísame antes de seguir.
5. Ventanas diarias (opcional): periodos de 8 meses con solape de 1 mes, mismos dos términos; solo si hacen falta.
