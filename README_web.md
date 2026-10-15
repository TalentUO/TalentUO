# Web: alerta temprana de presión turística

La web vive en `Afluencia Asturias/`: HTML, CSS y JavaScript sin compilación ni dependencias externas obligatorias. El mapa, las librerías y los datos van dentro del repositorio, así que **funciona sin internet**. Solo las tipografías se piden a Google Fonts; sin conexión se usan las de reserva.

## Arrancar (una orden)

```bash
python scripts/servir_web.py          # abre http://127.0.0.1:8000/
python scripts/servir_web.py --demo   # abre el modo demo
```

Solo necesita Python 3 (biblioteca estándar). También se puede abrir `Afluencia Asturias/index.html` con doble clic: los datos van en `datos/modelo/salidas.js`, que el navegador lee también desde `file://`.

## Modo demo (`?demo=1`)

Abre el **puente de diciembre de 2024**: el día del puente con más presión en la zona principal (Picos de Europa: Cangas de Onís, Covadonga y Lagos), con su panel abierto. Son predicciones fuera de muestra de la validación (conjunto `historico`, modelo de largo plazo con 8 días de antelación), con el valor observado al lado («Lo que pasó de verdad»).

Recorrido de la presentación:

1. **Mapa**: los Picos en rojo, con icono, trama y porcentaje sobre un día normal.
2. **¿Por qué?**: los 3 factores que más pesan, con su efecto en %.
3. **Alternativa**: el mejor día a ±3 días y la zona cercana con menos presión (de `alternativas.json`).
4. **Gestión** (pestaña de la persona 2).

## Actualizar los datos (mañana, con datos reales)

```bash
python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos   # el modelo regenera salidas/
python -X utf8 scripts/actualizar_datos_web.py                            # valida y copia a la web
```

Después basta con recargar la página. El script:

- valida `salidas/` con el validador del modelo y no copia nada si algo falla;
- copia los cinco JSON a `Afluencia Asturias/datos/modelo/`;
- elige `config/mapeo_zonas.csv` si cubre las zonas de las predicciones (si no, el de ejemplo);
- exporta el calendario oficial (puentes y festivos);
- genera `salidas.js`.

Mientras los datos sean sintéticos, la web muestra arriba y en todas las pestañas el aviso **«DATOS SINTÉTICOS – solo para pruebas»**. Con datos reales (`sintetico: false`) el aviso desaparece solo.

## Estructura

| Ruta | Qué es | Quién |
|---|---|---|
| `index.html`, `estilos/`, `interfaz/` | Base, mapa (Leaflet + límites del IGN), pestaña Inicio | Persona 1 |
| `datos/datos.js` | Módulo «datos»: carga y valida las salidas del modelo (`window.DatosModelo`) | Persona 1 |
| `datos/fuente-modelo.js` | Traduce las salidas al contrato de la interfaz (`window.Datos`) | Persona 1 |
| `datos/modelo/` | Copia de las salidas (generada por el script; no editar) | Script |
| `pestanas/gestion/`, `pestanas/sobre/` | Pestañas Gestión y Sobre los datos | Persona 2 |

Contrato de las salidas: `notas/contrato_web.md`. Coordinación entre las dos personas, fuente del mapa y huecos del contrato: `notas/coordinacion_web.md`.

## Comprobaciones

```bash
node --check "Afluencia Asturias/interfaz/app.js" "Afluencia Asturias/interfaz/mapa.js" "Afluencia Asturias/datos/"*.js
```

Revisado a 1366×768 y 1920×1080, sin errores en la consola, en modo normal y en modo demo.
