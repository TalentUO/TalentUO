# Auditoría independiente de la fase B (descarga en bruto de factores explicativos)

> **Documento histórico.** Auditoría del 2026-10-15 sobre la descarga en bruto de los factores (fase B). Describe el estado de ese momento: Open-Meteo aún descargaba y faltaba la zonificación del MITMA. Las correcciones están en `notas/historico/correcciones_fase_B.md` y el estado final de los datos, en `notas/diccionario_B.md` y `notas/control_calidad_B.md`.

Fecha de la auditoría: 2026-10-15, 17:00–17:35. Auditoría de solo lectura: no se ha tocado nada de `data/raw/` ni de `data/manual/`. Lo único escrito en el repositorio es este informe y los scripts de comprobación de `src/auditoria/` (`aud_aemet.py`, `aud_aemet_live.py`, `aud_openmeteo.py`, `aud_openmeteo_live.py`, `aud_openmeteo_resumen.py`, `aud_calendarios.py`, `aud_senales.py`). Las pruebas de reproducibilidad se hicieron en una copia temporal fuera del repositorio.

**Aviso importante sobre Open-Meteo:** cuando se escribió este informe la sesión de Open-Meteo **seguía descargando** (dos procesos `python src/descarga_openmeteo.py` activos desde las 17:06; aparecían ficheros nuevos cada pocos minutos). Todo lo que se dice de ese bloque es una foto de las 17:28-17:30 (a las 17:30 ya había 6 de 9 zonas en Historical Forecast y en Previous Runs; faltaban oviedo, madrid, sevilla y la previsión en vivo). Para ver el estado actual: `python -X utf8 src/auditoria/aud_openmeteo_resumen.py`.

Escala de veredictos: **CUMPLE**, **PARCIAL**, **NO CUMPLE**, **NO VERIFICABLE**. Cuando un registro dice una cosa y el fichero otra, se anota como hallazgo.

---

## 1. Veredicto global (5 líneas)

1. **No está lista del todo para pasar a limpieza: sí para AEMET, Calendarios, Wikipedia/OAPN y los eventos locales y partidos; no para Open-Meteo ni para cruceros.**
2. Los datos descargados son buenos: no se encontró ningún valor alterado, duplicado ni inventado en lo que se pudo contrastar con la fuente (AEMET, Open-Meteo, Wikipedia, 6 PDF oficiales por hash, 3 partidos en vivo en LaLiga, 3 cruceros contra el PDF).
3. Lo que falla es **cobertura**: Open-Meteo va por 5 de 9 zonas y le falta la previsión en vivo; cruceros 2022-2024 no existen (y 2025-2026 son previsiones, no escalas); Trends tiene un ancla inservible.
4. Hay **una afirmación falsa en los registros** (el HTML de Noticias Jurídicas figura como obtenido y es una página de error de 25 bytes) y un fallo del script que lo causó.
5. **No se puede cruzar con la zonificación MITMA** porque `data/raw/zonas_mitma_asturias.csv` no existe todavía (parte A).

## 2. Tabla resumen

| Bloque | Veredicto | Hallazgos principales |
|---|---|---|
| 1. AEMET | **CUMPLE** | 12 estaciones + inventario (926) + previsión, todo válido, 0 fechas duplicadas, rango 2022-01-01 a 2026-10-11 (4 días de retraso al bajar; hoy la API llega a 2026-10-12). Huecos y cobertura coinciden exactamente con los registros. Muestra de 10 días contrastada con la API: idéntica. Menores: nombre con codificación rota en la previsión; 1178R y 1203D tienen huecos/corte; 1208/1208A ya no se reproducen con el script. |
| 2. Open-Meteo | **PARCIAL** (en curso) | Lo descargado es correcto y reproducible (3 fechas y 1 día horario contrastados con la API, 0 diferencias). Pero solo 5-6 de 9 zonas, falta `openmeteo_prevision_ejemplo.json`, y la tabla de `notas/fuentes/openmeteo/registro_openmeteo.md` está desfasada. Todas las coordenadas siguen `provisional=si`. Confirmado: el tramo 2022-01-01→2022-11-09 de Historical Forecast se comporta como reanálisis. |
| 3. Calendarios | **PARCIAL** | 55/55 ficheros registrados existen; páginas, año y comunidad coinciden en todos los PDF; 6 PDF re-descargados son idénticos por hash. Defectos: `juridicas_...html` es una página de error ("ERROR Host NO CONFIGURADO") registrada como obtenida; falta el BOPA oficial del curso 2021-22 (documentado); correcciones/modificaciones de BOPA no bajadas (documentado). Solo el folleto de Lagos es imagen. |
| 4. Eventos | **PARCIAL** | CSV con las 13 columnas, 378 filas, ninguna sin fuente ni estado, sin duplicados, fechas válidas. Partidos coherentes con football-data (208/208) y con LaLiga 2026-27 (42/42). **Cruceros 2022-2024: NO CUMPLE** (3 filas `no_encontrado`); 2025-2026 son previsiones. 339 de 378 filas (89,7 %) son `probable`. |
| 5. Señales (opcional) | **PARCIAL** | Wikipedia: **CUMPLE** (20 artículos, rangos y huecos idénticos al registro, sin redirecciones, 3 valores contrastados en vivo). OAPN: **CUMPLE** (2022-2025 coinciden con la referencia, diferencia 0). Trends: **PARCIAL** (9 ficheros válidos con parámetros guardados, pero el ancla "picos de europa" aplasta los demás términos a 0-4; sin ventanas diarias; falta ES-MD de covadonga). |
| 6. Transversales | **PARCIAL** | Scripts reproducibles (AEMET, Open-Meteo, Wikipedia y Calendarios probados: salen los mismos datos) y sin claves ni rutas personales. Nada modificado en `data/raw/`. Cruce con zonas MITMA: **NO VERIFICABLE** (fichero inexistente). Menores: carácter BEL en el README, `requirements.txt` sin `pytrends`/`pypdf`, correo personal en un `User-Agent`, 4 PDF duplicados entre sesiones, `notas/fuentes/demanda/registro_descargas.md` vacío. |

