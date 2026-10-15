# Decisiones y consideraciones del proyecto

Un apunte por decisión. Añadir al final, con fecha y autoría.

## 2026-10-15 · Persona A · Zonificación MITMA (Paso 1, Fase 1)

### Decisiones
1. **Zonificación municipal, versión 2** (`Zones(zones='municipalities', version=2)` de `pyspainmobility`). La v2 es la de los datos de 2022 en adelante. La v1 (2020-2021) no se usa.
2. **Cangas de Onís es zona propia** (`33012`, solo ese municipio). La demanda en la puerta de los Picos se puede medir a nivel municipal. Detalle y registro: `registro_descargas.md`.
3. **Fichero de zonas de Asturias** (`data/raw/zonas_mitma_asturias.csv`): se construye agrupando la tabla oficial `relacion_ine_zonificacionMitma.csv` (una fila por sección censal) por zona MITMA, con los códigos INE unidos por `;`. Es un derivado de dos ficheros descargados, no una descarga directa. `agrupada` = `sí` si hay más de un código.
4. **Rango de datos MITMA a usar**: no mezclar datos anteriores y posteriores al 1 de julio de 2025 (cambio de metodología; lo dice la página oficial). Cualquier modelo debe tratarlas como series distintas o usar solo una.
5. Se borró `municipios_2.geojson` (57 MB) que genera la librería: es caché derivado. Se puede regenerar con la misma llamada.

### Consideraciones (límites a tener en cuenta)
- **Resolución espacial**: el mínimo es el municipio. Covadonga y Lagos están dentro del municipio 33012 y MITMA **no** los separa del resto de Cangas de Onís. Medir presión en Covadonga/Lagos exigirá otra fuente (aforos, aparcamientos, accesos) o asumir que el municipio es un proxy.
- **Cabrales y Onís comparten zona** (`33008_AM`, con Peñamellera Alta, Peñamellera Baja y Ribadedeva), y **Amieva** va con Caso, Ponga y Sobrescobio (`33015_AM`). No se pueden separar en MITMA. Ribadesella y Llanes son propias.
- **Huecos en la serie**: faltan días por incidencias (Orange 2023 y 2024, apagón 28-29 abr 2025). Se tratan como **ausentes, nunca 0**. Del 29 al 31 oct 2024 hay datos con anomalías (DANA).
- **Segundo semestre de 2025**: solo 17 días publicados (semana tipo de octubre y días sueltos de agosto y diciembre). Riesgo para entrenar y validar con datos posteriores al cambio de metodología.
- **No verificado**: el contenido del PDF metodológico (`leeme_cambiometodologia_indicadoresbigdata_posteriores_a_20250701.pdf`); que MITMA publique nuevos días del segundo semestre de 2025; los códigos INE frente al INE directo (se cotejaron con Wikidata P772).

### Entorno (Windows)
- Se importa `pyspainmobility` (minúsculas).
- `python -I` falló al cargar un DLL de numpy por un bloqueo de Windows (Control de aplicaciones); sin `-I` funciona.
- La página oficial de Transportes da 403 a WebFetch/curl simple; carga con cabeceras de navegador (`User-Agent`, `Accept-Language`).
- La guía está en `notas/persona_A_demanda_movilidad` (el fichero se guardó **sin extensión `.md`**; conviene renombrarlo). Contrastada con este paso el 2026-10-15: los días sin datos, el aviso del 1 jul 2025, el código de `Zones(...)` y las columnas del CSV coinciden.

### Discrepancias con la guía
- La guía (marcada ✅) dice que la tabla de zonas trae una columna `municipalities`. **No es así**: `get_zone_geodataframe()` solo devuelve `name` y `population`. Los códigos INE salen de `get_zone_relations()` (tabla por sección censal, columnas `municipalities` y `municipalities_mitma`). Corregir la guía.
- La guía pide buscar los códigos de Ribadesella, Cabrales, Onís y Amieva en la lista del INE; se cotejaron con Wikidata (fuente secundaria), no con el INE.

### Pendiente
- Leer el PDF metodológico y anotar qué cambia exactamente.
- Hacer commit de `data/raw/zonas_mitma_asturias.csv` y del registro para que la Persona B los reciba (siguen sin commitear).
- Los ficheros de los pasos 2 y 3 que ya están en `data/raw/` no los ha revisado este apunte (solo cubre el Paso 1).

