# Tablas generadas (algoritmo lightgbm, experimento base)

Fuente: `salidas/backtest.parquet`. WAPE y sesgo en visitantes (sesgo = previsto / observado − 1); color frente al día normal de referencia (2024). B0 = día normal del bloque; B1 = mismo día de la semana 364 días antes (solo referencia). Métricas en %.

## Bloque × zona × horizonte

| bloque | zona | modelo | n | WAPE modelo | WAPE B0 | WAPE B1 | sesgo modelo | acierto color modelo / B1 | rojos obs. | recall rojo modelo / B1 | precisión rojo modelo / B1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023-S2 (verano 2023) | Cangas de Onís | corto h1-3 | 531 | 11,8 | 39,9 | 10,7 | -1,4 | 84,0 / 87,0 | 105 | 82,9 / 80,0 | 72,5 / 82,4 |
| 2023-S2 (verano 2023) | Cangas de Onís | corto h4-7 | 708 | 11,2 | 39,9 | 10,7 | -1,6 | 83,9 / 87,0 | 140 | 79,3 / 80,0 | 71,2 / 82,4 |
| 2023-S2 (verano 2023) | Cangas de Onís | largo (8+) | 177 | 9,6 | 39,9 | 10,7 | -2,6 | 83,6 / 87,0 | 35 | 80,0 / 80,0 | 87,5 / 82,4 |
| 2023-S2 (verano 2023) | Gijón | corto h1-3 | 531 | 6,2 | 10,7 | 7,6 | -4,7 | 98,3 / 98,9 | 0 | — / — | — / — |
| 2023-S2 (verano 2023) | Gijón | corto h4-7 | 708 | 6,2 | 10,7 | 7,6 | -4,7 | 98,3 / 98,9 | 0 | — / — | — / — |
| 2023-S2 (verano 2023) | Gijón | largo (8+) | 177 | 6,1 | 10,7 | 7,6 | -3,9 | 98,3 / 98,9 | 0 | — / — | — / — |
| 2023-S2 (verano 2023) | Llanes | corto h1-3 | 531 | 18,7 | 51,2 | 12,0 | -12,6 | 83,8 / 88,1 | 198 | 80,8 / 90,9 | 96,4 / 93,8 |
| 2023-S2 (verano 2023) | Llanes | corto h4-7 | 708 | 18,9 | 51,2 | 12,0 | -12,8 | 80,6 / 88,1 | 264 | 70,5 / 90,9 | 94,9 / 93,8 |
| 2023-S2 (verano 2023) | Llanes | largo (8+) | 177 | 12,2 | 51,2 | 12,0 | -2,6 | 86,4 / 88,1 | 66 | 86,4 / 90,9 | 93,4 / 93,8 |
| 2023-S2 (verano 2023) | Oviedo | corto h1-3 | 531 | 6,0 | 8,5 | 7,3 | -4,8 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2023-S2 (verano 2023) | Oviedo | corto h4-7 | 708 | 6,0 | 8,5 | 7,3 | -4,7 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2023-S2 (verano 2023) | Oviedo | largo (8+) | 177 | 6,3 | 8,5 | 7,3 | -4,0 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2023-S2 (verano 2023) | Ribadesella | corto h1-3 | 531 | 13,5 | 51,5 | 14,1 | -9,2 | 88,1 / 85,3 | 198 | 86,4 / 86,4 | 98,8 / 95,0 |
| 2023-S2 (verano 2023) | Ribadesella | corto h4-7 | 708 | 14,3 | 51,5 | 14,1 | -9,8 | 86,9 / 85,3 | 264 | 83,0 / 86,4 | 97,3 / 95,0 |
| 2023-S2 (verano 2023) | Ribadesella | largo (8+) | 177 | 12,3 | 51,5 | 14,1 | -7,6 | 87,6 / 85,3 | 66 | 84,8 / 86,4 | 98,2 / 95,0 |
| 2024-S1 | Cangas de Onís | corto h1-3 | 537 | 10,6 | 23,8 | 18,3 | -3,3 | 93,5 / 91,6 | 9 | 66,7 / 0,0 | 100,0 / 0,0 |
| 2024-S1 | Cangas de Onís | corto h4-7 | 716 | 10,4 | 23,8 | 18,3 | -3,6 | 95,8 / 91,6 | 12 | 66,7 / 0,0 | 100,0 / 0,0 |
| 2024-S1 | Cangas de Onís | largo (8+) | 179 | 10,3 | 23,8 | 18,3 | -4,0 | 93,3 / 91,6 | 3 | 33,3 / 0,0 | 100,0 / 0,0 |
| 2024-S1 | Gijón | corto h1-3 | 537 | 5,6 | 6,5 | 7,6 | -3,5 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2024-S1 | Gijón | corto h4-7 | 716 | 5,6 | 6,5 | 7,6 | -3,5 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2024-S1 | Gijón | largo (8+) | 179 | 6,8 | 6,5 | 7,6 | -5,3 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2024-S1 | Llanes | corto h1-3 | 537 | 11,0 | 26,6 | 22,7 | -3,2 | 92,7 / 84,4 | 24 | 50,0 / 12,5 | 80,0 / 14,3 |
| 2024-S1 | Llanes | corto h4-7 | 716 | 11,2 | 26,6 | 22,7 | -3,9 | 93,4 / 84,4 | 32 | 53,1 / 12,5 | 100,0 / 14,3 |
| 2024-S1 | Llanes | largo (8+) | 179 | 11,2 | 26,6 | 22,7 | -5,4 | 93,9 / 84,4 | 8 | 50,0 / 12,5 | 100,0 / 14,3 |
| 2024-S1 | Oviedo | corto h1-3 | 537 | 8,2 | 7,3 | 10,2 | -7,6 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2024-S1 | Oviedo | corto h4-7 | 716 | 8,1 | 7,3 | 10,2 | -7,6 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2024-S1 | Oviedo | largo (8+) | 179 | 9,1 | 7,3 | 10,2 | -8,7 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2024-S1 | Ribadesella | corto h1-3 | 537 | 10,4 | 27,4 | 22,4 | -1,2 | 95,7 / 86,6 | 18 | 66,7 / 16,7 | 80,0 / 11,1 |
| 2024-S1 | Ribadesella | corto h4-7 | 716 | 10,1 | 27,4 | 22,4 | -1,9 | 96,4 / 86,6 | 24 | 62,5 / 16,7 | 100,0 / 11,1 |
| 2024-S1 | Ribadesella | largo (8+) | 179 | 10,3 | 27,4 | 22,4 | -1,4 | 96,6 / 86,6 | 6 | 66,7 / 16,7 | 100,0 / 11,1 |
| 2024-S2 (verano 2024) | Cangas de Onís | corto h1-3 | 531 | 14,3 | 42,8 | 14,0 | -13,0 | 85,5 / 81,5 | 135 | 69,6 / 71,1 | 100,0 / 91,4 |
| 2024-S2 (verano 2024) | Cangas de Onís | corto h4-7 | 708 | 15,8 | 42,8 | 14,0 | -14,3 | 81,2 / 81,5 | 180 | 58,9 / 71,1 | 100,0 / 91,4 |
| 2024-S2 (verano 2024) | Cangas de Onís | largo (8+) | 177 | 12,9 | 42,8 | 14,0 | -11,0 | 87,6 / 81,5 | 45 | 75,6 / 71,1 | 100,0 / 91,4 |
| 2024-S2 (verano 2024) | Gijón | corto h1-3 | 531 | 8,7 | 13,6 | 9,4 | -7,3 | 96,0 / 96,5 | 0 | — / — | — / — |
| 2024-S2 (verano 2024) | Gijón | corto h4-7 | 708 | 10,0 | 13,6 | 9,4 | -8,8 | 96,0 / 96,5 | 0 | — / — | — / — |
| 2024-S2 (verano 2024) | Gijón | largo (8+) | 177 | 8,7 | 13,6 | 9,4 | -7,5 | 96,0 / 96,5 | 0 | — / — | — / — |
| 2024-S2 (verano 2024) | Llanes | corto h1-3 | 531 | 12,5 | 51,7 | 14,1 | -8,7 | 90,8 / 87,3 | 198 | 90,4 / 93,8 | 98,4 / 92,4 |
| 2024-S2 (verano 2024) | Llanes | corto h4-7 | 708 | 14,0 | 51,7 | 14,1 | -10,6 | 89,0 / 87,3 | 264 | 86,7 / 93,8 | 98,3 / 92,4 |
| 2024-S2 (verano 2024) | Llanes | largo (8+) | 177 | 11,6 | 51,7 | 14,1 | -6,5 | 89,3 / 87,3 | 66 | 87,9 / 93,8 | 98,3 / 92,4 |
| 2024-S2 (verano 2024) | Oviedo | corto h1-3 | 531 | 9,1 | 9,1 | 10,1 | -7,9 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2024-S2 (verano 2024) | Oviedo | corto h4-7 | 708 | 10,1 | 9,1 | 10,1 | -9,4 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2024-S2 (verano 2024) | Oviedo | largo (8+) | 177 | 9,8 | 9,1 | 10,1 | -9,0 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2024-S2 (verano 2024) | Ribadesella | corto h1-3 | 531 | 14,0 | 53,3 | 14,5 | -12,0 | 91,7 / 86,7 | 198 | 89,4 / 93,9 | 100,0 / 93,9 |
| 2024-S2 (verano 2024) | Ribadesella | corto h4-7 | 708 | 15,7 | 53,3 | 14,5 | -13,7 | 90,0 / 86,7 | 264 | 83,3 / 93,9 | 100,0 / 93,9 |
| 2024-S2 (verano 2024) | Ribadesella | largo (8+) | 177 | 13,6 | 53,3 | 14,5 | -10,9 | 89,8 / 86,7 | 66 | 89,4 / 93,9 | 98,3 / 93,9 |
| 2025-S1 (bloque final) | Cangas de Onís | corto h1-3 | 537 | 10,6 | 23,1 | 18,0 | -6,7 | 94,6 / 90,3 | 12 | 50,0 / 0,0 | 100,0 / 0,0 |
| 2025-S1 (bloque final) | Cangas de Onís | corto h4-7 | 716 | 13,2 | 23,1 | 18,0 | -9,3 | 92,6 / 90,3 | 16 | 50,0 / 0,0 | 100,0 / 0,0 |
| 2025-S1 (bloque final) | Cangas de Onís | largo (8+) | 179 | 12,9 | 23,1 | 18,0 | -9,8 | 94,4 / 90,3 | 4 | 50,0 / 0,0 | 100,0 / 0,0 |
| 2025-S1 (bloque final) | Gijón | corto h1-3 | 537 | 8,2 | 7,8 | 9,6 | -7,6 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2025-S1 (bloque final) | Gijón | corto h4-7 | 716 | 11,1 | 7,8 | 9,6 | -10,4 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2025-S1 (bloque final) | Gijón | largo (8+) | 179 | 11,2 | 7,8 | 9,6 | -10,7 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2025-S1 (bloque final) | Llanes | corto h1-3 | 537 | 10,8 | 27,2 | 21,8 | -5,4 | 89,8 / 82,4 | 36 | 63,9 / 20,0 | 71,9 / 22,2 |
| 2025-S1 (bloque final) | Llanes | corto h4-7 | 716 | 12,5 | 27,2 | 21,8 | -6,9 | 91,1 / 82,4 | 48 | 60,4 / 20,0 | 87,9 / 22,2 |
| 2025-S1 (bloque final) | Llanes | largo (8+) | 179 | 13,6 | 27,2 | 21,8 | -7,9 | 88,8 / 82,4 | 12 | 41,7 / 20,0 | 83,3 / 22,2 |
| 2025-S1 (bloque final) | Oviedo | corto h1-3 | 537 | 6,5 | 4,8 | 7,3 | -5,9 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2025-S1 (bloque final) | Oviedo | corto h4-7 | 716 | 9,5 | 4,8 | 7,3 | -9,2 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2025-S1 (bloque final) | Oviedo | largo (8+) | 179 | 11,5 | 4,8 | 7,3 | -11,1 | 100,0 / 100,0 | 0 | — / — | — / — |
| 2025-S1 (bloque final) | Ribadesella | corto h1-3 | 537 | 15,0 | 26,9 | 25,0 | -12,3 | 87,7 / 79,0 | 48 | 62,5 / 14,3 | 93,8 / 28,6 |
| 2025-S1 (bloque final) | Ribadesella | corto h4-7 | 716 | 16,9 | 26,9 | 25,0 | -13,8 | 86,0 / 79,0 | 64 | 51,6 / 14,3 | 89,2 / 28,6 |
| 2025-S1 (bloque final) | Ribadesella | largo (8+) | 179 | 16,7 | 26,9 | 25,0 | -14,4 | 84,9 / 79,0 | 16 | 37,5 / 14,3 | 85,7 / 28,6 |

