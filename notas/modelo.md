# Modelo de presión turística: decisiones, validación y cómo conectar los datos reales

Fecha: 2026-10-15; actualizado el 2026-10-16 con las 46 zonas. Código en `src/modelo/`, configuración en `config/modelo.yaml`, `config/semaforo.yaml`, `config/factores.yaml` y `config/mitma_calidad.yaml`. Contratos: `notas/contrato_objetivo.md` (entrada: el objetivo del MITMA) y `notas/contrato_web.md` (salida para la web).

> **Estado (2026-10-16): el modelo está entrenado con datos reales** del MITMA para **las 46 zonas de Asturias** (`data/clean/objetivo_diario.parquet`, 58 742 filas, 2022-01-01 → 2025-06-30; ampliación en `notas/ampliacion_zonas.md`). Todas las salidas de la web llevan `sintetico=false`. Resumen (cifras completas, con su fichero, en `README.md` → «Resultados»):
> - **Algoritmo: XGBoost**, por la regla de elección v2 (paso 1): recall de rojos en verano 64,2 % frente a 53,9 % de LightGBM, con una precisión 1,4 puntos menor (87,2 % frente a 88,6 %) y WAPE medio 9,8 % frente a 10,1 % (`salidas/comparacion_algoritmos.json`, `salidas/resumen_ejecucion.json → seleccion_algoritmo`).
> - **Error, todos los bloques (`salidas/metricas.json → tablas.global`):** WAPE del 9,7 % (corto) y 9,9 % (largo), frente al 12,9 % del día normal (B0) y al 10,9 % del año anterior (B1). Recall de rojos del 54,7 % y 68,7 %, con precisión del 88,6 % y 85,2 % (B1: 70,2 % y 74,1 %).
> - **Peor de lo esperado:**
>   - a corto plazo detecta menos rojos que B1 (54,7 % frente a 70,2 %), aunque con más precisión;
>   - en el bloque final (2025-S1), el largo plazo no gana a B0 en WAPE (10,8 % frente a 9,2 %); el corto sí (8,9 %);
>   - se queda corto en volumen en todos los bloques (entre −1,2 % y −6,7 %; en los Picos, hasta −15,7 % en el verano de 2024), según `salidas/backtest.parquet`;
>   - el corto plazo es peor que el largo para detectar rojos;
>   - los intervalos p10-p90 cubren de media el 74,8 % (objetivo: 80 %);
>   - falla en los puentes de diciembre.
> - **Regulación (Picos):** 39 días rojos en 2023 y 48 en 2024, y 85 de esos 87 caen en días regulados. El umbral que mejor reproduce la regulación de los Lagos es 1,10× (F1 0,87). Para 2026 se prevén 40 rojos (27-72) y para 2027, 30 (24-62).
>
> Las secciones de resultados que siguen («Resultados», «SHAP recupera…», «Fiabilidad» y «Calibración») son las de la **prueba con el objetivo sintético** del 2026-10-15. Se conservan como registro de la validación de la cadena y **no describen Asturias**. La tabla «LightGBM frente a XGBoost» sí está regenerada con datos reales. La primera ejecución real, con 5 zonas y LightGBM, está en `notas/historico/resultados_reales.md`.

## Cómo se ejecuta

```bash
python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos      # salidas actuales: compara LightGBM y XGBoost (~15 min con 46 zonas)
python -X utf8 src/modelo/ejecutar.py --objetivo sintetico                     # prueba de la cadena con un objetivo inventado
python -X utf8 -m pytest -q src/modelo/tests                 # todo (~4 min: incluye la cadena completa con cada algoritmo)
python -X utf8 -m pytest -q src/modelo/tests -m "not lento"  # rápido (~30 s)
```

Semilla fija (42); LightGBM y XGBoost deterministas: dos ejecuciones dan el mismo resultado. `--algoritmo lightgbm|xgboost|ambos` (sin la opción se usa el de `config/modelo.yaml`, `lightgbm`; las salidas actuales salen de `ambos`, que eligió XGBoost). Al final, `ejecutar.py` comprueba el contrato de la web y se detiene si algo no cumple.

