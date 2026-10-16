# Ampliación del modelo a toda Asturias (46 zonas MITMA, 78 concejos)

Fecha: 2026-10-16. Rama: `zonas-asturias` (desde `main`).

## Por qué
El modelo y la web cubrían 5 zonas (Cangas de Onís, Llanes, Ribadesella, Gijón y Oviedo). Los otros 73 concejos salían como «Sin previsión». Los viajes del MITMA descargados por la parte A cubren las 46 zonas de Asturias (`data/raw/zonas_mitma_asturias.csv`, `notas/cobertura_mitma.md`).

## Qué cambia (hecho)
- **`config/mapeo_zonas.csv`: 46 zonas.**
  - Las 5 de antes no cambian; solo ganan `lat` y `lon`.
  - Las 41 nuevas toman sus concejos de `zonas_mitma_asturias.csv`.
  - Su nombre es la lista de sus concejos (`geo-asturias.js`, IGN).
  - `lat`/`lon` es el centroide de sus concejos, ponderado por área.
  - Sin estación AEMET: el modelo no la usa como variable.
- **Tiempo de las zonas nuevas (decisión del equipo): punto de Open-Meteo más cercano** entre los de valle o ciudad (cangas_de_onis, llanes, ribadesella, gijon, oviedo).
  - Es una aproximación, peor en el occidente: hasta unos 90 km.
  - Está anotada en la columna `notas` de cada zona.
  - El tiempo pesa poco en el modelo: SHAP 0,016 frente a 0,126 de las vacaciones (`notas/resultados_reales.md` §3).
- **`src/modelo/web_salidas.py`: las coordenadas de cada zona salen de `lat`/`lon` del mapeo** (antes, del punto del tiempo). Sin ellas, las zonas que comparten punto saldrían superpuestas y a 0 km entre sí. No toca el entrenamiento.
- **`data/clean/factores_B_diario.parquet`** regenerado con `unir_B.py`: 80 454 filas, 46 zonas.

## Lo que tiene que hacer Adrián (necesita `data/raw/mitma_viajes/` y `data/raw/mitma_pernoctaciones/`)

```bash
git fetch && git switch zonas-asturias
python -X utf8 src/modelo/construir_objetivo.py --mapeo config/mapeo_zonas.csv
python -X utf8 src/modelo/construir_llegadas_por_hora.py
git add data/clean/objetivo_diario.parquet data/clean/llegadas_por_hora.parquet
git commit -m "Parte A: objetivo y llegadas por hora de las 46 zonas de Asturias"
git push
```

Comprobaciones antes de subir:
- `objetivo_diario.parquet` con 46 zonas × 1 277 días (2022-01-01 → 2025-06-30) = 58 742 filas.
- La columna `calidad` marca los mismos días sin dato que antes (16 `sin_dato_mitma` y 3 `anomalia_mitma` por zona).
- `llegadas_por_hora.parquet` con 46 zonas.

## Hecho por Adrián
`80828e1`: `objetivo_diario.parquet` (58 742 filas = 46 zonas × 1 277 días; 736 `sin_dato_mitma` y 138 `anomalia_mitma`, 16 y 3 por zona) y `llegadas_por_hora.parquet` (26 496 filas). Las 5 zonas antiguas son idénticas a las de `main`.

## Resultado: el modelo de 46 zonas y un fallo de la parada temprana

**1.ª ejecución (configuración de `main`): muy mala en las zonas turísticas.**

| Largo plazo | 5 zonas (`main`) | 46 zonas, parada a 90 días |
|---|---|---|
| Rojos de los Picos detectados | 65 de 87 (75 %) | 29 de 87 (33 %) |
| Árboles del modelo final | 158 | 86 |

- Demo del 15-08-2024: Picos en ámbar. Ninguna zona en rojo (hubo 20 de verdad).
- Entrenar solo las zonas con temporada daba lo mismo (32 %), así que el problema no era mezclar zonas urbanas y turísticas.

**Causa: la parada temprana.**
- El número de árboles se elegía con los **últimos 90 días** del entrenamiento: en el modelo final, de abril a junio de 2025, sin verano.
- Con 46 zonas, el error de primavera deja de mejorar antes. El modelo paraba a unos 80 árboles y no aprendía los picos de agosto.

**Arreglo (`config/modelo.yaml` + `src/modelo/modelo.py`):**
- La ventana de parada temprana pasa a **365 días**, con un verano dentro.
- Tope del 40 % del periodo, para que el experimento «desde el corte», con menos de un año de datos, siga teniendo con qué entrenar.
- Tests: 92 pasan.

**Con el arreglo, la regla de elección da XGBoost** (`salidas/comparacion_algoritmos.json`):
- recall de rojos en verano: 64,2 % frente a 53,9 %;
- precisión: 87,2 % frente a 88,6 %;
- WAPE medio: 9,8 % frente a 10,2 %.

| Largo plazo, todos los bloques | 5 zonas (`main`) | **46 zonas (XGBoost)** |
|---|---|---|
| WAPE modelo / día normal (B0) | 9,3 % / 13,2 % | 9,9 % / 12,9 % |
| Rojos detectados / precisión, todas las zonas | 79,9 % / 96,0 % | 68,7 % / 85,2 % |
| Picos: rojos detectados (precisión) | 65 de 87 (94 %) | **71 de 87 (93 %)** |
| Llanes / Ribadesella | — | 80 % / 81 % |
| Colunga / Cudillero / Cabrales y 4 más / Tapia | — | 86 % / 80 % / 83 % / 86 % |
| Demo 15-08-2024, Picos (h=8) | rojo, ×3,00 (+200 %) | **rojo, ×3,27 (+227 %)**; observado ×3,90 |
| Zonas en rojo el 15-08-2024 (previstas / reales) | — | 16 / 20 |
| Días rojos previstos en los Picos, 2026 / 2027 | 36 (29–66) / 34 (28–61) | 40 (27–72) / 30 (24–62) |

**Siguen flojas** (detectan menos del 10 % de sus días rojos):
- Villaviciosa (4 de 39);
- Vegadeo y 4 más (los Oscos: 0 de 29);
- Somiedo y 5 más (4 de 29).

Son zonas con poco volumen y con el tiempo de un punto lejano.

## Nombres cortos
Las zonas de 3 o más concejos se llaman «<concejo de más superficie> y N más» (p. ej. «Cabrales y 4 más», «Somiedo y 5 más»). Con la lista completa, las etiquetas del mapa ocupaban hasta 7 líneas. La lista sigue en `concejos_ine` y en el panel de cada zona.
