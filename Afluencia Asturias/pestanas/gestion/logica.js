/* ==========================================================================
 * LÓGICA de la pestaña Gestión (persona 2). Funciones puras, sin DOM.
 * Entrada: el objeto `datos` de window.DatosModelo (formato en
 * notas/contrato_web.md). Salida: estructuras listas para pintar.
 * Pruebas: pestanas/gestion/pruebas.html (se abre en el navegador).
 * No inventa cifras: todo sale de regulacion.json, predicciones.json y
 * metricas.json.
 * ========================================================================== */
(function (raiz, fabrica) {
  const api = fabrica(raiz);
  if (typeof module === 'object' && module.exports) module.exports = api;
  raiz.GestionLogica = api;
})(typeof window !== 'undefined' ? window : globalThis, function (raiz) {
  'use strict';

  const EPS = 1e-9;
  const configBase = () => raiz.GestionConfig || {};

  /* ---------- Zonas ---------- */

  /** Zonas con la principal primero (Picos de Europa), el resto por nombre. */
  function zonas(datos) {
    return datos.predicciones.zonas.slice().sort((a, b) =>
      (b.es_principal ? 1 : 0) - (a.es_principal ? 1 : 0) || a.nombre_zona.localeCompare(b.nombre_zona, 'es'));
  }
  const zonaPrincipal = datos => (zonas(datos)[0] || null);
  const nombreZona = (datos, id) => {
    const z = datos.predicciones.zonas.find(x => x.zona_mitma_id === id);
    return z ? z.nombre_zona : id;
  };

  /* ---------- Días por encima de un umbral ---------- */

  /** Umbrales (veces el día normal) para los que el modelo ya trae los días observados. */
  function umbralesDisponibles(datos) {
    const s = new Set();
    datos.regulacion.por_zona.forEach(z => z.curva_umbral.forEach(c => s.add(c.umbral)));
    return Array.from(s).sort((a, b) => a - b);
  }

  /** Años que hay en regulacion.json, con su tipo (observado | previsto). */
  function aniosDisponibles(datos) {
    const m = new Map();
    datos.regulacion.por_zona.forEach(z => z.anios.forEach(a => m.set(a.anio, a.tipo)));
    return Array.from(m, ([anio, tipo]) => ({ anio, tipo })).sort((a, b) => a.anio - b.anio);
  }

  function filasCalendario(datos, zonaId, anio) {
    const pre = String(anio) + '-';
    return datos.regulacion.calendario_alertas.filter(c => c.zona_mitma_id === zonaId && c.fecha.startsWith(pre));
  }

  /**
   * Días de `anio` en los que la zona supera `umbral` (veces el día normal).
   * - previsto: se recalcula día a día con el cociente de calendario_alertas
   *   (vale cualquier umbral); min/max usan p10/p90 sobre el mismo `normal`. Por el
   *   redondeo del JSON, fuera de los umbrales por defecto puede diferir de
   *   curva_umbral en 1-3 días.
   * - observado: solo hay la curva del modelo (rejilla de umbralesDisponibles);
   *   fuera de la rejilla devuelve dias = null (no se interpola).
   * Devuelve { anio, tipo, dias, min, max, exacto } o null si no hay ese año.
   */
  function diasSobreUmbral(datos, zonaId, anio, umbral) {
    const zona = datos.regulacion.por_zona.find(z => z.zona_mitma_id === zonaId);
    if (!zona) return null;
    const info = zona.anios.find(a => a.anio === anio);
    if (!info) return null;
    if (info.tipo === 'previsto') {
      // Con los umbrales de la cabecera se cuenta por el color del modelo (exacto): el JSON
      // redondea el cociente a 3 decimales y en el umbral justo bailaría algún día.
      const um = datos.regulacion.umbrales || {};
      const esRojo = Math.abs(umbral - um.rojo) < 1e-6, esAmbar = Math.abs(umbral - um.ambar) < 1e-6;
      let dias = 0, min = 0, max = 0;
      filasCalendario(datos, zonaId, anio).forEach(f => {
        if (f.color === 'gris' || f.cociente == null) return;
        if (esRojo ? f.color === 'rojo' : esAmbar ? (f.color === 'rojo' || f.color === 'ambar') : f.cociente >= umbral - EPS) dias++;
        if (f.normal) {
          if (f.p10 != null && f.p10 / f.normal >= umbral - EPS) min++;
          if (f.p90 != null && f.p90 / f.normal >= umbral - EPS) max++;
        }
      });
      return { anio, tipo: info.tipo, dias, min, max, exacto: true };
    }
    const c = zona.curva_umbral.find(x => x.anio === anio && Math.abs(x.umbral - umbral) < 1e-6);
    return c
      ? { anio, tipo: info.tipo, dias: c.dias, min: c.dias_min ?? null, max: c.dias_max ?? null, exacto: true }
      : { anio, tipo: info.tipo, dias: null, min: null, max: null, exacto: false };
  }

  /** Veredicto orientativo según los días al año (criterio editable en config-gestion.js). */
  function veredicto(dias, config) {
    const crit = (config || configBase()).criterio;
    if (dias == null) return 'sin_dato';
    return dias >= crit.estudiar ? 'estudiar' : dias >= crit.vigilar ? 'vigilar' : 'ok';
  }

  /**
   * Tabla «¿hace falta regular?»: por zona (principal primero), los días de cada año
   * con el umbral dado y el veredicto del año de referencia (el primer año previsto
   * por defecto, que es el que importa a quien planifica).
   */
  function tablaRegulacion(datos, umbral, opciones) {
    const o = opciones || {};
    const anios = aniosDisponibles(datos);
    const ref = o.anioReferencia ?? (anios.filter(a => a.tipo === 'previsto')[0] || anios[anios.length - 1]).anio;
    return zonas(datos).map(z => {
      const porAnio = anios.map(a => diasSobreUmbral(datos, z.zona_mitma_id, a.anio, umbral)).filter(Boolean);
      const r = porAnio.find(x => x.anio === ref);
      return {
        zona_mitma_id: z.zona_mitma_id, nombre_zona: z.nombre_zona, es_principal: !!z.es_principal,
        anios: porAnio, anioReferencia: ref,
        dias: r ? r.dias : null, veredicto: veredicto(r ? r.dias : null, o.config),
      };
    });
  }

  /* ---------- Comparación con los días de acceso regulado a los Lagos ---------- */

  /**
   * Por año: días con acceso regulado, y cuántas alertas (ámbar+rojo) y días rojos
   * caen dentro / fuera de esos días (umbrales por defecto del modelo).
   * `calibracion` trae qué umbral reproduce mejor el calendario regulado (F1).
   */
  function compararLagos(datos) {
    const l = datos.regulacion.lagos;
    if (!l) return null;
    const pct = (a, b) => (b > 0 ? Math.round(100 * a / b) : null);
    const anios = l.por_anio.map(a => {
      const totalAlerta = a.alerta_en_dias_regulados + a.alerta_fuera_de_regulacion;
      const totalRojos = a.rojos_en_dias_regulados + a.rojos_fuera_de_regulacion;
      return {
        anio: a.anio, tipo: a.tipo, supuesta: !!a.regulacion_supuesta,
        dias_regulados: a.dias_regulados,
        alerta_en_regulados: a.alerta_en_dias_regulados, alerta_fuera: a.alerta_fuera_de_regulacion,
        rojos_en_regulados: a.rojos_en_dias_regulados, rojos_fuera: a.rojos_fuera_de_regulacion,
        regulados_sin_alerta: Math.max(0, a.dias_regulados - a.alerta_en_dias_regulados),
        pct_alertas_en_regulados: pct(a.alerta_en_dias_regulados, totalAlerta),
        pct_rojos_en_regulados: pct(a.rojos_en_dias_regulados, totalRojos),
      };
    });
    const cal = l.calibracion || {};
    const rel = (cal.observado_2023_2024 || {}).relativo || null;
    return {
      zona_mitma_id: l.zona_mitma_id, nombre_zona: l.nombre_zona, anios,
      calibracion: rel ? { mejor_umbral: rel.mejor_umbral, f1: rel.f1, precision: rel.precision, recall: rel.recall } : null,
      nota: cal.nota || null,
    };
  }

  /* ---------- Alertas de las próximas semanas ---------- */

  function accionPara(color, config) {
    const ac = (config || configBase()).acciones || {};
    return ac[color] || ac.gris || { titulo: '', texto: '' };
  }

  function sumarDias(iso, n) {
    const d = new Date(iso + 'T12:00:00Z');
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }

  /**
   * Alertas desde `desde` (por defecto fecha_hoy) durante `dias` días. Para cada
   * fecha × zona usa futuro_corto si existe y, si no, futuro_largo (regla del contrato);
   * si ninguno cubre el día, cae a calendario_alertas. Devuelve todas las filas
   * (el filtro por color lo hace quien pinta) con la acción sugerida.
   */
  function alertasProximas(datos, opciones) {
    const o = opciones || {};
    const desde = o.desde || datos.predicciones.fecha_hoy;
    const dias = o.dias ?? (o.config || configBase()).diasAlertas ?? 28;
    const hasta = sumarDias(desde, dias - 1);
    const rango = { futuro_corto: 2, futuro_largo: 1 };
    const elegida = new Map();
    datos.predicciones.predicciones.forEach(p => {
      const r = rango[p.conjunto];
      if (!r || p.fecha < desde || p.fecha > hasta) return;
      const k = p.fecha + '|' + p.zona_mitma_id;
      const previa = elegida.get(k);
      if (!previa || r > previa.r || (r === previa.r && p.horizonte < previa.p.horizonte)) elegida.set(k, { p, r });
    });
    const filas = [];
    datos.regulacion.calendario_alertas.forEach(c => {
      if (c.fecha < desde || c.fecha > hasta) return;
      const e = elegida.get(c.fecha + '|' + c.zona_mitma_id);
      const p = e ? e.p : c;
      filas.push({
        fecha: c.fecha, zona_mitma_id: c.zona_mitma_id, nombre_zona: nombreZona(datos, c.zona_mitma_id),
        color: p.color, cociente: p.cociente, prediccion: p.prediccion, normal: p.normal,
        p10: p.p10, p90: p.p90, incierto: !!p.incierto,
        horizonte: e ? p.horizonte : null, modelo: e ? p.modelo : 'largo',
        lagos_regulado: c.lagos_regulado, calendario_supuesto: !!c.calendario_supuesto,
        factores: e ? p.factores : null,
        accion: accionPara(p.color, o.config),
      });
    });
    const orden = { rojo: 0, ambar: 1, verde: 2, gris: 3 };
    return filas.sort((a, b) => a.fecha.localeCompare(b.fecha) || orden[a.color] - orden[b.color] ||
      (b.cociente ?? -1) - (a.cociente ?? -1));
  }

  /* ---------- Fiabilidad ---------- */

  const ordenHorizonte = h => (h === '8+' ? 99 : parseInt(h, 10));

  /**
   * Fiabilidad por zona y horizonte (de metricas.json). Cada fila conserva la `nota`
   * del modelo. `grupos` resume 1-3, 4-7 y 8+ días ponderando por `n`.
   */
  function fiabilidad(datos, zonaId) {
    const filas = datos.metricas.fiabilidad.filter(f => f.zona_mitma_id === zonaId)
      .slice().sort((a, b) => ordenHorizonte(a.horizonte_txt) - ordenHorizonte(b.horizonte_txt));
    const defGrupos = [['1-3 días', ['1', '2', '3']], ['4-7 días', ['4', '5', '6', '7']], ['8 días o más', ['8+']]];
    const grupos = defGrupos.map(([etiqueta, hs]) => {
      const g = filas.filter(f => hs.includes(f.horizonte_txt));
      if (!g.length) return null;
      const n = g.reduce((s, f) => s + f.n, 0);
      const pond = k => {
        const v = g.filter(f => f[k] != null);
        const nn = v.reduce((s, f) => s + f.n, 0);
        return nn ? v.reduce((s, f) => s + f[k] * f.n, 0) / nn : null;
      };
      const rojos = g.reduce((s, f) => s + (f.rojos_obs || 0), 0);
      const detectados = g.filter(f => f.recall_rojo != null && f.rojos_obs)
        .reduce((s, f) => s + Math.round(f.recall_rojo * f.rojos_obs), 0);
      return {
        etiqueta, horizontes: hs, n, acierto_color: pond('acierto_color'), wape: pond('wape'), cobertura: pond('cobertura'),
        rojos_obs: rojos, rojos_detectados: rojos ? detectados : null, recall_rojo: rojos ? detectados / rojos : null,
      };
    }).filter(Boolean);
    return { zona_mitma_id: zonaId, nombre_zona: nombreZona(datos, zonaId), filas, grupos };
  }

  /* ---------- Exportación CSV ---------- */

  const celdaCSV = v => {
    if (v == null) return '';
    const s = typeof v === 'number' ? String(v).replace('.', ',') : String(v);
    return /[;"\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  /** CSV separado por «;» y decimales con coma (para abrir en Excel en español). */
  const aCSV = filas => filas.map(f => f.map(celdaCSV).join(';')).join('\r\n');

  const NOMBRE_COLOR = { verde: 'verde', ambar: 'ámbar', rojo: 'rojo', gris: 'sin datos' };
  const AVISO_CSV = 'DATOS SINTÉTICOS - NO SON REALES';

  /** CSV de la previsión que se está mostrando (lista de alertasProximas). */
  function csvPrevision(filas, sintetico) {
    const cab = ['fecha', 'zona', 'color', 'veces_dia_normal', 'visitantes_previstos', 'dia_normal', 'minimo_p10', 'maximo_p90',
      'incierto', 'lagos_regulado', 'accion_sugerida'];
    if (sintetico) cab.push('aviso');
    const cuerpo = filas.map(f => {
      const r = [f.fecha, f.nombre_zona, NOMBRE_COLOR[f.color] || f.color, f.cociente, f.prediccion, f.normal, f.p10, f.p90,
        f.incierto ? 'sí' : 'no', f.lagos_regulado == null ? '' : (f.lagos_regulado ? 'sí' : 'no'), f.accion.texto];
      if (sintetico) r.push(AVISO_CSV);
      return r;
    });
    return aCSV([cab].concat(cuerpo));
  }

  /** CSV de la tabla de días sobre el umbral (salida de tablaRegulacion). */
  function csvRegulacion(tabla, umbral, sintetico) {
    const anios = tabla.length ? tabla[0].anios : [];
    const cab = ['zona', 'umbral_veces_dia_normal']
      .concat(anios.flatMap(a => [`dias_${a.anio}_${a.tipo}`, `min_${a.anio}`, `max_${a.anio}`])).concat(['veredicto']);
    if (sintetico) cab.push('aviso');
    const cuerpo = tabla.map(t => {
      const r = [t.nombre_zona, umbral].concat(t.anios.flatMap(a => [a.dias, a.min, a.max])).concat([t.veredicto]);
      if (sintetico) r.push(AVISO_CSV);
      return r;
    });
    return aCSV([cab].concat(cuerpo));
  }

  return { zonas, zonaPrincipal, nombreZona, umbralesDisponibles, aniosDisponibles, diasSobreUmbral, veredicto, tablaRegulacion,
    compararLagos, accionPara, alertasProximas, fiabilidad, aCSV, csvPrevision, csvRegulacion, sumarDias };
});
