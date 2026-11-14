# CLAUDE.md

Este fichero orienta a Claude Code (claude.ai/code) cuando trabaja con el código de este repositorio.

## Qué es

NTT Tourism: un sistema de alerta temprana de presión turística en Asturias (Hackathon TalentUO 2026). Una cadena en Python predice las llegadas diarias de ocio a las 46 zonas del MITMA (78 concejos) en relación con el «día normal» de cada zona, y una web estática (`Afluencia Asturias/`) lo muestra como un semáforo (verde / ámbar ≥ 1,5× / rojo ≥ 2,0×).

**Todo está escrito en español**: identificadores, comentarios, documentación, textos de la interfaz y mensajes de commit. Hay que mantenerlo así.

## Órdenes

Python 3.11; todo se ejecuta desde la raíz del repositorio (los scripts usan rutas relativas a la raíz). En Windows, pasar siempre `-X utf8`.

```bash
pip install -r requirements.txt                 # requirements-lock.txt tiene las versiones exactas probadas

# Lint (solo errores de sintaxis y nombres sin usar o sin definir: E9, F)
python -m ruff check src scripts "Afluencia Asturias/herramientas"

# Pruebas del modelo
python -X utf8 -m pytest -q -m "not lento" src/modelo/tests        # rápidas (~30 s)
python -X utf8 -m pytest -q src/modelo/tests                       # todas (~4 min; ejecuta la cadena completa con cada algoritmo)
python -X utf8 -m pytest -q src/modelo/tests/test_antifuga.py      # un fichero
python -X utf8 -m pytest -q src/modelo/tests -k "nombre_del_test"  # una prueba

# Modelo: regenerar salidas/ y llevarlas a la web
python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos   # ~15 min, lo que publica la web
python -X utf8 src/modelo/ejecutar.py --objetivo sintetico                # comprobación de la cadena con un objetivo inventado
python -X utf8 scripts/actualizar_datos_web.py                            # valida salidas/ y las copia a la web

# Limpieza de factores (parte B): rehace data/clean/ desde data/raw/ (~50 s, se detiene en la primera comprobación fallida)
python -X utf8 src/limpieza_B/ejecutar_todo.py
python -X utf8 src/limpieza_B/test_unir_B.py    # un script normal con asserts, no una prueba de pytest

# Web
python scripts/servir_web.py            # http://127.0.0.1:8000/
python scripts/servir_web.py --demo     # modo demo (?demo=1): validación de agosto de 2024 con los valores observados
node --check "Afluencia Asturias/interfaz/app.js" "Afluencia Asturias/interfaz/mapa.js" "Afluencia Asturias/datos/"*.js
```

Las pruebas de la lógica de la interfaz están en `Afluencia Asturias/pestanas/gestion/pruebas.html` (se abre en un navegador; debe decir «TODO OK»). Despliegue: desde `Afluencia Asturias/`, `vercel deploy --prod` (proyecto `ntt-tourism`).

Variables de entorno: `AEMET_API_KEY` (descargas de AEMET), `TALENTUO_CONTACTO` (contacto en el User-Agent de las descargas), `MODELO_SALIDAS` (redirige las salidas del modelo fuera de `salidas/`; la usan las pruebas).

## Arquitectura

```
data/raw ──► src/descarga_*.py, scripts/descarga_*.py   (descargas; raw nunca se edita a mano)
         ──► src/limpieza_B/  ──► data/clean/*.parquet  (factores: calendario, eventos, tiempo, Wikipedia/Trends)
MITMA    ──► src/modelo/construir_objetivo.py ──► data/clean/objetivo_diario.parquet  (objetivo)
                      │
                      ▼
            src/modelo/ejecutar.py ──► salidas/*.json, backtest.parquet
                      │
                      ▼
            scripts/actualizar_datos_web.py ──► Afluencia Asturias/datos/modelo/  (salidas.js, salidas-inicio.js, *.json)
```

### Modelo (`src/modelo/`)

