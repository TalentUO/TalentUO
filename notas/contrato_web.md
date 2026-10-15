# Contrato de datos de la web (salidas del modelo)

Fecha: 2026-10-15. Los genera `python -X utf8 src/modelo/ejecutar.py --objetivo sintetico|real` en `salidas/`. La comprobación automática está en `src/modelo/validar_salidas.py`: se ejecuta al final de cada corrida y la detiene si algo no cumple el contrato. **La web se construye contra este documento.**

## Reglas comunes

- Codificación UTF-8. Fechas `AAAA-MM-DD`. Los números ausentes son `null`, nunca 0.
- **`sintetico`** está en la raíz de cada JSON y en cada registro. Si es `true`, la web **tiene que** mostrar el aviso `aviso` («DATOS SINTÉTICOS — NO SON REALES») de forma visible en todas las pestañas.
- Cabecera común: `sintetico` (bool), `aviso` (texto o null), `generado` («AAAA-MM-DD HH:MM»), `objetivo` (variable predicha, p. ej. `llegadas_ocio`) y `umbrales` (`{"ambar": 1.5, "rojo": 2.0, "por_zona": {}}`).
- `color` ∈ `verde | ambar | rojo | gris`. **Gris** = sin dato del MITMA, sin día normal o sin variables suficientes.
- `cociente` = visitantes / día normal (normal de esa zona y ese día de la semana). `pct_sobre_normal` = (cociente − 1) × 100.
- Los IDs de zona del modo sintético son ficticios (`EJEMPLO_*`). Con datos reales serán los `zona_mitma_id` del MITMA: **no los escribáis a mano en la web**; leedlos de `predicciones.json → zonas`.

## 1. `predicciones.json` (Inicio)

```text
{ cabecera…,
  "fecha_hoy": "2026-10-16",
  "zonas": [ {zona_mitma_id, nombre_zona, lat, lon, es_principal} ],
  "conjuntos": { "futuro_largo": texto, "futuro_corto": texto, "historico": texto },
  "info_corto_plazo": { fecha_emision, punto_prevision, zona_aplicada, horizontes_con_tiempo, fechas },
  "predicciones": [ registro… ] }
```

Cada registro es una predicción por `fecha` × `zona_mitma_id` × `horizonte` (× `modelo`):

| Campo | Tipo | Significado |
|---|---|---|
| `fecha` | fecha | Día previsto. |
| `zona_mitma_id`, `nombre_zona` | texto | Zona. |
| `horizonte` | entero | Días de antelación (fecha − `fecha_emision`). |
| `prediccion` | número | Visitantes previstos (llegadas de ocio por defecto). |
| `normal` | número | Día normal de esa zona y día de la semana. |
| `cociente`, `pct_sobre_normal` | número | Ver reglas comunes. |
| `color` | texto | Semáforo. |
| `p10`, `p90` | número | Intervalo del 80 % (visitantes). |
| `incierto` | bool | `true` si p10 y p90 caen en colores distintos: mostrar el color con un aviso de «incierto». |
| `factores` | lista de 3 | Los 3 factores con más peso: `{nombre, efecto_pct, signo}`. `efecto_pct` = exp(suma de SHAP del factor) − 1, **respecto al día medio del modelo** (no respecto al normal). Ejemplo: «Vacaciones escolares +44 %». |
| `sintetico` | bool | |
| `modelo` | `corto` \| `largo` | Corto plazo (1-7 días; con tiempo e interés) o largo plazo (8+ días; calendario y eventos). |
| `conjunto` | texto | `futuro_largo` (60 días desde `fecha_hoy`), `futuro_corto` (con la previsión meteorológica de ejemplo) o `historico` (validación fuera de muestra, para la demo). |
| `fecha_emision` | fecha | Día en que se habría hecho la predicción. |
| `observado`, `cociente_observado`, `color_observado` | número / texto / null | Solo en `historico`: el valor real, para enseñar acierto o fallo. |

Cómo elegir qué enseñar: para una fecha y una zona, usad `futuro_corto` si existe y, si no, `futuro_largo`. Para la demo del caso rojo con su explicación, usad `historico` (puente de diciembre y agosto de 2024, `modelo` `largo` con horizonte 8 y `corto` con horizonte 1).

