# NTT Tourism · frontend

Web estática de la alerta temprana de presión turística en Asturias: HTML, CSS y JavaScript sin frameworks ni compilación. Este documento describe el código del frontend: estructura, capa de datos, pestañas, convenciones y cómo comprobar los cambios. Cómo se generan y actualizan los datos, el modo demo y el despliegue en Vercel están en `README_web.md`, en la raíz del repositorio.

## 1. Qué hace

Para cada zona de Asturias y cada día, la web muestra cuántos visitantes prevé el modelo frente a un **día normal** de esa zona. Lo traduce en un semáforo:

| Nivel | Nombre en la interfaz | Regla (ratio = previstos / día normal) |
|---|---|---|
| `verde` | Normal | ratio < umbral ámbar |
| `ambar` | Alta | umbral ámbar ≤ ratio < umbral rojo |
| `rojo` | Saturación | ratio ≥ umbral rojo |
| `gris` | Sin datos | el modelo no tiene predicción para ese día y zona |

- Los umbrales vienen de las salidas del modelo (`predicciones.umbrales`). La interfaz no los fija.
- Con las salidas actuales, el umbral ámbar es 1,5 (+50 %) y el rojo 2,0 (+100 %).
- Las zonas son las **46 zonas MITMA** del modelo, que cubren los **78 concejos**.
- La zona principal es Cangas de Onís, con Covadonga y los Lagos.

## 2. Cómo se abre

- Con doble clic en `index.html`: funciona desde `file://`, sin servidor.
  - Por eso los scripts son clásicos, no módulos ES.
  - Los datos van en ficheros `.js` (`datos/modelo/salidas-inicio.js` y `salidas.js`), que el navegador puede cargar sin `fetch`.
- También con cualquier servidor estático, por ejemplo `python -m http.server`.
- El mapa usa **Leaflet 1.9.4** y **topojson-client 3.1.0**, copiados en `vendor/`.
  - No hay mapa base (sin teselas, calles ni nombres de pueblos): se dibuja solo Asturias sobre fondo liso.
  - Por eso el mapa funciona sin conexión.
- Las tipografías se cargan de Google Fonts: Schibsted Grotesk para los títulos y Atkinson Hyperlegible para el texto. Sin conexión se usan las de reserva.
- `?demo=1` activa el modo demo: «hoy» pasa a ser agosto de 2024, dentro del periodo de validación, y se abre la zona principal. Detalle en `README_web.md`.

## 3. Estructura

```
index.html                    Estructura de las 3 pestañas, variables de color (claro y oscuro) y orden de carga de los scripts
favicon.svg                   Icono de la pestaña del navegador (el semáforo de la cabecera)
estilos/estilos.css           Estilos generales (solo usan las variables de index.html)
datos/
  modelo/salidas-inicio.js    Salidas del modelo para Inicio (GENERADO, ≈13 MB; no editar)
  modelo/salidas.js           Salidas completas para Funciones avanzadas y Sobre los datos (GENERADO, ≈28 MB)
  modelo/*.json               Las mismas salidas en JSON: solo respaldo con fetch en local (no se publican)
  datos.js                    Módulo «datos» (window.DatosModelo): valida y entrega las salidas
  catalogo.js                 Lo que no son cifras (window.Catalogo): concejos, tipo de destino, lugares, criterio de eventos
  fuente-modelo.js            Fuente de Inicio (window.FuenteDatos): traduce las salidas al contrato de api.js
  api.js                      Fachada window.Datos y CONTRATO documentado en su comentario inicial
  sitios.js                   141 sitios de interés (GENERADO por herramientas/construir_sitios.py)
  eventos.js                  Eventos de PredictHQ (GENERADO por herramientas/eventos_phq.py)
interfaz/
  app.js                      Pestaña Inicio: solo pinta y gestiona la interacción; monta las otras dos pestañas
  mapa.js                     Mapa Leaflet: zonas, concejos, etiquetas, sitios, zoom y teclado (no sabe de previsiones)
  geo-asturias.js             Límites de los 78 concejos en TopoJSON (GENERADO; no editar a mano)
pestanas/
  gestion/gestion.js          Pestaña «Funciones avanzadas» (id interno: gestion)
  gestion/logica.js           Su lógica: funciones puras, sin DOM
  gestion/config-gestion.js   Textos y parámetros editables (acciones sugeridas, días de alertas)
  gestion/gestion.css         Sus estilos
  gestion/pruebas.html        Pruebas de logica.js (se abre en el navegador; no se publica)
  sobre/sobre.js              Pestaña «Sobre los datos»
  sobre/contenido.js          Sus textos
assets/sitios/                Fotos de los sitios de interés (Wikimedia Commons, 480 px)
vendor/                       Leaflet y topojson-client
herramientas/                 Scripts de Python que generan geo-asturias.js, sitios.js y eventos.js (no se publican)
```

