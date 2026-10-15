# Integración de los datos reales en la web

Fecha: 2026-10-16. Rama: `web-datos-reales` (desde `origin/web` 6fba3b5).

## Paso 0: estado en GitHub

Copia de trabajo limpia al empezar (rama `web`, al día con `origin/web`). `git fetch --all` hecho.

| Rama remota | Último commit |
|---|---|
| `main` | e5a3455 Web: datos del modelo con resultados reales (sintetico=false, previsión del 2026-10-16) |
| `resultados-reales` | ae7ea0d Resultados reales: guion con cifras reales, modelo.md y README actualizados |
| `web` | 6fba3b5 Web: revisión de usabilidad |
| `web-gestion` | bd39e83 Merge remote-tracking branch 'origin/web' into web-gestion |
| `web-frontend` | b0aba54 Web: añade el piloto de interfaz (frontend) con datos ficticios |
| `modelo` | a19b727 Fusiona main (PR #1 y #2, parte A) en modelo |
| `fase-A-objetivo` | e99268d Parte A: objetivo real (MITMA) y tabla horaria para la web |
| `fase-B-limpieza` | a74db11 Limpieza de la parte B |
| `calendarios` | de48238 Open-Meteo: descarga completa |
| `paso1-zonas-mitma` | bcf92a2 MITMA: documenta viajes 2024 y 2025 |

### `origin/resultados-reales`

- Están todos los ficheros pedidos: `salidas/{predicciones,alternativas,regulacion,perfil,metricas}.json`, `data/clean/llegadas_por_hora.parquet`, `config/mapeo_zonas.csv`, `notas/resultados_reales.md` y `notas/contrato_web.md`.
- Los cinco JSON de la web tienen `sintetico=false` en la raíz y en todos los registros, `aviso=null` y `generado=2026-10-16 01:36`. `src/modelo/validar_salidas.py`: «Contrato OK».
- **Dos JSON de `salidas/` sí tienen `sintetico=true`**: `sintetico_efectos_reales.json` y `sintetico_recuperacion_factores.json`. Son el experimento de recuperación de factores con datos inventados (sirve para validar el modelo). No forman parte del contrato de la web y **no se han traído** a esta rama.
- Mapeo real: 5 zonas, `zona_mitma_id` = código INE del concejo (33012 Cangas de Onís con Covadonga y Lagos [principal], 33036 Llanes, 33056 Ribadesella, 33024 Gijón, 33044 Oviedo). Coinciden con `predicciones.json → zonas`. Cada concejo está en una sola zona.

### `web-gestion`

- Ya integrada en `web`: `notas/coordinacion_web.md` dice «web-gestion lista — commit edcf286» y «integrada en web por avance rápido (fc6ebb5)». `git log` lo confirma.
- Después hay un único commit de su autor que no está en `web`: eb7cf76 «Gestión y Sobre los datos: README de las pestañas» (solo añade `Afluencia Asturias/pestanas/README.md`, sin código). **No se ha integrado** (es posterior al «lista»). Pendiente de confirmar.

### `origin/main`

- `main` ya integra `resultados-reales` (3b68d4d) y tiene un commit e5a3455 que ejecutó `actualizar_datos_web.py` con los datos reales. `web` es antecesora de `main`; `web-gestion` no.
- Esta rama no sale de `main`: sale de `web`, como se pidió. Los ficheros de datos generados aquí son idénticos byte a byte a los de `origin/main` (comprobado con `git diff --quiet`).

## Paso 1: rama de integración

- `web-datos-reales` creada desde `origin/web`.
- Traídos de `origin/resultados-reales` (sin código del modelo, sin conflictos): los cinco JSON de `salidas/`, `data/clean/llegadas_por_hora.parquet` y `config/mapeo_zonas.csv`.
- `python -X utf8 scripts/actualizar_datos_web.py`: «Copiados 5 JSON… Mapeo de zonas: config/mapeo_zonas.csv (5 zonas)… sintetico = {False} generado = 2026-10-16 01:36 fecha_hoy = 2026-10-16». Ha regenerado `datos/modelo/*.json`, `mapeo_zonas.json`, `salidas.js` y `salidas-inicio.js`.
- El script no exporta `llegadas_por_hora.parquet` (ver paso 2, patrón horario).