Ejemplo (histórico, sintético):

```json
{"fecha": "2024-08-01", "zona_mitma_id": "EJEMPLO_cangas", "nombre_zona": "Cangas de Onís (EJEMPLO)",
 "horizonte": 8, "prediccion": 4520.0, "normal": 1979.0, "cociente": 2.284, "pct_sobre_normal": 128.4,
 "color": "rojo", "p10": 3131.0, "p90": 7037.0, "incierto": true,
 "factores": [{"nombre": "Vacaciones escolares", "efecto_pct": 44.4, "signo": "+"},
              {"nombre": "Época del año", "efecto_pct": 35.6, "signo": "+"},
              {"nombre": "Festivo en origen (Madrid o Castilla y León)", "efecto_pct": -2.9, "signo": "-"}],
 "sintetico": true, "modelo": "largo", "conjunto": "historico", "fecha_emision": "2024-07-24",
 "observado": 6428.0, "cociente_observado": 3.248, "color_observado": "rojo"}
```

Nombres posibles de factor (`config/factores.yaml`): Vacaciones escolares · Festivo en origen (Madrid o Castilla y León) · Puente o festivo en Asturias · Fin de semana · Época del año · Acceso regulado a los Lagos · Evento · Partido · Tiempo en el valle · Tiempo en la montaña · Interés en internet. («Zona» y «Antelación» existen, pero nunca salen entre los 3 principales).

## 2. `alternativas.json` (Inicio: «mejor día alternativo»)

`{cabecera…, "parametros": {"dias_margen": 3, "km_zona_cercana": 60}, "alternativas": [ … ]}`. Hay un registro por cada predicción ámbar o roja (en el histórico de corto plazo, solo con horizonte 1):

| Campo | Significado |
|---|---|
| `fecha`, `zona_mitma_id`, `nombre_zona`, `conjunto`, `modelo`, `horizonte`, `cociente`, `color` | La predicción en alerta. |
| `mejor_dia` | `{fecha, cociente, color, prediccion, diferencia_pct}`: el día con menos presión a ±3 días en la misma zona, o `null` si ninguno tiene menos presión. |
| `zona_alternativa` | `{zona_mitma_id, nombre_zona, distancia_km, cociente, color}`: la zona a ≤ 60 km con menos presión ese mismo día, o `null`. |

```json
{"fecha": "2026-11-02", "zona_mitma_id": "EJEMPLO_gijon", "nombre_zona": "Gijón (EJEMPLO)", "conjunto": "futuro_largo",
 "modelo": "largo", "horizonte": 17, "cociente": 1.88, "color": "ambar",
 "mejor_dia": {"fecha": "2026-10-30", "cociente": 0.9535, "color": "verde", "prediccion": 8827, "diferencia_pct": -41.2},
 "zona_alternativa": {"zona_mitma_id": "EJEMPLO_oviedo", "nombre_zona": "Oviedo (EJEMPLO)", "distancia_km": 24.9,
                      "cociente": 1.874, "color": "ambar"}, "sintetico": true}
```

## 3. `regulacion.json` (Gestión: «¿hace falta regular?»)

`{cabecera…, "por_zona": [...], "lagos": {...}, "calendario_alertas": [...]}`

**`por_zona[]`** = `{zona_mitma_id, nombre_zona, anios: [...], curva_umbral: [...]}`

- `anios[]`: `{anio, tipo, dias_con_dato, dias_rojos, dias_ambar, dias_alerta}`. Los años 2023 y 2024 son `observado`. Los años 2026 y 2027 son `previsto` (modelo de largo plazo) y añaden el intervalo `dias_rojos_min/max` y `dias_alerta_min/max`: días cuyo p10 o p90 supera el umbral. También añaden `calendario_supuesto_dias`: en 2027, el curso escolar desde septiembre y la regulación de los Lagos no están publicados, y se suponen iguales a los de 364 días antes. `dias_alerta` = ámbar + rojo.
- `curva_umbral[]`: `{anio, tipo, umbral, dias[, dias_min, dias_max]}`, con los umbrales 1,2 a 3,0. Sirve para el **umbral ajustable** de la web: los días por encima de cualquier umbral sin recalcular nada.

