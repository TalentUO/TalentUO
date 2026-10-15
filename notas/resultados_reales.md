# Resultados con datos reales (MITMA, 2022-01-01 → 2025-06-30)

Fecha: 2026-10-16. Rama `resultados-reales`. Objetivo `llegadas_ocio` de `data/clean/objetivo_diario.parquet` (parte A), sin construirlo de nuevo. Orden ejecutada (entorno `.venv` con las versiones de `requirements.txt`):

```bash
python -X utf8 src/limpieza_B/unir_B.py --mapeo config/mapeo_zonas.csv        # 8 745 filas, 5 zonas, comprobaciones superadas
python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos       # 124 s, contrato de la web superado
python -X utf8 -m pytest -q -m "not lento" src/modelo/tests                    # 92 pasan (73 de test_antifuga.py), 2 deseleccionadas
python -X utf8 scripts/tablas_resultados_reales.py > salidas/tablas_resultados_reales.md
```

Sin cambios de código en el modelo: `datos.py` ya lee el parquet entregado y solo pide `construir_objetivo.py` si no existe. Decisiones de diseño sin tocar: inicio 2022-01-01, tiempo estricto, día normal (mediana de 2024 sin julio, agosto ni festivos), umbrales ámbar 1,5 y rojo 2,0, regla de elección v2.

Todas las salidas de esta ejecución llevan `sintetico: false` (comprobado en los 9 JSON regenerados y en las 138 840 filas de `backtest.parquet`). Quedan dos ficheros de la ejecución sintética anterior que **no** se regeneran con el objetivo real y llevan `sintetico: true`: `salidas/sintetico_efectos_reales.json` y `salidas/sintetico_recuperacion_factores.json` (ver paso 6).

**Nota sobre B0 y B1.**
- B0 = día normal del bloque, es decir, cociente 1 siempre. Por construcción nunca pinta un rojo y no capta la estacionalidad, así que es una referencia fácil de batir en las zonas turísticas.
- B1 = mismo día de la semana de 364 días antes. Usa el dato del MITMA, que no se publica en tiempo real, así que no se puede desplegar. Es la referencia exigente.

## 1. Algoritmo elegido

Fuente: `salidas/comparacion_algoritmos.json` (y la tabla regenerada en `notas/modelo.md`).

| Criterio de la regla | LightGBM | XGBoost |
|---|---|---|
| Recall de días rojos en verano | 82,7 % | 81,3 % |
| Precisión de días rojos en verano | 95,5 % | 96,0 % |
| F1 de días rojos en verano | 88,7 % | 88,0 % |
| WAPE medio | 9,04 % | 8,94 % |
| Tiempo total de entrenamiento | 5,4 s | 10,3 s |

**Gana LightGBM en el paso 3 de la regla.**
1. El de mayor recall (LightGBM) pierde solo 0,5 puntos de precisión, menos de 5, así que decide el recall.
2. La diferencia de recall es de 1,5 puntos, menos de 3, así que se mira el WAPE.
3. La diferencia de WAPE es de 0,1 puntos, menos de 1, así que gana LightGBM por desempate.

En la práctica, los dos algoritmos empatan. He recalculado las cuatro cifras desde `salidas/backtest.parquet` y coinciden.

## 2. Error frente al día normal (B0) y frente al año anterior (B1)

Fuente: `salidas/metricas.json → tablas.global` y `tablas.bloque`. Todos los bloques y las 5 zonas.

| Modelo | WAPE modelo | WAPE B0 | WAPE B1 | Acierto de color (modelo / B0 / B1) | Recall rojo (modelo / B1) | Precisión rojo (modelo / B1) |
|---|---|---|---|---|---|---|
| Corto (h = 1-7) | **8,8 %** | 13,2 % | 9,9 % | 93,3 / 82,4 / 91,3 % | 77,7 / 79,3 % | **94,1** / 84,3 % |
| Largo (8+ días) | **9,3 %** | 13,2 % | 9,9 % | 93,5 / 82,4 / 91,3 % | 79,9 / 79,3 % | **96,0** / 84,3 % |

Por bloque. Fuente: `salidas/tablas_resultados_reales.md`, generado desde `backtest.parquet`. El sesgo es lo previsto entre lo observado, menos 1.

