# Notas del proyecto

Índice de la documentación. **Vigente** = describe el estado actual del repositorio (46 zonas, XGBoost). **Histórico** = registro de trabajo de una fase ya superada: se conserva por trazabilidad y lleva un aviso arriba.

La visión general, los resultados y la instalación están en `README.md` (raíz). La web, en `README_web.md` y `Afluencia Asturias/README.md`. Las fuentes y sus licencias, en `FUENTES_Y_LICENCIAS.md`.

## Modelo y contratos (vigente)

| Documento | Contenido |
|---|---|
| `modelo.md` | Qué predice, variables, prueba anti-fuga, validación por bloques, regla de elección LightGBM/XGBoost (con la tabla que regenera `src/modelo/comparacion.py`), limitaciones y decisiones del equipo |
| `ampliacion_zonas.md` | Paso de 5 a 46 zonas, arreglo de la parada temprana y comparación 5 frente a 46 zonas |
| `contrato_objetivo.md` | Formato de `data/clean/objetivo_diario.parquet` (entrada del modelo) |
| `contrato_web.md` | Formato de los JSON de `salidas/` que lee la web |
| `guion_modelo.md` | El modelo en un minuto, para el jurado |

## Factores explicativos, parte B (vigente)

| Documento | Contenido |
|---|---|
| `diccionario_B.md` | Diccionario de las tablas limpias de `data/clean/` y de la unión por zona |
| `control_calidad_B.md` | Control de calidad (generado por `src/limpieza_B/control_calidad.py`); figuras en `figuras_qc/` |

## Fuentes de datos: registros y decisiones (`fuentes/`, vigente)

| Carpeta | Documentos |
|---|---|
| `fuentes/mitma/` | `descarga_mitma.md` (cómo regenerar la descarga), `registro_mitma.md` (resultado de la descarga), `cobertura_mitma.md` (filas y días por mes; generado), `mitma_referencia_filas_por_dia.csv` (filas por día y tipo, para comparar descargas) |
| `fuentes/demanda/` | `registro_descargas.md` (MITMA zonas, INE, SADEI, COGERSA), `decisiones_demanda.md` (decisiones y límites de esas descargas) |
| `fuentes/aemet/` | `registro_aemet.md`, `decisiones_aemet.md`, `estaciones_aemet.md`, `eleccion_estaciones.md` (generado), `huecos_aemet.md` (generado), `cobertura_aemet.md` (generado) |
| `fuentes/openmeteo/` | `registro_openmeteo.md` (incluye condiciones de uso), `openmeteo_tramo_2022.md` (el tramo de 2022 es reanálisis, no previsión) |
| `fuentes/calendarios/` | `registro_calendarios.md`, `inventario_calendarios.md`, `decisiones_calendarios.md`, `validacion_calendario.md` |
| `fuentes/eventos/` | `registro_eventos.md`, `eventos_fuentes.md`, `decisiones_eventos.md`, `solicitud_cruceros.md` |
| `fuentes/senales/` | `registro_senales.md`, `notas_senales.md`, `decisiones_senales.md` (Wikipedia, Google Trends, OAPN) |

Los registros y las decisiones se escribieron durante la descarga (2026-10-15). Algunas «decisiones pendientes» se resolvieron después: la resolución final está en `diccionario_B.md` y `modelo.md`.

## Capturas

| Carpeta | Contenido |
|---|---|
| `capturas_demo/` | Recorrido de la demo a 1366×768 y 1920×1080: Inicio, mapa, «¿Por qué?», alternativa, Sobre los datos, eventos y Funciones avanzadas |
| `historico/capturas/` | Capturas de versiones anteriores de la pestaña de gestión (comarcas, panel de los Lagos, «Gestión») |

## Histórico (`historico/`)

| Documento | Qué fue |
|---|---|
| `historico/guia_inicial_datos_movilidad.md` | Guía de tareas inicial para descargar los datos de demanda (MITMA, INE, SADEI) |
| `historico/auditoria_fase_B.md` | Auditoría de la descarga en bruto de los factores (2026-10-15) |
| `historico/correcciones_fase_B.md` | Correcciones tras esa auditoría |
| `historico/estado_resultados.md` | Estado de partida antes de entrenar con datos reales (5 zonas) |
| `historico/resultados_reales.md` | Resultados de la primera ejecución real: **5 zonas, LightGBM** |
| `historico/revision_objetivo.md` | Revisión rápida del objetivo de 5 zonas, con `figuras_objetivo/` |
| `historico/integracion_web.md` | Comprobación de la web con la primera ejecución real (5 zonas) |
| `historico/coordinacion_web.md` | Coordinación entre los dos responsables de la web |
