# NTT Tourism · piloto de interfaz

Contexto para seguir trabajando en este proyecto (también con Claude Code en VS Code). Léelo entero antes de tocar código.

## 1. El proyecto

Participamos en la **Hackathon TalentUO 2026** con el reto de NTT DATA *"Predicción de afluencia turística en Asturias"*. El reto pide tres cosas:

- Un sistema de machine learning que prediga la afluencia en destinos asturianos.
- Que explique qué factores influyen.
- Que ayude a decidir si hace falta regular el turismo para proteger la convivencia con los vecinos.

**Enfoque: sistema de alerta temprana de presión turística.**

1. Predecimos cuántos visitantes recibirá cada zona de Asturias cada día.
2. Lo comparamos con un **día normal** (la mediana de visitantes diarios de esa zona).
3. Lo traducimos en un **semáforo** acompañado de las causas en lenguaje llano.

| Nivel | Nombre en la interfaz | Regla actual (ratio = previstos / día normal) |
|---|---|---|
| `verde` | Normal | ratio < 1,2 |
| `ambar` | Alta | 1,2 ≤ ratio < 1,5 |
| `rojo` | Saturación | ratio ≥ 1,5 |
| `gris` | Sin datos | sin muestra suficiente |

Los umbrales los devuelve la capa de datos en `getInfo().umbrales`; la interfaz no los fija.

**Datos reales previstos** (todavía no están conectados):

- **Variable principal:** movilidad por telefonía del Ministerio de Transportes. Es diaria, cubre de 2022 a junio de 2025 y distingue visitantes de un día y con pernoctación.
- **Factores explicativos:**
  - Calendario: festivos, puentes, vacaciones escolares y días de acceso regulado a los Lagos de Covadonga.
  - Meteorología de AEMET.
- **Validación y contexto:**
  - INE: turistas mensuales por concejo.
  - SADEI: plazas de alojamiento y población.
- **Caso estrella:** la puerta de Picos de Europa (Cangas de Onís y Covadonga).

**Lo que NO podemos ofrecer, y la interfaz lo dice abiertamente:**

- Datos en tiempo real.
- Cifras de un punto concreto, como el lago Enol. La unidad mínima es el concejo (por confirmar con la granularidad real de los datos de telefonía, que agrupa algunos municipios pequeños).
- Visitantes extranjeros día a día. Solo hay dato mensual del INE.
- Meteorología fiable a más de 7 días.
- Una hora exacta. La "mejor hora" sale de un perfil típico y es orientativa.

## 2. Estado actual

Es un **piloto de interfaz con datos ficticios**. Todavía no existe el modelo predictivo. El objetivo es visualizar la interfaz y su funcionamiento, con mucha atención a la usabilidad y a la accesibilidad para todo tipo de usuario.

- La web es estática: HTML, CSS y JavaScript sin frameworks ni paso de compilación.
- Se abre con doble clic en `index.html`. No necesita servidor, así que funciona desde `file://`.
- Los scripts son clásicos, no módulos ES, precisamente para que funcione desde `file://`. Comparten estado mediante variables globales (`window.FuenteDatos`, `window.Datos`, `window.GeoAsturias`, `window.MapaAsturias`, y las de las librerías `window.L` y `window.topojson`).
- Las tipografías se cargan desde Google Fonts: Schibsted Grotesk para títulos y Atkinson Hyperlegible para el texto. Sin conexión se usan las de reserva.
- El mapa usa **Leaflet 1.9.4** y **topojson-client 3.1.0**, copiados en `vendor/` (no dependen de un CDN). **No hay mapa base**: se dibuja solo Asturias sobre fondo liso, sin calles ni nombres de pueblos (decisión de diseño minimalista), así que el mapa funciona sin conexión.
- Hay una banda fija en la parte superior que avisa de que los datos son ficticios. No hay que quitarla mientras lo sean.

## 3. Estructura