| Bloque | Modelo | WAPE modelo | WAPE B0 | WAPE B1 | Sesgo modelo | Recall rojo (modelo / B1) | Precisión rojo (modelo / B1) |
|---|---|---|---|---|---|---|---|
| 2023-S2 (verano 2023) | corto | 7,7 % | 16,2 % | 8,3 % | −5,4 % | 79,9 / 86,8 % | 90,2 / 91,8 % |
| | largo | 7,1 % | 16,2 % | 8,3 % | −3,9 % | 84,4 / 86,8 % | 94,0 / 91,8 % |
| 2024-S1 | corto | 7,5 % | 9,3 % | 10,6 % | −5,6 % | 58,8 / 11,8 % | 92,1 / 10,5 % |
| | largo | 8,4 % | 9,3 % | 10,6 % | −6,9 % | 52,9 / 11,8 % | 100 / 10,5 % |
| 2024-S2 (verano 2024) | corto | 10,4 % | 17,8 % | 10,6 % | −9,1 % | 81,1 / 88,1 % | 99,3 / 92,8 % |
| | largo | 9,9 % | 17,8 % | 10,6 % | −8,5 % | 85,3 / 88,1 % | 98,7 / 92,8 % |
| **2025-S1 (bloque final)** | corto | **9,5 %** | **8,6 %** | 9,9 % | −8,4 % | 57,6 / 15,4 % | 87,2 / 21,1 % |
| | largo | **11,7 %** | **8,6 %** | 9,9 % | −10,8 % | 40,6 / 15,4 % | 86,7 / 21,1 % |

- **En el bloque final (2025-S1) el modelo no gana al día normal en WAPE,** ni el de corto plazo (9,5 % frente a 8,6 %) ni el de largo (11,7 % frente a 8,6 %).
  - Por zonas, en 2025-S1 pierde frente a B0 en Gijón (corto 9,9 % frente a 7,8 %) y en Oviedo (corto 8,3 % frente a 4,8 %).
  - Gana en los Picos (12,1 % frente a 23,1 %), en Llanes y en Ribadesella.
  - Como el WAPE pondera por volumen, y Gijón y Oviedo suman la mayor parte de las llegadas, las ciudades deciden la cifra global.
- **En los veranos, B1 detecta más rojos que el modelo**: 86,8 % frente a 79,9 % (corto) en 2023 y 88,1 % frente a 81,1 % en 2024. El modelo da menos falsas alarmas (precisión del 99,3 % frente al 92,8 % en 2024-S2). B1 no se puede desplegar, pero hay que decirlo.
- Fuera del verano el modelo gana con claridad a B1 en los días rojos: B1 falla en Semana Santa, que cambia de fecha cada año.

### Zona de los Picos (Cangas de Onís, 33012)

Fuente: `salidas/tablas_resultados_reales.md` (bloque × zona × horizonte).

| Bloque | Horizonte | WAPE modelo | WAPE B0 | WAPE B1 | Sesgo | Acierto de color (modelo / B1) | Rojos observados | Recall rojo (modelo / B1) | Precisión rojo (modelo / B1) |
|---|---|---|---|---|---|---|---|---|---|
| 2023-S2 | corto h1-3 | 11,8 % | 39,9 % | **10,7 %** | −1,4 % | 84,0 / 87,0 % | 105 | 82,9 / 80,0 % | 72,5 / 82,4 % |
| | corto h4-7 | 11,2 % | 39,9 % | **10,7 %** | −1,6 % | 83,9 / 87,0 % | 140 | 79,3 / 80,0 % | 71,2 / 82,4 % |
| | largo 8+ | 9,6 % | 39,9 % | 10,7 % | −2,6 % | 83,6 / 87,0 % | 35 | 80,0 / 80,0 % | 87,5 / 82,4 % |
| 2024-S1 | corto h1-3 | 10,6 % | 23,8 % | 18,3 % | −3,3 % | 93,5 / 91,6 % | 9 | 66,7 / 0 % | 100 / 0 % |
| | corto h4-7 | 10,4 % | 23,8 % | 18,3 % | −3,6 % | 95,8 / 91,6 % | 12 | 66,7 / 0 % | 100 / 0 % |
| | largo 8+ | 10,3 % | 23,8 % | 18,3 % | −4,0 % | 93,3 / 91,6 % | 3 | 33,3 / 0 % | 100 / 0 % |
| 2024-S2 | corto h1-3 | 14,3 % | 42,8 % | 14,0 % | −13,0 % | 85,5 / 81,5 % | 135 | 69,6 / 71,1 % | 100 / 91,4 % |
| | corto h4-7 | 15,8 % | 42,8 % | **14,0 %** | −14,3 % | 81,2 / 81,5 % | 180 | **58,9** / 71,1 % | 100 / 91,4 % |
| | largo 8+ | 12,9 % | 42,8 % | 14,0 % | −11,0 % | 87,6 / 81,5 % | 45 | 75,6 / 71,1 % | 100 / 91,4 % |
| 2025-S1 | corto h1-3 | 10,6 % | 23,1 % | 18,0 % | −6,7 % | 94,6 / 90,3 % | 12 | 50,0 / 0 % | 100 / 0 % |
| | corto h4-7 | 13,2 % | 23,1 % | 18,0 % | −9,3 % | 92,6 / 90,3 % | 16 | 50,0 / 0 % | 100 / 0 % |
| | largo 8+ | 12,9 % | 23,1 % | 18,0 % | −9,8 % | 94,4 / 90,3 % | 4 | 50,0 / 0 % | 100 / 0 % |

