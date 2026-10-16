/* ==========================================================================
 * MÓDULO «datos»: salidas del modelo
 * --------------------------------------------------------------------------
 * Carga los cinco JSON del modelo (contrato en notas/contrato_web.md) y los
 * devuelve en un único objeto. Es la única puerta de entrada a las salidas.
 *
 *   window.DatosModelo.cargarInicio() -> Promise<{ predicciones, alternativas, perfil,
 *     metricas (solo cabecera, algoritmo y fiabilidad), mapeo, calendario, sintetico, aviso }>
 *     Lo que necesita la pestaña Inicio. Sale de datos/modelo/salidas-inicio.js (≈1 MB), que
 *     index.html carga al principio: así la página se pinta sin esperar a los datos de Gestión.
 *
 *   window.DatosModelo.cargar() -> Promise<{
 *     predicciones, alternativas, regulacion, perfil, metricas,  // JSON tal cual
 *     mapeo,        // { origen, zonas:[{ zona_mitma_id, nombre, concejos_ine:[INE] }] }
 *     calendario,   // { origen, dias:[{ fecha, finde, festivo|null, puente, vacaciones|null, lagos_regulado }] } | null
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
 *      la primera vez que se pide (al abrir Gestión). Funciona con doble clic (file://).
 *   2. fetch de datos/modelo/<nombre>.json: solo con servidor (http://).
 * ========================================================================== */
window.DatosModelo = (function () {
  'use strict';

  const FICHEROS = ['predicciones', 'alternativas', 'regulacion', 'perfil', 'metricas'];
  const CABECERA = ['sintetico', 'generado', 'objetivo', 'umbrales'];
  // Campos obligatorios: raíz de cada fichero y de sus registros (muestra)
  const RAIZ = {
    predicciones: ['fecha_hoy', 'zonas', 'predicciones'],
    alternativas: ['alternativas'],
    regulacion: ['por_zona', 'lagos', 'calendario_alertas'],
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
    const lista = ficheros || FICHEROS;
    lista.forEach(n => {
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
    if (window.SALIDAS_MODELO) return Promise.resolve(window.SALIDAS_MODELO);
    return insertarScript('datos/modelo/salidas.js')
      .then(() => { if (!window.SALIDAS_MODELO) throw new Error('salidas.js no define SALIDAS_MODELO'); return window.SALIDAS_MODELO; })
      .catch(() => leerJSON());
  }

  function leerJSON() {
    const json = n => fetch('datos/modelo/' + n + '.json').then(r => {
      if (!r.ok) throw new Error(`no se puede leer datos/modelo/${n}.json (${r.status})`);
      return r.json();
    });
    const opcional = n => json(n).catch(() => null);
    return Promise.all(FICHEROS.concat('mapeo_zonas').map(json).concat(opcional('calendario'))).then(v => {
      const d = {};
      FICHEROS.forEach((n, i) => { d[n] = v[i]; });
      d.mapeo = v[FICHEROS.length];
      d.calendario = v[FICHEROS.length + 1];
      return d;
    });
  }

  // Inicio: solo lo que necesita la pestaña. Sin el fichero ligero, se usa el completo
  const FICHEROS_INICIO = ['predicciones', 'alternativas', 'perfil', 'metricas'];
  let promesaInicio = null;
  function cargarInicio() {
    if (promesaInicio) return promesaInicio;
    const b = window.SALIDAS_MODELO_INICIO;
    if (!b) { promesaInicio = cargar(); return promesaInicio; }
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
      d.sintetico = FICHEROS.some(n => bruto[n].sintetico === true);
      d.aviso = (FICHEROS.map(n => bruto[n].aviso).filter(Boolean)[0]) || null;
      return Object.freeze(d);
    });
    return promesa;
  }

  return Object.freeze({ cargar, cargarInicio, validar, FICHEROS });
})();