| Paso | Módulo | Salida |
|---|---|---|
| Objetivo real a partir del MITMA | `construir_objetivo.py` | `data/clean/objetivo_diario.parquet` |
| Objetivo sintético | `objetivo_sintetico.py` | `salidas/sintetico/*.parquet`, `salidas/sintetico_efectos_reales.json` |
| Variables sin fuga | `features.py` | (en memoria) |
| Día normal | `dia_normal.py` | `metricas.json → dia_normal` |
| Validación por bloques y experimentos | `backtest.py` | `salidas/backtest.parquet` |
| Métricas y fiabilidad | `metricas.py` | `salidas/metricas.json` |
| Modelos finales y predicción | `produccion.py` | — |
| SHAP y gráficas | `explicar.py` | `salidas/explicacion_factores.json`, `salidas/figuras/*.png` |
| Calibración con los Lagos | `calibracion.py` | `salidas/calibracion_lagos.json`, `figuras/calibracion_lagos.png` |
| JSON de la web | `web_salidas.py` | `predicciones`, `alternativas`, `regulacion`, `perfil` y `metricas.json` |
| Comparación de algoritmos (`--algoritmo ambos`) | `comparacion.py` | `salidas/comparacion_algoritmos.json` y la tabla de este documento |
| Contrato | `validar_salidas.py` | — |

## Qué predice

Para cada día y zona: **cuántos visitantes llegarán** (por defecto `llegadas_ocio`, configurable a `llegadas_total` o `pernoctaciones_no_residentes`) y **cuánto supone frente a un día normal**.

- **Variable objetivo:** `y = log((x + 1) / (normal + 1))`. Visitantes previstos = `(normal + 1)·exp(ŷ) − 1`. El +1 evita el logaritmo de cero en zonas pequeñas.
- **Día normal** (`dia_normal.py`): mediana por zona y día de la semana en 2024, sin julio ni agosto, sin festivos (nacional, de Asturias o local) y sin días con problemas del MITMA. Es la misma idea que el MITMA. Si se quieren usar los estadísticos oficiales del MITMA (descargados en `data/raw/mitma_estadisticos_dia_normal_2024/`), basta con poner `dia_normal.fuente: mitma` y dejar el fichero `zona_mitma_id, dia_semana, normal`.
- **Semáforo** (`config/semaforo.yaml`): verde por debajo de 1,5 veces el normal, ámbar de 1,5 a 2,0 y rojo a partir de 2,0. Se puede ajustar por zona. Gris = sin datos. El umbral lo hemos definido nosotros: **no es un dato oficial de capacidad**.

Como el normal es por día de la semana, «Fin de semana» casi no aparece como factor: un sábado de agosto se compara con un sábado normal.

## Dos modelos (LightGBM o XGBoost, uno global para todas las zonas)

| | Largo plazo (h ≥ 8) | Corto plazo (h = 1-7) |
|---|---|---|
| Para qué | Planificar meses o el año siguiente («¿hay que regular?») | Alerta de la semana (Inicio) |
| Filas | fecha × zona | fecha × zona × horizonte |
| Variables | calendario, eventos, partidos y zona | lo mismo + tiempo + interés en internet + horizonte |

Parámetros (`config/modelo.yaml`), con el mismo criterio en los dos algoritmos (pocos datos, evitar sobreajuste):
- **LightGBM** (por defecto): `num_leaves` 15, `min_data_in_leaf` 50, `feature_fraction` y `bagging` 0,8, `lambda_l2` 1 y `learning_rate` 0,05;
- **XGBoost** (alternativa): `XGBRegressor` con `tree_method="hist"`, `enable_categorical=True` (zona como `category`), `max_depth` 5, `min_child_weight` 50 (con pérdida cuadrática equivale a `min_data_in_leaf`), `subsample` y `colsample_bytree` 0,8, `reg_lambda` 1 y `learning_rate` 0,05;
- en los dos, las mismas variables, los mismos bloques, el mismo día normal y la misma semilla;
- *early stopping* con los últimos 365 días del entrenamiento como validación temporal (como mucho el 40 % del periodo; `config/modelo.yaml → dias_validacion_interna`; antes eran 90 días, y con 46 zonas el modelo paraba sin aprender los picos de agosto: `notas/ampliacion_zonas.md`) y reentrenamiento con todo el periodo con ese número de árboles;
- sin búsqueda de hiperparámetros.

### Variables (`features.py`)