Los rojos observados de corto plazo cuentan filas (día × horizonte); los de largo plazo, días. En los Picos hubo 35 días rojos en 2023-S2 y 45 en 2024-S2.

- El modelo gana al día normal en los Picos en todos los bloques y horizontes, por 2 a 3 veces.
- **En los veranos, el corto plazo de los Picos no gana a B1 en WAPE:** 11,8 % y 11,2 % frente a 10,7 % en 2023, y 15,8 % frente a 14,0 % en 2024 (h4-7).
- **En el verano de 2024, el corto plazo a 4-7 días detecta solo el 58,9 % de los rojos de los Picos.** El de largo plazo, en los mismos días, detecta el 75,6 %.
- Global, por horizonte (`metricas.json → tablas.horizonte`): el recall de rojos del corto plazo baja del 82,4 % (h = 1) al 73,5 % (h = 7), mientras que el de largo plazo es del 79,9 %. **A partir de h = 4, el modelo de corto plazo es peor que el de largo**, con el mismo WAPE (9,3 %) y menos recall. Es el efecto del modo estricto: no hay previsión archivada a más de 3 días. La decisión pendiente de `notas/modelo.md` («mostrar el color del largo plazo cuando sea más alto») queda respaldada por los datos. No la aplico: es una decisión de diseño.
- Gijón y Oviedo no tienen ningún día rojo observado ni previsto en los 4 bloques. Su acierto de color (98,6 % y 100 %) es trivial: siempre verde.

## 3. Factores

Fuente: `salidas/explicacion_factores.json` (importancia global) y columnas `fx_*` de `salidas/backtest.parquet` (SHAP fuera de muestra) para la zona de los Picos y el signo. Tabla completa en `salidas/tablas_resultados_reales.md`.

Media de |SHAP| (escala log):

| Factor | Global, largo | Global, corto h=1 | Picos, largo | Picos, corto h=1 |
|---|---|---|---|---|
| Vacaciones escolares | 0,126 | 0,060 | 0,145 | 0,067 |
| Época del año | 0,106 | 0,072 | 0,127 | 0,087 |
| Acceso regulado a los Lagos | 0,065 | 0,040 | 0,078 | 0,046 |
| Zona | 0,107 | 0,096 | 0,046 | 0,031 |
| Fin de semana | 0,022 | 0,019 | 0,024 | 0,021 |
| Puente o festivo en Asturias | 0,024 | 0,021 | 0,023 | 0,020 |
| Festivo en origen (Madrid o CyL) | 0,011 | 0,008 | 0,012 | 0,009 |
| Partido | 0,005 | 0,003 | 0,005 | 0,003 |
| Evento | 0,003 | 0,003 | 0,002 | 0,001 |
| Tiempo en el valle | — | 0,016 | — | 0,017 |
| Tiempo en la montaña | — | 0,000 | — | 0,002 |
| Interés en internet | — | **0,111** | — | **0,149** |

¿Tienen sentido? Signo en los Picos, con el efecto medio en % sobre el día medio del modelo:

- **Verano: sí.** «Época del año» va de −24 % en enero a +29 % en agosto. Con vacaciones escolares de Madrid, +26 % (207 días); sin ellas, −10 %.
- **Puentes y festivos de Asturias: sí, pero con un efecto pequeño** (+1,8 % en 48 días frente a −0,2 %). Parte del efecto de los puentes lo recogen «Vacaciones escolares» y «Época del año».
- **Festivos en origen (Madrid o Castilla y León sin festivo en Asturias): sí,** +4,1 %, pero con solo 6 días: no es concluyente.
- **Lluvia: negativa, sí** (corto plazo, h = 1, valle):

  | Lluvia prevista | Efecto medio | Días |
  |---|---|---|
  | < 0,5 mm | +3,0 % | 310 |
  | 0,5-5 mm | +1,6 % | 113 |
  | 5-15 mm | +0,3 % | 60 |
  | > 15 mm | −2,8 % | 31 |

  La correlación del SHAP con la lluvia prevista es de −0,54, y con la temperatura máxima, de +0,39. El efecto es pequeño: solo hay previsión archivada desde enero de 2024. El tiempo en la montaña casi no aporta (0,002).
- **«Acceso regulado a los Lagos» (+9,6 % los días regulados, −6,2 % los demás) no es un efecto causal.** El calendario de regulación coincide con los fines de semana de temporada y el verano, así que actúa como otro marcador de temporada. No se puede leer como «regular atrae visitantes».
- **«Interés en internet» es el factor más importante del corto plazo, y no lo esperábamos.**
  - Su efecto medio cae de año en año: +7,3 % en 2023, −1,9 % en 2024 y −7,0 % en 2025.
  - En esos años, las llegadas reales suben (ver `notas/estado_resultados.md`).
  - Correlaciona 0,52 con «Época del año», así que en parte repite la estacionalidad.
  - Hipótesis no verificada: las visitas a Wikipedia bajan con el tiempo por causas ajenas al turismo y empujan hacia abajo la predicción de 2025. Explicaría una parte del sesgo negativo del corto plazo, pero no del de largo plazo, que no usa esta señal.
- Eventos y partidos: aportan muy poco (≤ 0,005).

## 4. Intervalos p10-p90

Fuente: `salidas/metricas.json → fiabilidad[].cobertura`, medida dejando fuera cada bloque. El objetivo es el 80 %.

| Zona | Mínima | Media | Máxima |
|---|---|---|---|
| Cangas de Onís | 75,7 % | 76,1 % | 77,0 % |
| Gijón | 77,1 % | 77,8 % | 78,9 % |
| Llanes | 78,5 % | 79,2 % | 80,2 % |
| Oviedo | 76,8 % | 77,8 % | 78,5 % |
| Ribadesella | 75,7 % | 77,5 % | 78,5 % |
| Todas (40 zona × horizonte) | 75,7 % | 77,7 % | 80,2 % |

**Los intervalos son algo estrechos:** solo 1 de las 40 combinaciones llega al 80 %. La peor es la zona de los Picos, con un 76 %.

## 5. Sensibilidad: con y sin eventos `probable`

Fuente: `salidas/metricas.json → tablas.global`.

| Experimento | Modelo | WAPE | Acierto de color | Recall rojo | Precisión rojo |
|---|---|---|---|---|---|
| base (con `probable`) | corto | 8,8 % | 93,3 % | 77,7 % | 94,1 % |
| | largo | 9,3 % | 93,5 % | 79,9 % | 96,0 % |
| solo eventos verificados | corto | 9,0 % | 93,3 % | 77,6 % | 94,0 % |
| | largo | 9,4 % | 93,6 % | 79,6 % | 96,0 % |
| desde el corte (2022-11-09) | corto | 9,3 % | 89,4 % | 42,6 % | 93,8 % |
| | largo | 10,1 % | 88,7 % | 43,5 % | 95,0 % |
| tiempo aproximado (cota optimista, no desplegable) | corto | 8,1 % | 93,9 % | 81,0 % | 93,8 % |

- **Los eventos `probable` casi no cambian nada:** de 0,1 a 0,2 puntos de WAPE y de 0,1 a 0,3 de recall. Con datos sintéticos, quitarlos empeoraba el largo plazo del 82 % al 70 % de recall; con datos reales, la diferencia es despreciable. Los eventos pesan muy poco en el modelo (sección 3).
- Empezar en 2022-01-01 (decisión del equipo) está muy justificado. Empezando en el corte, el recall de rojos cae al 43 %, porque el primer bloque no ve ningún verano.
- Con un tiempo casi observado, el corto plazo mejoraría de 8,8 % a 8,1 % de WAPE y de 77,7 % a 81,0 % de recall. Es el techo de lo que aportaría una mejor previsión.

