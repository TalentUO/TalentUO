# Fuentes de datos y licencias

Este repositorio usa y, en parte, redistribuye datos, imágenes y librerías de terceros. Para cada uno se indica para qué se usa, en qué condiciones se puede reutilizar y qué texto de atribución hay que poner.

**Aviso.** Es un resumen hecho para el hackathon, no asesoramiento jurídico. La columna «Comprobado» dice si la condición se leyó en la web de la fuente durante el proyecto (con la nota donde consta) o si es la condición habitual de esa fuente y **falta confirmarla** antes de un uso público o comercial.

La licencia del código del proyecto está pendiente de decidir por el equipo (ver `README.md`).

## Variable objetivo y validación

| Fuente | Uso en el proyecto | Dónde está | Condiciones de reutilización | Atribución | Comprobado |
|---|---|---|---|---|---|
| **MITMA**, Open Data Movilidad (estudios básicos, zonificación municipal v2) | Variable que se predice: llegadas de ocio por zona y día (2022-01 → 2025-06); día normal; zonificación | `data/clean/objetivo_diario.parquet`, `data/clean/llegadas_por_hora.parquet`, `data/raw/mitma_*` (los ficheros grandes no se versionan) | Datos abiertos del Ministerio de Transportes, reutilizables citando la fuente. Licencia exacta pendiente de confirmar en el aviso legal del portal | «Fuente: Ministerio de Transportes y Movilidad Sostenible, Open Data Movilidad (estudios básicos)» | No |
| **INE**: encuestas de ocupación (EOH, EOAP, campings, turismo rural), viviendas turísticas, turismo con móviles | Contexto y validación prevista (no realizada) | `data/raw/ine_*` | Reutilización libre citando al INE (aviso legal del INE). Pendiente de confirmar | «Fuente: INE» | No |
| **SADEI** (Instituto Asturiano de Estadística): turistas, plazas, apartamentos y padrón por concejo | Contexto | `data/raw/sadei_*.px`, `data/raw/padron_concejos.px` | Citando la fuente. Pendiente de confirmar en su aviso legal | «Fuente: SADEI» | No |
| **COGERSA**: residuos por concejo (2020-2021) | Contexto (no se usa en el modelo) | `data/raw/cogersa_residuos.xlsx` | Datos publicados por COGERSA. Pendiente de confirmar | «Fuente: COGERSA» | No |
| **OAPN / MITECO**: memorias e informes de visitantes de los Parques Nacionales | Visitantes anuales de Picos de Europa (contexto) | `data/raw/oapn/`, `data/raw/calendario/miteco_*` | Documentos públicos de la Administración. Pendiente de confirmar | «Fuente: Organismo Autónomo Parques Nacionales (MITECO)» | No |

## Factores explicativos

| Fuente | Uso en el proyecto | Dónde está | Condiciones de reutilización | Atribución | Comprobado |
|---|---|---|---|---|---|
| **AEMET OpenData** | Observación meteorológica (contraste; el modelo no la usa como variable) | `data/raw/aemet*`, `data/clean/aemet_diario.parquet` | Reutilización permitida citando a AEMET (aviso legal de AEMET). Pendiente de confirmar | «© AEMET» o «Fuente: AEMET» | No |
| **Open-Meteo** (Historical Forecast, Previous Runs, Archive/ERA5 y previsión) | Tiempo previsto en el modelo de corto plazo; ERA5 solo como referencia | `data/raw/openmeteo_*`, `data/prevision/`, `data/clean/openmeteo_*` | **CC BY 4.0**. Uso gratuito **solo no comercial**: un uso comercial exige plan de pago | «Datos meteorológicos: Open-Meteo.com (CC BY 4.0)»; para ERA5, «Contiene información modificada del Copernicus Climate Change Service» | Sí (`notas/fuentes/openmeteo/registro_openmeteo.md`) |
| **BOE** (fiestas laborales, medidas de tráfico de la DGT, regulación del acceso a los Lagos) | Calendario de festivos, puentes y días regulados | `data/raw/calendario/boe_*` | Textos oficiales: no están sujetos a derechos de autor (art. 13 de la Ley de Propiedad Intelectual) | «Fuente: BOE» | No |
| **BOPA** (fiestas locales, calendario escolar de Asturias), **Educastur**, calendarios escolares de **Madrid** y **Castilla y León** | Festivos locales y vacaciones escolares de destino y de origen | `data/raw/calendario/` | Textos oficiales (art. 13 LPI) | «Fuente: BOPA», «Fuente: Comunidad de Madrid», «Fuente: Junta de Castilla y León» | No |
| **Parque Nacional de los Picos de Europa** y **Turismo de Cangas de Onís** (regulación del acceso a los Lagos) | Calendario de acceso regulado | `data/raw/calendario/pnpe_*`, `turismocangasdeonis_*`, `data/clean/lagos_folleto_transcripcion.csv` | Páginas y folleto con derechos de sus titulares; se guardan como evidencia de la fecha | Citar la página de origen | No |
| **Webs de eventos y prensa** (Descenso del Sella, Fiesta del Pastor, San Mateo, Festival de la Sidra de Nava, Semana Negra, FICX, FIDMA, cruceros del Puerto de Gijón y otras) | Fechas de eventos (`data/manual/eventos_recopilado.csv`) | `data/raw/eventos/`, `data/raw/calendario/prensa_*` | Contenido con derechos de sus titulares. Las copias HTML y PDF solo son evidencia de la fecha: **conviene no redistribuirlas si el repositorio se hace público** | La URL de cada fecha está en `fuente_url` de `data/manual/eventos_recopilado.csv` | No |
| **football-data.co.uk** (resultados de LaLiga) y **LaLiga** (calendario 2026-27) | Partidos en casa del Real Oviedo y del Sporting | `data/raw/eventos/fd_SP*.csv`, `data/raw/eventos/laliga_*` | football-data.co.uk ofrece los CSV gratis bajo sus propias condiciones; las páginas de LaLiga tienen derechos de LaLiga. Pendiente de confirmar | «Fuente: football-data.co.uk», «Fuente: LaLiga» | No |
| **Wikimedia**: API de páginas vistas de Wikipedia | Señal de interés en internet (corto plazo) | `data/raw/wikipedia_*.json`, `data/clean/wikipedia_diario.parquet` | Los datos de páginas vistas se publican como dominio público (CC0). Pendiente de confirmar | «Fuente: Wikimedia Foundation, Pageviews API» | No |
| **Google Trends** | Señal de interés en internet (corto plazo) | `data/raw/trends/`, `data/clean/trends_*` | Condiciones de servicio de Google; se puede citar con atribución | «Fuente: Google Trends (www.google.com/trends)» | No |