- **Calendario:**
  - día de la semana, mes y día del año (seno y coseno), fin de semana;
  - festivo nacional, de Asturias y local del concejo (+ `festivo_local_parcial`);
  - festivo en Madrid y en Castilla y León;
  - puente y fin de semana largo (Asturias, Madrid y Castilla y León);
  - víspera de festivo (Asturias y Madrid), días hasta el próximo festivo y desde el último (tope 30);
  - Semana Santa (estricta y ampliada);
  - vacaciones escolares (Asturias, Madrid y Castilla y León);
  - acceso regulado a los Lagos.
- **Eventos:** número de eventos en el concejo e indicador por tipo (fiesta, festival, romería, deportivo, feria); partido en casa del Real Oviedo o del Sporting, y derbi. **Los cruceros quedan fuera**: solo hay previsiones de 2025-26.
- **Tiempo** (solo corto plazo; valle `tv_*` y, en la zona de Cangas de Onís, montaña de los Lagos `tm_*`): temperatura máxima, precipitación, horas de sol y viento máximo.
- **Interés en internet** (solo corto plazo): Wikipedia de la zona y de los Picos (media de log(1 + visitas) de los 7 días que terminan en d−h) y las 3 series fiables de Trends (última semana completa antes de d−h).
- **Zona** (categórica) y **horizonte**.
- 2027: el curso escolar desde septiembre y la regulación de los Lagos no están publicados. Se suponen iguales a los de 364 días antes (mismo día de la semana) y se marcan con `calendario_supuesto`.

### Sin fuga de información (regla 2)

Para predecir el día d con h días de antelación solo se usa lo que se conocía en d−h:

- **Tiempo, modo `estricto` (decisión del equipo, por defecto):** solo la previsión archivada emitida en d−h (`om_*_prev{h}`). Solo existe para h ≤ 3 y desde el 2024-01-22. Para h = 4-7, o antes de esa fecha, el tiempo es NaN y el modelo lo trata como desconocido. Nunca AEMET (observación) ni ERA5. **El efecto del tiempo se aprende solo con datos desde enero de 2024**: unos 17 meses de los 42 del periodo. Por eso sale con el signo correcto, pero infraestimado.
- **Modo `aproximado`:** solo para el experimento `tiempo_aproximado`. Rellena los huecos con la serie base de Historical Forecast (plazo ≈ 0, casi el tiempo observado), que no cumple la regla d−h. **Es una cota optimista**: indica cuánto podría aportar el tiempo con una previsión perfecta, no lo que se conseguirá en producción. En ningún modo se usa el tiempo del tramo de reanálisis (antes del 2022-11-09).
- **Wikipedia:** ventana que termina en d−h. Se usa la media del logaritmo, que aguanta picos sin necesitar el marcador de anomalía (ese marcador usa días futuros).
- **Trends:** semana completa (domingo-sábado) que termina antes de d−h.
- **Nunca valores pasados del propio objetivo:** el MITMA no se publica en tiempo real.
- **Prueba** `src/modelo/tests/test_antifuga.py` (73 casos). Corrompe en las fuentes todo lo publicado después de d−h y comprueba que ninguna variable cambia. Incluye un control: con el modo `aproximado`, la prueba sí detecta la fuga. También comprueba que la lista de variables no contiene AEMET, ERA5, cruceros ni el objetivo.

## Validación (`backtest.py`)

Validación por bloques temporales: se entrena con todo lo anterior a cada bloque, **desde el 2022-01-01** (decisión del equipo), y se evalúa en el bloque. Los bloques son 2023-S2 (verano de 2023), 2024-S1, 2024-S2 (verano de 2024) y 2025-S1 (bloque final).

- **Sin fuga en el nivel:** el día normal de cada bloque se recalcula con los 365 días anteriores. El normal de 2024 solo define el color.
- Los días `sin_dato_mitma` y `anomalia_mitma` no se entrenan ni se evalúan.
- **Líneas base:**
  - **B0**, día normal: cociente 1 siempre;
  - **B1**, mismo día de la semana del año anterior (364 días antes): solo como referencia, porque no se puede desplegar.
- **Métricas** por bloque, zona, mes y horizonte:
  - WAPE y MAE en visitantes;
  - semáforo: acierto de color, matriz de confusión y recall y precisión de los días rojos.
- **Experimentos de sensibilidad**, sobre los mismos bloques de prueba:
  - `desde_corte`: entrenamiento solo desde el corte del reanálisis (2022-11-09), la configuración anterior;
  - `solo_eventos_verificados`;
  - `tiempo_aproximado`.