## 6. Lo que ha salido peor de lo esperado

1. **El modelo no gana al día normal en el bloque final (2025-S1):** 9,5 % (corto) y 11,7 % (largo) de WAPE, frente al 8,6 % de B0. La diferencia viene de Gijón y Oviedo. En la zona de los Picos sí gana (12,1 % frente a 23,1 % en corto).
2. **El modelo se queda corto de forma sistemática en todos los bloques:** entre −3,9 % y −10,8 % del volumen total, y en los Picos hasta −14 % en el verano de 2024. Las llegadas crecen de un año a otro (+13 % en los Picos de 2022 a 2025, de enero a junio) y el modelo no tiene ninguna variable de tendencia. Causa **no verificada**: crecimiento no captado, y quizá también el descenso de las visitas a Wikipedia.
3. **En verano, B1 (el año anterior) detecta más rojos que el modelo** (86,8 % y 88,1 % frente a 79,9 % y 81,1 %), aunque con más falsas alarmas.
4. **En el bloque final, el largo plazo solo detecta el 40,6 % de los rojos** (13 de 32). Los que pierde son el puente de mayo (1 y 2 de mayo de 2025) y la segunda quincena de junio de 2025 en Llanes y Ribadesella (18 y del 23 al 30), con cocientes observados de 2,0 a 2,5 y previstos de 1,4 a 1,9. Encaja con el punto 2.
5. **El corto plazo a 4-7 días es peor que el largo plazo:** recall del 77 % al 73 % frente al 80 %, con el mismo WAPE.
6. **Intervalos p10-p90 con cobertura del 77,7 % de media,** por debajo del 80 % buscado; en los Picos, el 76 %.
7. **«Interés en internet» es el factor más importante del corto plazo** y tiene una tendencia temporal sospechosa (sección 3).
8. En Gijón y Oviedo el semáforo nunca sale de verde con los umbrales actuales: el producto solo tiene sentido en las 3 zonas turísticas.

## 7. ¿Hace falta regular? (zona de los Picos, Cangas de Onís 33012)

Fuentes:
- `salidas/regulacion.json` (`por_zona`, `lagos.por_anio`, `calendario_alertas`);
- `salidas/calibracion_lagos.json`;
- comprobación independiente de las cifras observadas con `scripts/verificar_regulacion.py`, que recalcula desde `data/clean/objetivo_diario.parquet` y la columna `lagos_regulado` de `data/clean/calendario_diario.parquet`. Coinciden todas.

Rojo = al menos 2,0 veces el día normal de ese día de la semana; ámbar = de 1,5 a 2,0 veces. Son umbrales definidos por nosotros, no una capacidad oficial.

### Observado (2023 y 2024)

| Año | Días con dato | Días rojos | Días ámbar | Días regulados en los Lagos (con dato) | Rojos en días regulados | Alerta (ámbar + rojo) en días regulados | Días regulados por debajo de lo normal (< 1,0) |
|---|---|---|---|---|---|---|---|
| 2023 | 358 | **39** | 43 | 172 | 38 de 39 | 79 de 82 | 16 |
| 2024 | 356 | **48** | 42 | 180 | 47 de 48 | 88 de 90 | 16 |

- **Días por encima de 2 veces lo normal: 39 en 2023 y 48 en 2024.** Están concentrados en agosto (25 y 29), julio (8 y 12) y Semana Santa (3 y 3).
- Casi todos los días de presión alta ya caen en días regulados: 85 de los 87 rojos y 167 de los 172 días en alerta de los dos años.
- Al revés no ocurre: la regulación cubre muchos más días de los que superan los umbrales. Solo el 24 % de los días regulados es rojo, y 93 días regulados en 2023 y 92 en 2024 están por debajo de 1,5 veces lo normal.

### ¿Qué umbral reproduce mejor la regulación actual?

Fuente: `salidas/calibracion_lagos.json`. Positivo = día regulado. Máximo F1 en una rejilla de 0,5 a 3,0 con paso 0,05.

