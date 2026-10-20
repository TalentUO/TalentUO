# Web: datos, demo, actualización y despliegue

La web vive en `Afluencia Asturias/`: HTML, CSS y JavaScript sin compilación ni dependencias externas obligatorias. El mapa, las librerías y los datos van dentro del repositorio, así que **funciona sin internet**. Solo las tipografías se piden a Google Fonts; sin conexión se usan las de reserva.

Este documento explica cómo se alimenta, se enseña y se publica la web. El código del frontend (estructura, capa de datos, convenciones y accesibilidad) se documenta en `Afluencia Asturias/README.md`.

## Estado de los datos

- **Datos reales** (`sintetico: false`): modelo XGBoost, elegido por regla frente a LightGBM, entrenado con el MITMA (2022-01-01 → 2025-06-30).
- **Fecha de las salidas:** generadas el **2026-10-16 a las 10:30**, con `fecha_hoy` 2026-10-16 y la previsión de Open-Meteo emitida ese día.
- **Toda Asturias:** 46 zonas MITMA (los 78 concejos) de `config/mapeo_zonas.csv`. La ampliación y sus decisiones están en `notas/ampliacion_zonas.md`.
- **Periodo:** predicciones del 2026-10-17 al 2027-10-16 (un año). El tiempo solo entra a 1-3 días.
- **Cifras del modelo:** `README.md` («Resultados»).
- **Capturas del recorrido de la demo** (plan B si falla la conexión en la presentación): `notas/capturas_demo/`.

## En internet (Vercel)

Publicada en **<https://ntt-tourism.vercel.app>** (proyecto `ntt-tourism` de Vercel).

- Es la carpeta `Afluencia Asturias/` tal cual, como sitio estático sin compilación.
- `Afluencia Asturias/.vercelignore` deja fuera las copias en JSON de los datos (ya van en `salidas.js`) y las herramientas de Python.

Para publicar una versión nueva, desde `Afluencia Asturias/` y con una cuenta con acceso al proyecto:

```bash
vercel link --yes --project ntt-tourism   # solo la primera vez en cada ordenador
vercel deploy --prod
```

## Arrancar en local

```bash
python scripts/servir_web.py          # abre http://127.0.0.1:8000/: la previsión desde hoy, un año
python scripts/servir_web.py --demo   # modo demo: validación con datos de agosto de 2024
```

Solo necesita Python 3 (biblioteca estándar). También se puede abrir `Afluencia Asturias/index.html` con doble clic: los datos van en `datos/modelo/salidas-inicio.js` y `salidas.js`, que el navegador lee también desde `file://`.

Por defecto la web abre **hoy** y deja elegir cualquier día del año siguiente.

## Modo demo (`?demo=1`)

No es la vista principal: sirve para enseñar cómo acierta el modelo en días pasados, con el valor real al lado.

- **Día que abre:** el día del puente con más presión en la zona principal (Picos de Europa: Cangas de Onís, Covadonga y Lagos), con su panel abierto. Es el **jueves 15 de agosto de 2024 (Asunción): Saturación, +227 %** sobre un día normal (observado: +290 %).
- **Mapa de ese día:** el modelo pinta 16 zonas en saturación; de verdad fueron 20.
- **Qué se enseña:** predicciones fuera de muestra de la validación (conjunto `historico`, modelo de largo plazo con 8 días de antelación), con el valor observado al lado («Lo que pasó de verdad»).
- **Cómo se cambia el mes:** en `DEMO_MES` (`Afluencia Asturias/datos/fuente-modelo.js`).

La demo anterior era el puente de diciembre de 2024. Con los datos reales sale en verde en los Picos (observado: ámbar), así que se cambió a agosto.

Recorrido de la presentación:

1. **Mapa:** los Picos en rojo, con icono, trama y porcentaje sobre un día normal.
2. **¿Por qué?:** los 3 factores que más pesan, con su efecto en %.
3. **Alternativa:** la zona cercana con menos presión (Mieres, −35 %, a 58 km; de `alternativas.json`). El mejor día a ±3 días (domingo 18) también está en saturación, con un 9 % menos de gente.
4. **Funciones avanzadas**, con estos paneles:
   - «Previsión de saturación»: buscador de zonas y concejos, periodo (por defecto, todo 2027) y umbral ajustable; días previstos por encima del umbral, con rachas y días por mes;
   - «Alertas»: por zona, con selección de concejos;
   - «Fiabilidad del modelo»: gráfica de lo real frente a lo previsto en la validación;
   - «Perfil del visitante»: incluye el patrón horario;
   - «Exportar datos»: saturación con su umbral y periodo, y perfil del visitante.

## Actualizar los datos

```bash
python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos   # el modelo regenera salidas/ (unos 15 min)
python -X utf8 scripts/actualizar_datos_web.py                            # valida y copia a la web
```

Después basta con recargar la página. El script `actualizar_datos_web.py`:

- valida `salidas/` con el validador del modelo y no copia nada si algo falla;
- copia los cinco JSON del modelo (`predicciones`, `alternativas`, `regulacion`, `perfil` y `metricas`) a `Afluencia Asturias/datos/modelo/`;
- elige `config/mapeo_zonas.csv` si cubre las zonas de las predicciones (si no, el de ejemplo) y lo exporta como `mapeo_zonas.json`;
- exporta además:
  - el calendario oficial (puentes y festivos), en `calendario.json`;
  - la serie real frente a la prevista de la validación (`salidas/backtest.parquet`), en `validacion.json`, para la gráfica de Fiabilidad;
  - las llegadas por hora (`data/clean/llegadas_por_hora.parquet`), en `horas.json`, para el patrón horario;
  - los festivos y partidos de la sección de eventos, en `agenda.json`;
  - las comarcas (`config/comarcas_asturias.csv`, Decreto 11/1991), en `comarcas.json`;
- genera `salidas.js` (todo) y `salidas-inicio.js` (lo que usa Inicio, para que la página cargue antes).

Si los datos fueran sintéticos, la web mostraría arriba y en todas las pestañas el aviso **«DATOS SINTÉTICOS – solo para pruebas»**. Con los datos reales actuales (`sintetico: false`) no sale.

Las salidas vigentes son las de `main`. No hay que traerlas de ramas antiguas: `resultados-reales` tiene las de 5 zonas.

## Comprobaciones

```bash
node --check "Afluencia Asturias/interfaz/app.js" "Afluencia Asturias/interfaz/mapa.js" "Afluencia Asturias/datos/"*.js
```

Las pruebas de la lógica de Funciones avanzadas están en `Afluencia Asturias/pestanas/gestion/pruebas.html`: se abre en el navegador.

Revisado con datos reales el 2026-10-16 a 1366×768 y 1920×1080, sin internet y sin errores en la consola, en modo normal y en modo demo.

Contrato de las salidas del modelo: `notas/contrato_web.md`.