---

## 3. Hallazgos detallados

### 3.1 AEMET — CUMPLE

**Qué se comprobó y resultado** (script `src/auditoria/aud_aemet.py`):

- Ficheros: `aemet_inventario.json` (926 estaciones, sin indicativos duplicados), `aemet_prediccion_ejemplo.json` (municipios 33012 y 33036, 7 días cada uno) y 12 `aemet_diario_<indicativo>.json`, uno por cada estación de `notas/fuentes/aemet/estaciones_aemet.md` (1178R, 1179B, 1183X, 1186P, 1199X, 1203D, 1207U, 1210X, 1212E, 1249X, 3195, 5783). Los 12 indicativos existen en el inventario.
- Estaciones exigidas: 1212E Asturias Aeropuerto, 1249X Oviedo, 1183X Llanes, 3195 Madrid Retiro, 5783 Sevilla Aeropuerto, y para Cangas/Picos 1186P Amieva-Panizales (con 1179B Cabrales, 1178R Sotres como alternativas). Justificación en `notas/fuentes/aemet/decisiones_aemet.md` (distancias 7-10 km). Comprobé las coordenadas del inventario: 1186P está en 43°16'N, 5°07'W, coherente con las distancias declaradas.
- JSON válidos y sin transformar en valores: todo sigue como texto con coma decimal (`"15,0"`), `Ip` en precipitación (1207U 51 días, 1212E 122, 1249X 72, 5783 86: coincide con lo declarado). Cada `aemet_diario_X.json` es exactamente la concatenación de sus tramos (`aemet/tramos/`, 117 ficheros), comprobado con igualdad de listas para las 12 estaciones.
- Contraste con la fuente: 1186P del 2024-08-01 al 2024-08-10 re-pedido a la API: 10/10 registros idénticos. 1203D junio 2026: la API devuelve 4 días y el fichero tiene 4 (la serie termina de verdad el 2026-06-04). Repetí la descarga de enero de 2022 para 1186P, 1212E, 3195 y 1178R: idénticas.

| Estación | Registros | Fechas dup. | Rango real | Huecos ≥5 días | ¿Coincide con `notas/fuentes/aemet/cobertura_aemet.md` / `notas/fuentes/aemet/estaciones_aemet.md`? |
|---|---|---|---|---|---|
| 1178R Sotres | 1185 | 0 | 2022-01-01 a 2026-10-11 | 2022-01-16→2023-07-06 (537), 2024-03-02→03-19 (18) | Sí |
| 1179B Cabrales | 1679 | 0 | idem | 5 (2024-03-26..31 de 6, 07-06..10 de 5, 07-12..23 de 12, 2025-08-01..08 de 8, 2026-05-10..15 de 6) | Sí (el registro cita 12 y 8) |
| 1183X Llanes | 1673 | 0 | idem | 2023-08-11→08-21 (11), 2023-09-28→10-02 (5) | Sí |
| 1186P Amieva | 1741 | 0 | idem | ninguno (faltan 4 días sueltos) | Sí |
| 1199X Piloña | 1736 | 0 | idem | ninguno | Sí |
| 1203D Colunga | 1616 | 0 | 2022-01-01 a 2026-06-04 | ninguno dentro del rango; **133 días de retraso** | Sí |
| 1207U Gijón Campus | 1696 | 0 | 2022-01-01 a 2026-10-11 | ninguno ≥5 | Sí (precip. 81 %) |
| 1210X Cabo Peñas | 1645 | 0 | idem | 28 (2024-08-16..09-12), 21 (2026-04-07..27), otros 4 de 5-7 | Sí |
| 1212E Aeropuerto | 1745 | 0 | idem | ninguno (serie completa) | Sí |
| 1249X Oviedo | 1732 | 0 | idem | 11 (2023-10-05..15) | Sí |
| 3195 Madrid | 1744 | 0 | idem | ninguno (falta 1 día) | Sí |
| 5783 Sevilla | 1745 | 0 | idem | ninguno | Sí |

- `notas/fuentes/aemet/cobertura_aemet.md` es **idéntico** a lo que regenera el propio script desde los JSON (recalculado: sin diferencias). La nota de `notas/fuentes/aemet/decisiones_aemet.md` de que "solo se revisó el principio" no afecta: la tabla completa es correcta.
- Retraso respecto a hoy (2026-10-15): última fecha 2026-10-11 → 4 días. Llamando hoy a la API, la última fecha disponible de 1212E es 2026-10-12 (3 días); es un retraso estructural de AEMET, no del script. Salvo Colunga (133 días). El rango pedido era "cerca de hoy": CUMPLE.
- Script `src/descarga_aemet.py`: reanudable (salta tramos válidos o registrados como 404 antiguos), la clave solo se lee de `AEMET_API_KEY`, no hay clave ni ruta personal. Prueba mínima (todas las estaciones, enero 2022) ejecutada en copia aparte: sin errores, 1 tramo por estación, resultado idéntico al guardado.
- **Clave:** `AEMET_API_KEY` está definida. Búsqueda de su valor en todo el árbol de trabajo (`data/`, `notas/`, `src/`, `config/`, README, `.git` a nivel de fichero) y con `git grep` sobre los 8 commits de todas las ramas: **no aparece en ningún sitio** (0 ficheros, 0 commits). No se imprimió ni se escribió.

**Observaciones (no bloqueantes):**

1. `aemet_prediccion_ejemplo.json`: el nombre del municipio 33012 está con codificación rota (`"Cangas de OnÃ\xads"`). Causa verificada en vivo: la respuesta declara `charset=ISO-8859-15` pero ese byte viene en UTF-8; el script prueba UTF-8, falla por otros bytes y recurre a latin-1 para todo el documento. El script actual reproduce el mismo resultado. Solo afecta a un campo de nombre; el resto de acentos es correcto.
2. `notas/fuentes/aemet/decisiones_aemet.md` dice que los ficheros están "vueltos a serializar con sangría de 1 espacio" (no son bytes idénticos a la API). Es correcto y está declarado; los valores sí son idénticos.
3. 1208 y 1208A se sacaron del diccionario `ESTACIONES`: el script ya no reproduce esos intentos; solo queda constancia en `estado_tramos.json` (20 entradas 404) y en las notas.
4. Etiquetas del script: "Pilona, Bargaú"; el inventario dice "PILOÑA, BARGAÉU" (los registros escriben "Bargañu"). Cosmético.
5. La variable `sol` solo existe en 1212E, 1183X, 1249X, 1207U y 5783 (comprobado en los JSON); en 1186P está vacía, como dicen las notas.