```
index.html                 Estructura de las 3 pestañas + variables de color (claro/oscuro)
estilos/estilos.css        Todos los estilos (usan solo las variables de index.html)
datos/fuente-ficticia.js   "Modelo" inventado y determinista  ← lo que se sustituirá
datos/api.js               Fachada window.Datos + CONTRATO documentado en el comentario inicial
interfaz/geo-asturias.js   Límites reales de los 78 concejos (TopoJSON generado; no editar a mano)
interfaz/mapa.js           Mapa Leaflet: capas de zonas y concejos, zoom, etiquetas, teclado (no sabe de previsiones)
interfaz/app.js            Interfaz: solo pinta y gestiona la interacción
vendor/                    Leaflet y topojson-client
herramientas/generar_geo.py  Regenera interfaz/geo-asturias.js a partir de los datos del IGN
```

### Geometría del mapa

- `interfaz/geo-asturias.js` contiene los límites de los 78 concejos en TopoJSON (objeto `concejos`, `id` = código INE). Fuente: IGN (CC BY 4.0), vía el conjunto `georef-spain-municipio` de OpenDataSoft (2022), simplificado con una tolerancia de unos 10 m sin romper las fronteras compartidas (unos 20.000 puntos, 230 KB).
- **Las zonas no tienen geometría propia:** `mapa.js` las calcula uniendo sus concejos (`topojson.merge`) según `getConcejos()`. Para mover un concejo de zona basta con cambiarlo en la capa de datos.
- Para regenerarla (Python 3 con `pip install topojson shapely`):
  1. Descarga `https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/georef-spain-municipio/exports/geojson?where=prov_code%3D%2233%22&limit=-1` y `https://cdn.jsdelivr.net/npm/es-atlas@0.6.0/es/municipalities.json` (de este último solo se toman los nombres oficiales en castellano).
  2. `python herramientas/generar_geo.py ods.geojson municipalities.json interfaz/geo-asturias.js 0.0001`

### Regla de oro: separación datos / interfaz

- `interfaz/app.js` **solo** llama a `window.Datos.*`. No calcula previsiones, niveles ni umbrales.
- `datos/api.js` delega en `window.FuenteDatos`. También cachea las promesas (salvo las de `simular`) y avisa por consola si falta alguna función.
- **Para conectar el modelo real:**
  1. Crea `datos/fuente-modelo.js` con las mismas funciones. Pueden devolver promesas, por ejemplo usando `fetch` o leyendo un JSON exportado del modelo.
  2. Cambia una línea en `index.html`.
  3. No toques `interfaz/`.
- Si añades un dato nuevo a la interfaz:
  1. Amplía el contrato en el comentario de `datos/api.js`.
  2. Añade el nombre a `METODOS` en `datos/api.js`.
  3. Impleméntalo en la fuente.
  4. Úsalo desde `app.js`.

### Contrato (resumen; el detalle está en `datos/api.js`)

Las fechas son siempre texto `'YYYY-MM-DD'` en hora local de Madrid. Un objeto `Prevision` tiene esta forma:
`{ zonaId, fecha, nivel, visitantes|null, min|null, max|null, normal|null, ratio|null, esPrediccion, conMeteo, motivo? }`