## Bloque × modelo (todas las zonas)

| bloque | modelo | WAPE modelo | WAPE B0 | WAPE B1 | sesgo modelo | sesgo B0 | recall rojo modelo / B1 | precisión rojo modelo / B1 |
|---|---|---|---|---|---|---|---|---|
| 2023-S2 (verano 2023) | corto | 7,7 | 16,2 | 8,3 | -5,4 | -11,5 | 79,9 / 86,8 | 90,2 / 91,8 |
| 2023-S2 (verano 2023) | largo | 7,1 | 16,2 | 8,3 | -3,9 | -11,5 | 84,4 / 86,8 | 94,0 / 91,8 |
| 2024-S1 | corto | 7,5 | 9,3 | 10,6 | -5,6 | -4,3 | 58,8 / 11,8 | 92,1 / 10,5 |
| 2024-S1 | largo | 8,4 | 9,3 | 10,6 | -6,9 | -4,3 | 52,9 / 11,8 | 100,0 / 10,5 |
| 2024-S2 (verano 2024) | corto | 10,4 | 17,8 | 10,6 | -9,1 | -13,3 | 81,1 / 88,1 | 99,3 / 92,8 |
| 2024-S2 (verano 2024) | largo | 9,9 | 17,8 | 10,6 | -8,5 | -13,3 | 85,3 / 88,1 | 98,7 / 92,8 |
| 2025-S1 (bloque final) | corto | 9,5 | 8,6 | 9,9 | -8,4 | -3,5 | 57,6 / 15,4 | 87,2 / 21,1 |
| 2025-S1 (bloque final) | largo | 11,7 | 8,6 | 9,9 | -10,8 | -3,5 | 40,6 / 15,4 | 86,7 / 21,1 |

