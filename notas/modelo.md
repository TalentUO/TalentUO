# Modelo de presión turística: decisiones, validación y cómo conectar los datos reales

Fecha: 2026-10-15. Rama `modelo`. Código en `src/modelo/`, configuración en `config/modelo.yaml`, `config/semaforo.yaml`, `config/factores.yaml` y `config/mitma_calidad.yaml`. Contratos: `notas/contrato_objetivo.md` (entrada de la parte A) y `notas/contrato_web.md` (salida para la web).

> **⚠ Todos los resultados de este documento son SINTÉTICOS.** Hoy el objetivo es inventado (`src/modelo/objetivo_sintetico.py`), porque el MITMA aún se está descargando. Las cifras demuestran que la cadena funciona y que el modelo recupera efectos conocidos. **No dicen nada de Asturias.**

## Cómo se ejecuta

```bash
python -X utf8 src/modelo/ejecutar.py --objetivo sintetico   # ~35 s (hasta ~2 min con la máquina cargada)
python -X utf8 -m pytest -q src/modelo/tests                 # anti-fuga, constructor del objetivo y contrato web
```

Semilla fija (42) y LightGBM determinista: dos ejecuciones dan el mismo resultado. Al final, `ejecutar.py` comprueba el contrato de la web y se detiene si algo no cumple.

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
| Contrato | `validar_salidas.py` | — |

## Qué predice

Para cada día y zona: **cuántos visitantes llegarán** (por defecto `llegadas_ocio`, configurable a `llegadas_total` o `pernoctaciones_no_residentes`) y **cuánto supone frente a un día normal**.

- **Variable objetivo:** `y = log((x + 1) / (normal + 1))`. Visitantes previstos = `(normal + 1)·exp(ŷ) − 1`. El +1 evita el logaritmo de cero en zonas pequeñas.
- **Día normal** (`dia_normal.py`): mediana por zona y día de la semana en 2024, sin julio ni agosto, sin festivos (nacional, de Asturias o local) y sin días con problemas del MITMA. Es la misma idea que el MITMA. Si A encuentra los estadísticos oficiales, basta con poner `dia_normal.fuente: mitma` y dejar el fichero `zona_mitma_id, dia_semana, normal`.
- **Semáforo** (`config/semaforo.yaml`): verde por debajo de 1,5 veces el normal, ámbar de 1,5 a 2,0 y rojo a partir de 2,0. Se puede ajustar por zona. Gris = sin datos. El umbral lo hemos definido nosotros: **no es un dato oficial de capacidad**.

Como el normal es por día de la semana, «Fin de semana» casi no aparece como factor: un sábado de agosto se compara con un sábado normal.

## Dos modelos (LightGBM, uno global para todas las zonas)

| | Largo plazo (h ≥ 8) | Corto plazo (h = 1-7) |
|---|---|---|
| Para qué | Planificar meses o el año siguiente («¿hay que regular?») | Alerta de la semana (Inicio) |
| Filas | fecha × zona | fecha × zona × horizonte |
| Variables | calendario, eventos, partidos y zona | lo mismo + tiempo + interés en internet + horizonte |

Parámetros (`config/modelo.yaml`):
- `num_leaves` 15, `min_data_in_leaf` 50, `feature_fraction` y `bagging` 0,8, `lambda_l2` 1 y `learning_rate` 0,05;
- *early stopping* con los últimos 90 días del entrenamiento como validación temporal y reentrenamiento con todo el periodo con ese número de árboles;
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

- **Tiempo, modo `estricto` (por defecto):** solo la previsión archivada emitida en d−h (`om_*_prev{h}`). Solo existe para h ≤ 3 y desde el 2024-01-22. Para h = 4-7, o antes de esa fecha, el tiempo es NaN y el modelo lo trata como desconocido. Nunca AEMET (observación) ni ERA5. La serie base de Historical Forecast (plazo ≈ 0) no cumple la regla d−h, así que solo se usa en el experimento `tiempo_aproximado`.
- **Wikipedia:** ventana que termina en d−h. Se usa la media del logaritmo, que aguanta picos sin necesitar el marcador de anomalía (ese marcador usa días futuros).
- **Trends:** semana completa (domingo-sábado) que termina antes de d−h.
- **Nunca valores pasados del propio objetivo:** el MITMA no se publica en tiempo real.
- **Prueba** `src/modelo/tests/test_antifuga.py` (73 casos). Corrompe en las fuentes todo lo publicado después de d−h y comprueba que ninguna variable cambia. Incluye un control: con el modo `aproximado`, la prueba sí detecta la fuga. También comprueba que la lista de variables no contiene AEMET, ERA5, cruceros ni el objetivo.