| Función | Devuelve |
|---|---|
| `getInfo()` | `{ hoy, horizonteDias:366, diasConMeteo:7, umbrales:{ambar,rojo}, ficticio }`; `horizonteDias` son los días que se pueden elegir desde hoy (un año) |
| `getZonas()` | `[{ id, nombre, tipos:['costa'\|'montana'\|'ciudad'], concejos[], lugares[], vecinos, sinDatos }]` (`concejos` son nombres) |
| `getConcejos()` | `[{ id, nombre, zonaId }]`; `id` es el código INE, el mismo que en `geo-asturias.js` |
| `getSitios()` | `[{ id, nombre, concejos:[INE], lat, lon, ubicacionAproximada, foto }]`; sin previsión propia, se usa la del concejo `concejos[0]` |
| `getEventos(desde, hasta?)` | `{ fuente, actualizado, hastaDatos, eventos:[{ id, titulo, categoria, inicio, fin, hora, lugar, concejo, lat, lon, asistencia, rango }] }` (datos reales de PredictHQ) |
| `getCalendario(desde, dias)` | `[{ fecha, finde, festivo, puente, vacaciones }]` |
| `getProximoPuente(desde)` | `{ nombre, inicio, fin } \| null` |
| `getPrevisionDia(fecha)` | `Prevision[]`, una por zona |
| `getPrevisionPeriodo(desde, hasta)` | `PrevisionPeriodo[]`, una por zona: valores **medios por día** + `{ desde, hasta, dias, pico: Prevision, diasPorNivel:{verde,ambar,rojo} }` |
| `getPrevisionConcejos(desde, hasta?)` | Una por concejo, con `concejoId` además de `zonaId`: `Prevision` del día o, con `hasta`, `PrevisionPeriodo` |
| `getSerieZona(zonaId, desde, dias)` | `Prevision[]`, una por día |
| `getFactores(zonaId, fecha)` | Los 3 factores que más pesan: `[{ clave, texto, efecto }]` (efecto en %, p. ej. 38) |
| `getMejorMomento(zonaId, desde, dias)` | `{ dia: Prevision, hora:{ texto, nota } }` |
| `getAlternativas(zonaId, fecha, hasta?)` | Zonas cercanas en verde: `Prevision + { nombre, minutos }`; con `hasta`, según la media del periodo |
| `getPerfil(zonaId, fecha, hasta?)` | `{ deUnDia, conPernocta, asturias, restoEspana }` en %; con `hasta`, media del periodo |
| `getFiabilidad(zonaId)` | Validación del 1.er semestre de 2025: `{ serie[{fecha, real, prediccion}], errorMedio, nivelAcertado, rojosReales, rojosDetectados }` |
| `getDiasSobreUmbral(umbral, anio)` | `[{ zonaId, dias, picoVisitantes, picoPor100 }]`; el umbral es un ratio (1,8 = +80 %) |
| `getAlertas(desde, dias)` | Avisos ámbar y rojo: `[{ fecha, zonaId, nivel, ratio, visitantes, accion }]` |
| `simular(zonaId, fecha, escenario)` | `{ base, escenario }`, donde escenario = `{ lluvia, puente, lagos }` |

### Zonas (15) y concejos (78)

`costa-occidental`, `oscos` (Oscos y Eo), `suroccidente` (siempre gris, a propósito, para mostrar el estado "sin datos"), `nalon` (Bajo Nalón, Grado y Salas), `somiedo`, `aviles`, `gijon`, `oviedo`, `cuencas`, `sidra`, `redes`, `ribadesella`, `cangas` (caso estrella), `llanes` y `cabrales`.

Los 78 concejos están en `LISTA_CONCEJOS` (`datos/fuente-ficticia.js`) con su código INE y su zona. `oscos` y `nalon` se añadieron para que todos los concejos tengan zona; Morcín y Riosa están en `cuencas`, y Ribera de Arriba en `oviedo`.

### La fuente ficticia

- Es determinista: la misma zona y la misma fecha dan siempre el mismo resultado. El azar se obtiene con un hash de texto.
- El valor de cada día se calcula como base × temporada × día de la semana × puente o festivo × vacaciones × lluvia o sol × acceso a los Lagos × un ruido pequeño. Cada zona tiene su propia sensibilidad (`kTemp`, `kFinde`, `region`).
- "Hoy" es la fecha real. Se puede fijar una fecha de demostración en `CONFIG.fechaReferencia`.
- El calendario de festivos es aproximado y hay que verificarlo con el oficial.
- Cada concejo sigue a su zona: se lleva una parte de sus visitantes (`peso`) y amplía o suaviza sus altibajos (`sensibilidad`, mayor en destinos muy turísticos como Cudillero, Taramundi u Onís), más una variación diaria pequeña. Las zonas de un solo concejo (Gijón, Llanes) coinciden con su concejo.

## 4. La interfaz

**Inicio** (público general)

