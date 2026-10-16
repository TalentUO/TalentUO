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
- El script no exportaba `llegadas_por_hora.parquet`; ahora sí (ver paso 2, patrón horario).

## Paso 2: cada funcionalidad con datos reales

Web arrancada con `python scripts/servir_web.py` (http://127.0.0.1:8000/). Cotejo automático en la página: la capa de datos de Inicio (`window.FuenteDatos`) frente a los JSON en bruto.

### Generales
- **Aviso «DATOS SINTÉTICOS»: desaparecido.** El elemento `#aviso-sintetico` queda `hidden` (`sintetico=false` en los cinco JSON). El CSV exportado tampoco lleva la marca.

### Inicio
| Funcionalidad | Estado | Cifra comprobada | Fuente |
|---|---|---|---|
| Mapa | Funciona | 5 zonas coloreadas con su nivel (33012, 33036, 33056, 33024, 33044); 73 concejos `sin-zona` («Sin previsión», gris liso); 78 en total | `predicciones.json → zonas`, `config/mapeo_zonas.csv` |
| Selector de fecha | Funciona | «Hoy» = 17 oct; «Este finde» 17-18 oct; «Próximos 7 días» 17-23 oct (meteorología hasta el 20); «Próximo puente» 31 oct-2 nov (Todos los Santos); flechas hasta el 15 dic (60 días) y se bloquean al final; barra de 14 días (`DIAS_BARRA`, diseño) | `predicciones.json` (`futuro_corto` 17-23 oct, `futuro_largo` 17 oct-15 dic), `calendario_diario.parquet` |
| «+X % sobre un día normal» | Funciona | 300 de 300 fecha × zona: mismo color y cociente que el JSON (prioridad `futuro_corto` > `futuro_largo`) | `predicciones.json` (`cociente`, `pct_sobre_normal`) |
| Ranking de las 5 zonas | Correcto | 17 oct: Cangas de Onís +21 %, Ribadesella +20 %, Llanes +17 %, Gijón +3 %, Oviedo −7 % (con 5 zonas, el ranking son todas) | `predicciones.json` (`futuro_corto`, h=1) |
| Panel: barras de los próximos días | Funciona | 14 días desde la fecha elegida, día normal y rango probable | `predicciones.json` |
| Panel: «¿por qué?» | Funciona | 17 oct, Picos: Interés en internet +15 %, Vacaciones escolares −4 %, Fin de semana −4 % | `predicciones.json → factores` |
| Panel: mejor día y zonas cercanas | Funciona | Único día en alerta de los 60: Llanes, 2 nov (ámbar, cociente 1,5445): mejor día 5 nov (verde, −35 % de visitantes); zona alternativa Cangas de Onís (32 km, verde) | `alternativas.json` |
| Panel: quién viene | Funciona | Picos, octubre: 61 % de Asturias, 39 % del resto de España, 72 % de un día (aprox.) | `perfil.json` (mes 10) |
| Panel: fiabilidad | Funciona | Picos, h=1: «Acierta el color en el 90 % de los días; detecta 7 de cada 10 días rojos.» | `metricas.json → fiabilidad[].nota` |
| Corto plazo con el tiempo real | Funciona | Previsión de Open-Meteo emitida el 2026-10-16, 6 puntos sin huecos; el tiempo solo a 1-3 días (hasta el 20 oct) | `predicciones.json → info_corto_plazo` |

Panel de los Picos el 17 oct: «Unos 8.655 visitantes, probablemente entre 7.725 y 10.741. Un día normal vienen unos 7.169.» (= `prediccion`, `p10`, `p90`, `normal`).

### Gestión
| Funcionalidad | Estado | Cifra comprobada (Picos, 33012) | Fuente |
|---|---|---|---|
| ¿Hace falta regular? | Funciona | +50 %: 2023 82 · 2024 90 · 2026 84 (63–131) · 2027 78 (56–126). +100 %: 39 · 48 · 36 (29–66) · 34 (28–61). Recalcula al mover el umbral (rejilla 1,2-3,0) | `regulacion.json → por_zona[].anios`, `curva_umbral` |
| Comparación con los Lagos | Funciona | Días regulados 172 / 180 / 185 / 185 (supuesto); alertas en días regulados 79+3 fuera, 88+2, 83+1, 74+4; saturación 38+1, 47+1, 36+0, 34+0. Mejor umbral +10 % (precisión 89 %, cobertura 84 %) | `regulacion.json → lagos` |
| Fiabilidad | Funciona **por antelación** | 1-3 días 89 %, 4-7 días 88 %, 8+ días 90 % de acierto de color; «A 8 días o más detecta 65 de 87 días de saturación reales» | `metricas.json → fiabilidad` |
| Fiabilidad por bloque frente al día normal | **No existe en la web** | Los datos están (`metricas.json → tablas.bloque`, `metodo` B0/B1), pero ninguna pestaña los enseña | — |
| Calendario de alertas con acciones | Funciona | 28 días desde `fecha_hoy` (16 oct). «Solo saturación»: ninguna. «Alta y saturación»: Llanes, 2 nov, +54 %, incierta, «Aviso al público y refuerzo del transporte.» | `predicciones.json` + `regulacion.json → calendario_alertas`, `config-gestion.js` |
| Perfil del visitante | Funciona | Picos, octubre: 61 % / 39 % / 72 %; unas 6.841 llegadas de ocio al día (86 días) | `perfil.json` |
| Patrón horario | **Conectado en esta rama** | Picos, octubre: laborables, de 10 a 11 h (unas 501 llegadas de ocio; 57 días); fines de semana y festivos, de 11 a 12 h (unas 1.000; 29 días) | `data/clean/llegadas_por_hora.parquet` (vía `actualizar_datos_web.py` → `salidas.js` → `datos.horas`) |
| Exportación a CSV | Funciona | «Previsión mostrada» y «Días sobre el umbral»; 17 oct, Picos: 1,207; 8655; 7169; 7725; 10741 | Los mismos datos que la pantalla |
| Pruebas (`pestanas/gestion/pruebas.html`) | 20/20 OK con los datos reales | | |

### Sobre los datos
- Fuentes, cómo funciona el modelo y limitaciones: presentes. El algoritmo sale de `metricas.json → algoritmo` = `lightgbm` («LightGBM»). Mapa: «Límites municipales: © Instituto Geográfico Nacional (CC BY 4.0)».
- Corregido con tu visto bueno, solo en textos:
  - el INE pasa a «Validación prevista… Esta comprobación aún no se ha hecho» (`resultados_reales.md` §8);
  - el tiempo solo entra a 1-3 días: «Cómo funciona el modelo», ficha de Open-Meteo y texto de Alertas de Gestión.

### Modo demo (`?demo=1`)
- **Puente de diciembre de 2024: verde.** Picos, 6 dic: +21 % previsto (h=8; cociente 1,209), observado 1,552 (ámbar). Ninguna zona en rojo; solo Llanes el 6 en ámbar (+51 %).
- **Cambiado a agosto de 2024** (`DEMO_MES = '2024-08'` en `datos/fuente-modelo.js`; con tu visto bueno). La demo abre el **15 ago 2024 (puente de la Asunción), Picos: Saturación, +200 %** (15.990 visitantes, de 14.543 a 19.984; normal 5.333; h=8). Observado: +290 % (20.784; cociente 3,897, rojo).
- Recorrido comprobado: mapa (Picos, Llanes y Ribadesella en saturación) → panel de los Picos → «¿por qué?» (Época del año +34 %, Vacaciones escolares +34 %, Acceso regulado a los Lagos +16 %) → alternativa → Gestión → días por encima del umbral.
- Alternativa del 15 ago:
  - el **mejor día** a ±3 días es el sábado 17, **también en saturación** (+129 %) y con un 2 % más de gente (`diferencia_pct` +2,4);
  - la **zona alternativa** sí sirve: Oviedo, −25 %, a 59 km.
  - En la demo conviene enseñar la zona y no el día.

## Paso 3: coherencia con `notas/resultados_reales.md`

| Cifra | Web | Referencia | ¿Cuadra? |
|---|---|---|---|
| Días rojos al año, Picos | 39 · 48 · 36 (29–66) · 34 (28–61) | 39 · 48 · 36 (29–66) · 34 (28–61) | Sí |
| Días en alerta, Picos | 82 · 90 · 84 (63–131) · 78 (56–126) | 82 · 90 · 84 (63–131) · 78 (56–126) | Sí |
| Lagos: rojos en días regulados | 38 de 39 (2023), 47 de 48 (2024) | 38 de 39, 47 de 48 | Sí |
| Lagos: mejor umbral | +10 %, precisión 89 %, cobertura 84 % | 1,10×, precisión 0,892, recall 0,844 | Sí |
| Rojos detectados, Picos, largo plazo | 65 de 87 (8+ días) | 69 rojos previstos frente a 87 observados; precisión 94,2 % → 65 aciertos | Sí |
| Rojos detectados, Picos, corto plazo | «7 de cada 10» de 1 a 7 días | Recall de 66,7 % a 74,7 % por horizonte (`fiabilidad`) | Sí (redondeo a décimas) |
| Error frente al día normal (WAPE modelo frente a B0) | **No se muestra** | Corto 8,8 % frente a 13,2 %; largo 9,3 % frente a 13,2 % (`tablas.global`: 0,0884 / 0,0933 / 0,1315) | Los datos sí cuadran; falta la vista |
| Precisión de los días rojos | **No se muestra** | 94,1 % (corto) y 96,0 % (largo) | Falta la vista |

Ninguna cifra mostrada contradice la referencia. Matices:
- **«+54 %» frente a `pct_sobre_normal` = 54,5** (Llanes, 2 nov): no es un error. `predicciones.json` redondea el cociente a 1,545, pero el valor es 1,5445 (`alternativas.json`), así que +54,45 % → «+54 %». La web calcula desde `cociente`.
- **«Hoy» es el 17 oct en Inicio y el 16 oct en Gestión.** `futuro_largo` y `futuro_corto` empiezan el día siguiente a `fecha_hoy`. Inicio toma como «hoy» el primer día con predicción. El calendario de alertas de Gestión empieza en `fecha_hoy` y, para el 16, usa `calendario_alertas`.
- **Llanes y Ribadesella tienen más días rojos que los Picos** (observados: 74 y 76 en 2023, 74 y 72 en 2024, con umbral +100 %). Está en `regulacion.json`; conviene tenerlo presente en la presentación.

## Paso 4: pruebas finales

- **Sin internet:** con Edge sin interfaz y todas las peticiones a otros hosts bloqueadas, la web carga y funciona entera. Solo fallan Google Fonts (usa las tipografías de reserva, ya documentado en `README_web.md`) y `favicon.ico` (404, no existe; no afecta).
- **1366×768 y 1920×1080:** sin desbordamiento horizontal en Inicio (normal y demo), Gestión y Sobre los datos (`scrollWidth = innerWidth`). Revisadas las capturas.
- **Consola:** sin excepciones ni errores de JavaScript (Chrome con la extensión y Edge sin interfaz), recorriendo las tres pestañas en modo normal y demo.
- **Capturas del recorrido de la demo** (plan B): `notas/capturas_demo/`, 10 por tamaño. Del 01 al 04b, Inicio (demo, mapa, ¿por qué?, alternativa, zonas cercanas); del 05 al 07, Gestión (umbral +50 %, umbral +100 %, Lagos); 08, Sobre los datos; 09, Inicio en modo normal.

## Ajustes mínimos propuestos (no aplicados)

1. **Fiabilidad por bloque frente al día normal:** añadir a «Ver el detalle» de Fiabilidad una tabla (clase `tabla`, ya existente) con WAPE del modelo, B0 y B1 por bloque, de `metricas.json → tablas.bloque`. Es la cifra que más defiende el modelo (y donde pierde: 2025-S1).
2. **Nombre largo de la zona principal:** «Cangas de Onís (incluye Covadonga y Lagos)» ocupa 4 líneas en la etiqueta del mapa a nivel de zona. Se podría mostrar el texto hasta el paréntesis solo en la etiqueta.
3. **«Hoy»:** decidir si Inicio debe llamar «Hoy» al primer día con predicción (17 oct) o si el modelo debe predecir también `fecha_hoy`.
4. `pestanas/README.md` (eb7cf76, de web-gestion, posterior a «lista»): sin integrar. Es solo documentación.
