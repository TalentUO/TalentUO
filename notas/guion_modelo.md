# Guion: el modelo en un minuto (para el jurado)

> Cifras de las salidas actuales: datos reales del MITMA, 46 zonas, XGBoost, ejecución del 2026-10-16 con `--objetivo real --algoritmo ambos`. Fuentes: `salidas/metricas.json` (`tablas.global` y `tablas.zona`), `salidas/explicacion_factores.json`, `salidas/regulacion.json` y `salidas/calibracion_lagos.json`. Resumen con cada cifra y su fichero en `README.md` («Resultados»).

1. **Qué predice.** Para cada día y cada una de las 46 zonas del MITMA en Asturias (los 78 concejos), el modelo predice cuántos visitantes de ocio llegarán y cuánto supone frente a un día normal de esa zona. El día normal es la mediana de ese día de la semana en 2024, fuera de julio, agosto y festivos. El resultado se muestra como un semáforo: ámbar a partir de 1,5 veces lo normal y rojo a partir de 2.

2. **Con qué datos.** Aprende de los viajes diarios del MITMA de 2022 a junio de 2025 y los explica con lo que se sabe de antemano: festivos de Asturias, Madrid y Castilla y León, puentes, vacaciones escolares, eventos y partidos. A una semana vista añade el interés en internet (Wikipedia y Google Trends) y, a 1-3 días, la previsión del tiempo en el valle y en la montaña de los Lagos.

3. **Qué modelo.** Son dos modelos de árboles de decisión con XGBoost: uno de largo plazo, que solo usa el calendario y sirve para planificar el año, y otro de corto plazo para la semana. Elegimos XGBoost frente a LightGBM con una regla fijada antes de ver los datos reales: detecta más días rojos en verano (64 % frente a 54 %) con una precisión parecida. Una prueba automática comprueba que ninguna variable usa datos posteriores al momento de la predicción.

4. **Cómo se valida.** Como se usaría de verdad: entrenamos con el pasado y predecimos semestres que el modelo no ha visto, entre ellos los veranos de 2023 y 2024. Lo comparamos con dos referencias: suponer siempre un día normal y repetir el mismo día del año anterior.

5. **Qué tal acierta.** Acierta el color en el 94 % de los días y comete un error del 10 % en visitantes, frente al 13 % de suponer un día normal y al 11 % de repetir el año anterior. En la zona de los Picos, a largo plazo, detecta 66 de los 87 días rojos de 2023 y 2024, y cuando avisa de rojo acierta el 93 % de las veces. Cada predicción viene con un intervalo y un aviso de «incierto» cuando el intervalo cruza de color. Con honestidad: a una semana vista detecta algo más de la mitad de los días rojos (55 %), menos que repetir el año anterior, aunque con menos falsas alarmas; y en general se queda corto en volumen, porque las llegadas crecen de un año a otro.

6. **Por qué.** Cada predicción muestra sus tres factores principales con su peso. Por ejemplo, el lunes 19 de agosto de 2024 en Cangas de Onís: «época del año +37 %, vacaciones escolares +29 %, acceso regulado a los Lagos +9 %». Los calculamos con SHAP. Con datos de efectos conocidos comprobamos que el modelo recupera su signo, y con los datos reales los signos tienen sentido: el verano y las vacaciones suben, y la lluvia prevista baja.

7. **¿Hay que regular?** La pestaña Funciones avanzadas cuenta los días por encima del umbral previstos en los próximos 12 meses en cada concejo, con el umbral ajustable. En Cangas de Onís se prevén unos 40 días rojos en 2026, entre 27 y 72 (en 2023 hubo 39 y en 2024, 48).

   Comprobado con datos reales: en 2023 y 2024, 85 de los 87 días rojos ya estaban dentro de la regulación actual del acceso a los Lagos, que en cambio cubre unas cuatro veces más días (352 con dato). La regulación se parece más a «cualquier día un 10 % por encima de lo normal» que a los días de presión extrema. Ojo: el MITMA mide llegadas al concejo de Cangas de Onís, no accesos a los Lagos.

8. **Límites, con honestidad.** El MITMA no cuenta a los visitantes extranjeros, sus datos diarios llegan hasta junio de 2025, los cruceros quedan fuera y el umbral del semáforo es nuestro, no una capacidad oficial. El modelo falla en los puentes de diciembre y su previsión de días rojos probablemente se queda corta. Por eso lo presentamos como un sistema de alerta temprana que ayuda a decidir, no como una cifra exacta de aforo.