- **Barra de fecha:** se puede consultar **un día o un periodo** (varios días seguidos), desde hoy hasta dentro de un año.
  - Accesos rápidos: Hoy, Este finde (sábado y domingo), Próximos 7 días y Próximo puente (el puente entero).
  - Flechas ‹ › para moverse un día, o tantos días como dure el periodo.
  - Calendario desplegable con selector «Un día / Varios días». En modo periodo se pulsa el primer día y luego el último; se sombrea el tramo al pasar el ratón. Teclado: flechas, Inicio/Fin (semana), Re Pág/Av Pág (mes; con Mayús, año), Intro para elegir y Escape para cerrar.
  - Con un periodo, el mapa, el ranking y la lista muestran la **media por día**; el tooltip, la lista y el panel añaden el día con más gente y los días en saturación. Las causas («¿Por qué?») se explican con el día con más gente, y el mejor día se busca dentro del periodo.
  - La gráfica del panel enseña al menos 14 días alrededor de la selección (como mucho 31).
- **Filtros:** buscador de lugares (un combobox ARIA que encuentra zonas, concejos y lugares sin distinguir tildes) y filtro por tipo de destino (costa, montaña o ciudad).
- **Forma de ver:** un selector alterna entre Mapa y Lista; la lista es una tabla alternativa al mapa.
- **Mapa real (Leaflet), minimalista:** solo Asturias, aislada sobre fondo liso. Se puede arrastrar y hacer zoom (rueda, pellizco, botones +/− o teclado), pero no alejarse más allá de Asturias entera ni salirse de ella.
  - Con poco zoom se ven las **15 zonas**; a partir de zoom 9,5 se ven los **78 concejos**, cada uno con su color, y las zonas quedan como líneas gruesas. Un aviso en la esquina dice qué se está viendo (en móvil solo se anuncia al lector de pantalla), y el botón «Ver toda Asturias» vuelve al inicio.
  - Etiquetas sin saturar (`colocarEtiquetas` en `mapa.js`): cada zona o concejo lleva su nombre, icono y porcentaje. Los nombres de zona se parten en dos líneas para ocupar menos ancho. Si una etiqueta choca con otra (margen de 6 px) o desborda mucho su concejo, se oculta entera y aparece al acercar el mapa. Prioridad: la seleccionada y las áreas grandes. No hay nombres de pueblos ni calles de fondo.
  - Ámbar, rojo y gris se rellenan con color + trama (patrones `#relleno-*` en `index.html`), para no depender solo del color.
  - **Sitios de interés (141):** al acercarse a la vista de concejos aparecen como puntos blancos pequeños (9 px; área pulsable de 22 px). No marcan el lugar exacto: tras cada zoom, `colocarSitios` (`mapa.js`) los separa al menos 16 px entre sí y los aparta de los carteles, que siempre van por encima; si un punto no encuentra hueco, se oculta hasta acercar más. Al pulsarlos se abre una viñeta con foto, nombre, concejo(s) y el nivel previsto **del concejo**: no se calcula afluencia propia de cada sitio.
  - Pulsar una zona abre su panel y acerca el mapa hasta ver sus concejos. Pulsar un concejo abre el panel de su zona con una tarjeta del concejo.
  - Teclado: el mapa enfocado se mueve con las flechas y acerca con +/−; con el tabulador se recorren las zonas o los concejos visibles (Intro para elegir).
- **Columna lateral:** las 5 zonas con más gente y las 3 más tranquilas.
- **Panel de zona** (sustituye a la columna lateral al pinchar una zona):
  1. «Por concejos»: cada concejo de la zona con su nivel; pulsar uno lo encuadra en el mapa.
  1. «Qué ver en…»: los sitios de interés del concejo elegido (o de toda la zona); pulsar uno abre su viñeta en el mapa.
  1. Barras de los próximos días, con el rango probable y la línea del día normal.
  2. "¿Por qué?", con los tres factores principales.
  3. Mejor día y mejor hora.
  4. Alternativas cercanas en verde.
  5. Quién viene.
  6. Línea de fiabilidad.

  Si se llega buscando un lugar concreto (por ejemplo, el lago Enol), el panel aclara que muestra los datos de toda la zona. Si se llega desde un concejo (en el mapa, el buscador o la lista «Por concejos» del panel), arriba aparece su tarjeta con sus cifras.