**`lagos`** (zona principal): `{zona_mitma_id, nombre_zona, por_anio: [...], calibracion: {...}}`

- `por_anio[]`: `{anio, tipo, dias_regulados, rojos_en_dias_regulados, rojos_fuera_de_regulacion, alerta_en_dias_regulados, alerta_fuera_de_regulacion}`. Los años previstos añaden `regulacion_supuesta` (true en 2027).
- `calibracion`: qué umbral reproduce mejor los días regulados (máximo F1), con el cociente `observado_2023_2024` y con el `previsto_fuera_de_muestra`. Cada uno tiene dos variantes:
  - `relativo`: frente al normal de ese día de la semana;
  - `absoluto`: frente al día normal medio de la zona.
  Cada variante lleva `{mejor_umbral, f1, precision, recall, dias_regulados, dias_alerta_con_mejor_umbral, mejor_en_borde_de_rejilla, con_umbral_ambar, con_umbral_rojo}`.

**`calendario_alertas[]`**: una fila por día de 2026 y 2027 y zona: `{fecha, zona_mitma_id, prediccion, normal, cociente, color, p10, p90, incierto, lagos_regulado (bool|null), calendario_supuesto, sintetico}`. Es el calendario de alertas de Gestión.

```json
{"anio": 2026, "tipo": "previsto", "dias_con_dato": 365, "dias_rojos": 44, "dias_rojos_min": 5, "dias_rojos_max": 90,
 "dias_ambar": 28, "dias_alerta": 72, "dias_alerta_min": 30, "dias_alerta_max": 189, "calendario_supuesto_dias": 0}
```

## 4. `perfil.json` (Gestión: perfil del visitante)

`{cabecera…, "perfil": [...], "nota": texto}`. Hay una fila por zona y mes (histórico, solo días `completa`):

| Campo | Significado |
|---|---|
| `zona_mitma_id`, `nombre_zona`, `mes` (1-12), `dias` | |
| `llegadas_ocio_media_dia` | Media diaria de llegadas de ocio. |
| `pct_desde_asturias`, `pct_resto_espana` | Reparto de las llegadas de ocio por residencia (suman 100). Sin extranjeros (el MITMA no los incluye). |
| `pernoctaciones_por_100_llegadas` | Pernoctaciones de no residentes por cada 100 llegadas de ocio. |
| `pct_excursionistas_aprox` | max(0, 100 − la anterior). **Aproximación**: una persona puede pernoctar varias noches. |

## 5. `metricas.json` (Gestión: fiabilidad; Sobre los datos)

`{cabecera…, tablas, fiabilidad, experimentos, modelos_finales, dia_normal, comprobacion_treeexplainer, calibracion_lagos[, recuperacion_sintetico]}`

- `tablas.{global, bloque, zona, horizonte, mes, bloque_zona_horizonte}`: filas con las claves de agrupación (`experimento`, `modelo`, `bloque`, `zona_mitma_id`, `horizonte_txt` = «1»…«7» u «8+», `mes`) y `metodo` (`modelo`, `B0` día normal, `B1` mismo día del año anterior). Las métricas son `n, wape, mae, acierto_color, rojos_obs, rojos_pred, recall_rojo, precision_rojo, recall_alerta, matriz_confusion` (claves «obs->pred»).
- `fiabilidad[]`: por zona y horizonte, `{zona_mitma_id, nombre_zona, horizonte_txt, n, wape, acierto_color, rojos_obs, recall_rojo, precision_rojo, nota, q10, q90, n_errores, cobertura}`. **`nota` es el texto para la web**, p. ej. «Acierta el color en el 86 % de los días; detecta 5 de cada 10 días rojos.». `cobertura` = proporción de días reales dentro del intervalo p10-p90, medida dejando fuera cada bloque (objetivo: 0,80).
- `experimentos[]`: resumen por experimento (`base`, `con_2022`, `solo_eventos_verificados`, `tiempo_aproximado`) y modelo.

## Comprobación

`python -X utf8 src/modelo/validar_salidas.py` comprueba:
- campos y tipos;
- colores válidos;
- 3 factores por predicción no gris;
- p10 ≤ p90;
- el mismo `sintetico` en todos los ficheros y registros.
