# Pestañas «Gestión» y «Sobre los datos»

Rama `web-gestion` (persona 2). Se montan en la web de `Afluencia Asturias/` con la interfaz de `window.Pestanas` (ver `notas/coordinacion_web.md`). No se ha tocado ningún estilo, `index.html`, `interfaz/` ni `datos/`: todo usa las clases de `estilos/estilos.css`.

## Estructura

| Fichero | Qué es |
|---|---|
| `gestion/config-gestion.js` | **Editable.** Acción sugerida por color, criterio «estudiar/vigilar» (30 y 10 días) y días de alertas (28). |
| `gestion/logica.js` | Lógica pura, sin DOM (`window.GestionLogica`). Todo número sale de los JSON del modelo. |
| `gestion/gestion.js` | Pinta la pestaña. Carga `config-gestion.js` y `logica.js` por su cuenta. |
| `gestion/pruebas.html` | 20 pruebas de la lógica con las salidas reales. |
| `sobre/contenido.js` | **Editable.** Todos los textos de «Sobre los datos»: fuentes, modelo, limitaciones, cita del mapa. |
| `sobre/sobre.js` | Maqueta los textos. Los umbrales del semáforo y el algoritmo salen de los datos. |

## Qué hace Gestión

1. **¿Hace falta regular?** Días por zona y año (2023-2024 observados, 2026-2027 previstos) que superan un umbral ajustable (veces el día normal), con veredicto orientativo y, en previstos, intervalo probable.
2. **Lagos de Covadonga.** Alertas y días rojos dentro y fuera de los días con acceso regulado, y el umbral que mejor reproduce el calendario regulado.
3. **Alertas.** Matriz de las próximas 4 semanas y lista con acción sugerida. Por fecha y zona usa `futuro_corto`, si no `futuro_largo`, si no `calendario_alertas`.
4. **Fiabilidad.** Acierto de color por zona y antelación (1-3, 4-7, 8+ días) y la nota del modelo.
5. **Perfil del visitante** (zona y mes, de `perfil.json`). El **patrón horario está pendiente de datos** (`data/clean/llegadas_por_hora.parquet` no existe).
6. **Exportar CSV** (`;`, decimales con coma, BOM al descargar; con columna de aviso si los datos son sintéticos).

## Cómo cambiar cosas

- **Acciones o criterios:** `gestion/config-gestion.js`.
- **Textos de «Sobre los datos»:** `sobre/contenido.js`.
- **Datos reales:** regenerar `salidas/` y `python -X utf8 scripts/actualizar_datos_web.py`. Mismo formato; no hay que tocar nada aquí.
- **IDs de zona:** nunca a mano; salen de `predicciones.zonas`.

## Pruebas

Abrir `gestion/pruebas.html` (doble clic). Arriba debe poner «TODO OK: 20 pruebas». Sin interfaz:

```powershell
chrome --headless=new --allow-file-access-from-files --virtual-time-budget=5000 --dump-dom file:///…/gestion/pruebas.html
```

## Límites conocidos

- `cociente`, `p10` y `p90` vienen redondeados en el JSON. Con los umbrales de la cabecera se cuenta por el color del modelo (exacto); con otros umbrales en años previstos puede diferir 1-3 días de `curva_umbral`.
- Los años observados solo tienen la curva de umbrales 1,2-3,0 (14 valores): no se interpola. Para cualquier umbral habría que añadir el cociente diario observado al contrato.
- Quitados del piloto por falta de datos en el contrato: simulador de escenarios y gráfica real frente a predicción.
