# Decisiones y consideraciones: señales adelantadas

Estado a 2026-10-15 (fase 1, descarga en bruto). Detalle de cada fuente en `notas/fuentes/senales/notas_senales.md`; ficheros en `notas/fuentes/senales/registro_senales.md`. Las señales son contexto, no la base del modelo.

## Decisiones tomadas
1. **Wikipedia, 20 ficheros:** 15 artículos es + 3 en + 2 fr, `agent=user`, `all-access`, diario, 2022-01-01 a 2026-10-14. Se usa siempre el título final tras redirección (`Santa Cueva de Covadonga`, `Pics d'Europe`).
2. **Formato de los JSON de Wikipedia/Trends:** `{"meta": {...}, "respuesta": <tal cual de la API>}`. El envoltorio `meta` solo guarda parámetros y fecha de descarga; los valores no se tocan.
3. **Trends con pytrends (no oficial), ritmo 60 s.** Paramos al recibir el 429 y no se esquiva. Lo que falta se exporta a mano a `data/raw/trends/`.
4. **OAPN:** se guardan los informes de visitantes 2022-2025 y las memorias de la Red 2018-2021. La serie 2015-2021 de Picos sale de la tabla de la memoria 2021 (p. 129).

## Decisiones pendientes (antes de limpiar)
1. **Ancla de Trends.** "picos de europa" tiene un pico único de 100 (semana del 2023-09-17) y mediana 3, así que aplasta los demás términos a valores enteros de 0 a 4 (cangas de onís, ruta del cares). Propuesta: ancla "covadonga" o "lagos de covadonga" y repetir las consultas. Las 9 descargas actuales no sirven para reescalar.
2. **Día ausente en Wikipedia = 0 o dato perdido.** La API omite días sin registro y además devuelve algunos `views: 0` explícitos (no sabemos por qué conviven). Hipótesis: ausente = 0. Afecta a `covadonga_fr` (630 omitidos, 405 ceros), `parque_nacional_..._europa` (1 omitido, 7 ceros) y `descenso_internacional_del_sella` (1 cero). Hay que reindexar a calendario completo.
3. **Pico anómalo en `picos_de_europa` (es):** máx. 61.525 visitas/día frente a mín. 55. Causa no verificada; decidir si se filtra o se acota.
4. **Datos mensuales del OAPN:** solo existen como gráficos de porcentaje; los brutos se piden a `seguimiento@oapn.es`. Decidir si se piden o se usa solo la serie anual.
5. **Cuántos artículos de Wikipedia entran como señal** y cuáles sirven de indicador extranjero (en/fr).

## Consideraciones importantes
- **Trends es relativo (0-100 por consulta)**, la muestra cambia entre descargas y la granularidad diaria solo existe en ventanas cortas (límite exacto sin verificar). Para encadenar ventanas diarias hacen falta solapes y un término común, y no se reescala hasta limpiar.
- **Trends pendiente:** ES-MD "covadonga", ES-CL, ES-AS y todas las ventanas diarias (instrucciones de exportación en `notas/fuentes/senales/notas_senales.md`, sección 2).
- **Cifras OAPN no comparables entre parques:** mezclan conteos directos y estimaciones modeladas con metodología propia de cada parque (vía SIR). Sirven para el nivel anual de Picos, no para la dinámica diaria.
- **Referencia previa verificada:** 2022 = 1.798.533, 2023 = 1.698.780, 2024 = 1.632.805; coinciden con el documento oficial. 2025 = 1.565.899.
- **Sin cifras por punto de acceso (Lagos, centros de visitantes)** en lo revisado; la búsqueda no fue exhaustiva.
- **Visitas a una redirección no se suman al destino** (comportamiento general; no medido aquí). Por eso se usan los títulos finales.
- **No verificado en documentación oficial:** límites de peticiones de la API de Wikimedia, definición exacta de `user`, límite diario de Trends y por qué conviven ceros y días omitidos.
- **Dependencias nuevas** (instaladas con pip, no añadidas a `requirements.txt`): `pytrends`, `pypdf`.
- **Orden de utilidad como indicador adelantado:** Wikipedia (diaria, completa) > Trends (si se completa con ancla mejor) > OAPN (calibración anual).
