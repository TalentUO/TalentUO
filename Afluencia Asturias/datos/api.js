/* ==========================================================================
 * CAPA DE ACCESO A DATOS
 * --------------------------------------------------------------------------
 * La interfaz SOLO habla con window.Datos. Este archivo no sabe de dónde
 * salen los números: delega en window.FuenteDatos, que hoy es
 * datos/fuente-ficticia.js.
 *
 * Para conectar el modelo real:
 *   1. Crea datos/fuente-modelo.js que defina window.FuenteDatos con las
 *      funciones de abajo. Pueden ser síncronas o devolver promesas
 *      (por ejemplo, con fetch('/api/prevision?fecha=...')).
 *   2. En index.html, cambia <script src="datos/fuente-ficticia.js"> por
 *      <script src="datos/fuente-modelo.js">.
 *   No hay que tocar nada en interfaz/.
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
 *
 * PrevisionPeriodo = Prevision con valores MEDIOS por día del periodo, más {
 *   desde, hasta, dias,     // fechas incluidas y número de días
 *   pico,                   // Prevision del día con más gente, o null si nivel = 'gris'
 *   diasPorNivel            // { verde, ambar, rojo } días de cada nivel, o null
 * }                         // conMeteo = true solo si todos los días tienen meteorología
 *
 * getInfo()                         -> { hoy, horizonteDias, diasConMeteo, umbrales:{ambar, rojo}, ficticio }
 *                                      horizonteDias = días que se pueden elegir desde hoy (366 = un año)
 * getZonas()                        -> [{ id, nombre, tipos:['costa'|'montana'|'ciudad'], concejos[], lugares[], vecinos, sinDatos }]
 * getConcejos()                     -> [{ id, nombre, zonaId }]   id = código INE (5 cifras, '33xxx'),
 *                                      el mismo que usa interfaz/geo-asturias.js; cada concejo pertenece a una zona
 * getSitios()                       -> [{ id, nombre, concejos:[INE], lat, lon, ubicacionAproximada, foto:{src, autor, licencia, pagina}|null }]
 *                                      sitios de interés; concejos[0] = concejo principal. NO llevan previsión propia:
 *                                      la interfaz muestra la de su concejo. Datos reales en datos/sitios.js
 * getEventos(desde, hasta?)         -> { fuente, actualizado, hastaDatos, eventos:[{ id, titulo, categoria, inicio, fin, hora|null,
 *                                      lugar, concejo (INE), lat, lon, asistencia, rango }] }
 *                                      eventos que se solapan con las fechas; hastaDatos = último día con eventos publicados.
 *                                      Datos reales de PredictHQ en datos/eventos.js (herramientas/eventos_phq.py)
 * getCalendario(desde, dias)        -> [{ fecha, finde, festivo|null, puente|null, vacaciones|null }]
 * getProximoPuente(desde)           -> { nombre, inicio, fin } | null
 * getPrevisionDia(fecha)            -> Prevision[]   (una por zona)
 * getPrevisionPeriodo(desde, hasta) -> PrevisionPeriodo[]   (una por zona; ambas fechas incluidas)
 * getPrevisionConcejos(desde, hasta?) -> una por concejo, con { concejoId, zonaId } además de zonaId:
 *                                      sin hasta: Prevision del día; con hasta: PrevisionPeriodo
 * getSerieZona(zonaId, desde, dias) -> Prevision[]   (una por día)
 * getFactores(zonaId, fecha)        -> [{ clave, texto, efecto }]   efecto en % (38 = +38 %), los 3 que más pesan
 * getMejorMomento(zonaId, desde, dias) -> { dia: Prevision, hora: { texto, nota } | null } | null
 * getMejorDia(zonaId, fecha)        -> { fecha, nivel, ratio, visitantes, diferenciaPct, margen } | { fecha:null, margen } | null
 *                                      mejor día alternativo del modelo (alternativas.json); null si el día no está en alerta
 * getAlternativas(zonaId, fecha, hasta?) -> [Prevision + { nombre, minutos|null, km|null, delModelo? }]   zonas cercanas
 *                                      con hasta: PrevisionPeriodo, comparando la media del periodo
 * getPerfil(zonaId, fecha, hasta?)  -> { deUnDia, conPernocta, asturias, restoEspana } en % | null
 *                                      con hasta: media del periodo
 * getFiabilidad(zonaId)             -> { porHorizonte: { '1'…'7', '8+': { nota, aciertoColor, n } }, algoritmo } | null
 *
 * Gestión y Sobre los datos (pestanas/) no usan esta fachada: leen window.DatosModelo directamente.
 * ========================================================================== */
window.Datos = (function () {
  'use strict';

  const METODOS = [
    'getInfo', 'getZonas', 'getConcejos', 'getSitios', 'getEventos', 'getCalendario', 'getProximoPuente', 'getPrevisionDia', 'getPrevisionPeriodo',
    'getPrevisionConcejos', 'getSerieZona',
    'getFactores', 'getMejorMomento', 'getMejorDia', 'getAlternativas', 'getPerfil', 'getFiabilidad',
  ];
  const SIN_CACHE = new Set();

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
      if (!SIN_CACHE.has(m) && cache.has(clave)) return cache.get(clave);
      const p = Promise.resolve().then(() => fuente[m].apply(fuente, args));
      if (!SIN_CACHE.has(m)) {
        cache.set(clave, p);
        p.catch(() => cache.delete(clave));
      }
      return p;
    };
  });

  api.limpiarCache = () => cache.clear();
  return Object.freeze(api);
})();