## 2026-10-15 · Persona A · MITMA viajes y pernoctaciones (Paso 2, Fase 1)

**Estado: EN CURSO, no completado.** La prueba del 2024-08-15 y el método están validados; la descarga completa (2022-01-01 a 2025-06-30) se lanzó a las ~17:00 y tardará unas 7-8 h. Falta ejecutar `scripts/verificar_mitma.py` por año y anotar sus resultados en `registro_descargas.md`. Hasta entonces no se da por cumplido el objetivo.

### Decisiones
1. **Descarga directa por HTTP, no con `pyspainmobility`.** Se usan las mismas URLs diarias que la librería (`estudios_basicos/por-municipios/{viajes,pernoctaciones}/ficheros-diarios/...`), pero con script propio: permite filtrar y borrar cada día, reanudar y controlar errores.
2. **Filtrado en origen, día a día**: viajes por `destino` y pernoctaciones por `zona_pernoctacion` ∈ las 46 zonas de Asturias; se borra el `.csv.gz` tras cada día (el nacional son cientos de GB; cada día de viajes pesa ~147 MB).
3. **Todo se lee y se guarda como texto** (`dtype=str`, `keep_default_na=False`). Motivo: pandas convertiría el `NA` de `edad`/`sexo` en vacío y perdería ceros a la izquierda en códigos (`01001`). Sin limpieza ni conversión de tipos en Fase 1.
4. **Se conservan todas las columnas**, incluidas `estudio_origen_posible` y `estudio_destino_posible` (no previstas en la guía). Salida separada por `,`.
5. **Un proceso por año en paralelo** (2022, 2023, 2024, 2025 hasta junio) para acortar de ~25 h a ~7-8 h. Es seguro porque cada proceso solo toca los ficheros de su año.
6. **Día sin datos = ausente.** Un 404 se registra como `NO_DISPONIBLE` y no se escribe nada ni se imputa. Los errores de red se reintentan y, si persisten, quedan como `ERROR` hasta relanzar.
7. **Tope duro en 2025-06-30** en el script (cambio de metodología del 1 de julio de 2025).
8. **Estadísticos de "día normal" encontrados** (MITMA, 2024): se descargan solo los 4 ficheros pequeños; el de origen-destino (1,08 GB) queda pendiente de decisión.

### Consideraciones y límites
- **Solo residentes en España**: no hay turistas extranjeros. La presión turística en Covadonga/Lagos queda subestimada en temporada alta internacional.
- **Resolución**: el mínimo es el municipio. Los viajes con destino 33012 incluyen Covadonga y Lagos, pero no se pueden separar. Cabrales/Onís y Amieva siguen agrupados (ver Paso 1).
- **Los viajes son por destino, no por visitante**: incluyen viajes de residentes asturianos (trabajo, vida diaria). Para aislar turismo habrá que usar `actividad_destino`, `residencia` y las pernoctaciones; es trabajo de la fase de limpieza, no se ha hecho.
- **`edad` y `sexo` = `NA` en ~45 % de filas** (muestra de un día); es dato ausente en origen, no un error nuestro.
- **Contradicción en días sin datos**: la lista de la página del MITMA y el RSS oficial no coinciden (2024-04-04, 04-19, 11-09, 11-10, 11-11, 11-26). Lo que diga el 404 real manda; está **NO VERIFICADO** hasta cerrar la verificación.
- **Días con anomalías** (29-31 oct 2024, DANA) se descargan normalmente; hay que marcarlos en la limpieza, no excluirlos aquí.
- **Volumen**: ~14 GB/año de viajes ya filtrados. `.gitignore` no excluye `data/raw/`: **no hacer commit de estos CSV** (decidir con el equipo si se ignoran o se comparten fuera de git).
- **Entorno**: se ejecuta con `.venv\Scripts\python.exe` y sin `-I` (ver bloqueo de DLL en el Paso 1). Si el PC se apaga, relanzar los 4 comandos; el script retoma donde quedó.
- **Estadísticos "día normal"**: sus umbrales son de 2024 sin julio ni agosto (según la página, **NO VERIFICADO** en los ficheros). Para una zona turística, comparar agosto contra un "día normal" que excluye el verano es justo lo que buscamos, pero el umbral no sirve como "normal de verano".

