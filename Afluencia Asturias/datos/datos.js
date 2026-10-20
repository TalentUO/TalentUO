/* ==========================================================================
 * MÓDULO «datos»: salidas del modelo
 * --------------------------------------------------------------------------
 * Carga las salidas del modelo (los cinco ficheros principales y sus anexos;
 * contrato en notas/contrato_web.md) y las devuelve en un único objeto. Es la
 * única puerta de entrada a las salidas.
 *
 *   window.DatosModelo.cargarInicio() -> Promise<{ predicciones, alternativas, perfil,
 *     metricas (solo cabecera, algoritmo y fiabilidad), mapeo, calendario, agenda, sintetico, aviso }>
 *     Lo que necesita la pestaña Inicio. Sale de datos/modelo/salidas-inicio.js (≈8 MB), que
 *     index.html carga al principio: así Inicio no espera a los datos de Funciones avanzadas (≈15 MB).
 *
 *   window.DatosModelo.cargar() -> Promise<{
 *     predicciones, alternativas, regulacion, perfil, metricas,  // JSON tal cual
 *     mapeo,        // { origen, zonas:[{ zona_mitma_id, nombre, concejos_ine:[INE] }] }
 *     calendario,   // { origen, dias:[{ fecha, finde, festivo|null, puente, vacaciones|null, lagos_regulado }] } | null
 *     horas,        // { origen, filas:[{ zona_mitma_id, mes, tipo_dia, hora, llegadas_ocio_media, n_dias }] } | null
 *     agenda,       // { origen, eventos:[{ id, titulo, categoria, inicio, fin, hora, lugar, concejo|null }] } | null (festivos y partidos)
 *     validacion,   // { algoritmo, horizonte, bloques:[…], filas:{ zona:[[fecha, real, previsto, normal, i_bloque]] } } | null (gráfica de Fiabilidad)
 *     sintetico,    // true si alguno de los cinco lo es
 *     aviso         // texto del aviso del modelo, o null
 *   }>
 *
 * La promesa es única (se carga una vez). Si falta un fichero o un campo
 * obligatorio, se rechaza con un Error cuyo mensaje lista los problemas.
 *
 * Origen de los datos, por orden:
 *   1. window.SALIDAS_MODELO (datos/modelo/salidas.js, generado por
 *      scripts/actualizar_datos_web.py). Si no está cargado, cargar() lo inserta
 *      la primera vez que se pide (al abrir Funciones avanzadas o Sobre los datos).
 *      Funciona con doble clic (file://).
 *   2. fetch de datos/modelo/<nombre>.json: solo con servidor (http://) y en local
 *      (en Vercel los JSON no se publican; ver .vercelignore).
 * ========================================================================== */
