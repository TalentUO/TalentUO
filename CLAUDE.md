# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

NTT Tourism: an early-warning system for tourist pressure in Asturias (Hackathon TalentUO 2026). A Python pipeline predicts daily leisure arrivals for the 46 MITMA zones (78 concejos) relative to each zone's "día normal", and a static web app (`Afluencia Asturias/`) shows it as a traffic light (verde / ámbar ≥ 1.5× / rojo ≥ 2.0×).

**Everything is written in Spanish**: identifiers, comments, docs, UI text and commit messages. Keep it that way.

## Commands

Python 3.11, run everything from the repository root (scripts use root-relative paths). Always pass `-X utf8` on Windows.

```bash
pip install -r requirements.txt                 # requirements-lock.txt has the exact tested versions

# Lint (only syntax errors and unused/undefined names: E9, F)
python -m ruff check src scripts "Afluencia Asturias/herramientas"

# Model tests
python -X utf8 -m pytest -q -m "not lento" src/modelo/tests        # fast (~30 s)
python -X utf8 -m pytest -q src/modelo/tests                       # all (~4 min; runs the full chain per algorithm)
python -X utf8 -m pytest -q src/modelo/tests/test_antifuga.py      # one file
python -X utf8 -m pytest -q src/modelo/tests -k "nombre_del_test"  # one test

# Model: regenerate salidas/ and push them to the web
python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos   # ~15 min, what the web publishes
python -X utf8 src/modelo/ejecutar.py --objetivo sintetico                # chain check with a made-up target
python -X utf8 scripts/actualizar_datos_web.py                            # validates salidas/ and copies to the web

# Factor cleaning (part B): rebuilds data/clean/ from data/raw/ (~50 s, stops at the first failed check)
python -X utf8 src/limpieza_B/ejecutar_todo.py
python -X utf8 src/limpieza_B/test_unir_B.py    # a plain script with asserts, not a pytest test

# Web
python scripts/servir_web.py            # http://127.0.0.1:8000/
python scripts/servir_web.py --demo     # demo mode (?demo=1): August 2024 validation with observed values
node --check "Afluencia Asturias/interfaz/app.js" "Afluencia Asturias/interfaz/mapa.js" "Afluencia Asturias/datos/"*.js
```

Frontend logic tests live in `Afluencia Asturias/pestanas/gestion/pruebas.html` (open in a browser; must say «TODO OK»). Deploy: from `Afluencia Asturias/`, `vercel deploy --prod` (project `ntt-tourism`).

Environment variables: `AEMET_API_KEY` (AEMET downloads), `TALENTUO_CONTACTO` (contact in download User-Agent), `MODELO_SALIDAS` (redirects model output away from `salidas/`; the tests use it).

## Architecture

```
data/raw ──► src/descarga_*.py, scripts/descarga_*.py   (downloads; raw is never hand-edited)
         ──► src/limpieza_B/  ──► data/clean/*.parquet  (factors: calendar, events, weather, Wikipedia/Trends)
MITMA    ──► src/modelo/construir_objetivo.py ──► data/clean/objetivo_diario.parquet  (target)
                      │
                      ▼
            src/modelo/ejecutar.py ──► salidas/*.json, backtest.parquet
                      │
                      ▼
            scripts/actualizar_datos_web.py ──► Afluencia Asturias/datos/modelo/  (salidas.js, salidas-inicio.js, *.json)
```

### Model (`src/modelo/`)