- Los módulos **no son un paquete**: cada punto de entrada hace `sys.path.insert(0, <su directorio>)` e importa a sus hermanos por el nombre a secas (`import backtest`, `from util import cfg`). Hay que seguir ese patrón; no añadir importaciones relativas.
- `ejecutar.py` es el orquestador: `datos.cargar` → `backtest` (validación por bloques + experimentos de sensibilidad) → `metricas` → `produccion.entrenar_finales` → `explicar` (SHAP) → `calibracion` (regulación de los Lagos) → `web_salidas` → `validar_salidas`. Aborta si no se cumple el contrato de la web.
- `util.py` contiene las rutas (`RAIZ`, `CLEAN`, `SALIDAS`…), los cargadores de configuración (`cfg()`, `cfg_semaforo()`…) y las funciones auxiliares del semáforo. Todos los parámetros ajustables están en `config/*.yaml`; `config/modelo.yaml → fuentes` es lo único que cambia entre el modo `sintetico` y el `real`.
- Objetivo: `y = log((x + 1) / (normal + 1))`. El «día normal» (`dia_normal.py`) = mediana por zona y día de la semana en 2024, sin julio, agosto ni festivos. En el backtest se recalcula con los 365 días anteriores a cada bloque.
- **Dos modelos globales** (uno para todas las zonas, con la zona como variable categórica): largo plazo (h ≥ 8, solo calendario y eventos) y corto plazo (h = 1–7, además previsión del tiempo, interés en internet y horizonte). `--algoritmo ambos` hace el backtest de LightGBM y de XGBoost y elige uno con la regla fijada de antemano en `comparacion.py` / `config/modelo.yaml → seleccion_algoritmo`; todo lo posterior usa el ganador (ahora mismo, XGBoost).
- **Regla anti-fuga (el invariante central):** para predecir el día d con horizonte h, `features.py` solo puede usar lo publicado hasta d−h. El tiempo es únicamente la previsión archivada (`om_*_prev{h}`, h ≤ 3, desde el 2024-01-22), nunca las observaciones de AEMET ni ERA5; nunca valores retardados del objetivo. `tests/test_antifuga.py` corrompe todo lo posterior a d−h y comprueba que ninguna variable cambia: cualquier cambio en `features.py` debe mantenerla en verde.
- Los días marcados `sin_dato_mitma` / `anomalia_mitma` ni se usan para entrenar ni se evalúan. Un dato que falta está ausente (NaN), nunca vale 0.
- El modo sintético marca `sintetico: true` en todas las salidas y la web muestra un aviso; nunca se publica como real.

### Contratos

- `notas/contrato_objetivo.md`: formato de `objetivo_diario.parquet` (entrada del modelo).
- `notas/contrato_web.md`: formato de los JSON de `salidas/` que lee la web. En Python lo hacen cumplir `validar_salidas.py` y `tests/test_contrato_web.py`; en JavaScript, `Afluencia Asturias/datos/datos.js`. Los tres se cambian a la vez.

### Web (`Afluencia Asturias/`)

HTML, CSS y JavaScript estáticos, sin compilación ni framework, con Leaflet y topojson-client incluidos en el repositorio. Tiene que seguir funcionando desde `file://` (doble clic) y sin conexión; por eso los scripts son clásicos (no módulos ES) y los datos van en ficheros `.js` en lugar de pedirse con fetch.

Capa de datos, en orden de carga:

```
salidas-inicio.js ─┐
                   ├─ datos.js (window.DatosModelo) ─ fuente-modelo.js (window.FuenteDatos) ─ api.js (window.Datos) ─ interfaz/app.js
salidas.js ────────┘              └─────────────── pestanas/ (Funciones avanzadas, Sobre los datos) leen DatosModelo directamente
```

- `interfaz/` solo pinta y gestiona la interacción: nunca calcula previsiones, niveles ni umbrales (los umbrales vienen de `predicciones.umbrales`). `mapa.js` no sabe nada de previsiones.
- Para añadir un dato a Inicio: documentarlo en el comentario de cabecera de `datos/api.js`, añadirlo a `METODOS`, implementarlo en `fuente-modelo.js` y después usarlo desde `app.js`.
- `pestanas/gestion/logica.js` son funciones puras sin DOM (las prueba `pruebas.html`).
- **Generados, nunca se editan a mano:** `datos/modelo/*` (los crea `actualizar_datos_web.py`), `interfaz/geo-asturias.js` y `datos/sitios.js` (los crea `herramientas/`).
- Convenciones (detalle en `Afluencia Asturias/README.md` §6): el diseño visual está congelado (el código puede cambiar, lo que se ve no); todos los colores son variables CSS definidas en `index.html` (claro, `prefers-color-scheme: dark` y `[data-theme="dark"]`), sin literales en CSS ni en JS; un nivel nunca se transmite solo con el color (icono + trama + palabra); se muestra y se oculta con el atributo `hidden`; las funciones asíncronas que pintan usan un contador `seq*` para descartar las respuestas tardías; los números se escriben `8.880`, con espacio de no separación antes de `%` y el signo menos real `−`.

## Datos y restricciones de licencia

- Las entradas pesadas o no redistribuibles están en `.gitignore` a propósito (≈27 GB de ficheros del MITMA, COGERSA, copias de páginas de eventos y calendarios de terceros, los `.px` de SADEI). No hay que volver a añadirlas; ver `data/raw/LEEME_datos_no_versionados.md` y `FUENTES_Y_LICENCIAS.md`. El modelo se entrena sin ellas, a partir de las tablas versionadas de `data/clean/`.
- Las salidas vigentes son las de `main` (46 zonas). Ramas antiguas como `resultados-reales` tienen salidas de 5 zonas; no hay que traer nada de ellas.
- `notas/historico/` y `src/auditoria/` son registros de fases terminadas, no el comportamiento actual. `notas/README.md` indica qué está vigente; `notas/modelo.md` es la referencia de las decisiones del modelo (ojo: varias secciones de resultados son de la ejecución sintética y están marcadas como tales).
- Las cifras citadas en `README.md` indican el fichero de `salidas/` del que salen; cuando se regeneren las salidas, hay que actualizar esas cifras a partir de los ficheros, no de memoria.