window.DatosModelo = (function () {
  'use strict';

  const FICHEROS = ['predicciones', 'alternativas', 'regulacion', 'perfil', 'metricas'];
  const CABECERA = ['sintetico', 'generado', 'objetivo', 'umbrales'];
  // Campos obligatorios: raíz de cada fichero y de sus registros (muestra)
  const RAIZ = {
    predicciones: ['fecha_hoy', 'zonas', 'predicciones'],
    alternativas: ['alternativas'],
    regulacion: ['por_zona', 'calendario_alertas'],
    perfil: ['perfil'],
    metricas: ['algoritmo', 'tablas', 'fiabilidad'],
  };
  const REGISTRO = {
    predicciones: ['predicciones', ['fecha', 'zona_mitma_id', 'nombre_zona', 'horizonte', 'prediccion', 'normal',
      'cociente', 'pct_sobre_normal', 'color', 'p10', 'p90', 'incierto', 'factores', 'sintetico', 'modelo', 'conjunto']],
    alternativas: ['alternativas', ['fecha', 'zona_mitma_id', 'nombre_zona', 'conjunto', 'modelo', 'horizonte',
      'cociente', 'color', 'mejor_dia', 'zona_alternativa']],
    regulacion: ['calendario_alertas', ['fecha', 'zona_mitma_id', 'prediccion', 'cociente', 'color', 'p10', 'p90', 'incierto']],
    perfil: ['perfil', ['zona_mitma_id', 'nombre_zona', 'mes', 'pct_desde_asturias', 'pct_resto_espana', 'pct_excursionistas_aprox']],
    metricas: ['fiabilidad', ['zona_mitma_id', 'nombre_zona', 'horizonte_txt', 'nota']],
  };
  const COLORES = ['verde', 'ambar', 'rojo', 'gris'];

  // ficheros: los que se comprueban (por defecto, los cinco). En metricas ligero (Inicio) no hay «tablas»
  function validar(d, ficheros) {
    const err = [];
    (ficheros || FICHEROS).forEach(n => {
      const f = d[n];
      if (!f || typeof f !== 'object') { err.push(`falta ${n}.json`); return; }
      const raiz = ficheros && n === 'metricas' ? ['algoritmo', 'fiabilidad'] : RAIZ[n];
      CABECERA.concat(raiz).forEach(k => { if (!(k in f)) err.push(`${n}.json: falta «${k}»`); });
      const [lista, campos] = REGISTRO[n];
      const regs = Array.isArray(f[lista]) ? f[lista] : [];
      // Basta con mirar una muestra: el validador del modelo ya revisa todo
      regs.slice(0, 300).forEach((r, i) => {
        campos.forEach(k => { if (!(k in r)) err.push(`${n}.json → ${lista}[${i}]: falta «${k}»`); });
        if ('color' in r && COLORES.indexOf(r.color) === -1) err.push(`${n}.json → ${lista}[${i}]: color no válido «${r.color}»`);
      });
    });
    if (d.predicciones && Array.isArray(d.predicciones.zonas)) {
      d.predicciones.zonas.forEach((z, i) => ['zona_mitma_id', 'nombre_zona'].forEach(k => {
        if (!(k in z)) err.push(`predicciones.json → zonas[${i}]: falta «${k}»`);
      }));
    }
    if (!d.mapeo || !Array.isArray(d.mapeo.zonas)) err.push('falta el mapeo de zonas (ejecuta scripts/actualizar_datos_web.py)');
    // Errores repetidos: se agrupan para que el mensaje sea legible
    const unicos = Array.from(new Set(err));
    return unicos.length > 15 ? unicos.slice(0, 15).concat(`… y ${unicos.length - 15} problemas más`) : unicos;
  }

  // Los .js generados guardan las listas largas por columnas ({ __columnas, __filas }) para pesar menos;
  // aquí se reconstruyen los mismos objetos que en los JSON del contrato (compactar() en scripts/actualizar_datos_web.py).
  function expandir(v) {
    if (Array.isArray(v)) return v.map(expandir);
    if (v === null || typeof v !== 'object') return v;
    if (Array.isArray(v.__columnas) && Array.isArray(v.__filas)) {
      const cols = v.__columnas;
      return v.__filas.map(f => {
        const o = {};
        for (let i = 0; i < cols.length; i++) o[cols[i]] = expandir(f[i]);
        return o;
      });
    }
    const o = {};
    for (const k of Object.keys(v)) o[k] = expandir(v[k]);
    return o;
  }

  // Inserta un <script> (funciona también desde file://, donde fetch no puede leer ficheros)
  function insertarScript(src) {
    return new Promise((ok, ko) => {
      const s = document.createElement('script');
      s.src = src;
      s.onload = ok;
      s.onerror = () => ko(new Error('no se puede cargar ' + src));
      document.head.appendChild(s);
    });
  }

  function leer() {
    if (window.SALIDAS_MODELO) return Promise.resolve(expandir(window.SALIDAS_MODELO));
    return insertarScript('datos/modelo/salidas.js')
      .then(() => { if (!window.SALIDAS_MODELO) throw new Error('salidas.js no define SALIDAS_MODELO'); return expandir(window.SALIDAS_MODELO); })
      // Sin salidas.js se prueban los JSON; si tampoco están, el error cuenta las dos cosas
      .catch(errScript => leerJSON().catch(errJSON => {
        throw new Error(errScript.message + '; y tampoco hay copia en JSON: ' + errJSON.message);
      }));
  }

  function leerJSON() {
    const json = n => fetch('datos/modelo/' + n + '.json').then(r => {
      if (!r.ok) throw new Error(`no se puede leer datos/modelo/${n}.json (${r.status})`);
      return r.json();
    });
    const opcional = n => json(n).catch(() => null);
    return Promise.all(FICHEROS.concat('mapeo_zonas').map(json).concat(opcional('calendario'), opcional('horas'), opcional('agenda'), opcional('validacion'))).then(v => {
      const d = {};
      FICHEROS.forEach((n, i) => { d[n] = v[i]; });
      d.mapeo = v[FICHEROS.length];
      d.calendario = v[FICHEROS.length + 1];
      d.horas = v[FICHEROS.length + 2];
      d.agenda = v[FICHEROS.length + 3];
      d.validacion = v[FICHEROS.length + 4];
      return d;
    });
  }

  // Inicio: solo lo que necesita la pestaña. Sin el fichero ligero, se usa el completo
  const FICHEROS_INICIO = ['predicciones', 'alternativas', 'perfil', 'metricas'];
  let promesaInicio = null;
  function cargarInicio() {
    if (promesaInicio) return promesaInicio;
    if (!window.SALIDAS_MODELO_INICIO) { promesaInicio = cargar(); return promesaInicio; }
    const b = expandir(window.SALIDAS_MODELO_INICIO);
    promesaInicio = Promise.resolve().then(() => {
      const errores = validar(b, FICHEROS_INICIO);
      if (errores.length) {
        const e = new Error('Las salidas del modelo no cumplen el contrato:\n- ' + errores.join('\n- '));
        e.errores = errores;
        throw e;
      }
      const d = {};
      FICHEROS_INICIO.forEach(n => { d[n] = b[n]; });
      d.mapeo = b.mapeo;
      d.calendario = b.calendario || null;
      d.agenda = b.agenda || null;
      d.sintetico = FICHEROS_INICIO.some(n => b[n].sintetico === true);
      d.aviso = (FICHEROS_INICIO.map(n => b[n].aviso).filter(Boolean)[0]) || null;
      return Object.freeze(d);
    });
    return promesaInicio;
  }

  let promesa = null;
  function cargar() {
    if (promesa) return promesa;
    promesa = leer().then(bruto => {
      const errores = validar(bruto);
      if (errores.length) {
        const e = new Error('Las salidas del modelo no cumplen el contrato:\n- ' + errores.join('\n- '));
        e.errores = errores;
        throw e;
      }
      const d = {};
      FICHEROS.forEach(n => { d[n] = bruto[n]; });
      d.mapeo = bruto.mapeo;
      d.calendario = bruto.calendario || null;
      d.horas = bruto.horas || null;
      d.agenda = bruto.agenda || null;
      d.validacion = bruto.validacion || null;
      d.sintetico = FICHEROS.some(n => bruto[n].sintetico === true);
      d.aviso = (FICHEROS.map(n => bruto[n].aviso).filter(Boolean)[0]) || null;
      return Object.freeze(d);
    });
    return promesa;
  }

  return Object.freeze({ cargar, cargarInicio, validar, expandir, FICHEROS });
})();