## Factores: media de |SHAP| fuera de muestra (escala log)

| factor | global, largo | global, corto h=1 | Picos, largo | Picos, corto h=1 |
|---|---|---|---|---|
| Vacaciones escolares | 0,126 | 0,060 | 0,145 | 0,067 |
| Época del año | 0,106 | 0,072 | 0,127 | 0,087 |
| Acceso regulado a los Lagos | 0,065 | 0,040 | 0,078 | 0,046 |
| Zona | 0,107 | 0,096 | 0,046 | 0,031 |
| Fin de semana | 0,022 | 0,019 | 0,024 | 0,021 |
| Puente o festivo en Asturias | 0,024 | 0,021 | 0,023 | 0,020 |
| Festivo en origen (Madrid o Castilla y León) | 0,011 | 0,008 | 0,012 | 0,009 |
| Partido | 0,005 | 0,003 | 0,005 | 0,003 |
| Evento | 0,003 | 0,003 | 0,002 | 0,001 |
| Tiempo en el valle | — | 0,016 | — | 0,017 |
| Tiempo en la montaña | — | 0,000 | — | 0,002 |
| Interés en internet | — | 0,111 | — | 0,149 |
| Antelación | — | 0,001 | — | 0,001 |

## Signo de los factores en los Picos (SHAP medio fuera de muestra, en % sobre el día medio del modelo)

