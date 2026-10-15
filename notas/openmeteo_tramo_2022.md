# Open-Meteo: el tramo 2022 de Historical Forecast no es previsión

Fecha del análisis: 2026-10-15. Script reproducible: `python -X utf8 src/auditoria/tramo_2022_openmeteo.py` (solo lectura; compara `openmeteo_<zona>.json` con `openmeteo_archive_<zona>.json`, ERA5, ya descargado para las 9 zonas). **No se ha modificado ni decidido nada**: esto es una propuesta para que decidáis.

## 1. Fecha de corte por zona

Criterio: se considera "reanálisis" el día en que las 5 variables sensibles (precipitación diaria, horas de precipitación, viento máx., racha máx., código WMO) son **idénticas** a ERA5. Además sol (`sunshine_duration`) es idéntico el 100 % de esos días.

| Zona | Último día idéntico a ERA5 | Primer día que ya difiere | Días de reanálisis (desde 2022-01-01) |
|---|---|---|---|
| covadonga, lagos_enol, cangas_de_onis, llanes, ribadesella, gijon, oviedo (las 7 de Asturias) | **2022-11-08** | **2022-11-09** | 312 |
| madrid, sevilla | **2022-11-15** | **2022-11-16** | 319 |

Evidencia (todas las zonas): antes del corte, precipitación, horas de precipitación, sol, viento, racha y código WMO coinciden con ERA5 el **100,0 %** de los días. Después del corte, la coincidencia cae a: precipitación 28–34 % (Asturias) / 62–70 % (Madrid, Sevilla; son días secos con 0 = 0), viento 0,2–1,5 %, racha 0,9–3,1 %, sol 3–8 %, código WMO 39–45 %. No hay ninguna racha de 7 o más días idénticos después del corte, en ninguna zona. Día a día en Covadonga: 2022-11-05…08 → 6/6 variables iguales; 2022-11-09 → solo 2/6 iguales (precipitación 5,3 vs 3,8 mm; viento 5,2 vs 7,2 km/h); desde el 10 ya difieren (los días secos coinciden por casualidad, 0 = 0).

Matices:
- **Temperatura (Tmax/Tmin): no es una copia exacta de ERA5 en ningún tramo** (1–6 % de días idénticos tanto antes como después, porque Open-Meteo la corrige a la elevación del punto). Por tanto la temperatura **no sirve para detectar el corte**, y no sé decir si el tramo 2022 de temperatura es reanálisis ajustado o previsión (error medio absoluto vs ERA5 en Covadonga: 1,41 °C antes del corte y 1,24 °C después: no discrimina). Tratadla como "no verificada".
- Corrección al registro anterior: `registro_openmeteo.md` ponía el corte en 2022-11-10 (fecha en la que `best_match` empieza a coincidir con Météo-France). La última fecha idéntica a ERA5 es 2022-11-08; el 2022-11-09 es día de transición.
- En Madrid y Sevilla el corte es una semana posterior (2022-11-15): el modelo/cobertura cambia en otro momento. La causa de ambos cortes **no está verificada** (la API no indica qué modelo usa).
- Rejilla: la API devuelve para ERA5 una celda distinta de la de Historical Forecast (en Covadonga ~5 km al noroeste), pero **aun así** los valores de precipitación y viento coinciden al 100 % antes del corte. Eso refuerza que la "previsión" de ese tramo es el propio reanálisis servido por Open-Meteo (la API aplica la misma celda a ambas); no se ha podido comprobar de otro modo.

## 2. ¿Cubre la Previous Runs API el tramo 2022?

**No.** Probado en Covadonga para 2022-01-01 → 2023-12-31 (horario): `*_previous_day1` es nulo el 100 % de las horas de 2022 y de 2023 (empieza a tener datos el 2024-01-19 14:00, como ya constaba). La serie "día 0" (`precipitation`, `wind_speed_10m`) sí existe en 2022, pero es la misma que Historical Forecast (42/53 días iguales en nov-dic 2022; 254/365 en 2023, diferencias de redondeo al sumar horas) y por tanto tiene el mismo problema. Previous Runs solo aporta previsión real (a 1–3 días) desde **2024-01-22**.

Prueba adicional (indicativa): pidiendo a Historical Forecast un modelo concreto para 2022-01-01 → 2022-10-31 en Covadonga, `ecmwf_ifs025`, `icon_seamless`, `meteofrance_seamless` y `ecmwf_ifs04` devuelven **solo nulos**; `gfs_seamless` devuelve datos completos (304/304 días) y coincide con ERA5 en 101 de 304 días de precipitación (probablemente días secos; no analizado). Es decir, existe al menos una serie de modelo real para ese tramo (GFS), pero no la he descargado ni evaluado.

## 3. Opciones (para que decidáis)

**A. Empezar el entrenamiento en la fecha de corte** (Asturias 2022-11-09; Madrid/Sevilla 2022-11-16 si se usan).
- + Sin fuga ni mezcla de regímenes; la meteorología de entrenamiento tiene el mismo carácter que la de producción. Sencillo.
- − Se pierden 312 días de 1749 (~18 % del histórico meteorológico) y, si el objetivo de movilidad cubre desde 2022, ~10 meses, incluido todo el verano de 2022: un ciclo estacional completo menos para aprender la estacionalidad.

**B. Usar Previous Runs (día 1) como serie de entrenamiento.**
- + Es la mejor réplica de producción (lo que se sabía 1 día antes), sin fuga, por hora (permite agregar como se quiera).
- − **No cubre 2022 ni 2023**: solo desde 2024-01-22 (~2,7 años), lo que no resuelve el tramo y reduce más el histórico que la opción A. Útil como serie de validación/contraste con A, no como sustituto.

**C. Mantener el tramo con una marca que lo identifique** (p. ej. columna `meteo_es_reanalisis = 1` hasta el corte de cada zona) y excluirlo de la evaluación.
- + Conserva todo el histórico de movilidad; permite medir cuánto "ayuda" una meteorología perfecta frente a una previsión (diagnóstico de fuga).
- − Con una variable meteorológica casi perfecta durante ese tramo, el modelo puede aprender a confiar demasiado en ella; la marca no corrige ese sesgo por sí sola. Hay que evaluar solo en periodos posteriores al corte y comprobar que el rendimiento no depende del tramo. La temperatura (no verificada, ver arriba) queda con un estatus dudoso.

**D. (Complemento a C) Rellenar el tramo con una previsión real de otro modelo (GFS seamless).**
- + Mantiene el histórico y es previsión archivada, no reanálisis.
- − Modelo distinto al del resto de la serie (`best_match` = Météo-France desde 2022-11-10): añade un cambio de régimen; además hay que descargar y validar, y la calidad de GFS en la orografía de los Picos no está evaluada. No se ha hecho.

Mi lectura (a vuestra decisión): A como línea base, y C solo si necesitáis los 10 meses de 2022 para el modelo de movilidad; en ese caso evaluad siempre en periodos posteriores al corte.

## 4. Pendiente / no verificado

- Qué modelo alimenta cada tramo (inferido, no declarado por la API).
- Si la temperatura del tramo 2022 es reanálisis ajustado.
- Si el día en curso (2026-10-15, último de cada serie) está incompleto.
- Calidad de GFS para este uso (opción D).