- **Sitios de interés** (debajo del mapa): tarjetas con foto, concejo y el nivel de su concejo para las fechas elegidas. Se ordenan por «menos gente primero», «más gente primero» o por concejo, respetan el filtro de tipo de destino y se cargan de 24 en 24. Cada tarjeta permite verlo en el mapa o abrir su concejo.
  - Datos en `datos/sitios.js` (nombre, concejos con código INE, lat/lon, foto con autor y licencia). Fotos en `assets/sitios/` (480 px, 4 MB en total), descargadas de Wikimedia Commons con licencias libres: el crédito se muestra siempre junto a la foto, como exige la licencia.
  - Posición: 137 por búsqueda en OpenStreetMap (Nominatim) y 2 por la geolocalización de la foto, todas comprobadas dentro de su concejo. Belmonte de Miranda (Monasterio de Lapedo) y el Llagar El Gaitero se colocaron a mano o en el centro del concejo (`ubicacionAproximada`). Conviene revisar las posiciones antes de una demo pública.
  - Para regenerarlos: `herramientas/sitios.tsv` (lista del documento) → `buscar_sitios.py` → `construir_sitios.py` (requiere `pip install shapely pillow`).

- **Eventos grandes y Sitios de interés** (debajo del mapa) son secciones desplegables (`<details>`), cerradas al principio; el resumen de la cabecera dice cuántos hay.
- **Eventos grandes:** eventos reales de **PredictHQ** que se solapan con las fechas elegidas, agrupados por día y ordenados por asistencia estimada. **Solo se muestran los que pueden mover la afluencia** (criterio en `IMPACTO`, `datos/fuente-ficticia.js`): asistencia ≥ 3.500 y ≥ 50 % de los visitantes de un día normal en su concejo, o ≥ 10.000 en cualquier caso. Se compara con el día normal del concejo (la misma base que el semáforo) para que el mismo evento pese más en un concejo pequeño. Cada evento indica ese impacto («1,3 veces los visitantes de un día normal en Gijón»). Con los datos actuales quedan 4 de 115. Al conectar el modelo real, el día normal de cada concejo saldrá de los datos reales. Filtro por tipo de evento (deporte, concierto, festival…), respetan el filtro de tipo de destino y se cargan de 20 en 20. Cada uno enlaza a su concejo. El panel de zona/concejo incluye «Eventos en estas fechas».
  - Datos en `datos/eventos.js`, generados con `herramientas/eventos_phq.py`: busca en un radio de 95 km, se queda con los que caen dentro de un concejo de Asturias y con asistencia estimada ≥ 150. Hoy hay 115 (sobre todo partidos) y PredictHQ solo tiene eventos publicados hasta el 10/01/2027; para fechas posteriores la interfaz dice «Todavía no hay eventos publicados». Conviene regenerar el archivo cada poco tiempo.
  - **El token de PredictHQ no va en la web**: la API no admite llamadas desde el navegador (sin CORS) y cualquiera podría copiarlo de la página. Se pasa al script como variable de entorno: `$env:PHQ_TOKEN = '...'; python herramientas/eventos_phq.py`. No lo guardéis en ningún archivo del proyecto.
  - Siguiente paso posible: usar la asistencia de los eventos como factor del modelo (ahora mismo no influye en la previsión).

**Gestión** (ayuntamientos, Principado, Parque Nacional)

- **"¿Hace falta regular?":** días de 2024 por encima de un umbral ajustable (+80 % por defecto). El veredicto es "Estudiar regulación" a partir de 30 días, "Vigilar" entre 10 y 29, y "Sin presión" por debajo. También muestra el pico de visitantes por cada 100 vecinos.
- **Alertas de 14 días** (constante `DIAS_GESTION` en `app.js`, independiente del horizonte de un año): una matriz de zona × día y una lista de alertas con la acción sugerida.
- **Fiabilidad:** gráfica SVG de real frente a predicción (medias semanales del 1.er semestre de 2025), tres métricas y la tabla de datos.
- **Simulador:** cualquier día del próximo año; permite cambiar lluvia, puente y acceso a los Lagos (este último solo afecta a Cangas).
- **Exportación CSV** (separador `;`): abre un diálogo con los botones Copiar y Descargar.