### 3.2 Open-Meteo — PARCIAL (en curso)

**Estado a las 17:28** (`aud_openmeteo_resumen.py`): existen 12 ficheros: Historical Forecast de covadonga, lagos_enol, cangas_de_onis, llanes, ribadesella (y gijon en descarga); Previous Runs de covadonga, lagos_enol, cangas_de_onis, llanes, ribadesella; ERA5 de covadonga y cangas_de_onis. **Faltan** (a esa hora) oviedo, madrid, sevilla (y gijón en previous), y `openmeteo_prevision_ejemplo.json`. El commit `a02df20` ya lo decía ("Descarga parcial: faltan 7 zonas por el limite horario de la API") y el proceso sigue reintentando.

- Cada fichero presente: sin duplicados de fecha, ordenado, sin huecos. Historical Forecast y ERA5: 1749 días (2022-01-01 → 2026-10-15), 0 nulos. Previous Runs: 24 456 horas (2024-01-01 → 2026-10-15), sin huecos de hora; nulos solo en `_previous_dayN` (446, 470, 494 por variable, exactamente las horas anteriores a 2024-01-19 14:00, 01-20 14:00 y 01-21 14:00). En Covadonga no hay ningún nulo desde 2024-01-22, como dice el registro. Los nulos que declara cada `_descarga` coinciden con los reales.
- Parámetros: zona horaria `Europe/Madrid` en todos; variables = `DIARIAS` / `HORARIAS_PREVIOUS` del script; las unidades son °C, mm, km/h, s y código WMO. Los JSON finales no son la respuesta cruda de la API sino una concatenación de tramos anuales con un bloque `_descarga` añadido y sin `generationtime_ms`. Las respuestas crudas están en `_chunks/` (no versionadas salvo `manifest.json`, como dice la nota). Está declarado y no altera valores.
- **Contraste con la API** (`aud_openmeteo_live.py`): zona lagos_enol, Historical Forecast, fechas 2022-03-15, 2024-08-10 y 2025-12-25: 0 diferencias en las 8 variables. Previous Runs de Covadonga, 2025-07-20 (24 horas, 4 variables): iguales.
- **Afirmaciones del registro verificadas** recalculando desde los ficheros: antes de 2022-11-10 (313 días) la "previsión" es idéntica a ERA5 en 312-313 días para precipitación, horas de precipitación, código de tiempo, viento, racha y sol, y solo 7/313 en Tmax; después, 17-67 de 1436 días idénticos. Sesgo Tmax +0,09 °C (MAE 1,27), precipitación −0,79 mm/día (MAE 2,00; correlación 0,81): coinciden con el registro. Es decir, **el tramo 2022-01-01→2022-11-09 de Historical Forecast no es una previsión** y supone riesgo de fuga. El registro lo dice y lo deja como decisión pendiente.
- Coordenadas y elevación (`config/zonas_meteo.csv`, 9 zonas, **todas `provisional=si`**): covadonga 278 m, lagos_enol 1070 m, cangas_de_onis 70 m, llanes 4 m, ribadesella 11 m. La diferencia Covadonga/Lagos/costa es coherente con el terreno (los Lagos están a ≈1070 m; la costa, a pocos metros). Covadonga y Lagos **no están verificadas con geocodificación** (lo dice el registro); la rejilla ERA5 devuelta para "covadonga" es 43,339/−5,120 (≈3 km al norte y ≈5-6 km al oeste, junto a Cangas) y la de "cangas_de_onis" es 43,409/−5,127 (≈6 km al norte); por tanto la comparación con ERA5 de Covadonga no es punto a punto.
- Informe: `notas/fuentes/openmeteo/registro_openmeteo.md` distingue Historical Forecast, Previous Runs y Archive, recomienda Previous Runs día 1 desde 2024-01-22 (con Historical Forecast desde 2022-11-10 como serie larga) con justificación, y anota límites (600/min, 5000/h, 10 000/día, 300 000/mes), uso solo no comercial y licencia CC BY 4.0. No pude verificar las condiciones de uso contra open-meteo.com (no se consultó la página); las cifras de límites son las del propio registro (**NO VERIFICABLE por mí**).
- **Registro desfasado:** la tabla entre marcadores lista 5 ficheros pero hay 12 en disco (el script la regenera solo al final).
- Script: reanudable por tramo (manifest + fichero), sin claves ni rutas personales. Prueba mínima en copia aparte (1 zona, 5 días, `--solo hist`): sin errores, valores idénticos a los guardados.

### 3.3 Calendarios — PARCIAL

**Comprobación contra los PDF reales** (`aud_calendarios.py`): 55 ficheros en `data/raw/calendario/` (excluyendo `.txt` y `_verificacion.csv`), exactamente los 55 del MANIFEST y los 55 del registro.