### Resultados (objetivo sintético, LightGBM; los reales están en `README.md` → «Resultados»)

Experimento base (entrenamiento desde 2022-01-01), todos los bloques:

| Modelo | Método | WAPE | Acierto de color | Recall rojo | Precisión rojo |
|---|---|---|---|---|---|
| Corto (1-7 d) | **modelo** | **0,101** | **93,4 %** | 58 % | 86 % |
| | B0 día normal | 0,179 | 87,3 % | 0 % | — |
| | B1 año anterior | 0,173 | 88,4 % | 55 % | 54 % |
| Largo (8+ d) | **modelo** | **0,106** | **94,2 %** | 82 % | 80 % |
| | B0 / B1 | 0,179 / 0,173 | | 0 % / 55 % | |

Recall de los días rojos por bloque:

| Modelo | 2023-S2 | 2024-S1 | 2024-S2 | 2025-S1 |
|---|---|---|---|---|
| Largo plazo | 82 % | 91 % | 82 % | 83 % |
| Corto plazo | **37 %** | 82 % | 74 % | 68 % |

- El modelo gana a B0 en WAPE en todos los bloques; en el verano de 2024, 0,108 frente a 0,218.
- **El corto plazo detecta menos rojos que el largo** (58 % frente a 82 %), aunque con más precisión (86 % frente a 80 %). Falla sobre todo en el verano de 2023, cuando aún no había previsión archivada. Hay que vigilarlo con datos reales; si se repite, la web puede mostrar el color del largo plazo cuando sea más alto (decisión pendiente, ver abajo).

Experimentos (todos los bloques; WAPE · recall de rojos):

| Experimento | Largo plazo | Corto plazo | Lectura |
|---|---|---|---|
| **base** (desde 2022-01-01, estricto) | **0,106 · 82 %** | **0,101 · 58 %** | Configuración elegida. |
| `desde_corte` (desde 2022-11-09) | 0,124 · 52 % | 0,117 · 47 % | Sin 2022, el primer bloque no ve ningún verano (recall del 13 % en 2023-S2). Incluir 2022 no introduce fuga: en modo estricto el tiempo de ese tramo no se usa. |
| `solo_eventos_verificados` | 0,110 · 70 % | 0,103 · 60 % | Quitar los eventos `probable` empeora el largo plazo: aportan información. |
| `tiempo_aproximado` | — | 0,088 · 62 % | Cota optimista (tiempo casi observado). No cumple la regla d−h. |

- **Por horizonte:** el WAPE del corto plazo sube de 0,098 (h = 1) a 0,103 (h = 5-7), cuando deja de haber previsión archivada; el recall de rojos baja del 61 % al 56-57 %.
- **B1 falla en Semana Santa:** cambia de fecha cada año, y en 2024-S1 y 2025-S1 su recall de los días rojos es 0.

### SHAP recupera los efectos del generador (objetivo sintético)

`salidas/sintetico_recuperacion_factores.json` y `figuras/sintetico_recuperacion_factores.png`. Se compara, fila a fila y fuera de muestra, la contribución verdadera de cada factor con la suma de SHAP de su grupo:

- **Signo:** recuperado en **8 de 8** factores en el corto plazo (correlación > 0,3; de 0,36 en «Vacaciones» a 0,99 en «Evento»). En el largo plazo, 6 de 8: los dos que faltan son los de tiempo, que ese modelo no tiene por diseño.
- **Orden de importancia:** «Época del año» y «Vacaciones escolares» están muy correlacionadas (el verano escolar es la temporada alta) y SHAP reparte el efecto entre las dos. Juntas, su suma SHAP correlaciona 0,91 con la verdadera. Con las dos fusionadas, el orden coincide (ρ de Spearman) con un **1,0** en largo plazo y un **0,93** en corto plazo (jul-2024 a jun-2025).
- **Factores sin efecto real** (interés en internet, regulación de los Lagos): SHAP pequeño (desviación ≤ 0,034 en escala log).
- **El tiempo** sale con el signo correcto, pero **infraestimado** (desviación 0,054 frente a 0,123 en montaña). El modelo solo ve previsiones, y solo desde enero de 2024.
- `shap.TreeExplainer` y el TreeSHAP nativo de LightGBM (el que usa el código) coinciden exactamente (diferencia máxima 0). Con XGBoost se usa su TreeSHAP nativo (`pred_contribs`), que también coincide con `shap.TreeExplainer`, incluida la zona categórica.