**Sobre los datos:** cómo leer el semáforo, qué es un día normal, las fuentes, lo que no podemos ofrecer y la nota sobre el piloto.

## 5. Convenciones (respétalas)

- **Idioma:** todo en español, tanto la interfaz como los nombres del código y los comentarios.
- **Textos de la interfaz:** frases cortas y en lenguaje llano, sin jerga técnica. Los números siguen el formato español: separador de miles `8.880` y espacio fino antes del signo de porcentaje, como en `+45 %`. El signo menos es el carácter real `−`.
- **Colores:**
  - Todos los colores son variables CSS definidas en `index.html`: la paleta clara en `:root` y la oscura repetida en `@media (prefers-color-scheme: dark)` y en `:root[data-theme="dark"]`.
  - No uses colores literales en `estilos.css`.
  - El semáforo usa `--verde`, `--ambar`, `--rojo` y `--gris`, con sus variantes `-suave` y `mapa-*`. El acento azul (`--acento`) es independiente del semáforo.
- **Accesibilidad (obligatoria en todo lo nuevo):**
  - Un nivel del semáforo nunca se comunica solo con el color. Siempre van juntos el icono (círculo, triángulo, octógono o círculo discontinuo), la trama y la palabra. Usa `pill(nivel)` en `app.js`.
  - Todo debe poder manejarse con teclado:
    - Pestañas con las flechas.
    - Zonas del mapa con Tab e Intro o Espacio.
    - Escape cierra el panel.
    - El foco tiene que ser siempre visible (`--foco`).
  - Los objetivos táctiles miden al menos 44 px.
  - Todo gráfico necesita una etiqueta ARIA o una tabla alternativa. Usa `anunciar()` para los cambios importantes.
  - El texto solo para lectores de pantalla lleva la clase `.sr`. El contenedor con scroll que lo rodee debe tener `position: relative`, porque si no se desborda la página.
  - Respeta `prefers-reduced-motion` y usa `rem`, no `px`, en los textos (así funciona el zoom del navegador). Se quitó el selector de tamaño de texto A/A+/A++ a petición del equipo.
- **Responsive:** la página debe funcionar a 390 px de ancho sin scroll horizontal. Solo las tablas, el mapa y las gráficas pueden desplazarse dentro de su propio contenedor con `overflow-x: auto`.
- **Visibilidad:** para mostrar u ocultar elementos usa el atributo `hidden`; existe la regla `[hidden]{display:none!important}`.
- **Carreras de peticiones:** las llamadas asíncronas que pintan algo usan un contador `seq*` para descartar las respuestas que lleguen tarde.

## 6. Cómo comprobar los cambios

```bash
node --check interfaz/app.js interfaz/mapa.js datos/*.js   # sintaxis
```

- Abre `index.html` y revisa:
  - Las tres pestañas.
  - El modo oscuro (cambia el tema del sistema).
  - El ancho de móvil (DevTools a 390 px).
  - La navegación solo con teclado.
- Para probar la capa de datos sin navegador, carga en Node `datos/fuente-ficticia.js` y `datos/api.js` con `global.window = {}` y llama a `window.Datos.*`.

## 7. Siguientes pasos posibles

- [ ] Conectar el modelo real (`datos/fuente-modelo.js`) o un JSON exportado desde el modelo (Python/R).
- [x] Cambiar el mapa esquemático por límites reales (hecho: Leaflet + concejos del IGN).
- [ ] Validar con el equipo la agrupación de concejos en zonas (sobre todo las nuevas `oscos` y `nalon`).
- [ ] Decidir cómo funciona la demo: los datos reales acaban en junio de 2025, así que hay que elegir entre fijar `fechaReferencia` dentro del periodo con datos o hacer predicción pura con calendario y clima.
- [ ] Revisar el calendario de festivos de Asturias (2024–2027) y las fechas de acceso regulado a los Lagos.
- [ ] Perfil detallado de visitantes en Gestión (estaba previsto como extra "si da tiempo").
- [ ] Añadir una prueba de accesibilidad automática (por ejemplo, axe) si da tiempo.