| Escala | Fuente del cociente | Mejor umbral | F1 | Precisión | Recall | F1 con el umbral ámbar (1,5) | F1 con el umbral rojo (2,0) |
|---|---|---|---|---|---|---|---|
| Relativa (la del semáforo) | observado 2023-2024 | **1,10×** | 0,867 | 0,892 | 0,844 | 0,637 | 0,387 |
| Absoluta (frente al día normal medio) | observado 2023-2024 | 1,05× | 0,867 | 0,854 | 0,881 | 0,678 | 0,388 |
| Relativa | previsto fuera de muestra (bloques de validación) | 1,05× | 0,911 | 0,949 | 0,877 | 0,596 | 0,324 |
| Absoluta | previsto fuera de muestra | 1,00× | 0,897 | 0,883 | 0,910 | 0,587 | 0,336 |

**La regulación actual equivale a «cualquier día un 10 % por encima de lo normal»,** no a los días de presión extrema. Se confirma, ahora con datos reales, la hipótesis que en `notas/modelo.md` estaba pendiente.

Hay que tener en cuenta dos cosas:
- la regulación es un calendario planificado (fines de semana de temporada y verano), no una respuesta a la afluencia medida;
- el MITMA mide llegadas al municipio de Cangas de Onís, no accesos a los Lagos.

Esta comparación orienta, pero no valida.

### Previsión con el modelo de largo plazo (2026 y 2027)

Fuente: `salidas/regulacion.json → por_zona` (33012). Intervalo = días con p10 por encima del umbral (mínimo) y días con p90 por encima del umbral (máximo).

| Año | Días rojos (intervalo) | Días ámbar | Días en alerta (intervalo) | Días regulados | Rojos en días regulados | Calendario supuesto |
|---|---|---|---|---|---|---|
| 2026 | **36** (29-66) | 48 | 84 (63-131) | 185 | 36 de 36 | no |
| 2027 | **34** (28-61) | 44 | 78 (56-126) | 185 (supuesta) | 34 de 34 | sí (los 365 días) |

- Rojos previstos por mes: en 2026, abril 2, julio 6 y agosto 28; en 2027, julio 5 y agosto 29.
- En 2027 no sale ningún rojo en Semana Santa. Es un año con el curso escolar y la regulación supuestos iguales a los de 364 días antes (`calendario_supuesto`); **no verificado** que la Semana Santa de 2027 (marzo) esté bien recogida.
- **La previsión cuenta probablemente de menos.** En la validación fuera de muestra de los Picos, el modelo de largo plazo predijo 69 rojos frente a 87 observados (−21 %) y 153 días en alerta frente a 179 (−15 %), por el sesgo a la baja de la sección 6. Las cifras centrales de 2026 (36) y 2027 (34) quedan por debajo de lo observado en 2023 (39) y 2024 (48); lo observado sí cae dentro del intervalo.

### Respuesta

**Hechos.**
- En la zona de los Picos, las llegadas de ocio superaron 2 veces lo normal 39 días en 2023 y 48 en 2024, sobre todo en agosto, y el modelo prevé de 29 a 66 días así en 2026.
- La regulación actual de los Lagos (172-180 días con dato al año) ya cubre 85 de esos 87 días.
- La regulación reproduce mejor un umbral de 1,1 veces lo normal (F1 0,87) que el de 2 veces (F1 0,39).

**Opinión del equipo.**
- Los datos respaldan que hace falta regular: hay un núcleo de unos 40-50 días al año con más del doble de visitantes de lo normal, y se repite cada verano.
- El calendario actual llega a esos días, pero es mucho más amplio: regula también días normales o casi normales.
- Un sistema de alerta como este podría servir para concentrar las medidas más duras en los días rojos y revisar el resto del calendario. No hemos medido la capacidad física de los Lagos, así que no podemos decir cuál es el umbral correcto.

## 8. Validación externa con el INE (paso 5): NO REALIZADA

No hay datos de turistas mensuales del INE medidos con teléfonos móviles en el repositorio.
- `data/raw/ine_moviles_*` está en `.gitignore`, y no existe en ninguna rama remota ni en local (buscado el 2026-10-16). Solo está el script `scripts/descarga_ine_moviles.py`.
- No se ha descargado nada.

Sí hay series mensuales del INE por punto turístico hasta 2026M08 (`notas/registro_descargas.md`):
- hoteles (`ine_eoh_2078.csv`): Cangas de Onís, Gijón, Llanes y Oviedo;
- apartamentos (`ine_eoap_2082.csv`) y campings (`ine_camping_2084.csv`): solo Llanes.

