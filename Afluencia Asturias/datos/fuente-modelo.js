/* ==========================================================================
 * FUENTE DE DATOS: SALIDAS DEL MODELO
 * --------------------------------------------------------------------------
 * Implementa el contrato de datos/api.js (window.FuenteDatos) para la pestaña
 * Inicio a partir del módulo «datos» (window.DatosModelo, datos/datos.js).
 * No calcula previsiones: solo elige, traduce y resume lo que da el modelo.
 *
 * Se carga DESPUÉS de fuente-ficticia.js y la sustituye. Del piloto solo se
 * reutiliza lo que no son cifras: nombres de los 78 concejos, tipo de destino
 * (costa, montaña, ciudad), sitios de interés, eventos de PredictHQ y, si no
 * hay calendario oficial en las salidas, su calendario aproximado.
 *
 * Qué predicción se enseña para una fecha y una zona (notas/contrato_web.md):
 *   futuro_corto si existe; si no, futuro_largo; si no, historico (solo en
 *   la demo), del modelo de largo plazo con 8 días de antelación.
 *
 * Modo demo (?demo=1): «hoy» pasa a ser el primer día del histórico de
 * agosto de 2024 (validación fuera de muestra, con el valor observado). Con los
 * datos reales, el puente de diciembre de 2024 no sale rojo en ninguna zona.
 * ========================================================================== */
