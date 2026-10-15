# Coordinación de la web (persona 1 ↔ persona 2)

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

## Integración

- `web-gestion` (`fc6ebb5`) integrada en `web` por avance rápido, sin conflictos. Probado: demo de Inicio → Gestión → Sobre los datos, 20/20 pruebas de `pestanas/gestion/pruebas.html`, sin errores propios en la consola.