- **Páginas:** las de los 45 PDF coinciden con `notas/fuentes/calendarios/inventario_calendarios.md` y `notas/fuentes/calendarios/registro_calendarios.md` (BOE fiestas 6/6/5/5/5/5, BOPA locales 4/4/5/4/4/4, escolar Asturias 2/2/3/3/3, DGT 61/65/61/60/65, OAPN 9/10/13/18, etc.). Ninguna discrepancia.
- **Año y comunidad:** cabecera y texto confirman año y organismo en todos los BOE de fiestas (títulos "para el año 2022…2027"), BOPA de fiestas locales (cada uno "para el año X", con Cangas de Onís, Llanes, Ribadesella, Gijón y Oviedo presentes en los seis años), BOPA de calendario escolar (resolución y curso correctos), Madrid y CyL (orden y curso correctos; las 12 órdenes citadas aparecen en el texto), DGT (BOE nº, fecha y tabla "Covadonga CO-04" en los cinco años).
- **Pistas del enunciado:** el PDF de Educastur 2025-26 **no** es el calendario escolar: su título es "Días sustitutivos de fiestas locales que coinciden con días no lectivos para el curso 2025-2026". BOPA 2026 (nº 114, 16-jun-2025) y BOPA 2027 (nº 110, 10-jun-2026) son realmente las fiestas locales de esos años. Coincide con el inventario.
- **Contraste con la fuente original:** re-descargué 6 PDF (BOE fiestas 2027, DGT 2022, BOPA locales 2027, BOPA escolar 2025-26, CyL 2024-25, Madrid 2026-27) y son **idénticos por hash** a los guardados.
- **Muestra de 10 fechas** contra el PDF: Lagos 2022-04-10 (9-17 abr), 2023-10-29 (28-31 oct), 2024-03-27 (23-31 mar), 2025-04-27 (12-30 y 26-30 abr), 2026-04-19 (18-19 abr); Cangas de Onís fiesta local 2022-06-13, 2023-06-13, 2024-06-13, 2026-09-24; BOE 2026 Día de Asturias 8 sep. **10/10 coinciden** con los PDF (la comparación con "fuente original" se apoya en el hash de los PDF y no en una segunda fuente independiente).
  - **Corrección (2026-10-15, fase de limpieza):** la versión original de esta muestra daba como fiestas locales de Cangas de Onís el 2022-05-16, el 2023-05-29 y el 2026-08-31, y los daba por coincidentes. **Era un error:** se leyeron del `.txt` de pdftotext, que en las tablas del BOPA desalinea las filas y pone junto a "Cangas de Onís" fechas de otros concejos (por ejemplo, el 16 de mayo, San Isidro, en 2022). Sobre la imagen renderizada de cada PDF (BOPA 2021-03949, 2022-03495 y 2025-04744), Cangas de Onís tiene 13-jun y 25-jul en 2022 y 2023, y 13-jun y 24-sep en 2026; el 2024-06-13 sí era correcto. La muestra se ha rehecho con esas fechas, que coinciden con `data/clean/festivos_locales.parquet`. Consecuencia: **el texto `.txt` de los BOPA de fiestas locales no sirve para leer la tabla**; la tabla limpia se valida contra la imagen del PDF (`notas/fuentes/calendarios/validacion_calendario.md`).
- **Dudas del inventario resueltas:** el texto extraído de la tabla de Lagos 2024 se lee bien (23-31 mar, 29-30 abr, fines de semana de abril, 1-3 mayo, 1/VI-13/X salvo 25/VII y 8/IX, 19-20 y 26-27 oct, 1-3 y 30 nov, 1-9 dic). En 2025 "12 al 30 de abril" y "26 al 30 de abril" se solapan **en el propio BOE**: no es error de extracción.
- **Oficial vs prensa:** cinco ficheros `prensa_*` y el HTML municipal (`turismocangasdeonis_*`) están marcados NO OFICIAL en el registro; ningún documento oficial se ha sustituido por prensa. **Internet Archive:** el inventario dice que no se usó y no he encontrado Wayback en `calendario/` (sí en `eventos/`, ver 3.4, donde sí está anotado).
- **PDF de imagen:** solo `turismocangasdeonis_folleto_acceso_lagos.pdf` (2 págs, 0 letras: necesita OCR o transcripción). Los demás tienen texto.
- **Defecto 1 — afirmación falsa:** `juridicas_res_calendario_escolar_asturias_2021-22.html` mide **25 bytes y contiene "ERROR Host NO CONFIGURADO"**. `notas/fuentes/calendarios/registro_calendarios.md` la lista sin problemas y `notas/fuentes/calendarios/inventario_calendarios.md` dice que hay "(b) copia NO OFICIAL del texto en Noticias Jurídicas". Causa: `descarga()` solo valida cabecera `%PDF` en los PDF; un HTML de error se guarda como "descargado". Reproducido en copia aparte (mismo resultado hoy).
- **Defecto 2 — hueco documentado:** el BOPA de 1-jun-2021 (calendario escolar 2021-22 de Asturias) no está; hay solo el calendario gráfico de Educastur (oficial) y el BOPA 2021-08142 (modificación para FP). Está bien documentado como PARCIAL; con el defecto 1, no hay copia del texto oficial del curso 2021-22. Tampoco se descargaron las correcciones del BOPA de fiestas locales 2022 (30-nov-2021) y 2025 (Vegadeo) ni la modificación de calendario 2025-26: declarado, no verificado si existen.
- Observación: `.txt` derivados (pdftotext) conviven con los PDF en `data/raw/calendario/`; está declarado, pero son datos añadidos, no bruto.
- Días regulados de Lagos 2022-2026: presentes (BOE-A-2022-1125, 2023-2159, 2024-1773, 2025-1329, 2026-1255). 2027 no existe aún (esperable).

### 3.4 Eventos — PARCIAL

**Estructura y coherencia** (`data/manual/eventos_recopilado.csv`, 378 filas):

