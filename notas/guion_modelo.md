# Guion: el modelo en un minuto (para el jurado)

> Cifras REALES (objetivo del MITMA, ejecución del 2026-10-16, `--objetivo real --algoritmo ambos`). Fuentes: `salidas/metricas.json` (`tablas.global`), `salidas/explicacion_factores.json`, `salidas/regulacion.json` y `salidas/calibracion_lagos.json`. Detalle y limitaciones en `notas/resultados_reales.md`. No queda ninguna cifra pendiente.

1. **Qué predice.** Para cada día y cada zona de Asturias, nuestro modelo predice cuántos visitantes de ocio llegarán y cuánto supone frente a un día normal de esa zona. El día normal es la mediana de ese día de la semana, fuera de verano y de festivos. El resultado se muestra como un semáforo: ámbar a partir de 1,5 veces lo normal y rojo a partir de 2.

2. **Con qué datos.** Aprende de los viajes diarios del MITMA de 2022 a 2025 y los explica con lo que se sabe de antemano: festivos de Asturias, Madrid y Castilla y León, puentes, vacaciones escolares, eventos y partidos. A una semana vista añade también la previsión del tiempo, en el valle y en la montaña de los Lagos, y el interés en internet (Wikipedia y Google Trends).

3. **Qué modelo.** Son dos modelos de árboles de decisión (LightGBM; probamos también XGBoost con una regla de elección fijada antes de ver los datos reales, y los dos empataron: gana LightGBM por la regla de desempate): uno de largo plazo, que solo usa el calendario y sirve para planificar el año, y otro de corto plazo para la semana. En los dos hemos impedido cualquier fuga de información: una prueba automática comprueba que ninguna variable usa datos posteriores al momento de la predicción.

4. **Cómo se valida.** Lo validamos como se usaría de verdad: entrenamos con el pasado y predecimos semestres que el modelo no ha visto, entre ellos los veranos de 2023 y 2024. Lo comparamos con dos referencias: suponer siempre un día normal y repetir el mismo día del año anterior.

5. **Qué tal acierta.** Acierta el color en el 93 % de los días y comete un error del 9 % en visitantes, frente al 13 % de suponer un día normal y al 10 % de repetir el año anterior. A largo plazo detecta 8 de cada 10 días rojos, y cuando avisa de rojo acierta el 96 % de las veces. Además, cada predicción viene con un intervalo y un aviso de «incierto» cuando el intervalo cruza de color. Con honestidad: en el último semestre que validamos, el de 2025, no mejora al día normal en Gijón y Oviedo, y en general se queda algo corto en volumen, porque las llegadas crecen de un año a otro.

6. **Por qué.** Cada predicción muestra sus tres factores principales con su peso: por ejemplo, un jueves de agosto de 2023 en Cangas de Onís: «época del año +40 %, vacaciones escolares +37 %». Los calculamos con SHAP. Con datos de efectos conocidos comprobamos que el modelo recupera su signo, y con los datos reales los signos tienen sentido: el verano y las vacaciones suben, y la lluvia prevista baja.

7. **¿Hay que regular?** La pestaña de Gestión cuenta los días rojos previstos para 2026 y 2027 en cada zona: unos 36 en Cangas de Onís en 2026, entre 29 y 66 (en 2023 hubo 39 y en 2024, 48). El umbral es ajustable. Además, compara esos días con los que ya se regula el acceso a los Lagos. Así, la administración puede ver si la regulación llega a los días de verdadera presión y si sobran o faltan días.

   Comprobado con datos reales: en 2023 y 2024, 85 de los 87 días rojos ya estaban dentro de la regulación actual de los Lagos, que en cambio cubre unas cuatro veces más días (352 con dato). La regulación se parece más a «cualquier día un 10 % por encima de lo normal» que a los días de presión extrema. Ojo: el MITMA mide llegadas al concejo de Cangas de Onís, no accesos a los Lagos.

8. **Límites, con honestidad.** El MITMA no cuenta a los visitantes extranjeros, sus datos diarios llegan hasta junio de 2025, los cruceros quedan fuera y el umbral del semáforo es nuestro, no una capacidad oficial. El modelo falla en los puentes de diciembre y su previsión de días rojos probablemente se queda corta. Por eso lo presentamos como un sistema de alerta temprana que ayuda a decidir, no como una cifra exacta de aforo.