### Pendiente
- Esperar fin de descarga, ejecutar `verificar_mitma.py` para 2022-2025, registrar filas/fechas/ausencias y contrastar con el RSS.
- Decidir si se baja el fichero ODS de estadísticos (1,08 GB).
- Leer el PDF metodológico de julio de 2025 (heredado del Paso 1).

## 2026-10-15 · Persona A · INE ocupación por punto turístico (Paso 4, Fase 1)

**Estado: COMPLETADO como descarga bruta, con cobertura PARCIAL respecto al objetivo.** Hoteles sí cubren Cangas de Onís; apartamentos, campings y rural no. Detalle de ficheros y ausencias en `registro_descargas.md`.

### Decisiones
1. **Descarga directa del CSV de JAXI** (`jaxiT3/files/t/csv_bdsc/<tabla>.csv`) en vez de exportar por pantalla: funciona, trae histórico completo (2005M01–2026M08) y es reproducible.
2. **Los números de tabla se verificaron con la API del INE** (`servicios.ine.es/wstempus`, `TABLAS_OPERACION/<operación>`), no con el catálogo supuesto: 2078/2076 = EOH, 2082 = EOAP. Operaciones: EOH 238, EOAP 239, EOAC 240, EOTR 241.
3. **Se descargaron tablas extra** que el reto no pedía pero completan el dato: 2083 (apartamentos: plazas/ocupación), 2085 (campings: parcelas/ocupación), 2005 (rural: plazas/ocupación). Sin ellas no hay denominador (plazas) para convertir viajeros en presión.
4. **Rural: zona turística "Costa Verde"** (tablas 1999/2005) como único dato disponible, al no existir tabla por punto. Se guarda aunque no sirve para Cangas/Covadonga.
5. **Se copian los ficheros tal cual** (UTF-8 con BOM, `;`, miles con `.`): sin limpieza, sin conversión de tipos.
6. **Se descartan por ahora las tablas 75191–75198** (solo desde 2025M01).
7. **Ausentes (`.`, `..`, vacío) se conservan como ausentes, nunca 0**; los `0` reales se respetan.

### Consideraciones y límites
- **Cangas de Onís solo existe en hoteles.** Apartamentos y campings solo cubren Llanes (y Cudillero en apartamentos); el INE no publica los demás por secreto estadístico o falta de muestra. Cualquier validación de Cangas/Covadonga con estos datos infravalora el alojamiento total (no incluye rural, apartamentos, campings ni vivienda de uso turístico, ni segundas residencias).
- **Covadonga y Lagos no existen como punto**; son parte de Cangas de Onís. No se puede validar el modelo a nivel de Lagos.
- **Granularidad mensual**: sirve para validar el patrón estacional y el nivel, no para validar predicciones diarias.
- **Cobertura de hoteles con huecos**: Cangas ~66/260 meses ausentes, Llanes 56, Villaviciosa ~115 (último dato real 2025M08). Hay que mirar en qué meses faltan antes de usarlo; si faltan en temporada baja el sesgo es hacia meses de mayor actividad.
- **Significado exacto de `.` vs `..` NO VERIFICADO.** Se asume "ausente" en ambos casos; no se ha leído la nota metodológica del INE.
- **Solape temporal con MITMA**: MITMA cubre 2022-01 a 2025-06 (tope por cambio metodológico); INE hasta 2026M08. Para validar, el solape útil es 2022M01–2025M06.
- **Los viajeros del INE son viajeros alojados en establecimientos**, no visitantes de un día (excursionistas); la presión real en Covadonga incluye muchos visitantes que no pernoctan. Es un límite de fondo de esta fuente.
- **Tablas viejas vs nuevas**: la 20xx llega a 2026M08 pese a existir las 751xx; se asume que ambas son consistentes, **NO VERIFICADO**.

### ¿Cumple el objetivo del proyecto?
Parcialmente. Sí: dato oficial, gratuito, mensual y largo para validar nivel y estacionalidad de Cangas de Onís, Llanes, Oviedo, Gijón y Villaviciosa en hoteles. No: no cubre toda la oferta ni el nivel diario ni Covadonga/Lagos. Úsese como **validación de contexto**, no como verdad de campo del modelo diario.