- Las 13 columnas pedidas, en el orden pedido. **Ninguna fila sin `fuente_url`, `fuente_tipo` ni `estado`.**
- Estados: `verificado` 35, `probable` 339, `no_encontrado` 4. Por tipo: crucero_gijon 92 (0 verificado, 89 probable, 3 no_encontrado); partido_futbol 251 (10 verificado, 240 probable, 1 no_encontrado = Copa del Rey); deportivo (Sella) 5 verificados; romería (Pastor) 1 verificado + 4 probable; fiesta (San Mateo 5 verificados; Nava 4 verificados + 1 probable); festival (Semana Negra 3+2; FICX 4+1); feria (FIDMA 3+2).
- Por año (fecha_ini): 2021: 21 (todo partidos), 2022: 49, 2023: 48, 2024: 50, 2025: 86, 2026: 97, 2027: 23.
- Fechas: 374 válidas; las 4 vacías son las filas `no_encontrado`. `fecha_fin` ≥ `fecha_ini` en todas. 0 duplicados por (evento, fecha_ini) y 0 filas exactas repetidas. Los concejos existen en Asturias; **"Cangas de Onis" está escrito sin tilde** (5 filas), inconsistente con "Cangas de Onís" del resto del proyecto y puede romper uniones por texto.
- Cobertura 2022-2026: los **seis eventos locales** tienen una fila por año (Pastor, Sella, San Mateo, Nava, Semana Negra, FIDMA; más FICX como extra). **Partidos**: 21 en casa por club y temporada (Oviedo 19 en Primera 2025-26), temporadas 2021-22 a 2026-27, con la categoría anotada en `competicion`. **Cruceros: solo 2025 (39 escalas) y 2026 (50 escalas), ambas son *previsiones*.** 2022, 2023 y 2024 son `no_encontrado`.
- **Partidos:** recalculé desde `fd_SP1/SP2_*.csv` (218 partidos en casa de ambos clubes): las 208 filas de 2021-22 a 2025-26 coinciden en fecha y en hora (+1 h) con football-data, y no hay partidos de football-data que falten en el CSV. Las 42 filas de 2026-27 coinciden con el JSON-LD de las 42 jornadas guardadas de LaLiga (hora convertida a Madrid con horario de verano/invierno); 29 filas llevan "calendario no confirmado". El único contraste con LaLiga de una jornada pasada (2024-25 jornada 1) coincide (Sporting–Levante 2024-08-18 17:00). **No se contrastó contra una fuente oficial las fechas de las temporadas 2021-22 a 2025-26** (lo dice la propia nota): "fecha realmente jugada" depende de que football-data actualice los aplazados.
- **Cruceros:** los dos PDF son tablas visuales correctas aunque `pdftotext` las desordena. Renderizados: 39 filas en 2025 y 32+18=50 en 2026 (el CSV tiene 39 y 50). Muestra (fila 24 MSC Virtuosa 2025-10-01, 6334 pax; fila 54 MSC Virtuosa 2026-06-01, 6334; fila 67 Nautica 2026-08-29, 824) y las dos primeras de 2025 (Arcadia 2388 y Britannia 3647): coinciden. Las erratas "30/5/05" y "1/10/29" del PDF son reales y fueron corregidas (1/10/25).
- **Muestra de 10 filas** (semilla 20261015; no existen cruceros `verificado`, por eso se usaron `probable`):
  1. Partido fila 300 Sporting–Burgos 2026-08-23 19:00 → LaLiga en vivo 17:00Z = 19:00 Madrid. Coincide.
  2. Partido fila 304 Oviedo–Sporting 2026-09-27 21:00 → LaLiga 19:00Z. Coincide.
  3. Partido fila 306 Oviedo–Eibar 2026-10-12 18:30 → LaLiga 16:30Z. Coincide.
  4. Sella 2022 (339): la noticia del organizador dice que el descenso "culminará el sábado"; 6-ago-2022 es sábado. Coincide.
  5. Sella 2023 (340): la página citada es la crónica sin fecha explícita en el texto; 5-ago-2023 es sábado y el resto de la nota del CSV remite a otras noticias. Coherente, no concluyente por esa sola URL.
  6. Semana Negra 2022 (359): programa guardado "VIERNES 8" (inicio 8-jul). Coincide.
  7. FICX 2023 (365): bases oficiales "del 17 al 25 de noviembre de 2023" (literal). Coincide.
  8-10. Cruceros filas 24, 54, 67 (`probable`): coinciden con el PDF (ver arriba).
- Otras comprobaciones puntuales en bruto: San Mateo 2025 "arranca el jueves 11", Nava 2026 "Martes 7 … XLIX Festival", Semana Negra 2026 "del viernes 3 al domingo 12" y FIDMA 2024 "Del 3 al 18 de agosto" aparecen en los ficheros guardados. **FIDMA 2023** cita una URL de la Universidad de Oviedo que hoy devuelve 404 (el propio registro lo dice): esa fecha es **NO VERIFICABLE** con lo guardado. Las fechas de Pastor 2022-2025 y San Mateo 2022-2024 no se contrastaron una a una.
- **Trazabilidad:** `notas/fuentes/eventos/registro_eventos.md` no recoge la URL exacta de unos 100 ficheros de Sella, Pastor, San Mateo, Nava, Semana Negra, FICX y FIDMA (dice "ver fuente_url en el CSV (dominio en el nombre)"); el propio registro lo reconoce. Wayback anotado: `nava_2023_..._wayback20230702.html`, `nava_2024_..._wayback20240715.html`, `nava_2025_..._wayback20250906.html` y la URL de Wayback de la fila Nava 2023. Los PDF de Nava 2025 y 2026 son imágenes sin texto (fechas "leídas a ojo", declarado).
- `notas/fuentes/eventos/eventos_fuentes.md` tiene la sección 4 "Candidatos adicionales (NO incluidos en el CSV)" (10 candidatos), separada de la tabla principal. Correcto.

### 3.5 Señales (opcional) — PARCIAL