(function () {
  'use strict';

  const piloto = window.FuenteDatos; // fuente-ficticia.js: solo nombres, tipos, sitios, eventos y calendario de reserva
  const DM = window.DatosModelo;

  const DEMO = /[?&]demo=1\b/.test(location.search);
  const DEMO_MES = '2024-08';
  const HISTORICO = { modelo: 'largo', horizonte: 8 }; // aviso con una semana de antelación
  const PRIORIDAD = { futuro_corto: 3, futuro_largo: 2, historico: 1 };

  /* ---------- Fechas ---------- */
  function deISO(s) { const p = s.split('-').map(Number); return new Date(p[0], p[1] - 1, p[2], 12); }
  function aISO(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function sumar(s, n) { const d = deISO(s); d.setDate(d.getDate() + n); return aISO(d); }
  function fechasEntre(a, b) { const out = []; for (let f = a; f <= b; f = sumar(f, 1)) out.push(f); return out; }
  const mediana = a => { if (!a.length) return null; const s = a.slice().sort((x, y) => x - y); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const media = a => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : null);
  const redondea = n => (n == null ? null : Math.round(n));
  function km(a, b) {
    const R = 6371, r = Math.PI / 180;
    const dLat = (b.lat - a.lat) * r, dLon = (b.lon - a.lon) * r;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  /* ---------- Índices (se construyen una vez) ---------- */
  let M = null;
  function preparar(d) {
    const pred = d.predicciones;
    // Umbrales generales y, si el modelo los trae, los de cada zona (config/semaforo.yaml → por_zona)
    const umbrales = { ambar: pred.umbrales.ambar, rojo: pred.umbrales.rojo, porZona: {} };
    Object.keys(pred.umbrales.por_zona || {}).forEach(z => {
      const u = pred.umbrales.por_zona[z];
      umbrales.porZona[z] = { ambar: u.umbral_ambar != null ? u.umbral_ambar : umbrales.ambar, rojo: u.umbral_rojo != null ? u.umbral_rojo : umbrales.rojo };
    });

    // Una predicción por fecha y zona, según la prioridad del contrato
    const elegida = {};
    pred.predicciones.forEach(r => {
      if (r.conjunto === 'historico' && (r.modelo !== HISTORICO.modelo || r.horizonte !== HISTORICO.horizonte)) return;
      const k = r.fecha + '|' + r.zona_mitma_id, prev = elegida[k];
      if (!prev || PRIORIDAD[r.conjunto] > PRIORIDAD[prev.conjunto]) elegida[k] = r;
    });

    const fechas = Array.from(new Set(Object.keys(elegida).map(k => k.split('|')[0]))).sort();
    const futuras = fechas.filter(f => f >= pred.fecha_hoy);
    const demo = fechas.filter(f => f.slice(0, 7) === DEMO_MES);
    const rango = DEMO && demo.length ? demo : futuras;
    const hoy = rango[0] || pred.fecha_hoy;
    const ultimo = rango[rango.length - 1] || hoy;

    // Zonas del modelo y sus concejos (config/mapeo_zonas*.csv vía el módulo «datos»)
    const concejosMapeo = {};
    d.mapeo.zonas.forEach(z => { concejosMapeo[z.zona_mitma_id] = z.concejos_ine; });
    const zonas = pred.zonas.map(z => ({
      id: z.zona_mitma_id, nombre: z.nombre_zona, lat: z.lat, lon: z.lon, principal: !!z.es_principal,
      ine: (concejosMapeo[z.zona_mitma_id] || []).slice(),
    }));

    // Cada concejo, en una sola zona. Si el mapeo lo pone en varias, gana la zona con menos concejos
    // (la más concreta); así se puede pintar el mapa sin solapes.
    const zonaDeConcejo = {}, repetidos = [];
    zonas.slice().sort((a, b) => a.ine.length - b.ine.length).forEach(z => z.ine.forEach(c => {
      if (zonaDeConcejo[c]) repetidos.push(`${c} en ${zonaDeConcejo[c]} y ${z.id}`);
      else zonaDeConcejo[c] = z.id;
    }));
    if (repetidos.length) console.info('Concejos en más de una zona (se pinta en la más concreta):', repetidos.join('; '));

    // Nombres y tipo de destino de cada concejo, del piloto (no son cifras)
    const zonasPiloto = {};
    piloto.getZonas().forEach(z => { zonasPiloto[z.id] = z; });
    const concejos = piloto.getConcejos().map(c => ({
      id: c.id, nombre: c.nombre, zonaId: zonaDeConcejo[c.id] || null,
      tipos: (zonasPiloto[c.zonaId] || { tipos: [] }).tipos,
    }));
    const concejoPorId = {};
    concejos.forEach(c => { concejoPorId[c.id] = c; });
    zonas.forEach(z => {
      const cs = z.ine.map(i => concejoPorId[i]).filter(Boolean);
      z.concejos = cs.filter(c => c.zonaId === z.id);
      z.tipos = Array.from(new Set([].concat.apply([], cs.map(c => c.tipos))));
      // Lugares: los del piloto cuyas zonas caen enteras dentro de esta zona del modelo
      z.lugares = [].concat.apply([], Object.keys(zonasPiloto).map(k => zonasPiloto[k])
        .filter(zp => { const ids = piloto.getConcejos().filter(c => c.zonaId === zp.id).map(c => c.id); return ids.length && ids.every(i => zonaDeConcejo[i] === z.id); })
        .map(zp => zp.lugares));
      const normales = pred.predicciones.filter(r => r.zona_mitma_id === z.id && r.normal != null).map(r => r.normal);
      z.normalTipico = mediana(normales);
    });
    const zonaPorId = {};
    zonas.forEach(z => { zonaPorId[z.id] = z; });

    // Alternativas: por fecha, zona, conjunto, modelo y horizonte
    const alternativas = {};
    d.alternativas.alternativas.forEach(a => { alternativas[[a.fecha, a.zona_mitma_id, a.conjunto, a.modelo, a.horizonte].join('|')] = a; });

    // Calendario oficial (si el script lo ha exportado)
    let calendario = null;
    if (d.calendario && Array.isArray(d.calendario.dias)) {
      calendario = {};
      d.calendario.dias.forEach(x => { calendario[x.fecha] = x; });
    }

    M = {
      d, umbrales, elegida, hoy, ultimo, zonas, zonaPorId, concejos, concejoPorId, alternativas, calendario,
      diasConMeteo: Math.max(0, ...(pred.info_corto_plazo && pred.info_corto_plazo.horizontes_con_tiempo || [0])),
      kmCercana: (d.alternativas.parametros && d.alternativas.parametros.km_zona_cercana) || 60,
    };
    return M;
  }
  const listo = () => (M ? Promise.resolve(M) : DM.cargarInicio().then(preparar));

  /* ---------- Traducción al contrato de la interfaz ---------- */
  const MOTIVO_SIN_PRED = 'El modelo no tiene predicción para este día en esta zona.';
  const umbralesDe = zonaId => M.umbrales.porZona[zonaId] || M.umbrales;
  function nivelDe(ratio, zonaId) {
    if (ratio == null) return 'gris';
    const u = umbralesDe(zonaId);
    return ratio >= u.rojo ? 'rojo' : ratio >= u.ambar ? 'ambar' : 'verde';
  }
  function prevision(zonaId, fecha) {
    const r = M.elegida[fecha + '|' + zonaId];
    if (!r) return { zonaId, fecha, nivel: 'gris', visitantes: null, min: null, max: null, normal: null, ratio: null, esPrediccion: true, conMeteo: false, motivo: MOTIVO_SIN_PRED };
    const gris = r.color === 'gris';
    return {
      zonaId, fecha, nivel: r.color,
      visitantes: gris ? null : redondea(r.prediccion), min: gris ? null : redondea(r.p10), max: gris ? null : redondea(r.p90),
      normal: redondea(r.normal), ratio: gris ? null : r.cociente,
      esPrediccion: true,
      conMeteo: r.modelo === 'corto' && r.horizonte <= M.diasConMeteo,
      motivo: gris ? 'Sin dato de movilidad, sin día normal o sin variables suficientes para esta zona y día.' : undefined,
      // Extras del modelo (la interfaz los usa si están)
      incierto: !!r.incierto, conjunto: r.conjunto, modelo: r.modelo, horizonte: r.horizonte, fechaEmision: r.fecha_emision || null,
      observado: r.observado != null ? redondea(r.observado) : null,
      ratioObservado: r.cociente_observado != null ? r.cociente_observado : null,
      nivelObservado: r.color_observado || null,
    };
  }
  function resumen(zonaId, desde, hasta, ident) {
    const dias = fechasEntre(desde, hasta).map(f => prevision(zonaId, f));
    const con = dias.filter(p => p.ratio != null);
    const base = Object.assign({ zonaId, desde, hasta, dias: dias.length }, ident || {});
    if (!con.length) return Object.assign(base, { fecha: desde, nivel: 'gris', visitantes: null, min: null, max: null, normal: null, ratio: null, esPrediccion: true, conMeteo: false, motivo: MOTIVO_SIN_PRED, pico: null, diasPorNivel: null });
    const ratio = media(con.map(p => p.ratio));
    const pico = con.reduce((a, b) => (b.ratio > a.ratio ? b : a));
    const diasPorNivel = { verde: 0, ambar: 0, rojo: 0 };
    con.forEach(p => { if (diasPorNivel[p.nivel] != null) diasPorNivel[p.nivel]++; });
    const m = k => (con.every(p => p[k] != null) ? redondea(media(con.map(p => p[k]))) : null);
    return Object.assign(base, {
      fecha: desde, nivel: nivelDe(ratio, zonaId), ratio,
      visitantes: m('visitantes'), min: m('min'), max: m('max'), normal: m('normal'),
      esPrediccion: true, conMeteo: con.every(p => p.conMeteo), pico, diasPorNivel,
    });
  }
  // Un concejo enseña la previsión de su zona. Las cifras absolutas solo si la zona es ese concejo
  function deConcejo(c, p) {
    if (!c.zonaId) return { zonaId: null, concejoId: c.id, fecha: p ? p.fecha : null, nivel: 'gris', visitantes: null, min: null, max: null, normal: null, ratio: null, esPrediccion: true, conMeteo: false, sinZona: true, motivo: 'Este concejo no está en ninguna zona del modelo.' };
    const z = M.zonaPorId[c.zonaId];
    const out = Object.assign({}, p, { concejoId: c.id });
    if (z.concejos.length > 1) Object.assign(out, { visitantes: null, min: null, max: null, normal: null, comoZona: true });
    return out;
  }

  /* ---------- Calendario ---------- */
  function diaCalendario(f) {
    const x = M.calendario[f];
    if (!x) return null;
    return { fecha: f, finde: x.finde, festivo: x.festivo, puente: x.puente ? nombrePuente(f) : null, vacaciones: x.vacaciones };
  }
  function tramoPuente(f) {
    let a = f, b = f;
    while (M.calendario[sumar(a, -1)] && M.calendario[sumar(a, -1)].puente) a = sumar(a, -1);
    while (M.calendario[sumar(b, 1)] && M.calendario[sumar(b, 1)].puente) b = sumar(b, 1);
    return [a, b];
  }
  function nombrePuente(f) {
    const [a, b] = tramoPuente(f);
    const festivos = fechasEntre(a, b).map(x => M.calendario[x].festivo).filter(Boolean);
    return festivos.length ? 'Puente: ' + festivos[0] : 'Fin de semana largo';
  }

  /* ======================= Funciones del contrato ======================= */
  window.FuenteDatos = {
    getInfo() {
      return listo().then(() => ({
        hoy: M.hoy,
        horizonteDias: Math.round((deISO(M.ultimo) - deISO(M.hoy)) / 86400000) + 1,
        diasConMeteo: M.diasConMeteo,
        umbrales: { ambar: M.umbrales.ambar, rojo: M.umbrales.rojo, porZona: Object.assign({}, M.umbrales.porZona) },
        ficticio: false, sintetico: M.d.sintetico, demo: DEMO,
      }));
    },
    getZonas() {
      return listo().then(() => M.zonas.map(z => ({
        id: z.id, nombre: z.nombre, tipos: z.tipos.slice(), concejos: z.concejos.map(c => c.nombre),
        lugares: z.lugares.slice(), vecinos: null, principal: z.principal,
        sinDatos: !Object.keys(M.elegida).some(k => k.endsWith('|' + z.id)),
      })));
    },
    getConcejos() { return listo().then(() => M.concejos.map(c => ({ id: c.id, nombre: c.nombre, zonaId: c.zonaId }))); },
    getSitios() { return piloto.getSitios(); },
    getEventos(desde, hasta) {
      // Mismo criterio que el piloto, pero el «día normal» es el del modelo (solo si la zona es ese concejo)
      return listo().then(() => {
        const d = piloto.getEventos(desde, hasta); // ya filtrados por fechas con el criterio del piloto…
        const todos = (window.EventosAsturias || { eventos: [] }).eventos.filter(e => e.inicio <= (hasta || desde) && e.fin >= desde);
        const crit = d.criterio || { minimo: 0.5, asistenciaMin: 3500, asistenciaSiempre: 10000 };
        let eventos = todos.map(e => {
          const c = M.concejoPorId[e.concejo], z = c && c.zonaId && M.zonaPorId[c.zonaId];
          const normal = z && z.concejos.length === 1 ? z.normalTipico : null;
          return Object.assign({}, e, { impacto: normal && e.asistencia ? e.asistencia / normal : null, normalConcejo: normal ? Math.round(normal) : null });
        }).filter(e => e.asistencia >= crit.asistenciaSiempre || (e.impacto != null && e.impacto >= crit.minimo && e.asistencia >= crit.asistenciaMin));
        // Festivos y partidos de fútbol de nuestros calendarios (datos.agenda): todos, sin criterio de tamaño.
        // Si PredictHQ tiene el mismo partido (mismo día y concejo, con el club en el título), se queda el
        // nuestro con la asistencia estimada de PredictHQ.
        const club = { '33024': /sporting/i, '33044': /oviedo/i };
        const agenda = ((M.d.agenda && M.d.agenda.eventos) || [])
          .filter(e => e.inicio <= (hasta || desde) && e.fin >= desde)
          .map(e => {
            const out = Object.assign({}, e, { impacto: null, normalConcejo: null });
            if (e.categoria !== 'Fútbol') return out;
            const i = eventos.findIndex(p => p.inicio === e.inicio && p.concejo === e.concejo && club[e.concejo] && club[e.concejo].test(p.titulo));
            if (i === -1) return out;
            const p = eventos.splice(i, 1)[0];
            return Object.assign(out, { asistencia: p.asistencia, impacto: p.impacto, normalConcejo: p.normalConcejo });
          });
        eventos = eventos.concat(agenda)
          .sort((a, b) => (a.inicio < b.inicio ? -1 : a.inicio > b.inicio ? 1 : (b.asistencia || 0) - (a.asistencia || 0)));
        return Object.assign({}, d, { eventos });
      });
    },
    getCalendario(desde, dias) {
      return listo().then(() => {
        if (!M.calendario) return piloto.getCalendario(desde, dias);
        const out = [];
        for (let i = 0; i < dias; i++) {
          const f = sumar(desde, i), x = diaCalendario(f);
          const dow = deISO(f).getDay();
          out.push(x || { fecha: f, finde: dow === 0 || dow === 6, festivo: null, puente: null, vacaciones: null });
        }
        return out;
      });
    },
    getProximoPuente(desde) {
      return listo().then(() => {
        if (!M.calendario) return piloto.getProximoPuente(desde);
        for (let i = 0; i < 400; i++) {
          const f = sumar(desde, i), x = M.calendario[f];
          if (!x) break;
          if (x.puente) { const [a, b] = tramoPuente(f); return { nombre: nombrePuente(f), inicio: a < desde ? desde : a, fin: b }; }
        }
        return null;
      });
    },
    getPrevisionDia(fecha) { return listo().then(() => M.zonas.map(z => prevision(z.id, fecha))); },
    getPrevisionPeriodo(desde, hasta) { return listo().then(() => M.zonas.map(z => resumen(z.id, desde, hasta))); },
    getPrevisionConcejos(desde, hasta) {
      return listo().then(() => {
        const porZona = {};
        M.zonas.forEach(z => { porZona[z.id] = hasta ? resumen(z.id, desde, hasta) : prevision(z.id, desde); });
        return M.concejos.map(c => deConcejo(c, c.zonaId ? porZona[c.zonaId] : { fecha: desde }));
      });
    },
    getSerieZona(zonaId, desde, dias) {
      return listo().then(() => { const out = []; for (let i = 0; i < dias; i++) out.push(prevision(zonaId, sumar(desde, i))); return out; });
    },
    getFactores(zonaId, fecha) {
      return listo().then(() => {
        const r = M.elegida[fecha + '|' + zonaId];
        if (!r || r.color === 'gris') return [];
        return r.factores.map(f => ({ clave: f.nombre, texto: f.nombre, efecto: Math.round(f.efecto_pct) }));
      });
    },
    // Mejor día: el de alternativas.json si el día está en alerta; si no, el de menos presión de la ventana
    getMejorMomento(zonaId, desde, dias) {
      return listo().then(() => {
        const serie = [];
        for (let i = 0; i < dias; i++) { const p = prevision(zonaId, sumar(desde, i)); if (p.ratio != null) serie.push(p); }
        if (!serie.length) return null;
        const dia = serie.reduce((a, b) => (b.ratio < a.ratio ? b : a));
        return { dia, hora: null };
      });
    },
    // Mejor día alternativo de alternativas.json (solo existe si ese día está en ámbar o rojo):
    // el de menos presión a ±dias_margen días en la misma zona, o null
    getMejorDia(zonaId, fecha) {
      return listo().then(() => {
        const r = M.elegida[fecha + '|' + zonaId];
        const a = r && M.alternativas[[fecha, zonaId, r.conjunto, r.modelo, r.horizonte].join('|')];
        if (!a) return null;
        const margen = (M.d.alternativas.parametros && M.d.alternativas.parametros.dias_margen) || 3;
        if (!a.mejor_dia) return { fecha: null, margen };
        const md = a.mejor_dia;
        return { fecha: md.fecha, nivel: md.color, ratio: md.cociente, visitantes: redondea(md.prediccion), diferenciaPct: md.diferencia_pct, margen };
      });
    },
    getAlternativas(zonaId, fecha, hasta) {
      return listo().then(() => {
        const z = M.zonaPorId[zonaId];
        const pz = hasta ? resumen(zonaId, fecha, hasta) : prevision(zonaId, fecha);
        const dia = hasta ? (pz.pico && pz.pico.fecha) : fecha;
        if (!dia || !z) return [];
        const r = M.elegida[dia + '|' + zonaId];
        const a = r && M.alternativas[[dia, zonaId, r.conjunto, r.modelo, r.horizonte].join('|')];
        const out = [];
        // 1) La zona cercana con menos presión que propone el modelo (alternativas.json)
        if (a && a.zona_alternativa) {
          const za = a.zona_alternativa;
          const p = hasta ? resumen(za.zona_mitma_id, fecha, hasta) : prevision(za.zona_mitma_id, fecha);
          out.push(Object.assign({}, p, { nombre: za.nombre_zona, km: Math.round(za.distancia_km), minutos: null, delModelo: true,
            nivel: hasta ? p.nivel : za.color, ratio: hasta ? p.ratio : za.cociente }));
        }
        // 2) Otras zonas en verde a menos de km_zona_cercana (distancia en línea recta entre centros)
        M.zonas.filter(o => o.id !== zonaId && !out.some(x => x.zonaId === o.id)).forEach(o => {
          const d = km(z, o);
          if (d > M.kmCercana) return;
          const p = hasta ? resumen(o.id, fecha, hasta) : prevision(o.id, fecha);
          if (p.nivel === 'verde') out.push(Object.assign({}, p, { nombre: o.nombre, km: Math.round(d), minutos: null }));
        });
        return out;
      });
    },
    // Quién viene: perfil.json del mes de la fecha (media histórica de la zona en ese mes)
    getPerfil(zonaId, fecha) {
      return listo().then(() => {
        const mes = +fecha.slice(5, 7);
        const r = M.d.perfil.perfil.find(x => x.zona_mitma_id === zonaId && x.mes === mes);
        if (!r || r.pct_desde_asturias == null) return null;
        const exc = r.pct_excursionistas_aprox;
        return {
          deUnDia: exc == null ? null : Math.round(exc), conPernocta: exc == null ? null : 100 - Math.round(exc),
          asturias: Math.round(r.pct_desde_asturias), restoEspana: 100 - Math.round(r.pct_desde_asturias),
          mes, dias: r.dias,
        };
      });
    },
    // Fiabilidad: la nota de metricas.json por zona y horizonte
    getFiabilidad(zonaId) {
      return listo().then(() => {
        const filas = M.d.metricas.fiabilidad.filter(f => f.zona_mitma_id === zonaId);
        if (!filas.length) return null;
        const porHorizonte = {};
        filas.forEach(f => { porHorizonte[f.horizonte_txt] = { nota: f.nota, aciertoColor: f.acierto_color, n: f.n }; });
        return { porHorizonte, algoritmo: M.d.metricas.algoritmo };
      });
    },
  };
})();