### Pendiente
- Leer la nota metodológica del INE sobre `.`/`..` y secreto estadístico.
- Decidir si se añade la tabla de viviendas turísticas (`ine_viviendas_turisticas.csv`, ya descargada en otro paso) como complemento de oferta.
- Borrar `data/raw/_ine_tmp/` si sigue existiendo (quedó bloqueada por un proceso).

## 2026-10-15 · Persona A · SADEI por concejo (Paso 5, Fase 1)

**Estado: COMPLETADO** (descarga en bruto y apertura comprobada). Detalle de ficheros, títulos y cobertura: `registro_descargas.md`. Cumple el objetivo de Fase 1; el valor para el modelo tiene los límites de abajo.

### Decisiones
1. **Se descarga por el visor PxWeb, no por los enlaces `?f=` de la guía.** Esos enlaces devuelven HTML y el enlace directo apunta a un host que no resuelve. El script reproduce el flujo del formulario (todos los valores → Continuar → "Archivo de PC-Axis"). Es frágil: si SADEI cambia la web, hay que revisarlo (`scripts/descarga_sadei.py`).
2. **Se baja siempre con todos los valores de todas las variables** (sin filtrar concejos ni fechas), para no perder nada en bruto.
3. **Receptor nacional en 4 partes por fecha** (límite de 100 000 celdas del PxWeb). Se guardan tal cual, sin unir; unirlas es trabajo de la Fase 2.
4. **Padrón: se eligió `02020202`** (evolución de la población por concejo, 1900-2026) porque es una sola tabla compacta concejo × periodo, suficiente para calcular visitantes/habitante. No es la serie de edad/sexo/nacionalidad (`02040202`), que queda sin bajar.
5. **Códigos de la guía validados por título**, no por suposición. Se borró el HTML que dejó el primer intento fallido con el nombre `.px`.
6. **Celdas vacías = ausentes, nunca 0** (secreto estadístico: <30 personas en los receptores).

### Consideraciones (qué aporta y qué no)
- **Utilidad real para el reto**: son datos **mensuales por concejo** de turistas nacionales (por provincia de origen) y extranjeros, más plazas/apartamentos y población. Sirven de **referencia y validación externa** de MITMA (otra fuente de visitantes, incluye extranjeros, que MITMA no tiene) y para la capacidad de carga (plazas) y la presión relativa (turistas/habitante). **No son diarios**: no alimentan directamente un modelo por día; sirven para calibrar niveles/estacionalidad mensual.
- **Los turistas son del INE (estadística experimental de teléfonos móviles)**, no de SADEI: misma familia de método que MITMA (telefonía), así que **no son fuentes independientes**; hay que tratarlas como contraste, no como confirmación.
- **Resolución**: concejo. Covadonga y Lagos no se pueden aislar (igual que en MITMA). Cangas de Onís sí aparece como concejo propio, y Cabrales/Onís no están agrupados aquí (a diferencia de MITMA), lo que da una comparación útil.
- **Cobertura temporal desigual**: nacional hasta 2026-02, extranjero hasta 2025-12, plazas/apartamentos solo **anuales** hasta 2025. Plazas anuales no captan cambios estacionales de oferta (apertura de temporada).
- **Rentabilidad y EOH (viajeros/pernoctaciones hoteleras) son solo Asturias**, sin concejo: contexto regional. Si se necesita ocupación hotelera por concejo, esta descarga no la cubre (**pendiente de buscar**, p. ej. otra tabla de la misma página o INE/Frontur).
- **Mucho dato ausente en el receptor nacional** (72–80 % de celdas vacías, sobre todo por la desagregación por provincia de origen). Para concejos pequeños puede haber meses sin dato; antes de usarlo, medir la ausencia en Cangas de Onís y Llanes (**no hecho, NO VERIFICADO**). Agregar por origen (total) reducirá los huecos.
- **No verificado**: qué filas del periodo 2021-2026 del padrón son definitivas o provisionales; si el límite de 100 000 celdas cambia en el futuro; que las tablas se actualicen con la periodicidad que sugiere su último dato.

### Pendiente
- Medir ausencias de Cangas de Onís y Llanes en los receptores.
- Concatenar las 4 partes del nacional (Fase 2) y comprobar que no se solapan fechas.
- Decidir si se baja `02040202` (padrón por edad/nacionalidad) y buscar ocupación hotelera por concejo.
- Los `.px` suman ~1,4 MB: se pueden versionar sin problema (a diferencia de los CSV de MITMA). Sin commit todavía.