En la web, el efecto de cada factor se da en % respecto al **día medio del modelo**, no respecto al normal.

### Fiabilidad (`metricas.py`; cifras del objetivo sintético; con datos reales la cobertura media es del 74,8 %)

- **Intervalo p10-p90:** conformal simple con los errores de validación (escala log) por zona y horizonte. La cobertura, medida dejando fuera cada bloque, es del **79-80 %** (objetivo: 80 %).
- `incierto = True` si p10 y p90 caen en colores distintos.
- La nota legible está en `metricas.json → fiabilidad[].nota`, por ejemplo: «Acierta el color en el 90 % de los días; detecta 8 de cada 10 días rojos» (Cangas, h = 1, sintético).

### Calibración con la regulación de los Lagos (objetivo sintético; comprobada después con datos reales)

`salidas/calibracion_lagos.json` y `figuras/calibracion_lagos.png`. Se busca el umbral cuyo «día en alerta» coincide mejor (F1) con los días regulados del BOE en 2023-2024. Hay dos escalas:

- **Relativa** (la del semáforo, frente al normal de ese día de la semana): mejor umbral 0,85× con el observado (F1 0,70) y 0,90× con el previsto (F1 0,80).
- **Absoluta** (frente al día normal medio de la zona): 1,0× con el observado (F1 0,74) y 0,80× con el previsto (F1 0,78).

> **Comprobado con datos reales (2026-10-16, `salidas/calibracion_lagos.json`, `notas/historico/resultados_reales.md` §7).**
> - Mejor umbral relativo: 1,10× con el observado (F1 0,867) y 1,05× con el previsto fuera de muestra (F1 0,930; con 5 zonas era 0,911).
> - Con el umbral rojo (2,0×), 85 de los 87 días rojos de 2023-2024 están regulados, pero solo se cubre el 24 % de los 352 días regulados con dato.
>
> La hipótesis de abajo (escrita con el objetivo sintético) se confirma en lo esencial. Las cifras sintéticas citadas en ella no valen.

Hipótesis: la regulación actual (unos 180 días al año, todos los fines de semana de temporada y el verano) equivaldría a **cualquier día por encima de lo normal**, no solo a los de presión extrema. Con el umbral rojo (2,0×), el 93 % de los días rojos ya estarían regulados, pero solo se cubriría el 22 % de los días regulados. **No se cambia el valor por defecto.** La regulación es un calendario planificado, no una medida de saturación.

## LightGBM frente a XGBoost

Con `--algoritmo ambos`, la validación por bloques del experimento base se hace con los dos algoritmos y se elige uno con la regla de abajo. Los experimentos de sensibilidad, los modelos finales, SHAP, el semáforo, los intervalos, la calibración con los Lagos y todos los JSON de la web se generan con el **ganador**. `metricas.json → algoritmo` dice cuál fue. El contrato de la web no cambia.

### Regla de elección (versión 2, fijada el 2026-10-15, antes de ver datos reales)

Gana el de mayor recall de días rojos en verano (con la agregación de abajo) siempre que su precisión de días rojos en verano no sea más de 5 puntos inferior a la del otro; si lo es, decide el F1 de días rojos en verano. Si la diferencia en el criterio decisivo es menor de 3 puntos, el de menor WAPE medio; si también es menor de 1 punto, LightGBM.

Agregación (la fijada con la versión 1, que se mantiene):
- recall de verano = media, entre el modelo de corto plazo (todas las filas de h = 1-7) y el de largo plazo, del recall de días rojos agregado sobre los dos bloques de verano (2023-S2 y 2024-S2);
- la precisión y el F1 de verano se agregan igual: la métrica de cada modelo sobre los dos bloques de verano y, después, la media entre corto y largo. Si un modelo no pinta ningún rojo, su precisión y su F1 cuentan como 0;
- WAPE medio = media del WAPE de los 4 bloques × 2 modelos.

La versión 1 («gana el de mayor recall de días rojos en verano; si la diferencia es menor de 3 puntos, el de menor WAPE medio; si también es menor de 1 punto, LightGBM») se sustituyó antes de ver datos reales porque premiaba al modelo que pintara más rojos, aunque fueran falsas alarmas.

Está implementada en `src/modelo/comparacion.py` y sus parámetros, en `config/modelo.yaml → seleccion_algoritmo`.

