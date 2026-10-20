/* ==========================================================================
 * CAPA DE ACCESO A DATOS
 * --------------------------------------------------------------------------
 * La pestaña Inicio (interfaz/app.js) SOLO habla con window.Datos. Este
 * archivo no sabe de dónde salen los números: delega en window.FuenteDatos,
 * que define datos/fuente-modelo.js a partir de las salidas del modelo.
 * Cada función devuelve una promesa, que se guarda en caché por argumentos.
 *
 * Para cambiar de fuente basta con otro fichero que defina window.FuenteDatos
 * con las funciones de abajo (síncronas o con promesas) y cargarlo en
 * index.html en lugar de fuente-modelo.js. No hay que tocar interfaz/.
 *
 * --------------------------------------------------------------------------
 * CONTRATO
 *
 * Fechas: siempre texto 'YYYY-MM-DD' (hora local de Madrid).
 * Nivel:  'verde' | 'ambar' | 'rojo' | 'gris'   (gris = sin datos)
 * ratio:  visitantes previstos / visitantes de un día normal (1.45 = +45 %)
 *
 * Prevision = {
 *   zonaId, fecha, nivel,
 *   visitantes, min, max,   // número o null si nivel = 'gris'
 *   normal,                 // visitantes de un día normal en la zona
 *   ratio,                  // número o null
 *   esPrediccion,           // true = predicción, false = dato medido
 *   conMeteo,               // la predicción usa meteorología
 *   motivo?                 // texto, solo si nivel = 'gris'
 * }
 * Extras del modelo que la interfaz usa si están: incierto, conjunto, modelo, horizonte,
 * fechaEmision, observado, ratioObservado, nivelObservado (los tres últimos, solo en la demo).
 *
 * PrevisionPeriodo = Prevision con valores MEDIOS por día del periodo, más {
 *   desde, hasta, dias,     // fechas incluidas y número de días
 *   pico,                   // Prevision del día con más gente, o null si nivel = 'gris'
 *   diasPorNivel            // { verde, ambar, rojo } días de cada nivel, o null
 * }                         // conMeteo = true solo si todos los días tienen meteorología
 *
 * getInfo()                         -> { hoy, horizonteDias, diasConMeteo, umbrales:{ambar, rojo}, sintetico, demo }
 *                                      horizonteDias = días que se pueden elegir desde hoy (hasta el último día con predicción);
 *                                      diasConMeteo = días de antelación con previsión del tiempo; demo = modo ?demo=1
 * getZonas()                        -> [{ id, nombre, tipos:['costa'|'montana'|'ciudad'], concejos[], lugares[], vecinos|null, principal, sinDatos }]
 *                                      zonas del modelo (MITMA); concejos = nombres; principal = zona estrella (Picos de Europa)
 * getConcejos()                     -> [{ id, nombre, zonaId|null }]   id = código INE (5 cifras, '33xxx'),
 *                                      el mismo que usa interfaz/geo-asturias.js; zonaId null = fuera de las zonas del modelo
 * getSitios()                       -> [{ id, nombre, concejos:[INE], lat, lon, ubicacionAproximada, foto:{src, autor, licencia, pagina}|null }]
 *                                      sitios de interés; concejos[0] = concejo principal. NO llevan previsión propia:
 *                                      la interfaz muestra la de su concejo. Datos reales en datos/sitios.js
 * getEventos(desde, hasta?)         -> { fuente, hastaDatos, eventos:[{ id, titulo, categoria, inicio, fin, hora|null,
 *                                      lugar, concejo (INE)|null, asistencia|null, impacto|null, normalConcejo|null }] }
 *                                      eventos que se solapan con las fechas: festivos, partidos en casa y grandes eventos
 *                                      de la agenda de las salidas (los mismos que usa el modelo). hastaDatos = último día
 *                                      con eventos en la agenda
 * getCalendario(desde, dias)        -> [{ fecha, finde, festivo|null, puente|null, vacaciones|null }]
 * getProximoPuente(desde)           -> { nombre, inicio, fin } | null
 * getPrevisionDia(fecha)            -> Prevision[]   (una por zona)
 * getPrevisionPeriodo(desde, hasta) -> PrevisionPeriodo[]   (una por zona; ambas fechas incluidas)
 * getPrevisionConcejos(desde, hasta?) -> una por concejo, con { concejoId, zonaId } además de zonaId:
 *                                      sin hasta: Prevision del día; con hasta: PrevisionPeriodo
 * getSerieZona(zonaId, desde, dias) -> Prevision[]   (una por día)
 * getFactores(zonaId, fecha)        -> [{ clave, texto, efecto }]   efecto en % (38 = +38 %), los 3 que más pesan
 * getMejorMomento(zonaId, desde, dias) -> { dia: Prevision } | null   el día con menos presión de la ventana
 * getMejorDia(zonaId, fecha)        -> { fecha, nivel, ratio, visitantes, diferenciaPct, margen } | { fecha:null, margen } | null
 *                                      mejor día alternativo del modelo (alternativas.json); null si el día no está en alerta
 * getAlternativas(zonaId, fecha, hasta?) -> [Prevision + { nombre, minutos|null, km|null, delModelo? }]   zonas cercanas
 *                                      con hasta: PrevisionPeriodo, comparando la media del periodo
 * getPerfil(zonaId, fecha)          -> { deUnDia|null, conPernocta|null, asturias, restoEspana, mes, dias } en % | null
 *                                      media histórica del mes de fecha (en un periodo, el mes del primer día)
 * getFiabilidad(zonaId)             -> { porHorizonte: { '1'…'7', '8+': { nota, aciertoColor, n } }, algoritmo } | null
 *
 * Funciones avanzadas y Sobre los datos (pestanas/) leen window.DatosModelo (datos/datos.js)
 * directamente; de esta fachada solo usan getConcejos(), para los nombres de los concejos.
 * ========================================================================== */
window.Datos = (function () {
  'use strict';

  const METODOS = [
    'getInfo', 'getZonas', 'getConcejos', 'getSitios', 'getEventos', 'getCalendario', 'getProximoPuente', 'getPrevisionDia', 'getPrevisionPeriodo',
    'getPrevisionConcejos', 'getSerieZona',
    'getFactores', 'getMejorMomento', 'getMejorDia', 'getAlternativas', 'getPerfil', 'getFiabilidad',
  ];

  const fuente = window.FuenteDatos;
  if (!fuente) throw new Error('No hay ninguna fuente de datos cargada (falta window.FuenteDatos).');

  const faltan = METODOS.filter(m => typeof fuente[m] !== 'function');
  if (faltan.length) console.warn('La fuente de datos no implementa: ' + faltan.join(', '));

  const cache = new Map();
  const api = {};

  METODOS.forEach(m => {
    api[m] = function () {
      const args = Array.prototype.slice.call(arguments);
      if (typeof fuente[m] !== 'function') return Promise.reject(new Error('Función no disponible: ' + m));
      const clave = m + JSON.stringify(args);
      if (cache.has(clave)) return cache.get(clave);
      const p = Promise.resolve().then(() => fuente[m].apply(fuente, args));
      cache.set(clave, p);
      p.catch(() => cache.delete(clave));
      return p;
    };
  });
  return Object.freeze(api);
})();
