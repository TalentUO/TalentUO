# Registro de descargas: señales adelantadas

Una línea por fichero. Fechas de descarga en UTC. Rango real = primer y último día con registro.

| Fichero | Fuente / endpoint | Parámetros | Descargado | Rango real | Registros | Problemas |
|---|---|---|---|---|---|---|
| wikipedia_cabrales.json | Wikimedia REST pageviews, `es.wikipedia/Cabrales` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_cangas_de_onis.json | Wikimedia REST pageviews, `es.wikipedia/Cangas de Onís` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_covadonga.json | Wikimedia REST pageviews, `es.wikipedia/Covadonga` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_covadonga_en.json | Wikimedia REST pageviews, `en.wikipedia/Covadonga` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_covadonga_fr.json | Wikimedia REST pageviews, `fr.wikipedia/Covadonga` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1118 | faltan 630 días (omitidos por la API); 405 días con views=0 explícito |
| wikipedia_descenso_internacional_del_sella.json | Wikimedia REST pageviews, `es.wikipedia/Descenso Internacional del Sella` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | 1 días con views=0 explícito |
| wikipedia_fuente_de.json | Wikimedia REST pageviews, `es.wikipedia/Fuente Dé` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_gijon.json | Wikimedia REST pageviews, `es.wikipedia/Gijón` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_lagos_de_covadonga.json | Wikimedia REST pageviews, `es.wikipedia/Lagos de Covadonga` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_llanes.json | Wikimedia REST pageviews, `es.wikipedia/Llanes` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_oviedo.json | Wikimedia REST pageviews, `es.wikipedia/Oviedo` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_parque_nacional_de_los_picos_de_europa.json | Wikimedia REST pageviews, `es.wikipedia/Parque nacional de los Picos de Europa` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1747 | faltan 1 días (omitidos por la API); 7 días con views=0 explícito |
| wikipedia_picos_de_europa.json | Wikimedia REST pageviews, `es.wikipedia/Picos de Europa` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_picos_de_europa_en.json | Wikimedia REST pageviews, `en.wikipedia/Picos de Europa` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_picos_de_europa_national_park_en.json | Wikimedia REST pageviews, `en.wikipedia/Picos de Europa National Park` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_pics_d_europe_fr.json | Wikimedia REST pageviews, `fr.wikipedia/Pics d'Europe` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_potes.json | Wikimedia REST pageviews, `es.wikipedia/Potes` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_ribadesella.json | Wikimedia REST pageviews, `es.wikipedia/Ribadesella` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_ruta_del_cares.json | Wikimedia REST pageviews, `es.wikipedia/Ruta del Cares` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_santa_cueva_de_covadonga.json | Wikimedia REST pageviews, `es.wikipedia/Santa Cueva de Covadonga` | all-access, agent=user, daily, 20220101–20261014 | 2026-10-15 | 20220101–20261014 | 1748 | ninguno |
| wikipedia_sonda_dias_ausentes.json | Wikimedia REST pageviews (sonda) | 5 casos, ver notas | 2026-10-15 | n/a | 5 consultas | solo diagnóstico del comportamiento de días ausentes |
| trends/trends_semanal_cangas_de_onis_ES-MD.json | Google Trends vía pytrends (no oficial) | kw=['picos de europa', 'cangas de onís'], geo=ES-MD, 2022-01-01 2026-10-15, semanal | 2026-10-15 | 2021-12-26–2026-10-11 | 251 | índice relativo 0-100 por consulta; última fila isPartial=True |
| trends/trends_semanal_cangas_de_onis_ES.json | Google Trends vía pytrends (no oficial) | kw=['picos de europa', 'cangas de onís'], geo=ES, 2022-01-01 2026-10-15, semanal | 2026-10-15 | 2021-12-26–2026-10-11 | 251 | índice relativo 0-100 por consulta; última fila isPartial=True |
| trends/trends_semanal_covadonga_ES.json | Google Trends vía pytrends (no oficial) | kw=['picos de europa', 'covadonga'], geo=ES, 2022-01-01 2026-10-15, semanal | 2026-10-15 | 2021-12-26–2026-10-11 | 251 | índice relativo 0-100 por consulta; última fila isPartial=True |
| trends/trends_semanal_lagos_de_covadonga_ES-MD.json | Google Trends vía pytrends (no oficial) | kw=['picos de europa', 'lagos de covadonga'], geo=ES-MD, 2022-01-01 2026-10-15, semanal | 2026-10-15 | 2021-12-26–2026-10-11 | 251 | índice relativo 0-100 por consulta; última fila isPartial=True |
| trends/trends_semanal_lagos_de_covadonga_ES.json | Google Trends vía pytrends (no oficial) | kw=['picos de europa', 'lagos de covadonga'], geo=ES, 2022-01-01 2026-10-15, semanal | 2026-10-15 | 2021-12-26–2026-10-11 | 251 | índice relativo 0-100 por consulta; última fila isPartial=True |
| trends/trends_semanal_llanes_ES-MD.json | Google Trends vía pytrends (no oficial) | kw=['picos de europa', 'llanes'], geo=ES-MD, 2022-01-01 2026-10-15, semanal | 2026-10-15 | 2021-12-26–2026-10-11 | 251 | índice relativo 0-100 por consulta; última fila isPartial=True |
| trends/trends_semanal_llanes_ES.json | Google Trends vía pytrends (no oficial) | kw=['picos de europa', 'llanes'], geo=ES, 2022-01-01 2026-10-15, semanal | 2026-10-15 | 2021-12-26–2026-10-11 | 251 | índice relativo 0-100 por consulta; última fila isPartial=True |
| trends/trends_semanal_ruta_del_cares_ES-MD.json | Google Trends vía pytrends (no oficial) | kw=['picos de europa', 'ruta del cares'], geo=ES-MD, 2022-01-01 2026-10-15, semanal | 2026-10-15 | 2021-12-26–2026-10-11 | 251 | índice relativo 0-100 por consulta; última fila isPartial=True |
| trends/trends_semanal_ruta_del_cares_ES.json | Google Trends vía pytrends (no oficial) | kw=['picos de europa', 'ruta del cares'], geo=ES, 2022-01-01 2026-10-15, semanal | 2026-10-15 | 2021-12-26–2026-10-11 | 251 | índice relativo 0-100 por consulta; última fila isPartial=True |
| oapn/oapn_memoria_red_2018.pdf | miteco.gob.es (OAPN), URL en `OAPN_PDFS` de src/descarga_senales.py | descarga directa | 2026-10-15 | n/a | 17067 KB | texto extraíble (ver notas) |
| oapn/oapn_memoria_red_2019.pdf | miteco.gob.es (OAPN), URL en `OAPN_PDFS` de src/descarga_senales.py | descarga directa | 2026-10-15 | n/a | 4986 KB | texto extraíble (ver notas) |
| oapn/oapn_memoria_red_2020.pdf | miteco.gob.es (OAPN), URL en `OAPN_PDFS` de src/descarga_senales.py | descarga directa | 2026-10-15 | n/a | 4266 KB | texto extraíble (ver notas) |
| oapn/oapn_memoria_red_2021.pdf | miteco.gob.es (OAPN), URL en `OAPN_PDFS` de src/descarga_senales.py | descarga directa | 2026-10-15 | n/a | 6610 KB | texto extraíble (ver notas) |
| oapn/oapn_visitantes_2022.pdf | miteco.gob.es (OAPN), URL en `OAPN_PDFS` de src/descarga_senales.py | descarga directa | 2026-10-15 | n/a | 867 KB | texto extraíble (ver notas) |
| oapn/oapn_visitantes_2023.pdf | miteco.gob.es (OAPN), URL en `OAPN_PDFS` de src/descarga_senales.py | descarga directa | 2026-10-15 | n/a | 869 KB | texto extraíble (ver notas) |
| oapn/oapn_visitantes_2024.pdf | miteco.gob.es (OAPN), URL en `OAPN_PDFS` de src/descarga_senales.py | descarga directa | 2026-10-15 | n/a | 1248 KB | texto extraíble (ver notas) |
| oapn/oapn_visitantes_2025.pdf | miteco.gob.es (OAPN), URL en `OAPN_PDFS` de src/descarga_senales.py | descarga directa | 2026-10-15 | n/a | 2332 KB | texto extraíble (ver notas) |
