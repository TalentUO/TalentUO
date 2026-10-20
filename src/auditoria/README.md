# Auditoría de los datos en bruto de la parte B

Scripts de comprobación de solo lectura que se ejecutaron una vez, el 2026-10-15, para auditar las descargas de la parte B. Su resultado está en `notas/historico/auditoria_fase_B.md` y `notas/fuentes/openmeteo/openmeteo_tramo_2022.md`. Ningún otro código los usa; se conservan como prueba de esa auditoría.

Se ejecutan desde la raíz del repositorio (usan rutas relativas a ella):

```bash
python -X utf8 src/auditoria/aud_aemet.py
```

| Script | Qué comprueba |
|---|---|
| `aud_aemet.py` | Ficheros de AEMET: tramos, fechas, huecos y valores |
| `aud_aemet_live.py` | Contraste de una muestra con la API de AEMET (necesita `AEMET_API_KEY`) |
| `aud_calendarios.py` | PDF de calendarios: páginas, año, comunidad e identificador |
| `aud_openmeteo.py` | JSON de Open-Meteo: fechas completas y nulos |
| `aud_openmeteo_live.py` | Repite llamadas a Open-Meteo y las compara con lo guardado |
| `aud_openmeteo_resumen.py` | Resumen de los JSON de Open-Meteo presentes |
| `aud_senales.py` | Wikipedia, Google Trends y OAPN (con muestras en vivo) |
| `tramo_2022_openmeteo.py` | Fecha en que Historical Forecast deja de coincidir con ERA5 en cada zona |

Los `*_live` llaman a las API con las fechas de aquella auditoría: hoy pueden dar diferencias si la fuente ha corregido datos.
