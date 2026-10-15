/* ==========================================================================
 * MÓDULO «datos»: salidas del modelo
 * --------------------------------------------------------------------------
 * Carga los cinco JSON del modelo (contrato en notas/contrato_web.md) y los
 * devuelve en un único objeto. Es la única puerta de entrada a las salidas.
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
 *      scripts/actualizar_datos_web.py): funciona con doble clic (file://).
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

  function validar(d) {
    const err = [];
    FICHEROS.forEach(n => {
      const f = d[n];
      if (!f || typeof f !== 'object') { err.push(`falta ${n}.json`); return; }
      CABECERA.concat(RAIZ[n]).forEach(k => { if (!(k in f)) err.push(`${n}.json: falta «${k}»`); });
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

  function leer() {
    if (window.SALIDAS_MODELO) return Promise.resolve(window.SALIDAS_MODELO);
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

  return Object.freeze({ cargar, validar, FICHEROS });
})();