- Modules are **not a package**: each entry point does `sys.path.insert(0, <its dir>)` and imports siblings by bare name (`import backtest`, `from util import cfg`). Follow that pattern; don't add relative imports.
- `ejecutar.py` is the orchestrator: `datos.cargar` → `backtest` (block validation + sensitivity experiments) → `metricas` → `produccion.entrenar_finales` → `explicar` (SHAP) → `calibracion` (Lagos regulation) → `web_salidas` → `validar_salidas`. It aborts if the web contract is not met.
- `util.py` holds paths (`RAIZ`, `CLEAN`, `SALIDAS`…), config loaders (`cfg()`, `cfg_semaforo()`…) and the traffic-light helpers. All tunables live in `config/*.yaml`; `config/modelo.yaml → fuentes` is the only thing that differs between `sintetico` and `real` mode.
- Target: `y = log((x + 1) / (normal + 1))`. "Día normal" (`dia_normal.py`) = median per zone and weekday in 2024, excluding July, August and holidays. In the backtest it is recomputed from the 365 days before each block.
- **Two global models** (one for all zones, zone as a categorical): long-term (h ≥ 8, calendar + events only) and short-term (h = 1–7, plus weather forecast, internet interest and horizon). `--algoritmo ambos` backtests LightGBM and XGBoost and picks one with the pre-registered rule in `comparacion.py` / `config/modelo.yaml → seleccion_algoritmo`; everything downstream uses the winner (currently XGBoost).
- **No-leakage rule (the central invariant):** to predict day d at horizon h, `features.py` may only use what was published by d−h. Weather is the archived forecast only (`om_*_prev{h}`, h ≤ 3, from 2024-01-22), never AEMET observations or ERA5; never lagged values of the target. `tests/test_antifuga.py` corrupts everything after d−h and asserts no feature changes — any change to `features.py` must keep it green.
- Days flagged `sin_dato_mitma` / `anomalia_mitma` are neither trained on nor evaluated. Missing data is absent (NaN), never 0.
- Synthetic mode stamps `sintetico: true` on every output and the web shows a warning banner; never publish it as real.

### Contracts

- `notas/contrato_objetivo.md`: format of `objetivo_diario.parquet` (model input).
- `notas/contrato_web.md`: format of the JSON in `salidas/` read by the web. Enforced on the Python side by `validar_salidas.py` and `tests/test_contrato_web.py`, and on the JS side by `Afluencia Asturias/datos/datos.js`. Change all three together.

### Web (`Afluencia Asturias/`)

Static HTML/CSS/JS with no build step, no framework, and vendored Leaflet + topojson-client. It must keep working from `file://` (double click) and offline, which is why scripts are classic (not ES modules) and data ships as `.js` files instead of being fetched.

Data layer, in load order:

```
salidas-inicio.js ─┐
                   ├─ datos.js (window.DatosModelo) ─ fuente-modelo.js (window.FuenteDatos) ─ api.js (window.Datos) ─ interfaz/app.js
salidas.js ────────┘              └─────────────── pestanas/ (Funciones avanzadas, Sobre los datos) read DatosModelo directly
```

- `interfaz/` only paints and handles interaction: it never computes forecasts, levels or thresholds (thresholds come from `predicciones.umbrales`). `mapa.js` knows nothing about forecasts.
- To add a datum to Inicio: document it in the header comment of `datos/api.js`, add it to `METODOS`, implement it in `fuente-modelo.js`, then use it from `app.js`.
- `pestanas/gestion/logica.js` is pure functions without DOM (tested by `pruebas.html`).
- **Generated, never hand-edit:** `datos/modelo/*` (from `actualizar_datos_web.py`), `interfaz/geo-asturias.js` and `datos/sitios.js` (from `herramientas/`).
- Conventions (details in `Afluencia Asturias/README.md` §6): the visual design is frozen (code may change, what is seen may not); all colours are CSS variables defined in `index.html` (light, `prefers-color-scheme: dark` and `[data-theme="dark"]`), no literals in CSS/JS; a level is never conveyed by colour alone (icon + pattern + word); show/hide with the `hidden` attribute; async painters use a `seq*` counter to drop late responses; numbers use `8.880`, NBSP before `%`, and the real minus sign `−`.

## Data and licensing constraints

- Heavy or non-redistributable inputs are gitignored on purpose (≈27 GB of MITMA files, COGERSA, copies of third-party event/calendar pages, SADEI `.px`). Don't add them back; see `data/raw/LEEME_datos_no_versionados.md` and `FUENTES_Y_LICENCIAS.md`. The model trains from the versioned `data/clean/` tables without them.
- The current outputs are the ones on `main` (46 zones). Old branches such as `resultados-reales` hold 5-zone outputs; don't pull from them.
- `notas/historico/` and `src/auditoria/` are records of finished phases, not current behaviour. `notas/README.md` indexes what is current; `notas/modelo.md` is the reference for model decisions (note that several result sections in it are from the synthetic run and are labelled as such).
- Figures quoted in `README.md` cite the `salidas/` file they come from; when outputs are regenerated, update those figures from the files rather than from memory.
