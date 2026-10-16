# Umbrales del semáforo por zona (opción B): resultado

Fecha: 2026-10-16. Rama `umbrales-por-zona` (desde `main` 002d805). **No se fusiona con `main`**: la versión de `main` (×1,5 alta y ×2,0 saturación para todas las zonas) es la defendible.

## Por qué se probó
Con un umbral igual para todas las zonas:
- en la costa oriental casi todo el verano sale rojo (Llanes, 77 días rojos al año);
- las ciudades no alertan nunca (16 zonas sin ningún día rojo; 6 sin ningún ámbar, con el 32 % de las llegadas de ocio).

La idea era comparar cada zona con su propia historia.

## Qué se hizo
- `scripts/umbrales_por_zona.py` calcula los umbrales y los escribe en `config/semaforo.yaml → por_zona` (46 zonas):
  - mismo día normal del semáforo;
  - años enteros 2022-2024 con dato completo;
  - alta = percentil 90 de la zona (como mínimo +15 %);
  - saturación = percentil 97 (como mínimo +30 % y 0,10 por encima de la alta).
- Ejemplos de umbrales (alta / saturación):

  | Zona | Alta | Saturación |
  |---|---|---|
  | Llanes | ×2,80 | ×4,00 |
  | Ribadesella | ×2,73 | ×3,87 |
  | Picos (Cangas de Onís) | ×2,09 | ×2,88 |
  | Somiedo y 5 más | ×1,55 | ×2,13 |
  | Gijón, Oviedo, Avilés, Siero, Mieres… | ×1,15 (mínimo) | ×1,30 (mínimo) |

- Modelo reentrenado (`--algoritmo ambos`; gana XGBoost por regla). Contrato OK y 92 tests OK.
- Web adaptada:
  - Inicio: color de los periodos con el umbral de cada zona, leyenda («lo habitual / de los días más concurridos / un día excepcional para esa zona»), umbral de la zona en su panel y ranking ordenado por nivel;
  - Sobre los datos: explicación del criterio;
  - Funciones avanzadas: selector «el umbral de saturación de cada zona / elegir un umbral»;
  - `pruebas.html`: 20/20 con los umbrales de cada zona.

## Resultado: el modelo no anticipa los días excepcionales

| Largo plazo, todos los bloques de validación | `main` (×1,5 / ×2,0) | Por zona (P90 / P97) |
|---|---|---|
| Días rojos detectados (recall) | 68,7 % | **8,5 %** |
| Precisión de los rojos | 85,2 % | 48 % |
| Días en alerta (ámbar o rojo) detectados | — | 40,9 % |
| Acierto de color (modelo / día normal fijo, B0) | 94,5 % / — | 90,6 % / 90,4 % |
| Corto plazo: rojos detectados / precisión | 54,7 % / 88,6 % | 3,0 % / 34,6 % |

- De los días que de verdad fueron de alerta, el modelo pinta verdes el 71 %.
- **El mapa del año siguiente sale aún más verde:** 96,1 % de días×zona en verde (94,1 % en `main`) y 0,2 % en rojo. Por meses (ámbar / rojo):
  - agosto, 36,7 % / 2,0 %;
  - julio, 4,0 % / 0 %;
  - octubre a diciembre, menos del 1 % de ámbar.
- **Las ciudades siguen sin alertar:** sus picos (+15-30 %) son días sueltos, sin patrón de calendario que el modelo aprenda.
- **La demo se mantiene:** el 15-08-2024 los Picos salen en rojo (×3,27, umbral ×2,88). Pero la fiabilidad de la zona dice «detecta 1 de cada 10 días rojos».

## Conclusión
- Los umbrales por zona describen mejor qué es un día excepcional en cada sitio.
- Pero el modelo, que se queda corto en los picos (ver `notas/ampliacion_zonas.md` y `notas/resultados_reales.md` §6), no los predice.
- Para que el mapa se mueva de forma realista haría falta mejorar la predicción de los picos (tendencia, calibración de la cola), no cambiar los umbrales.
- **Se queda la versión de `main`.**
