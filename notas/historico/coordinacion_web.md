# Coordinación de la web (persona 1 ↔ persona 2)

> **Documento histórico.** Notas de coordinación entre el responsable de la base de la web (Inicio, datos y mapa; «persona 1») y el de las pestañas Funciones avanzadas y Sobre los datos («persona 2»), del 2026-10-15 y 16. La documentación vigente del frontend está en `Afluencia Asturias/README.md` y `README_web.md`.

Ramas: **`web`** (persona 1: base, capa de datos, mapa, Inicio, demo) y **`web-gestion`** (persona 2: Gestión y Sobre los datos), creada desde `web`. La web vive en `Afluencia Asturias/` (HTML + CSS + JS clásicos, sin compilación).

## Quién toca qué

| Persona 2 (solo estos) | Persona 1 (el resto) |
|---|---|
| `Afluencia Asturias/pestanas/gestion/*` | `index.html`, `estilos/estilos.css`, `interfaz/*` |
| `Afluencia Asturias/pestanas/sobre/*` | `datos/*`, `scripts/actualizar_datos_web.py` |

Si necesitáis algo en un fichero del otro, apuntadlo abajo en «Peticiones».

## Cómo se monta una pestaña

`index.html` ya carga `pestanas/gestion/gestion.js` + `gestion.css` y `pestanas/sobre/sobre.js` + `sobre.css` (no hace falta tocar `index.html`; si necesitáis más ficheros, cargadlos desde vuestro JS o pedidlo aquí). Cada fichero registra un componente:

```js
window.Pestanas.gestion = {          // o window.Pestanas.sobre
  montar(contenedor, datos, util) { … },  // la primera vez que se abre la pestaña
  mostrar() { … },                        // cada vez que se vuelve a ella (opcional)
};
```

- `contenedor`: `<section id="panel-gestion">` (o `#panel-datos`), vacío. Usad `class="titulo-pagina"`, `tarjeta`, `g-lead`, `prosa`, `btn`… de `estilos/estilos.css` para mantener el estilo.
- `datos`: el objeto del módulo «datos» (abajo).
- `util` = `window.UtilWeb`: `$`, `$$`, `esc`, `num` (8.880), `pct` (cociente → «+45 %»), `delta` (cociente → «+45 % sobre un día normal»), `pill(color)` (icono + palabra del semáforo; **usadla siempre**: el nivel nunca solo con color), `anunciar(texto)` (lector de pantalla), `fechaLarga`, `fechaCorta`, `deISO`, `aISO`, `sumar`, `diasEntre`, `NIVEL`, `ICONO`, `NBSP`, `MENOS`.
- El aviso «DATOS SINTÉTICOS – solo para pruebas» es global (lo pinta `app.js` arriba, fijo, en todas las pestañas): no hace falta repetirlo.

La versión del piloto de Gestión y Sobre los datos (con datos ficticios) se quitó de `index.html` y `app.js`; sigue en el commit `b0aba54` (`index.html`, secciones `panel-gestion`/`panel-datos`; `interfaz/app.js`, bloque «Gestión») por si queréis reaprovechar marcado o estilos (las clases `g-*` siguen en `estilos/estilos.css`).

## Módulo «datos»

- Fichero: `Afluencia Asturias/datos/datos.js`. Se carga con `<script>` (ya está en `index.html`); expone `window.DatosModelo`.
- Uso:

```js
window.DatosModelo.cargar().then(datos => { … });   // promesa única, se puede llamar varias veces
```

- Forma del objeto (congelado; los JSON van **tal cual** los escribe el modelo, formato en `notas/contrato_web.md`):

```text
{
  predicciones,   // predicciones.json  → .fecha_hoy, .zonas[], .predicciones[] (fecha × zona × horizonte), .umbrales
  alternativas,   // alternativas.json  → .alternativas[] (mejor_dia, zona_alternativa)
  regulacion,     // regulacion.json    → .por_zona[] (anios, curva_umbral), .lagos, .calendario_alertas[]
  perfil,         // perfil.json        → .perfil[] (zona × mes), .nota
  metricas,       // metricas.json      → .algoritmo, .fiabilidad[] (nota por zona y horizonte), .tablas, .experimentos…
  mapeo,          // { origen, zonas:[{ zona_mitma_id, nombre, concejos_ine:[INE] }] } (de config/mapeo_zonas*.csv)
  sintetico,      // true si alguno de los cinco es sintético
  aviso           // texto «aviso» del modelo, o null
}
```

- Valida los campos obligatorios del contrato; si falta algo, la promesa se rechaza con un `Error` que lista los problemas (y la web lo muestra).
- **Los IDs de zona no se escriben a mano**: leedlos de `datos.predicciones.zonas` (hoy `EJEMPLO_*`, mañana los del MITMA).

## Datos: cómo se actualizan