## 4. Capa de datos

```
salidas-inicio.js ─┐                      ┌─ catalogo.js (concejos, tipos, lugares, sitios, eventos)
                   ├─ datos.js ─ fuente-modelo.js ─ api.js (window.Datos) ─ interfaz/app.js (Inicio)
salidas.js ────────┘        └──────────────────────────── pestanas/ (Funciones avanzadas, Sobre los datos)
```

- **`datos/datos.js`** (`window.DatosModelo`) es la única puerta de entrada a las salidas del modelo.
  - `cargarInicio()` usa `salidas-inicio.js`, que `index.html` carga al principio.
  - `cargar()` usa `salidas.js`, que se inserta la primera vez que se abre Funciones avanzadas o Sobre los datos.
  - Si no hay `salidas.js`, prueba los JSON con `fetch` (solo con servidor y en local).
  - Comprueba los campos obligatorios del contrato (`notas/contrato_web.md`). Si falta alguno, rechaza la promesa con un error que los enumera.
- **`datos/catalogo.js`** (`window.Catalogo`) guarda lo que no son cifras:
  - los 78 concejos (código INE y nombre oficial), agrupados en 15 comarcas turísticas. Las comarcas solo sirven para dar a cada concejo su tipo de destino (costa, montaña, ciudad) y los lugares que encuentra el buscador;
  - el criterio `IMPACTO` de los eventos;
  - el acceso a `sitios.js` y `eventos.js`.
- **`datos/fuente-modelo.js`** (`window.FuenteDatos`) implementa el contrato para Inicio. No calcula previsiones: elige, traduce y resume lo que da el modelo.
  - Para cada fecha y zona enseña `futuro_corto` si existe y, si no, `futuro_largo`.
  - En la demo usa `historico` (modelo de largo plazo con 8 días de antelación).
  - Un concejo enseña la previsión de su zona. Las cifras absolutas solo salen si la zona es ese mismo concejo.
- **`datos/api.js`** (`window.Datos`) delega en `window.FuenteDatos`, envuelve cada respuesta en una promesa y la guarda en caché por argumentos. Al cargar, avisa por consola si a la fuente le falta alguna función.
- Funciones avanzadas y Sobre los datos leen `window.DatosModelo` directamente. De `window.Datos` solo usan `getConcejos()`, para los nombres de los concejos.

### Contrato de `window.Datos` (resumen; el detalle está en `datos/api.js`)

Las fechas son siempre texto `'YYYY-MM-DD'` en hora local de Madrid. Una `Prevision` tiene esta forma:

`{ zonaId, fecha, nivel, visitantes|null, min|null, max|null, normal|null, ratio|null, esPrediccion, conMeteo, motivo? }`

Lleva además unos extras del modelo: `incierto`, `conjunto`, `modelo`, `horizonte`, `fechaEmision` y, en la demo, `observado`, `ratioObservado` y `nivelObservado`.