## Web (`Afluencia Asturias/`)

| Fuente | Uso en el proyecto | Dónde está | Condiciones de reutilización | Atribución | Comprobado |
|---|---|---|---|---|---|
| **IGN** (límites municipales), vía el conjunto `georef-spain-municipio` de OpenDataSoft (2022), y nombres oficiales del paquete `es-atlas` | Mapa de los 78 concejos | `Afluencia Asturias/interfaz/geo-asturias.js` | **CC BY 4.0** | «Límites municipales: © Instituto Geográfico Nacional (CC BY 4.0)» (ya está en «Sobre los datos») | Sí (`notas/historico/coordinacion_web.md`) |
| **Wikimedia Commons** (141 fotos de sitios de interés) | Fotos de los sitios | `Afluencia Asturias/assets/sitios/`, autor y licencia en `Afluencia Asturias/datos/sitios.js` | Licencia propia de cada foto (CC BY, CC BY-SA…): hay que mostrar autor y licencia junto a la foto, y la web ya lo hace | Autor y licencia de cada foto | Sí (`Afluencia Asturias/datos/sitios.js`) |
| **OpenStreetMap** (Nominatim) | Coordenadas de 137 sitios de interés | `Afluencia Asturias/datos/sitios.js` | **ODbL 1.0**: las coordenadas derivan de OpenStreetMap | «© colaboradores de OpenStreetMap» (falta añadirlo a «Sobre los datos») | No |
| **PredictHQ** | Eventos grandes de la sección «Eventos» de Inicio | `Afluencia Asturias/datos/eventos.js` | **Pendiente de confirmar.** Es un servicio de pago y sus condiciones podrían no permitir redistribuir sus datos en una web pública ni en un repositorio público | «Datos de eventos: PredictHQ» | No |
| **Leaflet** 1.9.4 | Mapa interactivo | `Afluencia Asturias/vendor/leaflet/` | BSD 2-Clause | Aviso de copyright incluido en la librería | No |
| **topojson-client** 3.1.0 | Lectura del TopoJSON | `Afluencia Asturias/vendor/topojson-client.min.js` | ISC | Aviso de copyright incluido en la librería | No |
| **Google Fonts**: Schibsted Grotesk y Atkinson Hyperlegible | Tipografías (se cargan desde Google Fonts) | No se redistribuyen | SIL Open Font License 1.1 | No hace falta en la página | No |

## Pendientes antes de hacer público el repositorio o la web

1. Confirmar las condiciones de PredictHQ y, si no permiten redistribuir, quitar `Afluencia Asturias/datos/eventos.js` del repositorio público o sustituirlo por los eventos propios (`data/manual/eventos_recopilado.csv`).
2. Completar las atribuciones de «Sobre los datos» (`Afluencia Asturias/pestanas/sobre/contenido.js`): MITMA, AEMET y Open-Meteo ya figuran como fuentes, pero sin su licencia (Open-Meteo: CC BY 4.0); faltan OpenStreetMap (ODbL) y PredictHQ.
3. Revisar si se publican las copias HTML y PDF de prensa y webs de eventos (`data/raw/eventos/`, `data/raw/calendario/prensa_*`).
4. Open-Meteo: su uso gratuito es solo no comercial; un uso comercial de la web exige plan de pago o servidor propio.
5. Confirmar las condiciones marcadas «No» en la columna «Comprobado».