```bash
python -X utf8 scripts/actualizar_datos_web.py
```

Valida `salidas/` con `src/modelo/validar_salidas.py`, copia los cinco JSON a `Afluencia Asturias/datos/modelo/` y genera `datos/modelo/salidas.js` (lo que lee la web; así funciona con doble clic). Elige `config/mapeo_zonas.csv` si cubre los IDs de las predicciones y, si no, `config/mapeo_zonas_ejemplo.csv`.

## Estado

- **Esqueleto listo** — commit `e446a48` (rama `web`).

## Mapa: fuente y licencia (para citar en «Sobre los datos»)

- Límites de los 78 concejos: **Instituto Geográfico Nacional (IGN), licencia CC BY 4.0**, vía el conjunto `georef-spain-municipio` de OpenDataSoft (2022); nombres oficiales de `es-atlas` (también del IGN). Simplificado a ~10 m sin romper fronteras (TopoJSON, 230 KB): `Afluencia Asturias/interfaz/geo-asturias.js`, regenerable con `herramientas/generar_geo.py`. Cita sugerida: «Límites municipales: © Instituto Geográfico Nacional (CC BY 4.0)».
- Sin teselas externas: el mapa funciona sin internet.
- Zonas = unión de concejos según `config/mapeo_zonas.csv` (columna `concejos_ine`, separados por `;`). Concejos fuera de toda zona: gris claro liso (distinto del gris con trama, que es «sin datos»).
- Calendario de los botones de fecha (puentes, festivos): `data/clean/calendario_diario.parquet` (parte B), exportado por el script.

## Peticiones / huecos del contrato

- **Concejo en dos zonas** en `config/mapeo_zonas_ejemplo.csv`: 33036 (Llanes) está en `EJEMPLO_llanes` y en `EJEMPLO_oriente`. La web lo pinta en la zona con menos concejos. Con el mapeo real, mejor que cada concejo esté en una sola zona.
- **Perfil por fecha**: `perfil.json` es por zona y mes (media histórica); la web enseña el mes de la fecha elegida. Si hiciera falta el perfil de un día concreto, habría que añadirlo al contrato.

## Persona 2 — Gestión y Sobre los datos (rama `web-gestion`)

### Inventario (piloto `b0aba54`)
- **Ya existía el diseño** de Gestión (índice, tarjetas `g-sec`, barras `rg-*`, matriz `matriz/cel`, `metricas/met`, `tabla`, diálogo CSV) y de Sobre los datos (`prosa`, `leyenda-grande`, `fuentes/fuente`, `no-lista`). Las clases `g-*`… siguen en `estilos/estilos.css`: **no se ha tocado ningún estilo, ni `index.html`, ni `interfaz/`, ni `datos/`**. `gestion.css` sigue vacío.
- Se reutiliza el marcado del piloto con datos del modelo. Quitado del piloto (sin datos del modelo): simulador de escenarios y gráfica de real frente a predicción (no hay serie diaria en el contrato).
- Añadido con clases existentes: comparación con los Lagos (`tabla`), perfil del visitante (`met`, `select`), selector de año de referencia (`select`).
- **Pendiente de datos:** patrón horario (no existe `data/clean/llegadas_por_hora.parquet`; la tarjeta lo dice).

### Ficheros míos
- `pestanas/gestion/`: `config-gestion.js` (acciones por color y criterios, editable), `logica.js` (funciones puras), `pruebas.html` (20 pruebas: abrir en el navegador), `gestion.js`.
- `pestanas/sobre/`: `contenido.js` (textos), `sobre.js`. Cargan sus scripts desde su propio JS.

### Notas para el contrato
- `cociente`, `p10` y `p90` van redondeados: al recalcular el umbral exacto de la cabecera puede bailar 1-3 días frente a `curva_umbral`. Con los umbrales por defecto se usa el color del modelo (exacto).
- Los años observados (2023, 2024) solo tienen la curva de umbrales 1,2-3,0 (14 valores): la barra deslizante va por esos valores. Si se quisiera cualquier umbral también en observados, habría que añadir al contrato el cociente diario observado.
- Mapa: la cita del IGN (CC BY 4.0) de arriba ya está en «Sobre los datos» (`SobreContenido.mapa`); cámbiala ahí si procede.

### Estado
- **web-gestion lista** — commit `edcf286` (incluye `origin/web` hasta `71ed483`).

## Usabilidad en móvil (persona 1, para la persona 2)

- Mapa: en pantallas táctiles un dedo desplaza la página y dos dedos mueven el mapa; con ratón, Ctrl + rueda acerca. Al tocar una zona en una sola columna, la página baja a su panel; al cerrarlo, vuelve al mapa.
- **Gestión a 390 px**: la tabla ancha (`table.tabla`, ~1.080 px) se desliza dentro de su contenedor, pero en el móvil cuesta leerla. Propuesta: menos columnas en móvil, o una tarjeta por zona. Es de `pestanas/gestion/`, no la he tocado.

