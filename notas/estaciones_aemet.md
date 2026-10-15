# Estaciones AEMET elegidas

Origen: `data/raw/aemet_inventario.json` (926 estaciones, descargado el 2026-10-15). Distancias en línea recta (haversine) desde coordenadas convertidas de grados-minutos-segundos. Referencias: Cangas de Onís 43.348N -5.127E, Covadonga 43.307N -5.056E, Lagos 43.270N -4.993E (del maestro de municipios para Cangas; Covadonga y Lagos aproximados). Última fecha disponible en todas las estaciones: **2026-10-11** (retraso de ~4 días).

## Zona Picos de Europa

| Indicativo | Nombre | Alt. (m) | Dist. Cangas / Covadonga / Lagos (km) | Días con dato (2022-01-01..2026-10-11) | Observaciones |
|---|---|---|---|---|---|
| **1186P** | Amieva, Panizales | 370 | 9 / 7 / 10 | 1741 de 1745 | **Recomendada.** Sin huecos >7 días, 99-100 % en temperatura, lluvia y viento. Sin sol. |
| 1179B | Cabrales | 458 | 23 / 16 / 12 | 1679 | Alternativa para Lagos y el lado este. Huecos de 12 y 8 días. Sin sol. |
| 1178R | Sotres, Parque Nacional Picos de Europa | 1236 | 34 / 27 / 21 | 1185 | Alta montaña, útil como contraste. **Hueco de 537 días** (2022-01-16 a 2023-07-06) y otro de 18 (2024-03-02 a 2024-03-19). |
| 1199X | Piloña, Bargañu | 280 | 22 / 29 / 35 | 1736 | Series completas, pero más lejos y hacia el interior. |
| 1203D | Colunga | 30 | 18 / 26 / 32 | 1616 | **Termina el 2026-06-04** (sin datos en el último tramo). Costa, no sirve para el presente. |

Elección de las dos candidatas: Amieva-Panizales es la más cercana a Cangas, Covadonga y Lagos y además la de series más completas. Cabrales queda como respaldo. Cangas de Onís no tiene estación propia en el inventario.

## Otras zonas de Asturias

| Indicativo | Nombre | Alt. (m) | Días con dato | Observaciones |
|---|---|---|---|---|
| 1212E | Asturias Aeropuerto | 127 | 1745 de 1745 | Indicativo correcto. Serie completa, incluye sol. |
| 1249X | Oviedo | 334 | 1732 | Indicativo correcto. Hueco de 11 días (2023-10-05 a 2023-10-15). Viento, racha y sol al 90-92 %. (`1249I` es otra estación de Oviedo, no descargada.) |
| 1183X | Llanes | 10 | 1673 | Indicativo correcto. Hueco de 11 días (2023-08-11 a 2023-08-21). Incluye sol. |
| 1207U | Gijón, Campus | 26 | 1696 | Temperatura y racha 90 %, lluvia 81 %, sin huecos largos. |
| 1210X | Cabo Peñas | 100 | 1645 | Huecos de 28 días (2024-08-16 a 2024-09-12) y 21 días (2026-04-07 a 2026-04-27). |

Sin conseguir:
- **Gijón `1208`**: 404 «No hay datos que satisfagan esos criterios» en los 10 tramos. Descartada (consta en `data/raw/aemet/estado_tramos.json`).
- **Gijón, La Merced `1208A`**: igual, 10 tramos con 404. Descartada.
- **Ribadesella**: no existe estación en el inventario. Las más cercanas son Colunga (1203D, cortada en junio de 2026), Piloña (1199X) y Llanes (1183X).

## Ciudades de origen

| Indicativo | Nombre | Días con dato | Observaciones |
|---|---|---|---|
| 3195 | Madrid, Retiro | 1744 | Estación principal. Sin huecos largos, 94 % por variable. (`3129` Aeropuerto y `3196` Cuatro Vientos no descargadas.) |
| 5783 | Sevilla Aeropuerto | 1745 | Serie completa. (`5790Y` Tablada no descargada.) |

## Sobre la variable `sol`

Solo 1212E, 1183X, 1249X, 1207U y 5783 registran horas de sol. En la estación recomendada para Picos (1186P) está vacía. Si el modelo necesita insolación habrá que usar Asturias Aeropuerto o Llanes como aproximación, o prescindir de ella.