| Función | Devuelve |
|---|---|
| `getInfo()` | `{ hoy, horizonteDias, diasConMeteo, umbrales:{ambar,rojo}, sintetico, demo }` |
| `getZonas()` | `[{ id, nombre, tipos[], concejos[] (nombres), lugares[], vecinos:null, principal, sinDatos }]` |
| `getConcejos()` | `[{ id (INE), nombre, zonaId\|null }]`; `id` es el mismo que en `geo-asturias.js` |
| `getSitios()` | `[{ id, nombre, concejos:[INE], lat, lon, ubicacionAproximada, foto }]`: sin previsión propia, se usa la de `concejos[0]` |
| `getEventos(desde, hasta?)` | `{ fuente, actualizado, hastaDatos, criterio, eventos[] }`: eventos grandes de PredictHQ más los festivos y partidos de la agenda del modelo |
| `getCalendario(desde, dias)` | `[{ fecha, finde, festivo, puente, vacaciones }]` (calendario de las salidas del modelo) |
| `getProximoPuente(desde)` | `{ nombre, inicio, fin } \| null` |
| `getPrevisionDia(fecha)` | `Prevision[]`, una por zona |
| `getPrevisionPeriodo(desde, hasta)` | Una por zona, con valores **medios por día** más `{ desde, hasta, dias, pico, diasPorNivel }` |
| `getPrevisionConcejos(desde, hasta?)` | Una por concejo (`concejoId` además de `zonaId`): la del día o, con `hasta`, la del periodo |
| `getSerieZona(zonaId, desde, dias)` | `Prevision[]`, una por día |
| `getFactores(zonaId, fecha)` | Los factores que más pesan: `[{ clave, texto, efecto }]` (efecto en %) |
| `getMejorMomento(zonaId, desde, dias)` | `{ dia: Prevision } \| null`: el día con menos presión de la ventana |
| `getMejorDia(zonaId, fecha)` | Mejor día alternativo del modelo, si el día está en alerta: `{ fecha, nivel, ratio, visitantes, diferenciaPct, margen }` |
| `getAlternativas(zonaId, fecha, hasta?)` | Zonas cercanas: la que propone el modelo y las que estén en verde a menos de `km_zona_cercana` |
| `getPerfil(zonaId, fecha)` | `{ deUnDia, conPernocta, asturias, restoEspana, mes, dias }` en %: media histórica del mes |
| `getFiabilidad(zonaId)` | `{ porHorizonte:{ '1'…'7', '8+': { nota, aciertoColor, n } }, algoritmo }` |

**Para añadir un dato nuevo a Inicio:**
1. Documéntalo en el comentario de `datos/api.js`.
2. Añade su nombre a `METODOS`.
3. Impleméntalo en `fuente-modelo.js`.
4. Úsalo desde `app.js`.

`interfaz/` no calcula previsiones, niveles ni umbrales.

## 5. Pestañas

### Inicio (público general)

- **Barra de fecha:** un día o un periodo, desde hoy hasta el último día con predicción (un año).
  - Accesos rápidos: Hoy, Este finde, Próximos 7 días y Próximo puente.
  - Flechas ‹ › para moverse un día, o tantos días como dure el periodo.
  - Calendario desplegable con selector «Un día / Varios días».
  - Teclado del calendario: flechas, Inicio/Fin (semana), Re Pág/Av Pág (mes; con Mayús, año), Intro para elegir y Escape para cerrar.
- **Filtros:** buscador de lugares y filtro por tipo de destino (costa, montaña o ciudad).
  - El buscador es un combobox ARIA que encuentra zonas, concejos y lugares sin distinguir tildes.
  - Un selector alterna entre Mapa y Lista (una tabla alternativa al mapa).