## Revisión de usabilidad (persona 1)

- **Carga en dos partes.** `index.html` carga `datos/modelo/salidas-inicio.js` (≈0,7 MB: predicciones, alternativas, perfil, fiabilidad, mapeo y calendario). `DatosModelo.cargar()` (la que usan Gestión y Sobre los datos) inserta `salidas.js` completo la primera vez que se pide. El objeto y su forma no cambian para la persona 2, y `pruebas.html` sigue leyendo `salidas.js`. Nuevo: `DatosModelo.cargarInicio()` (lo usa Inicio).
- **Decisión pendiente del equipo:** con `config/semaforo.yaml`, «Normal» (verde) llega hasta +49 % sobre un día normal. Un día con casi la mitad más de gente sale como «Normal». Opciones: bajar `umbral_ambar` o renombrar el verde (p. ej. «Sin presión»).

## Integración

- `web-gestion` (`fc6ebb5`) integrada en `web` por avance rápido, sin conflictos. Probado: demo de Inicio → Gestión → Sobre los datos, 20/20 pruebas de `pestanas/gestion/pruebas.html`, sin errores propios en la consola.

## Datos reales (rama `web-datos-reales`, 2026-10-16)

Detalle en `notas/historico/integracion_web.md`. Cambios en ficheros de la persona 2 (solo datos y textos; sin tocar estilos ni maquetación):
- `pestanas/gestion/gestion.js`:
  - **patrón horario conectado**: `pintarHoras()` rellena el mismo `#perfil-horas` desde `datos.horas` (nuevo en el módulo «datos», sale de `data/clean/llegadas_por_hora.parquet`); sin datos, queda el «Pendiente de datos»;
  - texto de Alertas: el tiempo entra a 1-3 días, no hasta una semana.
- `pestanas/sobre/contenido.js`:
  - INE como «Validación prevista» (aún no se ha hecho);
  - el tiempo, solo a 1-3 días.
- Demo: `DEMO_MES = '2024-08'`. Con datos reales, el puente de diciembre de 2024 sale en verde.

## Funciones avanzadas (antes Gestión), 2026-10-16

Cambios en `pestanas/gestion/` pedidos por el equipo (rama `interfaz-refinado`):
- La pestaña se llama **Funciones avanzadas** y la web, **NTT Tourism**. Cada apartado es un panel: el índice (`chip-btn` con `aria-pressed`) enseña uno cada vez.
- **Previsión de saturación** (antes «¿Hace falta regular?»): se basa solo en la predicción de los próximos 12 meses. El buscador encuentra concejos y comarcas y detalla los días previstos por encima del umbral, agrupados por mes. La barra deslizante se mantiene.
- **Alertas**: la matriz de 46 zonas pasa a ser dinámica. Desplegable de comarca y selección múltiple de sus concejos; «Todos los concejos de la comarca» y «Ver todas las comarcas» (por defecto: el peor nivel de cada comarca). La lista resumen no cambia.
- Comarcas: `config/comarcas_asturias.csv` (las 8 del Decreto 11/1991), exportadas por `actualizar_datos_web.py` como `datos.comarcas`.
- `gestion.css` copia el aspecto del buscador de Inicio para el buscador y el desplegable; no hay estilos nuevos de color ni tipografía.
- No había «simulador de escenarios» en la web (se quitó al conectar los datos reales). «Exportar datos» se mantiene, ahora con los días previstos sobre el umbral.

## Funciones avanzadas copiada de `referencia-gestion` (2026-10-16)

A petición del equipo, la pestaña es ahora la de la rama `referencia-gestion` (carpeta `referencia-gestion/`, commit `0fb737d`). Se copian tal cual sus `pestanas/gestion/{gestion.js, gestion.css, logica.js, config-gestion.js, pruebas.html}` (rama `funciones-referencia`). El resto de la carpeta de referencia es una versión anterior de la web y no se trae.

Qué incluye:
- paneles con pestañas;
- Previsión de saturación: buscador de zonas y concejos, periodo y umbral; detalle con rachas y días por mes;
- Alertas: zona, concejos con casillas, fichas, «Todas las zonas» y «Todos los concejos»;
- Exportar: 3 CSV.

Tres ajustes sobre la copia:
- el panel «Lagos de Covadonga» se llama «Regulación actual» (lo pidió el equipo);
- el patrón horario sigue con datos reales (`datos.horas`), porque la copia aún decía «Pendiente de datos»;
- los textos dicen que el tiempo entra a 1-3 días, no «hasta 7 días».

Pruebas: 28/28 de `pruebas.html` con los datos de 46 zonas. Las comarcas (`datos.comarcas`) dejan de usarse en esta pestaña.