- **Wikipedia — CUMPLE.** 20 artículos (15 es, 3 en, 2 fr) más `wikipedia_sonda_dias_ausentes.json`. Todos tienen `meta` (proyecto, título, agent=user, access=all-access, daily, fechas, hora de descarga, HTTP 200) y `respuesta` tal cual. Rango 2022-01-01 → 2026-10-14. Recuentos idénticos al registro: 1748 en 18 ficheros; `covadonga_fr` 1118 (630 omitidos, 405 ceros explícitos); `parque_nacional...` 1747 (1 omitido, 7 ceros); `descenso_sella` 1 cero. Consulté la API de Wikipedia por cada título: ninguno es una redirección (tampoco `Picos de Europa National Park` ni `Pics d'Europe`). Contraste en vivo de 3 valores (Covadonga 2023-09-17 = 193; Lagos de Covadonga 2025-08-15 = 169; Picos de Europa 2024-06-01 = 191): iguales. El comportamiento de los días ausentes está documentado y hay una sonda. Hallazgo anotado en el registro y confirmado: `picos_de_europa` es 61 525 visitas el 2023-09-17 frente a mediana de decenas/centenas (mismo día que el pico 100 de Trends).
- **Trends — PARCIAL.** 9 JSON (ES: cangas de onís, covadonga, lagos de covadonga, llanes, ruta del cares; ES-MD: 4 de ellos), 251 semanas cada uno (2021-12-26 → 2026-10-11, la última `isPartial=True`). Los parámetros de cada consulta (`kw_list`, `geo`, `timeframe`, hora) **sí están guardados** en `meta`. Hay un **término de anclaje común** ("picos de europa") en los 9, pero está mal elegido: máx. 100 una sola semana (2023-09-17), mediana 3, y aplasta al otro término (en `cangas_de_onís` máx. 3, mediana 1, 22 ceros). Falta ES-MD de "covadonga", ES-CL/ES-AS y toda ventana diaria. `notas/fuentes/senales/notas_senales.md` §2 contiene instrucciones claras de exportación manual. No hay CSV manuales en `data/raw/trends/`.
- **OAPN — CUMPLE.** `oapn_visitantes_2022..2025.pdf` y `oapn_memoria_red_2018..2021.pdf` (501, 214, 205 y 205 páginas), con texto extraíble. Cifras anuales de Picos de Europa leídas en los PDF: 2022 = **1.798.533**, 2023 = **1.698.780**, 2024 = **1.632.805** (referencia previa: idénticas, diferencia 0), 2025 = 1.565.899; serie 2015-2021 en la memoria 2021: 1.913.858, 2.101.293, 2.047.956, 1.958.240, 1.791.410, 1.383.338, 1.620.739 (coincide con `notas/fuentes/senales/notas_senales.md`). Solo hay datos anuales; los mensuales son gráficos de porcentaje (declarado).
- Los 4 PDF de visitantes de `oapn/` son **idénticos por hash** a los `miteco_visitantes_*` de `calendario/` (duplicado entre dos sesiones, ≈5,4 MB).

### 3.6 Transversales — PARCIAL

- **Ficheros esperados vs existentes:** AEMET 14/14 (+117 tramos + estado). Calendarios 55/55. Eventos 119/119 líneas de registro (la carpeta `laliga_2026-27/` cuenta como una). Señales: 21 Wikipedia + 9 Trends + 8 OAPN = 38, igual que el registro. **Open-Meteo: 12 de ~21 esperados (9+9+2+1) a las 17:28**, y la tabla del registro está desfasada.
- **Rangos declarados vs reales:** coinciden en AEMET, Wikipedia, Trends, Open-Meteo y OAPN.
- **Cruce con la zonificación:** `data/raw/zonas_mitma_asturias.csv` **no existe** (la parte A no está en este repositorio). **NO VERIFICABLE.** Las 9 zonas de `config/zonas_meteo.csv` (covadonga, lagos_enol, cangas_de_onis, llanes, ribadesella, gijon, oviedo, madrid, sevilla) son provisionales y no hay ninguna columna que las una con zonas MITMA; los eventos usan concejo, no zona MITMA (declarado).
- **Reproducibilidad (copia temporal, sin tocar el repo):** `descarga_aemet.py diarios --hasta 2022-01-31` (12 estaciones) y `prediccion`; `descarga_openmeteo.py --solo hist --hasta 2022-01-05` (1 zona); `descarga_senales.py wikipedia --hasta 20220110` (20 artículos); `descarga_calendarios.py --verifica` y `descarga()` de un PDF dos veces (la segunda devuelve "ya_existia"). Todos terminan sin errores y reproducen los valores guardados. Saltan lo ya descargado. **Tendrá que comprobarse aparte** `descarga_senales.py trends` y `oapn` (no ejecutados: Trends da 429 y OAPN son ≈35 MB).
- **Claves y rutas personales:** ninguna clave ni ruta absoluta en `src/`, `notas/`, `config/` ni README. Excepción menor: `src/descarga_calendarios.py` tiene un correo personal en el `User-Agent` (dato personal en un fichero versionado). *Corregido el 2026-10-15: el contacto se lee de la variable de entorno `TALENTUO_CONTACTO`, también en `descarga_senales.py`; el correo sigue en commits anteriores del historial.*
- **Nada modificado en `data/raw/`:** `git diff` solo muestra cambios en `data/raw/_chunks/manifest.json` (lo escribe Open-Meteo, en curso). Ningún cambio de cabeceras ni columnas en los JSON de AEMET/Wikipedia. Los únicos cambios respecto al bruto son los declarados: AEMET re-serializado (sangría 1), Open-Meteo concatenado con `_descarga`, `.txt` derivados en `calendario/`, y `wikipedia_*`/`trends_*` con envoltorio `{meta, respuesta}`.
- **Conflictos entre sesiones:** no hay ficheros de datos sobrescritos. Cada sesión escribió en sus rutas (`aemet*`, `openmeteo*`, `calendario/`, `eventos/` + `data/manual/`, `wikipedia_*`/`trends/`/`oapn/`). Ficheros compartidos tocados por varias sesiones: `.gitignore` (3 commits) y `README.md` (4). Solapes de contenido: 4 PDF OAPN duplicados entre `calendario/` y `oapn/`.
- **Pequeños defectos de documentación:** (a) `README.md` línea 16 contiene un carácter BEL (`^G`) en lugar de `\a` (`.venv\Scripts^Gctivate`), así que el comando de activación copiado/pegado falla; (b) `requirements.txt` no incluye `pytrends` ni `pypdf` (lo dice `notas/fuentes/senales/decisiones_senales.md`) y falta la dependencia externa `pdftotext/pdfinfo` (poppler) que usa `descarga_calendarios.py`; (c) `notas/fuentes/demanda/registro_descargas.md` (el registro común) está vacío: cada sesión llevó su registro propio; (d) `notas/fuentes/aemet/decisiones_aemet.md` avisa de que la clave se vio en la conversación de Claude Code: conviene regenerarla.

