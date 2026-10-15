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