- **Mapa:** solo Asturias, sobre fondo liso.
  - Con poco zoom se ven las zonas; a partir de zoom 9,5, los concejos.
  - Las etiquetas no se solapan: `colocarEtiquetas` en `mapa.js`.
  - Ámbar, rojo y gris llevan color y trama: patrones `#relleno-*` en `index.html`.
  - Los sitios de interés salen como puntos al acercarse. `colocarSitios` los separa entre sí y de las etiquetas.
  - Con el teclado, el mapa se mueve con las flechas y se acerca con +/−. El tabulador recorre las zonas o concejos visibles.
- **Columna lateral:** las 5 zonas con más presión y las 3 más tranquilas.
- **Panel de zona** (sustituye a la columna lateral al elegir una zona o un concejo):
  - tarjeta del concejo, si se ha llegado desde uno;
  - estado de la zona;
  - «Día a día» (de 14 a 31 días alrededor de la selección);
  - «¿Por qué?»;
  - «Mejor momento para ir»;
  - alternativas cercanas;
  - «Por concejos»;
  - eventos en esas fechas;
  - «Quién viene»;
  - «Qué ver»;
  - nota de fiabilidad.

  Las secciones secundarias se pliegan y recuerdan si estaban abiertas.
- **Eventos y festivos** y **Sitios de interés** son secciones desplegables debajo del mapa.
  - Los eventos de PredictHQ solo se muestran si pueden mover la afluencia (criterio `IMPACTO` en `catalogo.js`): asistencia ≥ 3.500 y ≥ 50 % de los visitantes de un día normal en su concejo, o ≥ 10.000 en cualquier caso.
  - Los festivos y partidos de la agenda del modelo salen siempre.
  - Las fotos de los sitios llevan siempre su crédito, como exige su licencia.

### Funciones avanzadas (ayuntamientos, Principado, Parque Nacional)

Paneles con pestañas internas:

- **Previsión de saturación:** días por encima de un umbral ajustable, por zona o concejo y para un periodo (por defecto, todo el año siguiente). Muestra rachas y el día más cargado.
- **Alertas:** matriz zona/concejo × día para los próximos `diasAlertas` días (`config-gestion.js`, 28 por defecto) y lista de días con alerta con la acción sugerida.
- **Fiabilidad del modelo:**
  - acierto del color por días de antelación;
  - gráfica SVG de lo real frente a lo previsto en días de validación;
  - tabla por meses como alternativa a la gráfica.
- **Perfil del visitante:** procedencia, visitas de un día y hora con más llegadas, por zona y mes.
- **Exportar datos:** CSV separado por `;` y con decimales con coma. Se abre en un diálogo con los botones Copiar y Descargar.

El acceso regulado a los Lagos de Covadonga solo se señala en la zona de los Lagos.

### Sobre los datos

Explica:
- cómo leer el semáforo, con los umbrales de las salidas;
- qué es un día normal;
- cómo funciona el modelo;
- las fuentes;
- lo que no podemos ofrecer;
- la licencia del mapa.

Los textos están en `pestanas/sobre/contenido.js`.

## 6. Convenciones

- **Estética fija:** la paleta, las tipografías, los componentes, la maquetación y el aspecto del mapa no se cambian. El código sí puede cambiar, siempre que lo que se ve quede igual.
- **Idioma:** todo en español: la interfaz, los nombres del código y los comentarios.
- **Textos:**
  - Frases cortas y en lenguaje llano.
  - Números con separador de miles (`8.880`).
  - Espacio de no separación (U+00A0, constante `NBSP` en `app.js`) antes del signo de porcentaje: `+45 %`.
  - El signo menos es el carácter real `−`.
- **Colores:**
  - Todos los colores son variables CSS definidas en `index.html`: la paleta clara en `:root` y la oscura repetida en `@media (prefers-color-scheme: dark)` y en `:root[data-theme="dark"]`.
  - No se usan colores literales en los `.css` ni en el JS.
  - El semáforo usa `--verde`, `--ambar`, `--rojo` y `--gris`, con sus variantes `-suave` y `--mapa-*`.
  - El acento azul (`--acento`) es independiente del semáforo.