---

## 4. Errores y riesgos, por gravedad

| # | Gravedad | Problema | ¿Bloquea la limpieza? |
|---|---|---|---|
| 1 | Alta | **Open-Meteo incompleto:** a las 17:28 faltan oviedo, madrid, sevilla (y gijón en previous) y `openmeteo_prevision_ejemplo.json`; la sesión sigue descargando. El registro está desfasado. | **Sí, para el bloque meteorológico.** No bloquea el resto. |
| 2 | Alta | **Cruceros 2022-2024 inexistentes** y 2025-2026 son previsiones (la nota declara que el modelo no puede aprender el factor). Los datos de movilidad a predecir cubren 2022 a jun 2025. | **Sí, para el factor cruceros** (requiere pedir las escalas realizadas a la Autoridad Portuaria). |
| 3 | Alta | **Historical Forecast 2022-01-01→2022-11-09 es reanálisis, no previsión** (312/313 días idénticos a ERA5 en precipitación y viento). Riesgo de fuga e inconsistencia con producción. Comprobado solo en Covadonga. | Sí: decisión previa a limpiar (descartar o marcar ese tramo). |
| 4 | Media | **`juridicas_…2021-22.html` es una página de error de 25 bytes registrada como obtenida**, y el inventario afirma que existe esa copia. Defecto del script (no valida HTML). | No (dato opcional), pero el registro es falso. |
| 5 | Media | **Trends: ancla "picos de europa" inservible** (pico de 100 una semana, otros términos 0-4); faltan ES-MD covadonga, ES-CL/AS y ventanas diarias. | No (señal opcional). |
| 6 | Media | **89,7 % de los eventos son `probable`**; los partidos 2021-22 a 2025-26 no se contrastaron con LaLiga/RFEF; FIDMA 2023 con URL muerta; Pastor 2022-25 sin nota oficial; ≈100 ficheros sin URL exacta registrada. | No, pero hay que decidir qué calidad de fuente se admite. |
| 7 | Media | **Coordenadas provisionales y no verificadas** de Covadonga y Lagos; ERA5 de "covadonga" cae a ≈4-5 km del punto pedido. Falta contraste con AEMET (1186P, 1212E). | No, pero condiciona la lectura del sesgo en los Lagos. |
| 8 | Media | **Falta el cruce con zonas MITMA** (parte A ausente en este repositorio): imposible saber si falta alguna zona. | No para descargar; sí para montar la tabla final. |
| 9 | Baja | BOPA oficial del curso 2021-22 de Asturias y correcciones (30-nov-2021, Vegadeo 2025, 12-jun-2025) no descargadas (declarado). | No. |
| 10 | Baja | Previsión AEMET con codificación rota en un nombre (`OnÃ­s`); 1178R tiene un hueco de 537 días y 1203D termina el 2026-06-04; `sol` vacía en la estación recomendada 1186P. | No (hay decisiones pendientes registradas). |
| 11 | Baja | Concejo "Cangas de Onis" sin tilde; nombres de club inconsistentes ("Sporting de Gijón" / "Real Sporting de Gijón SAD"). | No (normalizar al limpiar). |
| 12 | Baja | README con carácter BEL; `requirements.txt` incompleto (`pytrends`, `pypdf`, poppler); correo personal en un `User-Agent`; PDF OAPN duplicados; `notas/fuentes/demanda/registro_descargas.md` vacío; `.txt` derivados dentro de `data/raw/calendario/`. | No. |
| 13 | Baja | La clave AEMET fue visible en una conversación (según `notas/fuentes/aemet/decisiones_aemet.md`). No está en el repositorio. | No (regenerar por prudencia). |

## 5. Lista de correcciones priorizada (sin ejecutar)

1. **Open-Meteo (sesión Open-Meteo):** dejar terminar el script (o relanzarlo; es reanudable) hasta tener las 9 zonas en Historical Forecast y Previous Runs y `openmeteo_prevision_ejemplo.json`; comprobar que la tabla de `notas/fuentes/openmeteo/registro_openmeteo.md` se regenera con todos los ficheros. Re-ejecutar `aud_openmeteo_resumen.py` para cerrar.
2. **Open-Meteo (decisión):** decidir si el tramo 2022-01-01→2022-11-09 se descarta o se marca; repetir la comparación con ERA5 en Lagos y una zona costera para confirmar que no es solo Covadonga.
3. **Eventos (sesión Eventos):** pedir a la Autoridad Portuaria de Gijón las escalas realizadas 2022-2025/2026; mientras tanto mantener los cruceros como previsión y no usarlos como variable de entrenamiento antes de 2025. Contrastar los partidos pasados con LaLiga/RFEF al menos por muestra (aplazados) y buscar fuente oficial de Pastor 2022-2025, Nava 2022, Semana Negra 2023/2025 y FIDMA 2023/2025.
4. **Calendarios (sesión Calendarios):** borrar o marcar `juridicas_…2021-22.html` (es un error) y corregir `notas/fuentes/calendarios/registro_calendarios.md` e `notas/fuentes/calendarios/inventario_calendarios.md`; añadir al script una validación para HTML (tamaño mínimo y que no sea un mensaje de error). Bajar a mano el BOPA de 1-jun-2021 y las correcciones citadas si se quieren usar. Hacer OCR/transcripción del folleto de Lagos y de los PDF de Nava 2025/2026.
5. **Señales (sesión Señales):** repetir Trends con ancla estable ("covadonga" o "lagos de covadonga"), añadir ES-MD covadonga y ventanas diarias solapadas, o subir los CSV de la exportación manual. Quitar la duplicidad de los 4 PDF OAPN.
6. **Parte A / zonificación:** aportar `data/raw/zonas_mitma_asturias.csv`, y después cruzar con `config/zonas_meteo.csv` (mapa zona→estación AEMET→punto Open-Meteo). Verificar con geocodificación las coordenadas de Covadonga y los Lagos y quitar `provisional` solo entonces.
7. **Transversal:** arreglar el README (BEL), añadir `pytrends`/`pypdf` y la nota de poppler a los requisitos, quitar el correo del `User-Agent` si no debe ir al repo, rellenar o retirar `notas/fuentes/demanda/registro_descargas.md`, regenerar la clave AEMET.
8. **Al limpiar:** unificar "Cangas de Onís" y los nombres de club; conservar el estado (`verificado`/`probable`) como columna de calidad en lugar de descartar filas.

