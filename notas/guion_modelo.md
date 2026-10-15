# Guion: el modelo en un minuto (para el jurado)

> Las cifras entre [corchetes] son hoy SINTÉTICAS. Hay que sustituirlas por las de `salidas/resumen_ejecucion.json` y `salidas/metricas.json` tras ejecutar `--objetivo real`.

1. **Qué predice.** Para cada día y cada zona de Asturias, nuestro modelo predice cuántos visitantes de ocio llegarán y cuánto supone frente a un día normal de esa zona. El día normal es la mediana de ese día de la semana, fuera de verano y de festivos. El resultado se muestra como un semáforo: ámbar a partir de 1,5 veces lo normal y rojo a partir de 2.

2. **Con qué datos.** Aprende de los viajes diarios del MITMA de 2022 a 2025 y los explica con lo que se sabe de antemano: festivos de Asturias, Madrid y Castilla y León, puentes, vacaciones escolares, eventos y partidos. A una semana vista añade también la previsión del tiempo, en el valle y en la montaña de los Lagos, y el interés en internet (Wikipedia y Google Trends).

3. **Qué modelo.** Son dos modelos de árboles de decisión (LightGBM; probamos también XGBoost con una regla de elección fijada de antemano): uno de largo plazo, que solo usa el calendario y sirve para planificar el año, y otro de corto plazo para la semana. En los dos hemos impedido cualquier fuga de información: una prueba automática comprueba que ninguna variable usa datos posteriores al momento de la predicción.

4. **Cómo se valida.** Lo validamos como se usaría de verdad: entrenamos con el pasado y predecimos semestres que el modelo no ha visto, entre ellos los veranos de 2023 y 2024. Lo comparamos con dos referencias: suponer siempre un día normal y repetir el mismo día del año anterior.

5. **Qué tal acierta.** Acierta el color en el [94 %] de los días y comete un error del [11 %] en visitantes, frente al [18 %] de la referencia. A largo plazo detecta [8 de cada 10] días rojos. Además, cada predicción viene con un intervalo y un aviso de «incierto» cuando el intervalo cruza de color.

6. **Por qué.** Cada predicción muestra sus tres factores principales con su peso: por ejemplo, «[vacaciones escolares +44 %, época del año +36 %]». Los calculamos con SHAP, y hemos comprobado con datos de efectos conocidos que el modelo recupera el signo de todos ellos.

7. **¿Hay que regular?** La pestaña de Gestión cuenta los días rojos previstos para 2026 y 2027 en cada zona: [unos 42 en Cangas de Onís, entre 5 y 73]. El umbral es ajustable. Además, compara esos días con los que ya se regula el acceso a los Lagos. Así, la administración puede ver si la regulación llega a los días de verdadera presión y si sobran o faltan días.

   > **⚠ PENDIENTE DE DATOS REALES. No decir hasta comprobarlo con `--objetivo real`:** «[con el umbral rojo, el 93 % de los días rojos ya están dentro de la regulación actual, que en cambio cubre unas cuatro veces más días]». Hoy sale del objetivo sintético, que no tiene ningún efecto de la regulación: es una hipótesis, no una conclusión. Si no se ha podido comprobar el día de la presentación, se dice solo la frase sin corchetes.

8. **Límites, con honestidad.** El MITMA no cuenta a los visitantes extranjeros, sus datos diarios llegan hasta junio de 2025 y el umbral del semáforo es nuestro, no una capacidad oficial. Por eso lo presentamos como un sistema de alerta temprana que ayuda a decidir, no como una cifra exacta de aforo.
