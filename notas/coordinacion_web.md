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

- **Esqueleto listo** — commit `PENDIENTE` (rama `web`).

## Peticiones / huecos del contrato

- (vacío)
