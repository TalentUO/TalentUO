# Web: alerta temprana de presión turística

La web vive en `Afluencia Asturias/`: HTML, CSS y JavaScript sin compilación ni dependencias externas obligatorias. El mapa, las librerías y los datos van dentro del repositorio, así que **funciona sin internet**. Solo las tipografías se piden a Google Fonts; sin conexión se usan las de reserva.

## Estado de los datos

- **Datos reales** (`sintetico: false`): modelo XGBoost (elegido por regla frente a LightGBM) entrenado con el MITMA (2022-01-01 → 2025-06-30). Salidas generadas el **2026-10-16 09:41**, con `fecha_hoy` 2026-10-16 y la previsión de Open-Meteo emitida ese día.
- **Toda Asturias:** 46 zonas MITMA (los 78 concejos) de `config/mapeo_zonas.csv`. Predicciones del 2026-10-17 al 2027-10-16 (un año; con el tiempo a 1-3 días). Ampliación y sus decisiones: `notas/ampliacion_zonas.md`.
- Comprobación de cada pestaña y cotejo con `notas/resultados_reales.md`: `notas/integracion_web.md`. Capturas del recorrido de la demo (plan B): `notas/capturas_demo/`.

## Arrancar (una orden)

```bash
python scripts/servir_web.py          # abre http://127.0.0.1:8000/: la previsión desde hoy, un año
python scripts/servir_web.py --demo   # modo demo: validación con datos de agosto de 2024 (opcional)
```

Solo necesita Python 3 (biblioteca estándar). También se puede abrir `Afluencia Asturias/index.html` con doble clic: los datos van en `datos/modelo/salidas-inicio.js` y `salidas.js`, que el navegador lee también desde `file://`.

Por defecto la web abre **hoy** y deja elegir cualquier día del año siguiente (predicciones del 2026-10-17 al 2027-10-16).

## Modo demo (`?demo=1`, opcional)

No es la vista principal: sirve para enseñar cómo acierta el modelo en días pasados, con el valor real al lado.

Abre **agosto de 2024**, en el día del puente con más presión en la zona principal (Picos de Europa: Cangas de Onís, Covadonga y Lagos), con su panel abierto: **jueves 15 de agosto de 2024 (Asunción), Saturación, +227 %** sobre un día normal (observado: +290 %). Ese día el modelo pinta 16 zonas en saturación (fueron 20). Son predicciones fuera de muestra de la validación (conjunto `historico`, modelo de largo plazo con 8 días de antelación), con el valor observado al lado («Lo que pasó de verdad»). El mes se fija en `DEMO_MES` (`datos/fuente-modelo.js`).

Con los datos reales, el puente de diciembre de 2024 (la demo anterior) sale en verde en los Picos (observado: ámbar), así que se cambió a agosto.

Recorrido de la presentación:

1. **Mapa**: los Picos en rojo, con icono, trama y porcentaje sobre un día normal.
2. **¿Por qué?**: los 3 factores que más pesan, con su efecto en %.
3. **Alternativa**: la zona cercana con menos presión (Mieres, −35 %, a 58 km; de `alternativas.json`). El mejor día a ±3 días (domingo 18) también está en saturación, con un 9 % menos de gente.
4. **Gestión**: días por encima del umbral (Picos: 39 en 2023 y 48 en 2024 con +100 %; 8 zonas superan los 30 días en 2026) y comparación con los Lagos.

## Actualizar los datos

```bash
python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos   # el modelo regenera salidas/
python -X utf8 scripts/actualizar_datos_web.py                            # valida y copia a la web
```

Después basta con recargar la página. El script:

- valida `salidas/` con el validador del modelo y no copia nada si algo falla;
- copia los cinco JSON a `Afluencia Asturias/datos/modelo/`;
- elige `config/mapeo_zonas.csv` si cubre las zonas de las predicciones (si no, el de ejemplo);
- exporta el calendario oficial (puentes y festivos) y las llegadas por hora (`data/clean/llegadas_por_hora.parquet`, para el patrón horario de Gestión);
- genera `salidas.js` (todo) y `salidas-inicio.js` (lo que usa Inicio, para que la página cargue antes).

Si los datos fueran sintéticos, la web mostraría arriba y en todas las pestañas el aviso **«DATOS SINTÉTICOS – solo para pruebas»**. Con los datos reales actuales (`sintetico: false`) no sale.

Para traer unas salidas nuevas de la rama del modelo sin su código:

```bash
git checkout origin/resultados-reales -- salidas/predicciones.json salidas/alternativas.json salidas/regulacion.json salidas/perfil.json salidas/metricas.json config/mapeo_zonas.csv data/clean/llegadas_por_hora.parquet
python -X utf8 scripts/actualizar_datos_web.py
```

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

Revisado con datos reales el 2026-10-16 a 1366×768 y 1920×1080, sin internet y sin errores en la consola, en modo normal y en modo demo.
