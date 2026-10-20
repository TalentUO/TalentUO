/* ==========================================================================
 * LÓGICA de la pestaña Funciones avanzadas. Funciones puras, sin DOM.
 * Entrada: el objeto `datos` de window.DatosModelo (datos/datos.js; formato en
 * notas/contrato_web.md). Salida: estructuras listas para pintar.
 * Pruebas: pestanas/gestion/pruebas.html (se abre en el navegador).
 * No inventa cifras: todo sale de regulacion.json, predicciones.json,
 * metricas.json y perfil.json (con horas.json, si está).
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
  const nombreZona = (datos, id) => {
    const z = datos.predicciones.zonas.find(x => x.zona_mitma_id === id);
    return z ? z.nombre_zona : id;
  };

  /* ---------- Umbrales ---------- */

  /** Umbrales (veces el día normal) de la rejilla del modelo: son los pasos de los deslizadores. */
  function umbralesDisponibles(datos) {
    const s = new Set();
    datos.regulacion.por_zona.forEach(z => z.curva_umbral.forEach(c => s.add(c.umbral)));
    return Array.from(s).sort((a, b) => a - b);
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
    // El acceso regulado a los Lagos solo se marca en su zona (calendario_alertas lo trae en todas)
    const zonaLagos = (datos.regulacion.lagos && datos.regulacion.lagos.zona_mitma_id) || null;
    const nombres = new Map(datos.predicciones.zonas.map(z => [z.zona_mitma_id, z.nombre_zona]));
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
        fecha: c.fecha, zona_mitma_id: c.zona_mitma_id, nombre_zona: nombres.get(c.zona_mitma_id) || c.zona_mitma_id,
        color: p.color, cociente: p.cociente, prediccion: p.prediccion, normal: p.normal,
        p10: p.p10, p90: p.p90, incierto: !!p.incierto,
        horizonte: e ? p.horizonte : null, modelo: e ? p.modelo : 'largo',
        lagos_regulado: c.zona_mitma_id === zonaLagos ? c.lagos_regulado : null, calendario_supuesto: !!c.calendario_supuesto,
        factores: e ? p.factores : null,
        accion: accionPara(p.color, o.config),
      });
    });
    const orden = { rojo: 0, ambar: 1, verde: 2, gris: 3 };
    return filas.sort((a, b) => a.fecha.localeCompare(b.fecha) || orden[a.color] - orden[b.color] ||
      (b.cociente ?? -1) - (a.cociente ?? -1));
  }

  /* ---------- Previsión de saturación (solo predicción, nunca años observados) ---------- */

  /** Último día con previsión: el final de calendario_alertas o de las predicciones futuras. */
  function finPrevision(datos) {
    let fin = datos.predicciones.fecha_hoy;
    datos.regulacion.calendario_alertas.forEach(c => { if (c.fecha > fin) fin = c.fecha; });
    datos.predicciones.predicciones.forEach(p => { if (p.conjunto !== 'historico' && p.fecha > fin) fin = p.fecha; });
    return fin;
  }

  const diasEntreISO = (a, b) => Math.round((Date.parse(b + 'T12:00:00Z') - Date.parse(a + 'T12:00:00Z')) / 86400000);

  /**
   * ¿La fila (de alertasProximas) supera el umbral? Con los umbrales de la cabecera
   * se usa el color del modelo (exacto); con otro, el cociente redondeado del JSON.
   */
  function superaUmbral(fila, umbral, umbrales) {
    if (!fila || fila.color === 'gris' || fila.cociente == null) return false;
    const um = umbrales || {};
    if (um.rojo != null && Math.abs(umbral - um.rojo) < 1e-6) return fila.color === 'rojo';
    if (um.ambar != null && Math.abs(umbral - um.ambar) < 1e-6) return fila.color === 'rojo' || fila.color === 'ambar';
    return fila.cociente >= umbral - EPS;
  }

  /** Agrupa fechas ISO ordenadas en rachas de días seguidos: [{ desde, hasta, dias }]. */
  function rachas(fechas) {
    const out = [];
    fechas.forEach(f => {
      const u = out[out.length - 1];
      if (u && sumarDias(u.hasta, 1) === f) { u.hasta = f; u.dias++; } else out.push({ desde: f, hasta: f, dias: 1 });
    });
    return out;
  }

  /**
   * Días con saturación prevista entre `desde` y `hasta` (incluidos) para cada zona.
   * Usa la misma predicción que las alertas: futuro_corto, si no futuro_largo y, más
   * allá, la previsión de calendario_alertas. Cada día lleva `lejana` = true cuando
   * solo hay previsión de calendario (sin modelo de corto ni de largo plazo).
   * `filas` (opcional): las de alertasProximas para ese mismo rango, si ya se tienen
   * (así, al mover el deslizador del umbral no se recalculan).
   * Devuelve [{ zona_mitma_id, nombre_zona, es_principal, dias:[fila], rachas, pico }].
   */
  function previsionSaturacion(datos, opciones) {
    const o = opciones || {};
    const desde = o.desde || datos.predicciones.fecha_hoy;
    const hasta = o.hasta || finPrevision(datos);
    const umbrales = datos.regulacion.umbrales || datos.predicciones.umbrales;
    const umbral = o.umbral ?? umbrales.rojo;
    const filas = o.filas || alertasProximas(datos, { desde, dias: diasEntreISO(desde, hasta) + 1, config: o.config });
    const porZona = new Map();
    filas.forEach(f => { if (superaUmbral(f, umbral, umbrales)) (porZona.get(f.zona_mitma_id) || porZona.set(f.zona_mitma_id, []).get(f.zona_mitma_id)).push(f); });
    return zonas(datos).map(z => {
      const dias = (porZona.get(z.zona_mitma_id) || [])
        .map(f => Object.assign({}, f, { lejana: f.horizonte == null }))
        .sort((a, b) => a.fecha.localeCompare(b.fecha));
      const pico = dias.reduce((m, d) => (!m || d.cociente > m.cociente ? d : m), null);
      return { zona_mitma_id: z.zona_mitma_id, nombre_zona: z.nombre_zona, es_principal: !!z.es_principal,
        dias, rachas: rachas(dias.map(d => d.fecha)), pico };
    });
  }

  /* ---------- Concejos de cada zona (mapeo del modelo) ---------- */

  /** Códigos INE de los concejos de una zona, tal cual el mapeo. */
  function concejosDeZona(datos, zonaId) {
    const z = ((datos.mapeo && datos.mapeo.zonas) || []).find(x => x.zona_mitma_id === zonaId);
    return z ? z.concejos_ine.slice() : [];
  }

  /** Zonas (ids) que incluyen un concejo; puede ser más de una si el mapeo lo repite. */
  function zonasDeConcejo(datos, ine) {
    return ((datos.mapeo && datos.mapeo.zonas) || []).filter(z => z.concejos_ine.indexOf(ine) !== -1).map(z => z.zona_mitma_id);
  }

  /** Texto sin tildes y en minúsculas, para buscar. */
  const normalizar = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

  /**
   * Busca en un índice [{ nombre, ... }]: primero los que empiezan por el texto,
   * luego los que lo contienen en alguna palabra o en cualquier parte.
   */
  function buscar(indice, texto, max) {
    const t = normalizar(texto);
    if (!t) return indice.slice(0, max || indice.length);
    const puntua = x => {
      const n = normalizar(x.nombre);
      if (n.startsWith(t)) return 0;
      if (n.split(/[\s()+\-/]+/).some(p => p.startsWith(t))) return 1;
      return n.indexOf(t) !== -1 ? 2 : -1;
    };
    return indice.map(x => ({ x, p: puntua(x) })).filter(r => r.p >= 0)
      .sort((a, b) => a.p - b.p || a.x.nombre.localeCompare(b.x.nombre, 'es'))
      .slice(0, max || indice.length).map(r => r.x);
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

  /** CSV de los días con saturación prevista (salida de previsionSaturacion). */
  function csvSaturacion(resultado, umbral, sintetico) {
    const cab = ['fecha', 'zona', 'umbral_veces_dia_normal', 'color', 'veces_dia_normal', 'visitantes_previstos', 'dia_normal',
      'minimo_p10', 'maximo_p90', 'incierto', 'solo_calendario', 'lagos_regulado', 'accion_sugerida'];
    if (sintetico) cab.push('aviso');
    const cuerpo = [];
    resultado.forEach(z => z.dias.forEach(f => {
      const r = [f.fecha, z.nombre_zona, umbral, NOMBRE_COLOR[f.color] || f.color, f.cociente, f.prediccion, f.normal, f.p10, f.p90,
        f.incierto ? 'sí' : 'no', f.lejana ? 'sí' : 'no', f.lagos_regulado == null ? '' : (f.lagos_regulado ? 'sí' : 'no'), f.accion.texto];
      if (sintetico) r.push(AVISO_CSV);
      cuerpo.push(r);
    }));
    cuerpo.sort((a, b) => a[0].localeCompare(b[0]) || String(a[1]).localeCompare(String(b[1]), 'es'));
    return aCSV([cab].concat(cuerpo));
  }

  /**
   * CSV del perfil del visitante: todas las zonas y meses de perfil.json y, si hay datos.horas,
   * la hora con más llegadas de ocio en laborables y en fines de semana o festivos.
   */
  function csvPerfil(datos, sintetico) {
    const MES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
    const horas = datos.horas && datos.horas.filas;
    const pico = (zona, mes, tipo) => {
      if (!horas) return [null, null];
      const f = horas.filter(x => x.zona_mitma_id === zona && x.mes === mes && x.tipo_dia === tipo);
      if (!f.length) return [null, null];
      const m = f.reduce((x, y) => (y.llegadas_ocio_media > x.llegadas_ocio_media ? y : x));
      return [`${m.hora}-${m.hora + 1} h`, Math.round(m.llegadas_ocio_media)];
    };
    const cab = ['zona', 'mes', 'dias_de_muestra', 'llegadas_ocio_media_dia', 'pct_ocio_desde_asturias', 'pct_ocio_resto_espana',
      'pct_todas_desde_asturias', 'pct_todas_resto_espana', 'pernoctaciones_por_100_llegadas', 'pct_de_un_dia_aprox',
      'hora_punta_laborable', 'llegadas_hora_punta_laborable', 'hora_punta_finde_o_festivo', 'llegadas_hora_punta_finde_o_festivo'];
    if (sintetico) cab.push('aviso');
    const r1 = v => (v == null ? null : Math.round(v * 10) / 10);
    const orden = new Map(zonas(datos).map((z, i) => [z.zona_mitma_id, i]));
    const cuerpo = datos.perfil.perfil.slice()
      .sort((a, b) => (orden.get(a.zona_mitma_id) ?? 999) - (orden.get(b.zona_mitma_id) ?? 999) || a.mes - b.mes)
      .map(f => {
        const lab = pico(f.zona_mitma_id, f.mes, 'laborable'), fin = pico(f.zona_mitma_id, f.mes, 'fin_de_semana_o_festivo');
        const r = [f.nombre_zona, MES[f.mes - 1], f.dias, Math.round(f.llegadas_ocio_media_dia), r1(f.pct_desde_asturias), r1(f.pct_resto_espana),
          r1(f.pct_total_desde_asturias), r1(f.pct_total_resto_espana), r1(f.pernoctaciones_por_100_llegadas), r1(f.pct_excursionistas_aprox),
          lab[0], lab[1], fin[0], fin[1]];
        if (sintetico) r.push(AVISO_CSV);
        return r;
      });
    return aCSV([cab].concat(cuerpo));
  }

  return { zonas, nombreZona, umbralesDisponibles, accionPara, alertasProximas, fiabilidad, aCSV, csvPrevision, csvPerfil,
    sumarDias, finPrevision, diasEntreISO, superaUmbral, rachas, previsionSaturacion, concejosDeZona, zonasDeConcejo,
    normalizar, buscar, csvSaturacion };
});
