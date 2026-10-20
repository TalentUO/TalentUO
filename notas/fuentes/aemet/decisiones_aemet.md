# AEMET: decisiones, límites y pendientes antes de limpiar

Fase 1 (descarga en bruto), 2026-10-15. Complementa `notas/fuentes/aemet/estaciones_aemet.md`, `notas/fuentes/aemet/cobertura_aemet.md` y `notas/fuentes/aemet/registro_aemet.md`. No se ha limpiado ni transformado nada.

## Decisiones tomadas durante la descarga

1. **Se descargaron 12 estaciones**, más de las tres fijas del enunciado (1212E, 1249X, 1183X), para poder comparar candidatas cercanas a Cangas de Onís por completitud de la serie: 1186P, 1179B, 1178R, 1199X y 1203D. Se añadieron además Gijón Campus (1207U), Cabo Peñas (1210X), Madrid Retiro (3195) y Sevilla Aeropuerto (5783).
2. **Estación recomendada para Cangas de Onís / Picos: 1186P Amieva-Panizales** (7 km de Covadonga, 9 de Cangas, 10 de Lagos; 1741 de 1745 días, sin huecos de más de 7 días). Respaldo para Lagos y el lado este: 1179B Cabrales.
3. **Gijón `1208` y Gijón La Merced `1208A` se quitaron de `ESTACIONES`** en `src/descarga_aemet.py` porque devuelven 404 («No hay datos que satisfagan esos criterios») en los 10 tramos. Se sustituyeron por `1207U`. Por tanto, el script ya no reproduce esos intentos: solo quedan documentados en `data/raw/aemet/estado_tramos.json`, en `notas/fuentes/aemet/estaciones_aemet.md` y en `notas/fuentes/aemet/registro_aemet.md`. Si se quiere reintentar alguna vez, hay que volver a añadirlas al diccionario.
4. **Tramos de 6 meses naturales** (ene-jun y jul-dic), el último hasta ayer (2026-10-14). La última fecha con dato real es 2026-10-11 (~4 días de retraso).
5. **Pausa de 2 s entre peticiones** con backoff exponencial ante 429, 5xx y errores de red. Aparecieron 429 y un `ConnectionError` aislados, resueltos con espera. No se ha medido el límite real de peticiones por minuto.
6. **Códigos de previsión**: Cangas de Onís `33012` (incluye Covadonga y Lagos) y Llanes `33036`, tomados del maestro `/api/maestro/municipios`. Los códigos que se habían supuesto al principio (33016 y 33034) eran incorrectos y se corrigieron antes de guardar el ejemplo.

## Limitaciones de lo entregado

- **«Tal cual» se cumple en los valores, no en los bytes.** Los ficheros están decodificados (UTF-8, con latin-1 de reserva) y vueltos a serializar con sangría de 1 espacio. Ningún valor se ha cambiado.
- **Distancias aproximadas**: las coordenadas de Cangas vienen del maestro de municipios; las de Covadonga y Lagos son aproximadas (estimadas a mano), no oficiales. No altera la recomendación de 1186P, que está claramente más cerca, pero las cifras exactas no son oficiales.
- **Cangas de Onís no tiene estación propia** en el inventario, y **Ribadesella tampoco**.
- **`notas/fuentes/aemet/cobertura_aemet.md` solo se revisó al principio** (cabecera y primeros meses). La tabla completa se generó por script y no se leyó entera.
- **La previsión no se archiva en AEMET**: sirve para la app en producción, no para entrenar.

## Datos con problemas conocidos

| Estación | Problema |
|---|---|
| 1178R Sotres | Hueco de 537 días (2022-01-16 a 2023-07-06) y otro de 18 (2024-03-02 a 2024-03-19). 1185 días de 1745 |
| 1203D Colunga | La serie termina el 2026-06-04 (404 en el último tramo) |
| 1210X Cabo Peñas | Huecos de 28 días (2024-08-16 a 2024-09-12) y 21 (2026-04-07 a 2026-04-27) |
| 1207U Gijón Campus | Temperatura y racha al 90 %, precipitación al 81 % |
| 1249X Oviedo | Hueco de 11 días (2023-10-05 a 2023-10-15); viento, racha y sol al 90-92 % |
| 1183X Llanes | Hueco de 11 días (2023-08-11 a 2023-08-21) |
| 1179B Cabrales | Huecos de 12 días (2024-07-12 a 2024-07-23) y 8 (2025-08-01 a 2025-08-08) |
| 1208 y 1208A Gijón | Sin ningún dato (404 en todos los tramos) |

**Horas de sol (`sol`)**: solo 1212E, 1183X, 1249X, 1207U y 5783 la registran. En 1186P (la estación recomendada) está vacía, igual que en Madrid Retiro y el resto de las de Picos.

## Formato de los valores (comprobado en los ficheros)

- Todo viene como **texto**, con **coma decimal** (por ejemplo `"20,4"`, `"0,0"`); las fechas son `AAAA-MM-DD` y las horas `HH:MM`.
- **`Ip` (precipitación inapreciable)** aparece solo en cuatro estaciones: 1207U (51 días), 1212E (122), 1249X (72) y 5783 (86). En las demás no hay valores no numéricos en `tmax`, `tmin`, `tmed`, `prec`, `velmedia`, `racha` ni `sol`.
- En `notas/fuentes/aemet/cobertura_aemet.md` un día con `Ip` cuenta como día con dato.
- Campos presentes además de los analizados: `dir`, `hrMedia`, `hrMax`, `hrMin`, `pintMax` y sus horas.

## Decisiones pendientes antes de limpiar

1. Confirmar 1186P como estación principal de Picos y decidir de dónde sacar la insolación (Aeropuerto o Llanes como aproximación, o prescindir de ella).
2. Cómo convertir `Ip` a número (por ejemplo 0, o un valor pequeño).
3. Cómo tratar los huecos: Sotres, Cabo Peñas, Gijón Campus y los huecos cortos de Oviedo, Llanes y Cabrales (dejar vacíos, interpolar o completar con una estación vecina).
4. Qué hacer con Colunga, cuya serie termina en junio de 2026.
5. Si se descargan estaciones no incluidas (`1249I` Oviedo, `3129` Madrid Aeropuerto, `5790Y` Sevilla Tablada) o se mantiene la lista actual.

## Seguridad de la clave

- La clave se lee solo de la variable de entorno `AEMET_API_KEY` y se envía en la cabecera `api_key`. No está en ningún fichero del repo (comprobado con `grep` del valor, excluyendo `.venv` y `.git`).
- `.gitignore` ahora cubre `.env` y `.env.*`, que antes no estaban.
