# Registro de descargas AEMET

Fecha de descarga: 2026-10-15. Todas las peticiones llevan la clave en la cabecera `api_key` (no se registra). Base: `https://opendata.aemet.es/opendata`. Última fecha disponible: 2026-10-11.

| Fichero | Fuente / endpoint | Rango real | Registros | Problemas |
|---|---|---|---|---|
| `data/raw/aemet_inventario.json` | AEMET OpenData `/api/valores/climatologicos/inventarioestaciones/todasestaciones` (2 pasos) | n/a | 926 estaciones | Ninguno |
| `data/raw/aemet_diario_1178R.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1178R` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1185 (sin duplicados de fecha) | 404 sin datos en 2022-07-01..2022-12-31, 2023-01-01..2023-06-30 |
| `data/raw/aemet_diario_1179B.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1179B` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1679 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet_diario_1183X.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1183X` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1673 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet_diario_1186P.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1186P` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1741 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet_diario_1199X.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1199X` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1736 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet_diario_1203D.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1203D` (tramos de 6 meses) | 2022-01-01 a 2026-06-04 | 1616 (sin duplicados de fecha) | 404 sin datos en 2026-07-01..2026-10-14 |
| `data/raw/aemet_diario_1207U.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1207U` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1696 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet_diario_1210X.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1210X` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1645 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet_diario_1212E.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1212E` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1745 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet_diario_1249X.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/1249X` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1732 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet_diario_3195.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/3195` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1744 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet_diario_5783.json` | `/api/valores/climatologicos/diarios/datos/fechaini/{ini}/fechafin/{fin}/estacion/5783` (tramos de 6 meses) | 2022-01-01 a 2026-10-11 | 1745 (sin duplicados de fecha) | Ninguno |
| `data/raw/aemet/tramos/*.json` | Mismo endpoint, un fichero por tramo y estación | 2022-01-01 a 2026-10-14 pedido | ver ficheros por estación | Sin datos: ver `data/raw/aemet/estado_tramos.json` |
| `data/raw/aemet_diario_1208.json`, `aemet_diario_1208A.json` | Gijón y Gijón La Merced | n/a | 0 (no se conservan) | 404 «No hay datos que satisfagan esos criterios» en los 10 tramos de cada una |
| `data/raw/aemet_prediccion_ejemplo.json` | `/api/prediccion/especifica/municipio/diaria/33012` y `/33036` (Cangas de Onís y Llanes) | elaborada 2026-10-15, 7 días | 2 municipios | 429 en el primer intento; se resolvió con espera. **La previsión no se archiva en AEMET: sirve para producción, no para entrenar.** |

Notas: el primer lanzamiento de `diarios` se interrumpió al cerrar la tubería de salida (no fue fallo de la API) y se reanudó sin repetir tramos. Hubo un `ConnectionError` puntual y 429 aislados, resueltos con backoff exponencial.