Miden viajeros alojados en un tipo de establecimiento, no turistas, y no incluyen Ribadesella. Usarlas en lugar de las de móviles queda pendiente de decisión del equipo.

## 9. Salidas para la web (paso 6)

Ejecución del 2026-10-16:

```bash
python -X utf8 src/modelo/descargar_prevision.py              # Open-Meteo, emisión 2026-10-16
python -X utf8 src/modelo/ejecutar.py --objetivo real --algoritmo ambos
```

Previsión descargada:
- 63 filas = 9 puntos × 7 días (2026-10-16 → 2026-10-22), en `data/clean/openmeteo_prevision.parquet`;
- respuestas en bruto en `data/prevision/2026-10-16/`;
- columnas y tipos idénticos a `openmeteo_prevision_ejemplo.parquet` (lo comprueba el script);
- ningún punto sin previsión.

Las métricas regeneradas son idénticas a las de la ejecución anterior: la ejecución es determinista y solo cambia la previsión.

| Conjunto (`predicciones.json`) | Modelo | Registros | Fechas |
|---|---|---|---|
| `futuro_largo` | largo | 300 (5 zonas × 60 días) | 2026-10-17 → 2026-12-15 |
| `futuro_corto` | corto | 35 (5 zonas × 7 días) | 2026-10-17 → 2026-10-23 (emisión 2026-10-16; tiempo a 1-3 días) |
| `historico` | largo h8 y corto h1 | 180 + 180 | 2024-08-01 → 08-31 y 2024-12-05 → 12-09 |

Comprobaciones:
- `validar_salidas.validar(salidas/)` da 0 errores.
- Los 9 JSON del modelo llevan `sintetico: false` en la raíz, y los 695 registros de `predicciones.json`, también.
- **Siguen en `salidas/` dos ficheros con `sintetico: true`** que esta ejecución no regenera: `sintetico_efectos_reales.json` y `sintetico_recuperacion_factores.json`. No forman parte del contrato de la web ni los copia `scripts/actualizar_datos_web.py`. No se han borrado; queda pendiente de decisión del equipo.

### Casos de la demo

- **Primera quincena de agosto de 2024, Picos.**
  - Los 15 días son rojos observados (de 2,12 a 3,90 veces lo normal).
  - El largo plazo (h = 8) los pinta rojos los 15, y el corto plazo (h = 1), 14 de 15.
  - El modelo se queda corto en los días más altos: el 15 de agosto predice 3,00 veces lo normal y se observa 3,90.
  - Factores del caso de ejemplo (2023-08-17, `explicacion_factores.json`): «Época del año» +40 %, «Vacaciones escolares» +37 %, «Acceso regulado a los Lagos» +17 % y «Fin de semana» +2,5 %.
- **Puente de diciembre de 2024: no es un caso rojo con datos reales.**
  - No hubo ningún día rojo observado en ninguna zona. Lo más alto es ámbar: Llanes, 1,69 y 1,66 veces lo normal los días 5 y 6; Picos, 1,55 el día 6.
  - El modelo lo pinta todo de verde salvo Llanes el 6 a largo plazo (ámbar, 1,51).
  - En el puente de 2023 sí hubo rojos (Llanes, 2,24 y 2,02 veces lo normal los días 6 y 7) y el modelo predijo de 1,25 a 1,36 (verde).
  - **Los puentes de diciembre son un fallo claro del modelo.** No se han cambiado los periodos de la demo, porque es una decisión del equipo.

### Actualizar la web (sin ejecutar: no se ha tocado la rama `web`)

`origin/web` (`6fba3b5`) tiene `scripts/actualizar_datos_web.py`. Comprueba el contrato y copia los 5 JSON a `Afluencia Asturias/datos/modelo/`, junto con el mapeo y el calendario. En `origin/web`, `config/mapeo_zonas.csv` todavía tiene `zona_mitma_id` vacío, así que con los identificadores reales el script se pararía si no se trae también el mapeo. Orden, en una copia con la rama `web`:

```bash
git checkout web && git pull
git checkout origin/resultados-reales -- salidas/predicciones.json salidas/alternativas.json salidas/regulacion.json salidas/perfil.json salidas/metricas.json config/mapeo_zonas.csv
python -X utf8 scripts/actualizar_datos_web.py
```