## Validación (`backtest.py`)

Validación por bloques temporales: se entrena con todo lo anterior a cada bloque y se evalúa en el bloque. Los bloques son 2023-S2 (verano de 2023), 2024-S1, 2024-S2 (verano de 2024) y 2025-S1 (bloque final).

- **Sin fuga en el nivel:** el día normal de cada bloque se recalcula con los 365 días anteriores. El normal de 2024 solo define el color.
- Los días `sin_dato_mitma` y `anomalia_mitma` no se entrenan ni se evalúan.
- **Líneas base:**
  - **B0**, día normal: cociente 1 siempre;
  - **B1**, mismo día de la semana del año anterior (364 días antes): solo como referencia, porque no se puede desplegar.
- **Métricas** por bloque, zona, mes y horizonte:
  - WAPE y MAE en visitantes;
  - semáforo: acierto de color, matriz de confusión y recall y precisión de los días rojos.
- **Experimentos de sensibilidad**, sobre los mismos bloques de prueba:
  - `con_2022`: entrenamiento desde el 2022-01-01;
  - `solo_eventos_verificados`;
  - `tiempo_aproximado`.

### Resultados (SINTÉTICOS)

Experimento base, todos los bloques:

| Modelo | Método | WAPE | Acierto de color | Recall rojo | Precisión rojo |
|---|---|---|---|---|---|
| Corto (1-7 d) | **modelo** | **0,117** | **91,6 %** | 47 % | 83 % |
| | B0 día normal | 0,179 | 87,3 % | 0 % | — |
| | B1 año anterior | 0,173 | 88,4 % | 55 % | 54 % |
| Largo (8+ d) | **modelo** | **0,124** | **91,4 %** | 52 % | 79 % |
| | B0 / B1 | 0,179 / 0,173 | | 0 % / 55 % | |

Por bloque (modelo de largo plazo, recall de los días rojos): 2023-S2, **13 %**; 2024-S1, 100 % (11 días); 2024-S2, 82 %; 2025-S1, 72 %. El modelo gana a B0 en WAPE en todos los bloques; en el verano de 2024, 0,112 frente a 0,218.

Experimentos (modelo de largo plazo, todos los bloques):

| Experimento | WAPE | Recall rojo | Lectura |
|---|---|---|---|
| base (desde el corte, 2022-11-09) | 0,124 | 52 % | El primer bloque se entrena **sin ningún verano** y no detecta el verano de 2023 (13 %). |
| `con_2022` (desde 2022-01-01) | **0,106** | **82 %** | Con el verano de 2022, el bloque de 2023 pasa al 82 %. En modo estricto, el tramo de reanálisis no entra como variable de tiempo, así que esto **no introduce fuga**. |
| `solo_eventos_verificados` | 0,125 | 51 % | Prácticamente igual: los eventos `probable` no meten ruido apreciable. |
| `tiempo_aproximado` (corto plazo) | 0,102 (frente a 0,117) | 52 % | La serie base mejora porque es casi el tiempo observado. Es optimista y no cumple la regla d−h. |

- **Por horizonte:** el WAPE del corto plazo sube de 0,115 (h = 1) a 0,118 (h = 4-7), cuando deja de haber previsión archivada.
- **B1 falla en Semana Santa:** cambia de fecha cada año, y en 2024-S1 y 2025-S1 su recall de los días rojos es 0.

### SHAP recupera los efectos del generador (SINTÉTICO)