Pruebas (`src/modelo/tests/test_algoritmos.py`), con los dos algoritmos:
- anti-fuga de punta a punta: la predicción y el SHAP de (d, h) no cambian al corromper lo publicado después de d−h;
- SHAP suma la predicción;
- la cadena completa con el objetivo sintético genera JSON que cumplen el contrato.

La prueba anti-fuga de variables (`test_antifuga.py`) no depende del algoritmo.

### Resultado

La tabla siguiente la regenera cada ejecución con `--algoritmo ambos`.

<!-- comparacion_algoritmos:inicio (generado por src/modelo/comparacion.py) -->
Objetivo: `llegadas_ocio`. Experimento base. Generado el 2026-10-16 10:22.

| Criterio de la regla | LightGBM | XGBoost |
|---|---|---|
| Recall de días rojos en verano (%) | 53,9 | 64,2 |
| Precisión de días rojos en verano (%) | 88,6 | 87,2 |
| F1 de días rojos en verano (%) | 66,7 | 73,6 |
| WAPE medio (%) | 10,1 | 9,8 |
| Tiempo total de entrenamiento (s) | 23,0 | 145,7 |

**Resultado de la regla:** xgboost (paso 1: la precisión del de mayor recall (xgboost) no es más de 5 puntos inferior (1.4): decide el recall; recall de días rojos en verano 10.3 puntos mayor (≥ 3)).

Detalle por bloque y horizonte (WAPE, acierto de color, recall y precisión de rojos en %; MAE en visitantes; tiempo = entrenamiento del modelo que produce ese horizonte, en segundos). Corto plazo: media de h = 1-7.

| Bloque | Horizonte | Algoritmo | WAPE | MAE | Acierto color | Recall rojo | Precisión rojo | Rojos obs. | Tiempo (s) |
|---|---|---|---|---|---|---|---|---|---|
| 2023-S2 (verano 2023) | 1-7 (corto) | lightgbm | 10,0 | 1197 | 91,2 | 64,1 | 84,8 | 521 | 1,96 |
| 2023-S2 (verano 2023) | 1-7 (corto) | xgboost | 9,4 | 1127 | 91,4 | 70,0 | 83,0 | 521 | 58,69 |
| 2023-S2 (verano 2023) | 8+ (largo) | lightgbm | 9,8 | 1176 | 91,6 | 72,4 | 80,9 | 521 | 0,42 |
| 2023-S2 (verano 2023) | 8+ (largo) | xgboost | 9,4 | 1132 | 91,7 | 74,3 | 79,0 | 521 | 3,52 |
| 2024-S1 | 1-7 (corto) | lightgbm | 9,1 | 1009 | 98,1 | 57,5 | 62,0 | 36 | 10,28 |
| 2024-S1 | 1-7 (corto) | xgboost | 9,2 | 1016 | 98,1 | 49,2 | 70,5 | 36 | 47,08 |
| 2024-S1 | 8+ (largo) | lightgbm | 9,2 | 1023 | 98,3 | 50,0 | 69,2 | 36 | 1,17 |
| 2024-S1 | 8+ (largo) | xgboost | 9,3 | 1034 | 98,2 | 22,2 | 88,9 | 36 | 4,00 |
| 2024-S2 (verano 2024) | 1-7 (corto) | lightgbm | 12,0 | 1514 | 88,7 | 33,2 | 99,1 | 611 | 1,77 |
| 2024-S2 (verano 2024) | 1-7 (corto) | xgboost | 11,3 | 1433 | 89,8 | 45,4 | 98,5 | 611 | 10,34 |
| 2024-S2 (verano 2024) | 8+ (largo) | lightgbm | 11,8 | 1489 | 90,0 | 50,2 | 97,2 | 611 | 0,30 |
| 2024-S2 (verano 2024) | 8+ (largo) | xgboost | 10,2 | 1292 | 91,7 | 69,4 | 92,2 | 611 | 5,00 |
| 2025-S1 (bloque final) | 1-7 (corto) | lightgbm | 8,9 | 1036 | 96,7 | 42,9 | 72,1 | 68 | 6,24 |
| 2025-S1 (bloque final) | 1-7 (corto) | xgboost | 8,9 | 1045 | 96,7 | 23,9 | 95,0 | 68 | 12,06 |
| 2025-S1 (bloque final) | 8+ (largo) | lightgbm | 10,5 | 1224 | 96,5 | 35,3 | 72,7 | 68 | 0,90 |
| 2025-S1 (bloque final) | 8+ (largo) | xgboost | 10,8 | 1260 | 96,5 | 44,1 | 78,9 | 68 | 5,04 |

