# Elección de estación AEMET por zona

Generado por `python -X utf8 src/limpieza_B/elige_estaciones.py`. La regla y cómo se aplica están en el docstring del script. La cobertura es el % mínimo de días con tmax y precipitación desde 2022-01-01 hasta 2026-10-11. «activa» = publica hasta la última semana.

| zona_meteo | elegida | motivo |
|---|---|---|
| cangas_de_onis | **1186P** | la más cercana y con mejor cobertura |
| lagos_enol | **1186P** | la más cercana y con mejor cobertura |
| llanes | **1183X** | la más cercana y con mejor cobertura |
| ribadesella | **1183X** | empate (1183X más cercana, 1199X mejor cobertura): preferencia del equipo |
| gijon | **1207U** | empate (1207U más cercana, 1212E mejor cobertura): preferencia del equipo |
| oviedo | **1249X** | empate (1249X más cercana, 1212E mejor cobertura): preferencia del equipo |

Detalle de las candidatas:

| zona_meteo | estacion | nombre | altitud_m | dist_km | cobertura_pct | activa | elegida |
|---|---|---|---|---|---|---|---|
| cangas_de_onis | 1186P | AMIEVA, PANIZALES | 370 | 9.3 | 99.0 | True | True |
| cangas_de_onis | 1179B | CABRALES | 458 | 22.8 | 95.0 | True | False |
| lagos_enol | 1186P | AMIEVA, PANIZALES | 370 | 10.5 | 99.0 | True | True |
| lagos_enol | 1179B | CABRALES | 458 | 12.0 | 95.0 | True | False |
| lagos_enol | 1178R | SOTRES, PARQUE NACIONAL PICOS DE EUROPA | 1236 | 20.8 | 67.5 | True | False |
| llanes | 1183X | LLANES | 10 | 0.2 | 93.9 | True | True |
| ribadesella | 1183X | LLANES | 10 | 25.6 | 93.9 | True | True |
| ribadesella | 1199X | PILOÑA, BARGAÉU | 280 | 28.7 | 98.5 | True | False |
| ribadesella | 1203D | COLUNGA | 30 | 15.5 | 92.4 | False | False |
| gijon | 1207U | GIJÓN, CAMPUS | 26 | 3.2 | 87.4 | True | True |
| gijon | 1212E | ASTURIAS AEROPUERTO | 127 | 31.2 | 99.5 | True | False |
| gijon | 1210X | CABO PEÑAS | 100 | 20.7 | 92.5 | True | False |
| oviedo | 1249X | OVIEDO | 334 | 1.3 | 99.1 | True | True |
| oviedo | 1212E | ASTURIAS AEROPUERTO | 127 | 27.4 | 99.5 | True | False |

Aviso (no cambia la elección): para Ribadesella, 1186P Amieva-Panizales está algo más cerca (22.0 km) que Llanes, pero es una estación de valle de montaña a 370 m. No se ha incluido entre las candidatas de una zona costera.