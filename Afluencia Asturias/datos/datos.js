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
 * Coherencia del rango probable: las salidas pueden traer una predicción fuera
 * de su propio rango p10-p90 (en zonas donde el modelo se queda corto siempre,
 * los dos cuantiles del error salen positivos). Al cargar se acota el rango para
 * que contenga la predicción (p10 = min(p10, predicción), p90 = max(p90,
 * predicción)), que es lo mismo que daría exigir q10 <= 0 <= q90 en el modelo,
 * y se recalcula «incierto» en los registros tocados. Ver coherencia().
 *
 * Fecha de los datos: las salidas se calculan un día (predicciones.fecha_hoy) y
 * la web puede abrirse semanas después. referencia() compara esa fecha con la
 * del reloj y dice qué día es «hoy» en pantalla, si de verdad es hoy y si la
 * previsión del tiempo sigue vigente. La usan las tres pestañas.
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

  /* ---------- Coherencia del rango probable ----------
   * Solo corrige registros incoherentes; los demás quedan como los dio el modelo. */
  function nivelDe(cociente, zona, um) {
    if (cociente == null || !isFinite(cociente)) return 'gris';
    const z = (um.por_zona && um.por_zona[zona]) || {};
    const ambar = z.umbral_ambar != null ? z.umbral_ambar : um.ambar;
    const rojo = z.umbral_rojo != null ? z.umbral_rojo : um.rojo;
    return cociente >= rojo ? 'rojo' : cociente >= ambar ? 'ambar' : 'verde';
  }
  // Acota p10 <= prediccion <= p90 en un registro. Devuelve true si lo ha cambiado
  function acotarRango(r, um) {
    if (r.prediccion == null || r.p10 == null || r.p90 == null) return false;
    if (r.p10 <= r.prediccion && r.prediccion <= r.p90) return false;
    r.p10 = Math.min(r.p10, r.prediccion);
    r.p90 = Math.max(r.p90, r.prediccion);
    if (r.color !== 'gris' && r.normal > 0) {
      r.incierto = nivelDe(r.p10 / r.normal, r.zona_mitma_id, um) !== nivelDe(r.p90 / r.normal, r.zona_mitma_id, um);
    }
    return true;
  }
  // Recuentos «entre X e Y días» de regulacion.por_zona: si el valor central queda fuera de su rango,
  // se recuentan con el calendario ya acotado (misma regla que el modelo: días con p10 o p90 sobre el umbral)
  function acotarRecuentos(reg, um) {
    let porZonaAnio = null;
    const filas = (zona, anio) => {
      if (!porZonaAnio) {
        porZonaAnio = {};
        reg.calendario_alertas.forEach(c => {
          const k = c.zona_mitma_id + '|' + c.fecha.slice(0, 4);
          (porZonaAnio[k] || (porZonaAnio[k] = [])).push(c);
        });
      }
      return porZonaAnio[zona + '|' + anio] || [];
    };
    const cuenta = (cal, campo, umbral) => cal.filter(c => c[campo] != null && c.normal > 0 && c[campo] / c.normal >= umbral).length;
    const fuera = (o, k) => o[k + '_min'] != null && o[k + '_max'] != null && (o[k + '_min'] > o[k] || o[k + '_max'] < o[k]);
    const ajustar = (o, k, cal, umbral) => {
      if (!fuera(o, k)) return;
      o[k + '_min'] = Math.min(o[k], cuenta(cal, 'p10', umbral));
      o[k + '_max'] = Math.max(o[k], cuenta(cal, 'p90', umbral));
    };
    (reg.por_zona || []).forEach(z => {
      const zu = (um.por_zona && um.por_zona[z.zona_mitma_id]) || {};
      const ambar = zu.umbral_ambar != null ? zu.umbral_ambar : um.ambar;
      const rojo = zu.umbral_rojo != null ? zu.umbral_rojo : um.rojo;
      (z.anios || []).filter(a => a.tipo === 'previsto').forEach(a => {
        if (!fuera(a, 'dias_rojos') && !fuera(a, 'dias_alerta')) return;
        const cal = filas(z.zona_mitma_id, a.anio);
        ajustar(a, 'dias_rojos', cal, rojo);
        ajustar(a, 'dias_alerta', cal, ambar);
      });
      (z.curva_umbral || []).filter(c => c.tipo === 'previsto' && fuera(c, 'dias'))
        .forEach(c => ajustar(c, 'dias', filas(z.zona_mitma_id, c.anio), c.umbral));
    });
  }
  // d: datos ya expandidos (cualquier subconjunto de los ficheros). Los modifica antes de congelarlos
  function coherencia(d) {
    if (d.predicciones && Array.isArray(d.predicciones.predicciones) && d.predicciones.umbrales) {
      d.predicciones.predicciones.forEach(r => acotarRango(r, d.predicciones.umbrales));
    }
    const reg = d.regulacion;
    if (reg && Array.isArray(reg.calendario_alertas) && reg.umbrales) {
      reg.calendario_alertas.forEach(r => acotarRango(r, reg.umbrales));
      acotarRecuentos(reg, reg.umbrales);
    }
    return d;
  }

  /* ---------- Fecha de los datos ---------- */
  // Fecha real 'YYYY-MM-DD' (hora local). ?hoy=YYYY-MM-DD la sustituye, para pruebas y capturas
  function hoyReal() {
    const m = /[?&]hoy=(\d{4}-\d{2}-\d{2})(?:&|$)/.exec((window.location && window.location.search) || '');
    if (m) return m[1];
    const d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  const diasEntre = (a, b) => Math.round((Date.parse(b + 'T00:00:00Z') - Date.parse(a + 'T00:00:00Z')) / 86400000);
  /**
   * fechaDatos: día en que se calcularon las salidas; primera y ultima: primer y último día con previsión;
   * real: fecha del reloj (por defecto, hoyReal()). Devuelve:
   *   hoy          día de referencia en pantalla: la fecha real si tiene previsión; si no, el día más cercano que la tenga
   *   esHoy        true solo si ese día es la fecha real (si no, no se puede llamar «hoy»)
   *   desfaseDias  días transcurridos desde que se calcularon los datos
   *   vigente      la previsión del tiempo de las salidas sigue sirviendo (calculadas hoy o ayer)
   *   fueraDeRango la fecha real es posterior al último día con previsión
   */
  function referencia(fechaDatos, primera, ultima, real) {
    real = real || hoyReal();
    const fueraDeRango = real > ultima;
    const hoy = real < primera ? primera : fueraDeRango ? ultima : real;
    const desfaseDias = Math.max(0, diasEntre(fechaDatos, real));
    return { fechaDatos, hoyReal: real, hoy, esHoy: hoy === real, desfaseDias, vigente: desfaseDias <= 1, fueraDeRango };
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
      coherencia(d);
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
      coherencia(d);
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

  return Object.freeze({ cargar, cargarInicio, validar, expandir, coherencia, hoyReal, referencia, diasEntre, FICHEROS });
})();