`salidas/sintetico_recuperacion_factores.json` y `figuras/sintetico_recuperacion_factores.png`. Se compara, fila a fila y fuera de muestra, la contribución verdadera de cada factor con la suma de SHAP de su grupo:

- **Signo:** recuperado en **8 de 8** factores en el corto plazo (correlación > 0,3; de 0,36 en «Vacaciones» a 0,98 en «Evento»). En el largo plazo, 6 de 8: los dos que faltan son los de tiempo, que ese modelo no tiene por diseño.
- **Orden de importancia:** «Época del año» y «Vacaciones escolares» están muy correlacionadas (el verano escolar es la temporada alta) y SHAP reparte el efecto entre las dos. Juntas, su suma SHAP correlaciona 0,91 con la verdadera. Con las dos fusionadas, el orden coincide (ρ de Spearman) con un **1,0** en largo plazo y un **0,82** en corto plazo (jul-2024 a jun-2025).
- **Factores sin efecto real** (interés en internet, regulación de los Lagos): SHAP pequeño (desviación ≤ 0,03 en escala log).
- **El tiempo** sale con el signo correcto, pero **infraestimado** (desviación 0,05 frente a 0,12 en montaña). El modelo solo ve previsiones, y solo desde 2024-01-22.
- `shap.TreeExplainer` y el TreeSHAP nativo de LightGBM (el que usa el código) coinciden exactamente (diferencia máxima 0).

En la web, el efecto de cada factor se da en % respecto al **día medio del modelo**, no respecto al normal.

### Fiabilidad (`metricas.py`)

- **Intervalo p10-p90:** conformal simple con los errores de validación (escala log) por zona y horizonte. La cobertura, medida dejando fuera cada bloque, es del **79 %** (objetivo: 80 %).
- `incierto = True` si p10 y p90 caen en colores distintos.
- La nota legible está en `metricas.json → fiabilidad[].nota`, por ejemplo: «Acierta el color en el 86 % de los días; detecta 5 de cada 10 días rojos» (Cangas, h = 1, sintético, base). Con `con_2022`, esa nota mejoraría bastante.

### Calibración con la regulación de los Lagos (SINTÉTICA)

`salidas/calibracion_lagos.json` y `figuras/calibracion_lagos.png`. Se busca el umbral cuyo «día en alerta» coincide mejor (F1) con los días regulados del BOE en 2023-2024. Hay dos escalas:

- **Relativa** (la del semáforo, frente al normal de ese día de la semana): mejor umbral 0,85× con el observado (F1 0,70) y 0,95× con el previsto (F1 0,80).
- **Absoluta** (frente al día normal medio de la zona): 1,0× con el observado (F1 0,74) y 0,85× con el previsto.

Lectura para la presentación, que habrá que repetir con datos reales: la regulación actual (unos 180 días al año, todos los fines de semana de temporada y el verano) equivale a **cualquier día por encima de lo normal**, no solo a los de presión extrema. Con el umbral rojo (2,0×), el 93 % de los días rojos ya están regulados, pero solo se cubre el 22 % de los días regulados.

Dicho de otro modo: el semáforo marca menos días que la regulación, pero los que marca ya caen dentro de ella. **No se cambia el valor por defecto.** La regulación es un calendario planificado, no una medida de saturación.

## Predicciones para la web

- **Futuro de largo plazo:** 60 días desde el 2026-10-16. Solo calendario y eventos: no necesita tiempo ni datos recientes del MITMA.
- **Futuro de corto plazo:** `openmeteo_prevision_ejemplo.parquet` (emitida el 2026-10-15, punto `covadonga`) se coloca como `_prev{h}` del valle de la zona principal para h = 1-3. Covadonga está en el concejo de Cangas de Onís, así que se usa como aproximación del valle. La montaña y el resto de zonas quedan sin tiempo.
- **En producción:**
  1. cada día se descarga la previsión de Open-Meteo de cada `zona_meteo` y `zona_meteo_montana`;
  2. la previsión para d emitida hoy se coloca en `<var>_prev{h}` con h = d − hoy (h ≤ 3);
  3. la Wikipedia se toma hasta ayer (ventana que termina en a−1, más conservadora que en el entrenamiento);
  4. se llama a `produccion.predecir` con el modelo `corto`.