## 6. Lo que no se pudo verificar y por qué

- **Estado final de Open-Meteo:** la descarga seguía en curso; el informe es una foto de las 17:28.
- **Cruce con la zonificación MITMA:** el fichero de la parte A no existe en el repositorio.
- **Condiciones de uso y límites de Open-Meteo** y de la API de Wikimedia: no se consultaron las páginas oficiales; se toman de los registros.
- **Partidos 2021-22 a 2025-26 contra fuente oficial:** solo coherencia con football-data (secundaria) y una jornada de LaLiga 2024-25. Las fechas aplazadas no se comprobaron una a una.
- **Eventos locales:** de 35 filas (7 eventos × 5 años) solo se contrastaron en fuente 8 (Sella 2022/2023, Semana Negra 2022/2026, FICX 2023, San Mateo 2025, Nava 2026, FIDMA 2024 en bruto). Pastor 2022-2025, San Mateo 2022-2024, Nava 2022-2025, Semana Negra 2023-2025 y FIDMA 2022/2023/2025 **no verificados** por mí. FIDMA 2023: fuente en 404.
- **Muestra de "3 cruceros verificados":** no existe ningún crucero `verificado`; se usaron 3 `probable` contra el PDF oficial.
- **Segunda fuente independiente para los festivos:** la comparación se apoya en que el PDF guardado es idéntico al publicado (hash) y en que el texto coincide; no se consultó otra fuente (p. ej. calendario laboral de la comunidad).
- **Scripts `descarga_senales.py trends`/`oapn`:** no se ejecutaron (Trends devuelve 429 y OAPN descarga ≈35 MB). Solo se probó `wikipedia`.
- **Cambios de modelo posteriores al 2025-06-30 en Open-Meteo** y si Previous Runs cambia de modelo: no se comprobó (tampoco lo hizo la sesión).
- **Si hay correcciones o modificaciones oficiales no descargadas** (BOPA 2021/2025): no se buscaron.

---

## 7. Re-verificación (2026-10-15, tras `notas/historico/correcciones_fase_B.md`)

Comprobaciones repetidas con `src/auditoria/aud_openmeteo_resumen.py`, una validación independiente de los JSON (fechas completas, igualdad con `_chunks/`), `aud_calendarios.py`, una comprobación del manifiesto de calendarios y una relectura del CSV de eventos. Cualquier cosa no comprobada sigue marcada como tal.

| Bloque | Veredicto antes | Veredicto ahora | Evidencia / lo que sigue abierto |
|---|---|---|---|
| 1. AEMET | CUMPLE | CUMPLE (no re-ejecutado; no se tocó) | Sin cambios en esta ronda. |
| 2. Open-Meteo | PARCIAL (en curso) | **CUMPLE en cobertura; el tramo 2022 sigue siendo una DECISIÓN ABIERTA** | 9/9 zonas × Historical Forecast + Previous Runs + ERA5 y previsión de ejemplo; 0 duplicados, fechas contiguas, iguales a los tramos. Coordenadas de Covadonga y Lagos verificadas (Lagos con Wikipedia, no con la API de geocodificación). Tramo 2022: último día idéntico a ERA5 el 2022-11-08 (Asturias) y 2022-11-15 (Madrid, Sevilla); Previous Runs no lo cubre. Abierto: elección de tratamiento (`notas/fuentes/openmeteo/openmeteo_tramo_2022.md`), temperatura del tramo no clasificable, celda real del modelo y sesgo orográfico de los Lagos. |
| 3. Calendarios | PARCIAL | **PARCIAL (mejorado)** | Registro y manifiesto honestos: 54/55 ficheros presentes y válidos; el HTML de error está en `_descartados/` y marcado no obtenido; el script valida HTML. Sigue el hueco oficial del BOPA 2021-22 (no localizado) y siguen sin bajar las correcciones/modificaciones de BOPA. |
| 4. Eventos | PARCIAL | **PARCIAL (sin cambio de fondo)** | CSV íntegro (378 filas, 13 columnas, sin duplicados, 0 filas sin fuente/estado), tilde corregida. Estados sin cambio: 35 verificado / 339 probable / 4 no_encontrado. Partidos: 7/7 de una muestra coinciden con laliga.com. FIDMA 2023: URL muerta, sin alternativa. **Posible error de un día en FIDMA 2025 (1 vs 2 de agosto)**. Cruceros 2022–2024: NO DISPONIBLE (solicitud redactada, sin enviar). |
| 5. Señales | PARCIAL | **PARCIAL** | Wikipedia y OAPN sin cambios (CUMPLE). Trends: ancla nueva "cabrales" y 3 de 20 consultas descargadas (sin ceros, medianas 9–24); 429 en la 4.ª; faltan 17, con instrucciones de exportación manual en `notas/historico/correcciones_fase_B.md`. |
| 6. Transversales | PARCIAL | **PARCIAL (mejorado)** | README (BEL) y `requirements*.txt` arreglados. Siguen: correo personal en un `User-Agent`, poppler sin documentar, `notas/fuentes/demanda/registro_descargas.md` vacío, duplicado de PDF OAPN, clave AEMET por regenerar, cruce con zonas MITMA NO VERIFICABLE. |

**¿Se puede pasar a limpieza?** Open-Meteo: sí en cuanto decidáis el tratamiento del tramo 2022. AEMET, calendarios (con el hueco 2021-22 conocido), Wikipedia y OAPN: sí. Eventos locales y partidos: sí, conservando la columna de calidad (`estado`). Cruceros: no hay datos de 2022–2024 y 2025–2026 son previsiones.
