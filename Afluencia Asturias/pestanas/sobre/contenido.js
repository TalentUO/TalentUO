/* ==========================================================================
 * CONTENIDO de «Sobre los datos» (persona 2). Solo textos: se editan aquí
 * sin tocar sobre.js. Las cifras no se escriben a mano: las que aparecen
 * salen de las salidas del modelo (umbrales, algoritmo, fechas).
 * ========================================================================== */
window.SobreContenido = {
  intro: 'Predecimos cuántos visitantes recibirá cada zona de Asturias cada día, lo comparamos con un día normal y lo traducimos en un semáforo. Aquí explicamos de dónde salen las cifras, cómo funciona el modelo y qué no podemos saber.',

  // «Qué es un día normal»
  diaNormal: 'Es un día típico en esa zona: la mediana de visitantes del mismo día de la semana en 2024, sin julio ni agosto, sin festivos y sin días con problemas de datos. Si el semáforo dice «+45 %», esperamos casi la mitad más de visitantes que en un día típico. Comparar con la propia zona permite tratar igual a Gijón, con muchos visitantes diarios, y a una zona pequeña.',

  // Fuentes: eyebrow = papel que juega en el modelo
  fuentes: [
    { etiqueta: 'Variable principal', titulo: 'MITMA Open Data Movilidad',
      texto: 'Ministerio de Transportes. Llegadas diarias de visitantes a cada zona, estimadas con telefonía móvil, separando a quien viene de paso y a quien hace noche.' },
    { etiqueta: 'Validación', titulo: 'INE',
      texto: 'Instituto Nacional de Estadística. Turismo mensual por concejo y medición con telefonía móvil, para comprobar que las cifras diarias cuadran.' },
    { etiqueta: 'Contexto', titulo: 'SADEI',
      texto: 'Sociedad Asturiana de Estudios e Investigación. Población y alojamiento por concejo, para entender la presión sobre quien vive allí.' },
    { etiqueta: 'Factor explicativo', titulo: 'AEMET',
      texto: 'Agencia Estatal de Meteorología. Temperatura y lluvia observadas en estaciones del valle y de la montaña.' },
    { etiqueta: 'Factor explicativo', titulo: 'Open-Meteo',
      texto: 'Previsión del tiempo para los próximos días y datos históricos. El tiempo solo se usa en el corto plazo, hasta una semana vista.' },
    { etiqueta: 'Factor explicativo', titulo: 'BOE y BOPA',
      texto: 'Boletín Oficial del Estado y Boletín Oficial del Principado de Asturias. Festivos nacionales, autonómicos y locales, y las resoluciones de acceso regulado a los Lagos de Covadonga.' },
    { etiqueta: 'Factor explicativo', titulo: 'Calendarios escolares',
      texto: 'Vacaciones escolares de Asturias, Madrid y Castilla y León, las principales comunidades de origen de quien visita Asturias.' },
    { etiqueta: 'Factor explicativo', titulo: 'Eventos',
      texto: 'Partidos, conciertos, festivales y ferias en Asturias, recopilados de fuentes oficiales y de los organizadores.' },
    { etiqueta: 'Factor explicativo', titulo: 'Wikipedia y Google Trends',
      texto: 'Interés en internet por los lugares más visitados (visitas a artículos y búsquedas). Una señal adelantada, no la base del modelo.' },
  ],

  // «Cómo funciona el modelo»: 4-5 frases. {algoritmo} lo rellena la web con metricas.algoritmo.
  modelo: [
    'Para cada día y zona calculamos un día normal y medimos cuánto se aleja la previsión de él.',
    'Un modelo de aprendizaje automático ({algoritmo}) aprende de los datos de movilidad, el calendario, los eventos y el tiempo qué días se llenan más.',
    'Hay dos modelos: uno a corto plazo (de 1 a 7 días), que usa además el tiempo y el interés en internet, y uno a largo plazo (más de 7 días), que solo usa calendario y eventos.',
    'El resultado se muestra como semáforo según las veces que supera el día normal, junto con los tres factores que más pesan y un rango probable.',
    'Se valida con días que el modelo no ha visto al entrenar, y esa fiabilidad se muestra en Gestión.',
  ],

  // Limitaciones
  limitaciones: [
    { titulo: 'Sin turistas extranjeros.', texto: 'Los datos de movilidad del MITMA no incluyen a los visitantes extranjeros, así que no podemos medirlos día a día.' },
    { titulo: 'Datos diarios hasta junio de 2025.', texto: 'El modelo aprende de ese periodo; lo posterior es previsión, no medida.' },
    { titulo: 'El umbral lo fijamos nosotros.', texto: 'El semáforo y los umbrales (ámbar, rojo) son una decisión del equipo, no un dato oficial de capacidad de ninguna zona.' },
    { titulo: 'Medimos presión relativa, no personas.', texto: 'La cifra es la presión frente a un día normal en la zona. No cuenta cuánta gente hay en los Lagos ni en un punto concreto: la unidad mínima es la zona.' },
    { titulo: 'Los cruceros quedan fuera.', texto: 'No tenemos las escalas realizadas por fecha, así que la llegada de cruceristas no entra en el modelo.' },
  ],

  // Mapa: fuente y licencia (datos de la persona 1, notas/coordinacion_web.md)
  mapa: {
    titulo: 'Mapa',
    texto: 'Límites municipales: © Instituto Geográfico Nacional (CC BY 4.0). El mapa no usa teselas externas.',
  },
};