- **Accesibilidad:**
  - Un nivel nunca se comunica solo con el color: van juntos el icono, la trama y la palabra (`pill(nivel)` en `app.js`).
  - Todo se maneja con teclado.
  - El foco siempre se ve (`--foco`).
  - Los objetivos táctiles miden al menos 44 px.
  - Cada gráfico tiene etiqueta ARIA o tabla alternativa.
  - Los cambios importantes se anuncian con `anunciar()`.
  - El texto solo para lectores de pantalla lleva la clase `.sr`. El contenedor con scroll que lo rodee necesita `position: relative`.
  - Se respeta `prefers-reduced-motion`.
  - Los textos van en `rem`.
- **Responsive:** la página funciona a 390 px de ancho sin scroll horizontal. Solo las tablas, el mapa y las gráficas se desplazan dentro de su contenedor.
- **Visibilidad:** para mostrar u ocultar se usa el atributo `hidden`.
- **Carreras de peticiones:** las llamadas asíncronas que pintan algo usan un contador `seq*` para descartar las respuestas que llegan tarde.
- **Ficheros generados** (`datos/modelo/*`, `geo-asturias.js`, `sitios.js`, `eventos.js`): no se editan a mano.

## 7. Cómo comprobar los cambios

```bash
# Sintaxis de todos los scripts propios
node --check interfaz/app.js interfaz/mapa.js datos/api.js datos/datos.js datos/catalogo.js datos/fuente-modelo.js \
  pestanas/gestion/*.js pestanas/sobre/*.js
```

- **Lógica de Funciones avanzadas:** abre `pestanas/gestion/pruebas.html` en el navegador (doble clic). Tiene que decir «TODO OK».
- **Capa de datos de Inicio sin navegador:**
  1. En Node, con `global.window = global` y `global.location = { search: '' }`, carga en este orden: `datos/sitios.js`, `datos/eventos.js`, `datos/modelo/salidas-inicio.js`, `datos/datos.js`, `datos/catalogo.js`, `datos/fuente-modelo.js` y `datos/api.js`.
  2. Llama a `window.Datos.*`.
- **En el navegador:**
  - las tres pestañas;
  - el modo oscuro (tema del sistema);
  - el ancho de móvil (390 px en las herramientas de desarrollo);
  - la navegación solo con teclado;
  - que la consola no muestre errores.

## 8. Datos generados en esta carpeta

- **Límites del mapa** (`interfaz/geo-asturias.js`):
  - Fuente: IGN (CC BY 4.0), vía el conjunto `georef-spain-municipio` de OpenDataSoft (2022), simplificado a unos 10 m sin romper las fronteras compartidas.
  - Para regenerarlo (Python 3 con `pip install topojson shapely`):
    ```
    python herramientas/generar_geo.py ods.geojson municipalities.json interfaz/geo-asturias.js 0.0001
    ```
    - `ods.geojson` es la exportación de `georef-spain-municipio` filtrada a la provincia 33.
    - `municipalities.json` es el de `es-atlas@0.6.0`, del que solo se toman los nombres oficiales.
- **Sitios de interés** (`datos/sitios.js`, fotos en `assets/sitios/`):
  - `herramientas/sitios.tsv` → `buscar_sitios.py` (posición con OpenStreetMap Nominatim) → `construir_sitios.py` (requiere `pip install shapely pillow`).
  - Los sitios colocados a mano o en el centro del concejo llevan `ubicacionAproximada`.
- **Eventos** (`datos/eventos.js`):
  - Los genera `herramientas/eventos_phq.py` con la API de PredictHQ: radio de 95 km, solo los que caen dentro de un concejo de Asturias y con asistencia estimada ≥ 150.
  - El token no va en la web ni en ningún fichero del proyecto. Se pasa como variable de entorno: `$env:PHQ_TOKEN = '...'; python herramientas/eventos_phq.py`.
  - Conviene regenerarlo a menudo: PredictHQ publica los eventos con unos meses de antelación.