- **Histórico de demo:** predicciones fuera de muestra del puente de diciembre y de agosto de 2024, con el valor observado y los factores.
- **Regulación 2026-2027:** modelo de largo plazo, con el intervalo de días rojos `[días con p10 rojo, días con p90 rojo]`.

## Limitaciones

- **Sin extranjeros:** el MITMA solo cuenta residentes en España. Picos tiene un turismo internacional apreciable que no se ve.
- **Datos diarios hasta junio de 2025:** el modelo no puede aprender cambios posteriores (la nueva regulación, el auge del turismo, etc.). En 2026-2027 asume que el comportamiento es como el de 2022-2025.
- **El umbral es nuestro:** 1,5× y 2,0× el normal no salen de un dato oficial de capacidad. La calibración con los Lagos orienta, pero la regulación es un calendario planificado, no una medida de saturación.
- **Cruceros fuera:** solo hay previsiones de 2025-26; en 2022-2024 serían ceros por falta de dato.
- **Tiempo en el entrenamiento:** solo hay previsión archivada desde 2024-01-22 y hasta 3 días. Antes de esa fecha, o a 4-7 días, el modelo corto no usa tiempo. Su efecto está infraestimado.
- **2027:** el curso escolar desde septiembre y la regulación de los Lagos son supuestos. Los partidos de 2026-27 tienen fechas de jornada sin confirmar.
- **Los factores son asociaciones, no causas.** SHAP reparte el efecto entre variables correlacionadas («Época del año» frente a «Vacaciones escolares»).
- **El día normal de 2024** es una referencia propia. Si existen los estadísticos oficiales del MITMA, conviene usarlos.

## Cómo conectar los datos reales (pasos exactos)

1. A deja `data/raw/zonas_mitma_asturias.csv` (`zona_mitma_id`, `nombre`) y los ficheros mensuales `data/raw/mitma_viajes/AAAA-MM.csv` y `data/raw/mitma_pernoctaciones/AAAA-MM.csv`, del 2022-01 al 2025-06, en el formato del MITMA o de spanishoddata (`notas/contrato_objetivo.md`).
2. Rellenar `zona_mitma_id` en `config/mapeo_zonas.csv`, una fila por zona del proyecto. Si A separa Covadonga y los Lagos en otra zona MITMA, hay que añadir una fila; la zona principal es la del concejo INE 33012.
3. `python -X utf8 src/modelo/construir_objetivo.py`: genera `data/clean/objetivo_diario.parquet` y comprueba que los IDs existen.
4. `python -X utf8 src/modelo/ejecutar.py --objetivo real`: reescribe todas las salidas con `sintetico=false`.
5. Revisar en `notas/modelo.md` y en el guion las cifras marcadas como SINTÉTICAS y sustituirlas por las reales (`salidas/resumen_ejecucion.json` y `metricas.json`).

No hay que tocar el código. Si las zonas reales tienen otros puntos meteorológicos, basta con que existan en `config/zonas_meteo.csv` y en `openmeteo_diario`. `objetivo_sintetico.PARAMS` solo se usa en modo sintético.

## Decisiones pendientes del equipo

1. **Inicio del entrenamiento** (`inicio_entrenamiento` en `config/modelo.yaml`). Hoy está en `corte`, como se pidió. Recomiendo `"2022-01-01"`, por dos razones: en modo estricto no se usa el tiempo del tramo de reanálisis, y sin 2022 el primer bloque no ve ningún verano (recall de días rojos del 13 % frente al 82 %, sintético). Cambia una línea.
2. **Modo del tiempo:** el `estricto` cumple la regla d−h; el `aproximado` gana unos 1,5 puntos de WAPE, pero es optimista. Propongo mantener el estricto.
3. **Reparto por residencia sobre las llegadas de ocio** (y no sobre el total): ver `contrato_objetivo.md`.
4. **Umbrales del semáforo:** se mantienen en 1,5× y 2,0×. Hay que decidir si se enseña la calibración con los Lagos como argumento, una vez repetida con datos reales.
