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

## Después (yo)
1. Volver a ejecutar `unir_B.py` y `ejecutar.py --objetivo real --algoritmo ambos`.
2. Validar con `validar_salidas.py` y los tests.
3. Regenerar la web y repetir las comprobaciones de `notas/integracion_web.md`.
4. Revisar qué cifras de `notas/resultados_reales.md` cambian.