El detalle por cada horizonte (1, 2, … 7, 8+) está en `salidas/comparacion_algoritmos.json → tabla`.
<!-- comparacion_algoritmos:fin -->

## Predicciones para la web

- **Futuro de largo plazo:** 365 días desde el 2026-10-16 (`config/modelo.yaml → dias_futuro_demo`). Solo calendario y eventos: no necesita tiempo ni datos recientes del MITMA.
- **Futuro de corto plazo:** previsión de 7 días de Open-Meteo para las 9 zonas de `config/zonas_meteo.csv`, incluida la montaña de los Lagos (`lagos_enol`). La descarga `python -X utf8 src/modelo/descargar_prevision.py`, con el mismo esquema que `openmeteo_prevision_ejemplo`:
  - en bruto: `data/prevision/AAAA-MM-DD/<zona>.json`;
  - limpia: `data/clean/openmeteo_prevision.parquet`.

  La de la demo se emitió el 2026-10-16. Para d = emisión + h, con h = 1-3, se coloca como `_prev{h}` del valle y de la montaña de cada zona; para h = 4-7 el tiempo queda vacío, como en el entrenamiento. Si el fichero no existe, se usa el ejemplo (solo `covadonga`, aplicado al valle de la zona principal).
- **En producción:**
  1. cada mañana, `descargar_prevision.py` (previsión de cada `zona_meteo` y `zona_meteo_montana`);
  2. la previsión para d emitida hoy se coloca en `<var>_prev{h}` con h = d − hoy (h ≤ 3);
  3. la Wikipedia se toma hasta ayer (ventana que termina en a−1, más conservadora que en el entrenamiento);
  4. se llama a `produccion.predecir` con el modelo `corto`.
- **Histórico de demo:** predicciones fuera de muestra del puente de diciembre y de agosto de 2024, con el valor observado y los factores.
- **Regulación 2026-2027:** modelo de largo plazo, con el intervalo de días rojos `[días con p10 rojo, días con p90 rojo]`.

## Limitaciones

- **Sin extranjeros:** el MITMA solo cuenta residentes en España. Picos tiene un turismo internacional apreciable que no se ve.
- **Datos diarios hasta junio de 2025:** el modelo no puede aprender cambios posteriores (la nueva regulación, el auge del turismo, etc.). En 2026-2027 asume que el comportamiento es como el de 2022-2025.
- **El umbral es nuestro:** 1,5× y 2,0× el normal no salen de un dato oficial de capacidad. La calibración con los Lagos orienta, pero la regulación es un calendario planificado, no una medida de saturación. Además, el MITMA mide llegadas al concejo de Cangas de Onís, no accesos a los Lagos.
- **Cruceros fuera:** solo hay previsiones de 2025-26; en 2022-2024 serían ceros por falta de dato.
- **Tiempo en el entrenamiento:** solo hay previsión archivada desde 2024-01-22 y hasta 3 días: el efecto del tiempo se aprende solo con datos desde enero de 2024. Antes de esa fecha, o a 4-7 días, el modelo corto no usa tiempo. Su efecto está infraestimado. El modo aproximado es solo una cota optimista.
- **El corto plazo detecta menos rojos que el largo** en todos los horizontes: recall del 57,0 % a h = 1 y del 52,8 % a h = 7, frente al 68,7 % del largo, con un WAPE parecido (9,4-10,0 % frente a 9,9 %; `metricas.json → tablas.horizonte`). También detecta menos rojos que B1 (70,2 %), aunque con más precisión (88,6 % frente a 74,1 %).
- **Sesgo a la baja:** se queda corto en todos los bloques, entre −1,2 % y −6,7 % del volumen total, y en los Picos hasta −15,7 % en el verano de 2024 (`salidas/backtest.parquet`, XGBoost, experimento base). Fuera de muestra, el largo plazo pintó 71 rojos en los Picos frente a 87 observados (acertó 66), así que la previsión de rojos para 2026-2027 probablemente se queda corta. No hay ninguna variable de tendencia, y las llegadas crecen de un año a otro.
- **Bloque final (2025-S1):** el largo plazo no gana al día normal en WAPE (10,8 % frente a 9,2 %); el corto sí, por poco (8,9 %).
- **Puentes de diciembre:** el modelo los infraestima mucho (2023 y 2024).
- **Intervalos p10-p90:** cobertura media del 74,8 % en las 368 combinaciones de zona y horizonte (mínima 60,5 %), por debajo del 80 %; en los Picos, el 76,9 %.
- **«Interés en internet»** es, con «Zona», el factor que más pesa en el corto plazo (`salidas/explicacion_factores.json`) y, con 5 zonas, mostró una tendencia temporal sospechosa (efecto medio de +7 % en 2023 y −7 % en 2025; `notas/historico/resultados_reales.md` §3).
- **17 de las 46 zonas** (entre ellas Gijón, Oviedo, Avilés, Siero y Mieres) no tuvieron ningún día rojo observado en 2023 ni en 2024 con los umbrales actuales (`salidas/regulacion.json`): en las zonas urbanas el semáforo casi siempre está en verde.
- **2027:** el curso escolar desde septiembre y la regulación de los Lagos son supuestos. Los partidos de 2026-27 tienen fechas de jornada sin confirmar.
- **Los factores son asociaciones, no causas.** SHAP reparte el efecto entre variables correlacionadas («Época del año» frente a «Vacaciones escolares»).
- **El día normal de 2024** es una referencia propia. Si existen los estadísticos oficiales del MITMA, conviene usarlos.