| factor | condición | n días | efecto medio con la condición | sin ella |
|---|---|---|---|---|
| Puente o festivo en Asturias | sí | 48 | 1,8 | -0,2 |
| Festivo en origen | sí | 6 | 4,1 | -0,1 |
| Vacaciones escolares | vacaciones escolares de Madrid | 207 | 26,2 | -9,8 |
| Acceso regulado a los Lagos | sí | 357 | 9,6 | -6,2 |

Época del año, Picos, largo plazo (efecto medio por mes, %): 1: -24, 2: -11, 3: -5, 4: -0, 5: 8, 6: 7, 7: 13, 8: 29, 9: 15, 10: 7, 11: -9, 12: -16

Tiempo en el valle, Picos, corto plazo h=1, por lluvia prevista a 1 día (Open-Meteo, `prec_mm_prev1`): < 0,5 mm: 3,0 % (n=310); 0,5-5 mm: 1,6 % (n=113); 5-15 mm: 0,3 % (n=60); > 15 mm: -2,8 % (n=31). Correlación SHAP-lluvia -0.54; SHAP-tmax 0.39.

Interés en internet, global, corto h=1 (efecto medio por año, %): 2023: 7,3, 2024: -1,9, 2025: -7,0. Correlación con «Época del año»: 0.52.

## Cobertura de los intervalos p10-p90 (`metricas.json → fiabilidad`)

| zona | mínima | media | máxima |
|---|---|---|---|
| Cangas de Onís | 75,7 | 76,1 | 77,0 |
| Gijón | 77,1 | 77,8 | 78,9 |
| Llanes | 78,5 | 79,2 | 80,2 |
| Oviedo | 76,8 | 77,8 | 78,5 |
| Ribadesella | 75,7 | 77,5 | 78,5 |
| todas (40 combinaciones zona × horizonte) | 75,7 | 77,7 | 80,2 |

Combinaciones con cobertura ≥ 80 %: 1 de 40.

## Experimentos de sensibilidad (`metricas.json → tablas.global`, solo el modelo)

| experimento | modelo | WAPE | acierto color | recall rojo | precisión rojo |
|---|---|---|---|---|---|
| base | corto | 8,8 | 93,3 | 77,7 | 94,1 |
| base | largo | 9,3 | 93,5 | 79,9 | 96,0 |
| desde_corte | corto | 9,3 | 89,4 | 42,6 | 93,8 |
| desde_corte | largo | 10,1 | 88,7 | 43,5 | 95,0 |
| solo_eventos_verificados | corto | 9,0 | 93,3 | 77,6 | 94,0 |
| solo_eventos_verificados | largo | 9,4 | 93,6 | 79,6 | 96,0 |
| tiempo_aproximado | corto | 8,1 | 93,9 | 81,0 | 93,8 |