## Cómo regenerar el objetivo real

El objetivo de las 46 zonas lo generó el equipo de demanda (commit `80828e1`). Para rehacerlo hacen falta los ficheros mensuales del MITMA, que no están en el repositorio (`notas/fuentes/mitma/descarga_mitma.md`):

1. `data/raw/zonas_mitma_asturias.csv` (columna `id_zona_mitma`) y los ficheros mensuales `data/raw/mitma_viajes/AAAA-MM.csv` y `data/raw/mitma_pernoctaciones/AAAA-MM.csv`, del 2022-01 al 2025-06, en el formato del MITMA o de spanishoddata (`notas/contrato_objetivo.md`).
2. `python -X utf8 src/modelo/construir_objetivo.py --mapeo config/mapeo_zonas.csv`: genera `data/clean/objetivo_diario.parquet` y comprueba que los IDs existen.
3. `python -X utf8 src/modelo/construir_llegadas_por_hora.py`: genera `data/clean/llegadas_por_hora.parquet`.
4. `python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos`: reescribe todas las salidas con `sintetico=false`.

No hay que tocar el código. Si una zona usa otro punto meteorológico, basta con que exista en `config/zonas_meteo.csv` y en `openmeteo_diario`. `objetivo_sintetico.PARAMS` solo se usa en modo sintético.

## Decisiones del equipo

Tomadas el 2026-10-15 (antes de ver datos reales):

1. **Inicio del entrenamiento: 2022-01-01, en modo estricto.** No se usa el tiempo del tramo de reanálisis: en estricto solo entra la previsión archivada, desde 2024-01-22. La configuración anterior queda como el experimento `desde_corte`.
2. **Tiempo: modo estricto.** El aproximado es una cota optimista, y el efecto del tiempo se aprende solo con datos desde enero de 2024.
3. **Perfil:** el reparto por residencia se calcula sobre las llegadas de ocio, y además sobre `llegadas_total` como campo aparte (`pct_total_*` en `perfil.json`).
4. **Previsión:** previsión de 7 días de Open-Meteo en todas las zonas, incluida la montaña (`descargar_prevision.py`).
5. **Algoritmo:** regla de elección, versión 2 (sección «LightGBM frente a XGBoost»). Al llegar los datos reales: `--objetivo real --algoritmo ambos`. El resultado sintético no cuenta.
6. **Calibración con los Lagos:** los umbrales del semáforo se mantienen en 1,5× y 2,0×. Con datos reales, la regulación se parece a un umbral de 1,10× (`notas/historico/resultados_reales.md` §7).

Pendiente:
- Qué color enseña la web cuando el corto y el largo plazo no coinciden. Hoy, el corto cuando existe. Con datos reales, el corto detecta menos rojos que el largo en todos los horizontes (sección «Limitaciones»), lo que apoya enseñar el más alto de los dos. **Sin aplicar:** decisión del equipo.
