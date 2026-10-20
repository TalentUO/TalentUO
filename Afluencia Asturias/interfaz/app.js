/* ==========================================================================
 * INTERFAZ
 * --------------------------------------------------------------------------
 * Solo pinta y gestiona la interacción. Todos los datos llegan por
 * window.Datos (datos/api.js); este archivo no calcula previsiones.
 * ========================================================================== */
(function () {
  'use strict';

  const D = window.Datos;

  /* ---------- Utilidades ---------- */
  const $ = (sel, el) => (el || document).querySelector(sel);
  const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const NBSP = ' ';
  const MENOS = '−';

  function deISO(s) { const p = s.split('-').map(Number); return new Date(p[0], p[1] - 1, p[2], 12); }
  function aISO(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function sumar(s, n) { const d = deISO(s); d.setDate(d.getDate() + n); return aISO(d); }
  function diasEntre(a, b) { return Math.round((deISO(b) - deISO(a)) / 86400000); }
  function sumarMeses(f, n) {
    const d = deISO(f), dia = d.getDate();
    d.setDate(1);
    d.setMonth(d.getMonth() + n);
    d.setDate(Math.min(dia, new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate()));
    return aISO(d);
  }
  const primeroMes = f => f.slice(0, 8) + '01';
  const diasMes = f => { const d = deISO(f); return new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate(); };
  const capital = s => s.charAt(0).toUpperCase() + s.slice(1);
  const FMT_LARGA = new Intl.DateTimeFormat('es-ES', { weekday: 'long', day: 'numeric', month: 'long' });
  const FMT_LARGA_A = new Intl.DateTimeFormat('es-ES', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const FMT_CORTA = new Intl.DateTimeFormat('es-ES', { weekday: 'short', day: 'numeric', month: 'short' });
  const FMT_DIAMES = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short' });
  const FMT_MES = new Intl.DateTimeFormat('es-ES', { month: 'short' });
  const FMT_MES_ANIO = new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric' });
  const DIA_SEM = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
  const MES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const anioHoy = () => +E.info.hoy.slice(0, 4);
  // El año solo se muestra cuando no es el actual
  const fechaLarga = f => capital((+f.slice(0, 4) !== anioHoy() ? FMT_LARGA_A : FMT_LARGA).format(deISO(f)));
  const fechaCorta = f => capital(FMT_CORTA.format(deISO(f)).replace(/\./g, ''));
  const diaMes = f => FMT_DIAMES.format(deISO(f)).replace('.', '');
  function periodoTexto(a, b) {
    const da = deISO(a), db = deISO(b), ya = da.getFullYear(), yb = db.getFullYear();
    const dia = d => DIA_SEM[d.getDay()] + ' ' + d.getDate();
    const anio = y => (y !== anioHoy() ? ' de ' + y : '');
    if (ya !== yb) return `Del ${dia(da)} de ${MES[da.getMonth()]} de ${ya} al ${dia(db)} de ${MES[db.getMonth()]} de ${yb}`;
    if (da.getMonth() === db.getMonth()) return `Del ${dia(da)} al ${dia(db)} de ${MES[db.getMonth()]}${anio(yb)}`;
    return `Del ${dia(da)} de ${MES[da.getMonth()]} al ${dia(db)} de ${MES[db.getMonth()]}${anio(yb)}`;
  }
  const LETRA = ['D', 'L', 'M', 'X', 'J', 'V', 'S'];
  const TIPO_NOMBRE = { costa: 'Costa', montana: 'Montaña', ciudad: 'Ciudad' };

  function num(n) { return n == null ? '—' : String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
  function pct(r) {
    if (r == null) return '—';
    const p = Math.round((r - 1) * 100);
    if (p === 0) return '±0' + NBSP + '%';
    return (p > 0 ? '+' : MENOS) + Math.abs(p) + NBSP + '%';
  }
  // media = true cuando el ratio es la media de un periodo
  function delta(r, media) {
    if (r == null) return 'Sin datos suficientes';
    const p = Math.round((r - 1) * 100);
    const m = media ? ', de media' : '';
    if (Math.abs(p) < 3) return 'Como un día normal' + m;
    return (p > 0 ? '+' + p + NBSP + '% sobre un día normal' : Math.abs(p) + NBSP + '% menos que un día normal') + m;
  }
  function listaNatural(a) { return a.length <= 1 ? a.join('') : a.slice(0, -1).join(', ') + ' y ' + a[a.length - 1]; }

  /* ---------- Semáforo: nombre, icono y descripción ---------- */
  const NIVEL = {
    verde: { nombre: 'Normal' },
    ambar: { nombre: 'Alta' },
    rojo: { nombre: 'Saturación' },
    gris: { nombre: 'Sin datos' },
  };
  const ICONO = {
    verde: '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" class="ico-verde"/></svg>',
    ambar: '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.6 15 14.4H1z" class="ico-ambar"/></svg>',
    rojo: '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M5.2 1.2h5.6l4 4v5.6l-4 4H5.2l-4-4V5.2z" class="ico-rojo"/></svg>',
    gris: '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" class="ico-gris"/></svg>',
  };
  const ICONO_INFO = '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" class="ico-info-c"/><rect x="7.1" y="6.6" width="1.8" height="5.4" rx=".9" class="ico-info-t"/><circle cx="8" cy="4.4" r="1.05" class="ico-info-t"/></svg>';
  const ICONO_CERRAR = '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9" class="ico-trazo"/></svg>';

  function pill(n, extra) {
    return `<span class="pill pill-${n}${extra ? ' ' + extra : ''}">${ICONO[n]}<span>${NIVEL[n].nombre}</span></span>`;
  }
  function textosNivel() {
    const a = Math.round((E.info.umbrales.ambar - 1) * 100);
    const r = Math.round((E.info.umbrales.rojo - 1) * 100);
    return {
      verde: `Menos de +${a}${NBSP}% sobre un día normal`,
      ambar: `Entre +${a}${NBSP}% y +${r}${NBSP}%`,
      rojo: `+${r}${NBSP}% o más`,
      gris: 'No hay muestra suficiente',
    };
  }

  /* ---------- Estado ---------- */
  const E = {
    info: null, zonas: [], zonasPorId: {}, puente: null,
    // Selección: un día (desde = hasta) o un periodo, ambas fechas incluidas
    tab: 'inicio', desde: null, hasta: null, maxFecha: null, calSel: [],
    tipo: 'todos', vista: 'mapa', zona: null, concejo: null, lugarBuscado: null,
    concejos: [], concejosPorId: {}, mapa: null,
    sitios: [], sitiosPorId: {}, sitiosOrden: 'menos', sitiosVisibles: 0,
    eventos: { eventos: [] }, eventosCat: 'todas', eventosVisibles: 0,
    prevDia: [], prevPorZona: {}, prevPorConcejo: {}, plegablesAbiertos: {}, zonaPanelAnterior: null,
  };
  const esPeriodo = () => E.desde !== E.hasta;
  const nDias = () => diasEntre(E.desde, E.hasta) + 1;
  const textoSel = () => (esPeriodo() ? periodoTexto(E.desde, E.hasta) : fechaLarga(E.desde));
  const nombreZ = id => (E.zonasPorId[id] ? E.zonasPorId[id].nombre : 'fuera de las zonas del modelo');
  const nombreC = id => (E.concejosPorId[id] ? E.concejosPorId[id].nombre : id);
  const coincideTipo = z => E.tipo === 'todos' || (z && z.tipos.indexOf(E.tipo) !== -1);

  // Una sola columna (móvil y tableta): el panel de zona va debajo del mapa
  const estrecho = () => !!(window.matchMedia && matchMedia('(max-width: 1060px)').matches);

  let temporizadorAviso = null;
  function anunciar(texto) {
    const v = $('#aviso-vivo');
    v.textContent = '';
    clearTimeout(temporizadorAviso);
    temporizadorAviso = setTimeout(() => { v.textContent = texto; }, 60);
  }

  // Error al pedir datos: se avisa donde va la fecha, igual que si falla el arranque
  function avisarError(err) {
    console.error(err);
    $('#fecha-estado').innerHTML = '<span class="etq etq-aviso">No se han podido cargar los datos. Recarga la página. Si sigue sin funcionar, revisa la fuente de datos.</span>';
    anunciar('No se han podido cargar los datos.');
  }

  /* ====================================================================
   * Arranque
   * ==================================================================== */
  async function iniciar() {
    avisoSintetico();
    // Recuerda qué secciones plegables del panel ha abierto el usuario (el panel se repinta al cambiar de fecha)
    $('#panel-zona').addEventListener('toggle', e => {
      const h = e.target.matches && e.target.matches('.pz-plegable') && e.target.querySelector('h3[id]');
      if (h) E.plegablesAbiertos[h.id] = e.target.open;
    }, true);
    try {
      E.info = await D.getInfo();
      E.zonas = await D.getZonas();
      E.zonas.forEach(z => { E.zonasPorId[z.id] = z; });
      E.concejos = await D.getConcejos();
      E.concejos.forEach(c => { E.concejosPorId[c.id] = c; });
      E.sitios = await D.getSitios();
      E.sitios.forEach(s => { E.sitiosPorId[s.id] = s; });
      E.puente = await D.getProximoPuente(E.info.hoy);
      E.maxFecha = sumar(E.info.hoy, E.info.horizonteDias - 1);

      construirMapa();
      pintarLeyendas();
      configurarPestanas();
      configurarFecha();
      configurarBuscador();
      configurarFiltros();
      configurarLateral();
      configurarSitios();
      await configurarEventos();

      await cambiarSeleccion(E.info.hoy, E.info.hoy, { anunciar: false });
      leerHash();
      if (E.info.demo) await arrancarDemo();
    } catch (err) {
      console.error(err);
      $('#fecha-texto').textContent = 'No se han podido cargar los datos';
      $('#fecha-estado').innerHTML = '<span class="etq etq-aviso">Recarga la página. Si sigue sin funcionar, revisa la fuente de datos.</span>';
    }
  }

  /* ---------- Modo demo (?demo=1) ----------
   * La fuente fija «hoy» en el histórico de agosto de 2024 (validación fuera de muestra).
   * Se abre el día del puente con más presión en la zona principal (Picos de Europa) y su panel.
   * Recorrido: mapa → Picos en rojo → ¿Por qué? → alternativa → Funciones avanzadas. */
  async function arrancarDemo() {
    const principal = E.zonas.find(z => z.principal) || E.zonas[0];
    if (!principal) return;
    let dia = E.info.hoy;
    if (E.puente) {
      const serie = await D.getSerieZona(principal.id, E.puente.inicio, diasEntre(E.puente.inicio, E.puente.fin) + 1);
      const con = serie.filter(p => p.ratio != null);
      if (con.length) dia = con.reduce((a, b) => (b.ratio > a.ratio ? b : a)).fecha;
    }
    await cambiarSeleccion(dia, dia, { anunciar: false });
    await abrirZona(principal.id, { foco: false, mostrar: false });
    encuadrar('zona', principal.id);
  }

  /* ====================================================================
   * Pestañas
   * ==================================================================== */
  const TABS = ['inicio', 'gestion', 'datos'];
  function configurarPestanas() {
    const botones = TABS.map(t => document.getElementById('tab-' + t));
    botones.forEach((b, i) => {
      b.addEventListener('click', () => irPestana(TABS[i], true));
      b.addEventListener('keydown', e => {
        let j = null;
        if (e.key === 'ArrowRight') j = (i + 1) % TABS.length;
        else if (e.key === 'ArrowLeft') j = (i - 1 + TABS.length) % TABS.length;
        else if (e.key === 'Home') j = 0;
        else if (e.key === 'End') j = TABS.length - 1;
        if (j !== null) { e.preventDefault(); irPestana(TABS[j], true); botones[j].focus(); }
      });
    });
    window.addEventListener('hashchange', leerHash);
  }
  function leerHash() {
    const h = (location.hash || '').slice(1);
    if (TABS.indexOf(h) !== -1) irPestana(h, false);
  }
  function irPestana(t, actualizarHash) {
    E.tab = t;
    TABS.forEach(x => {
      const b = $('#tab-' + x), p = $('#panel-' + x), on = x === t;
      b.setAttribute('aria-selected', String(on));
      b.tabIndex = on ? 0 : -1;
      p.hidden = !on;
    });
    if (actualizarHash) { try { history.replaceState(null, '', '#' + t); } catch (e) { /* sin historial */ } }
    mostrarComponente(t);
  }

  /* ====================================================================
   * Fecha
   * ==================================================================== */
  const limitarFecha = f => (f < E.info.hoy ? E.info.hoy : f > E.maxFecha ? E.maxFecha : f);
  const limiteMeteo = () => sumar(E.info.hoy, E.info.diasConMeteo);

  // Accesos rápidos: devuelven [desde, hasta]
  function rangoFinde() {
    const h = E.info.hoy, dow = deISO(h).getDay();
    if (dow === 0) return [h, h];
    const sab = sumar(h, 6 - dow);
    return [sab, sumar(sab, 1)];
  }
  const rangoSemana = () => [E.info.hoy, sumar(E.info.hoy, 6)];
  const rangoPuente = () => (E.puente ? [limitarFecha(E.puente.inicio), limitarFecha(E.puente.fin)] : null);

  function configurarFecha() {
    $('#btn-hoy').addEventListener('click', () => cambiarSeleccion(E.info.hoy, E.info.hoy));
    $('#btn-finde').addEventListener('click', () => cambiarSeleccion(...rangoFinde()));
    $('#btn-semana').addEventListener('click', () => cambiarSeleccion(...rangoSemana()));
    const bp = $('#btn-puente');
    if (E.puente) {
      const txt = E.puente.inicio === E.puente.fin ? diaMes(E.puente.inicio) : diaMes(E.puente.inicio) + '–' + diaMes(E.puente.fin);
      bp.querySelector('.sub').textContent = txt;
      bp.setAttribute('aria-label', `Próximo puente: ${E.puente.nombre}, del ${fechaLarga(E.puente.inicio)} al ${fechaLarga(E.puente.fin)}`);
      bp.title = E.puente.nombre;
      bp.addEventListener('click', () => cambiarSeleccion(...rangoPuente()));
    } else {
      bp.disabled = true;
      bp.querySelector('.sub').textContent = 'ninguno a la vista';
    }
    $('#btn-antes').addEventListener('click', () => desplazarSeleccion(-1));
    $('#btn-despues').addEventListener('click', () => desplazarSeleccion(1));
    configurarCalendario();
  }

  // Mueve la selección un día, o tantos días como dure el periodo
  function desplazarSeleccion(signo) {
    const n = nDias(), desde = sumar(E.desde, signo * n), hasta = sumar(E.hasta, signo * n);
    if (desde < E.info.hoy || hasta > E.maxFecha) return;
    cambiarSeleccion(desde, hasta);
  }

  let seqFecha = 0;
  async function cambiarSeleccion(desde, hasta, opts) {
    opts = opts || {};
    desde = limitarFecha(desde);
    hasta = limitarFecha(hasta || desde);
    if (hasta < desde) { const t = desde; desde = hasta; hasta = t; }
    const s = ++seqFecha;
    E.desde = desde;
    E.hasta = hasta;
    const periodo = desde !== hasta;

    let prev, prevC, cal, eventos;
    try {
      [prev, prevC, cal, eventos] = await Promise.all([
        periodo ? D.getPrevisionPeriodo(desde, hasta) : D.getPrevisionDia(desde),
        periodo ? D.getPrevisionConcejos(desde, hasta) : D.getPrevisionConcejos(desde),
        D.getCalendario(desde, diasEntre(desde, hasta) + 1),
        D.getEventos(desde, hasta),
      ]);
    } catch (err) {
      if (s === seqFecha) avisarError(err);
      return;
    }
    if (s !== seqFecha) return;
    E.eventos = eventos;
    E.prevDia = prev;
    E.prevPorZona = {};
    prev.forEach(p => { E.prevPorZona[p.zonaId] = p; });
    E.prevPorConcejo = {};
    prevC.forEach(p => { E.prevPorConcejo[p.concejoId] = p; });
    E.calSel = cal;

    renderFecha();
    if (!$('#calendario').hidden) {
      CAL.inicio = null;
      CAL.foco = desde;
      CAL.mes = primeroMes(desde);
      renderCalendario();
    }
    renderMapa();
    renderRanking();
    if (E.vista === 'lista') renderLista();
    if (E.zona) renderPanel();
    renderSitios();
    renderEventos({ reiniciar: true });

    if (opts.anunciar !== false) {
      const rojos = prev.filter(p => p.nivel === 'rojo').length, ambar = prev.filter(p => p.nivel === 'ambar').length;
      anunciar(`${textoSel()}. ${periodo ? 'De media, ' : ''}${rojos} ${rojos === 1 ? 'zona' : 'zonas'} en saturación y ${ambar} con afluencia alta.`);
    }
  }

  function renderFecha() {
    const hoy = E.info.hoy, periodo = esPeriodo(), n = nDias(), lim = limiteMeteo();
    $('#fecha-eyebrow').textContent = periodo ? `Periodo elegido · ${n} días` : 'Día elegido';
    $('#fecha-texto').textContent = textoSel();

    const chips = [];
    if (E.info.demo) chips.push('<span class="etq etq-hoy">Demo · validación con datos de 2024</span>');
    else if (E.desde === hoy) chips.push(`<span class="etq etq-hoy">${periodo ? 'Desde hoy' : 'Hoy'}</span>`);
    const especiales = [];
    E.calSel.forEach(c => {
      const t = c.puente || (c.festivo ? 'Festivo: ' + c.festivo : null);
      if (t && especiales.indexOf(t) === -1) especiales.push(t);
    });
    especiales.slice(0, 2).forEach(t => chips.push(`<span class="etq etq-esp">${esc(t)}</span>`));
    if (especiales.length > 2) chips.push(`<span class="etq etq-esp">y ${especiales.length - 2} más</span>`);
    const conDato = E.prevDia.filter(p => p.ratio != null);
    if (!conDato.length) chips.push('<span class="etq etq-aviso">Sin predicción para estas fechas</span>');
    else if (conDato.every(p => p.conMeteo)) chips.push('<span class="etq">Previsión con meteorología</span>');
    else if (E.desde <= lim && E.hasta > lim) chips.push(`<span class="etq etq-aviso">Meteorología solo hasta el ${esc(diaMes(lim))}</span>`);
    else chips.push('<span class="etq etq-aviso">Solo calendario y eventos, sin meteorología</span>');
    $('#fecha-estado').innerHTML = chips.join('');

    const igual = r => !!r && E.desde === r[0] && E.hasta === r[1];
    $('#btn-hoy').setAttribute('aria-pressed', String(igual([hoy, hoy])));
    $('#btn-finde').setAttribute('aria-pressed', String(igual(rangoFinde())));
    $('#btn-semana').setAttribute('aria-pressed', String(igual(rangoSemana())));
    $('#btn-puente').setAttribute('aria-pressed', String(igual(rangoPuente())));

    // aria-disabled en vez de disabled, para no perder el foco al llegar al límite
    const paso = (id, signo, txt) => {
      const b = $('#' + id), fuera = signo < 0 ? sumar(E.desde, -n) < hoy : sumar(E.hasta, n) > E.maxFecha;
      b.setAttribute('aria-disabled', String(fuera));
      b.title = txt;
      $('#' + id + '-txt').textContent = txt;
    };
    paso('btn-antes', -1, periodo ? `${n} días antes` : 'Día anterior');
    paso('btn-despues', 1, periodo ? `${n} días después` : 'Día siguiente');
  }

  /* ---------- Calendario: un día o un periodo, de hoy a dentro de un año ---------- */
  const CAL = { mes: null, foco: null, modo: 'dia', inicio: null };

  function configurarCalendario() {
    const cal = $('#calendario'), dias = $('#cal-dias');
    $('#btn-calendario').addEventListener('click', () => (cal.hidden ? abrirCalendario() : cerrarCalendario(true)));
    $('#cal-cerrar').addEventListener('click', () => cerrarCalendario(true));
    $('#cal-ant').addEventListener('click', () => cambiarMes(-1));
    $('#cal-sig').addEventListener('click', () => cambiarMes(1));
    $$('input[name="modo-fecha"]').forEach(r => r.addEventListener('change', () => {
      CAL.modo = r.value;
      CAL.inicio = null;
      renderCalendario();
    }));
    const diaDe = e => e.target.closest('button[data-fecha]');
    dias.addEventListener('click', e => { const b = diaDe(e); if (b) elegirDia(b.dataset.fecha); });
    dias.addEventListener('mouseover', e => { const b = diaDe(e); if (b) marcarPrevia(b.dataset.fecha); });
    dias.addEventListener('mouseleave', () => marcarPrevia(null));
    dias.addEventListener('focusin', e => { const b = diaDe(e); if (b) { CAL.foco = b.dataset.fecha; marcarPrevia(b.dataset.fecha); } });
    dias.addEventListener('keydown', teclaCalendario);
    cal.addEventListener('keydown', e => {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); cerrarCalendario(true); }
    });
  }

  function abrirCalendario() {
    CAL.modo = esPeriodo() ? 'periodo' : 'dia';
    CAL.inicio = null;
    CAL.foco = E.desde;
    CAL.mes = primeroMes(E.desde);
    $$('input[name="modo-fecha"]').forEach(r => { r.checked = r.value === CAL.modo; });
    $('#calendario').hidden = false;
    $('#btn-calendario').setAttribute('aria-expanded', 'true');
    renderCalendario({ foco: true });
  }

  function cerrarCalendario(devolverFoco) {
    $('#calendario').hidden = true;
    $('#btn-calendario').setAttribute('aria-expanded', 'false');
    CAL.inicio = null;
    if (devolverFoco) $('#btn-calendario').focus();
  }

  function cambiarMes(n) {
    const mes = sumarMeses(CAL.mes, n);
    if (mes < primeroMes(E.info.hoy) || mes > primeroMes(E.maxFecha)) return;
    CAL.mes = mes;
    CAL.foco = limitarFecha(sumarMeses(CAL.foco, n));
    renderCalendario();
  }

  function elegirDia(f) {
    CAL.foco = f;
    if (CAL.modo === 'dia') { cerrarCalendario(true); cambiarSeleccion(f, f); return; }
    if (!CAL.inicio) { CAL.inicio = f; renderCalendario({ foco: true }); return; }
    const a = CAL.inicio < f ? CAL.inicio : f, b = CAL.inicio < f ? f : CAL.inicio;
    cerrarCalendario(true);
    cambiarSeleccion(a, b);
  }

  // Al elegir el periodo, sombrea los días entre el primero y el que está bajo el ratón o el foco
  function marcarPrevia(f) {
    const ini = CAL.inicio;
    $$('#cal-dias button[data-fecha]').forEach(b => {
      const x = b.dataset.fecha;
      b.classList.toggle('previa', !!(ini && f) && x !== ini && ((x > ini && x <= f) || (x < ini && x >= f)));
    });
  }

  function enfocarDia() {
    const b = $(`#cal-dias button[data-fecha="${CAL.foco}"]`);
    if (b) b.focus();
  }

  function teclaCalendario(e) {
    const b = e.target.closest('button[data-fecha]');
    if (!b) return;
    const f = b.dataset.fecha, dowL = (deISO(f).getDay() + 6) % 7; // lunes = 0
    let n;
    switch (e.key) {
      case 'ArrowLeft': n = sumar(f, -1); break;
      case 'ArrowRight': n = sumar(f, 1); break;
      case 'ArrowUp': n = sumar(f, -7); break;
      case 'ArrowDown': n = sumar(f, 7); break;
      case 'Home': n = sumar(f, -dowL); break;
      case 'End': n = sumar(f, 6 - dowL); break;
      case 'PageUp': n = sumarMeses(f, e.shiftKey ? -12 : -1); break;
      case 'PageDown': n = sumarMeses(f, e.shiftKey ? 12 : 1); break;
      default: return;
    }
    e.preventDefault();
    CAL.foco = limitarFecha(n);
    if (primeroMes(CAL.foco) !== CAL.mes) {
      CAL.mes = primeroMes(CAL.foco);
      renderCalendario({ foco: true });
    } else {
      $$('#cal-dias button[data-fecha]').forEach(x => { x.tabIndex = x.dataset.fecha === CAL.foco ? 0 : -1; });
      enfocarDia();
    }
  }

  let seqCal = 0;
  async function renderCalendario(opts) {
    opts = opts || {};
    const s = ++seqCal, mes = CAL.mes, hoy = E.info.hoy;
    const cal = await D.getCalendario(mes, diasMes(mes));
    if (s !== seqCal) return;

    $('#cal-titulo').textContent = capital(FMT_MES_ANIO.format(deISO(mes)));
    $('#cal-ant').setAttribute('aria-disabled', String(mes <= primeroMes(hoy)));
    $('#cal-sig').setAttribute('aria-disabled', String(mes >= primeroMes(E.maxFecha)));

    const celdas = [];
    for (let i = (deISO(mes).getDay() + 6) % 7; i > 0; i--) celdas.push('<td></td>');
    cal.forEach(c => {
      const f = c.fecha, dia = deISO(f).getDate(), esp = c.puente || c.festivo;
      const cls = ['cal-dia'];
      if (c.finde) cls.push('finde');
      if (f === hoy) cls.push('hoy');
      const punto = `<span class="m-punto${esp ? ' on' : ''}" aria-hidden="true"></span>`;
      if (f < hoy || f > E.maxFecha) {
        cls.push('fuera');
        celdas.push(`<td><span class="${cls.join(' ')}" aria-hidden="true">${dia}</span></td>`);
        return;
      }
      let pulsado = false;
      if (CAL.inicio) {
        if (f === CAL.inicio) { cls.push('pendiente'); pulsado = true; }
      } else if (f >= E.desde && f <= E.hasta) {
        pulsado = true;
        cls.push(E.desde === E.hasta ? 'sel ini fin' : f === E.desde ? 'sel ini' : f === E.hasta ? 'sel fin' : 'en-rango');
      }
      const etiqueta = fechaLarga(f) + (esp ? '. ' + esp : '') + (f === hoy ? '. Hoy' : '');
      celdas.push(`<td><button type="button" class="${cls.join(' ')}" data-fecha="${f}" tabindex="${f === CAL.foco ? 0 : -1}"` +
        ` aria-pressed="${pulsado}" aria-label="${esc(etiqueta)}"${f === hoy ? ' aria-current="date"' : ''}>${dia}${punto}</button></td>`);
    });
    while (celdas.length % 7) celdas.push('<td></td>');
    let filas = '';
    for (let i = 0; i < celdas.length; i += 7) filas += '<tr>' + celdas.slice(i, i + 7).join('') + '</tr>';
    const cuerpo = $('#cal-dias');
    cuerpo.innerHTML = filas;
    if (!$('button[tabindex="0"]', cuerpo)) { const b = $('button[data-fecha]', cuerpo); if (b) { b.tabIndex = 0; CAL.foco = b.dataset.fecha; } }

    $('#cal-instr').textContent = CAL.modo === 'dia' ? 'Elige un día.'
      : CAL.inicio ? `Primer día: ${fechaLarga(CAL.inicio)}. Ahora elige el último.`
      : 'Elige el primer día del periodo.';
    $('#cal-meteo').textContent = `Desde el ${diaMes(sumar(limiteMeteo(), 1))}, sin meteorología`;
    if (opts.foco) enfocarDia();
  }

  /* ====================================================================
   * Buscador (combobox accesible)
   * ==================================================================== */
  const normalizar = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

  function configurarBuscador() {
    const input = $('#buscar'), lista = $('#buscar-lista');
    // tipo: 'zona' | 'concejo' | 'lugar'. Si un lugar se llama como su concejo, gana el concejo.
    const indice = [];
    const vistos = new Set();
    const meter = (texto, tipo, zonaId, concejoId) => {
      const k = normalizar(texto) + '|' + zonaId;
      if (vistos.has(k)) return;
      vistos.add(k);
      indice.push({ texto, tipo, zonaId, concejoId, n: normalizar(texto) });
    };
    E.zonas.forEach(z => meter(z.nombre, 'zona', z.id));
    E.concejos.forEach(c => meter(c.nombre, 'concejo', c.zonaId, c.id));
    E.zonas.forEach(z => z.lugares.forEach(l => meter(l, 'lugar', z.id)));
    E.sitios.forEach(st => { const c = E.concejosPorId[st.concejos[0]]; if (c && c.zonaId) meter(st.nombre, 'lugar', c.zonaId); });
    // Lugares muy buscados que no son concejo ni sitio de la lista, con el concejo (INE) donde están
    const ALIAS = [['Lagos de Covadonga', '33012'], ['Covadonga', '33012'], ['Lago Enol', '33012'], ['Lago Ercina', '33012'],
      ['Picos de Europa', '33012'], ['Bulnes', '33008'], ['Naranjo de Bulnes', '33008'], ['Ruta del Cares', '33008'],
      ['Luarca', '33034'], ['Lastres', '33019'], ['Tazones', '33076'], ['Cudillero', '33021']];
    ALIAS.forEach(([t, ine]) => { const c = E.concejosPorId[ine]; if (c && c.zonaId) meter(t, 'lugar', c.zonaId); });
    const PRIORIDAD = { zona: 2, concejo: 1, lugar: 0 };

    let resultados = [], activo = -1;

    function cerrar() {
      lista.hidden = true;
      input.setAttribute('aria-expanded', 'false');
      input.removeAttribute('aria-activedescendant');
      activo = -1;
    }
    function pintar() {
      if (!resultados.length) {
        lista.innerHTML = '<li role="option" aria-disabled="true" class="sin-res" id="op-vacia">No encontramos ese lugar. Prueba con un concejo, como Llanes o Cangas de Onís.</li>';
      } else {
        lista.innerHTML = resultados.map((r, i) =>
          `<li role="option" id="op-${i}" data-i="${i}" aria-selected="${i === activo}">` +
          `<span>${esc(r.texto)}</span>` +
          `<span class="op-zona">${r.tipo === 'zona' ? 'Zona' : r.tipo === 'concejo' ? (r.zonaId ? 'Concejo · ' + esc(nombreZ(r.zonaId)) : 'Concejo · sin previsión') : 'en ' + esc(nombreZ(r.zonaId))}</span>` +
          '</li>').join('');
      }
      lista.hidden = false;
      input.setAttribute('aria-expanded', 'true');
      if (activo >= 0) {
        input.setAttribute('aria-activedescendant', 'op-' + activo);
        const el = document.getElementById('op-' + activo);
        if (el) el.scrollIntoView({ block: 'nearest' });
      } else input.removeAttribute('aria-activedescendant');
    }
    function buscar() {
      const q = normalizar(input.value.trim());
      if (!q) { cerrar(); return; }
      resultados = indice
        .filter(i => i.n.indexOf(q) !== -1)
        .sort((a, b) => (b.n.startsWith(q) - a.n.startsWith(q)) || (PRIORIDAD[b.tipo] - PRIORIDAD[a.tipo]) || a.texto.localeCompare(b.texto, 'es'))
        .slice(0, 8);
      activo = resultados.length ? 0 : -1;
      pintar();
    }
    function elegir(i) {
      const r = resultados[i];
      if (!r) return;
      input.value = '';
      cerrar();
      $('#buscar-estado').textContent = '';
      if (r.tipo === 'concejo' && !r.zonaId) {
        $('#buscar-estado').textContent = `${r.texto} no tiene previsión: no está en ninguna zona del modelo. Lo señalamos en el mapa.`;
        abrirConcejo(r.concejoId, { foco: false, encuadrar: true });
        return;
      }
      if (r.tipo === 'concejo') { abrirConcejo(r.concejoId, { foco: true, encuadrar: true }); return; }
      abrirZona(r.zonaId, { foco: true, lugar: r.tipo === 'lugar' ? r.texto : null });
      encuadrar('zona', r.zonaId);
    }

    input.addEventListener('input', () => { $('#buscar-estado').textContent = ''; buscar(); });
    input.addEventListener('focus', () => { if (input.value.trim()) buscar(); });
    input.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (lista.hidden) { buscar(); return; }
        if (resultados.length) { activo = (activo + 1) % resultados.length; pintar(); }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (resultados.length) { activo = (activo - 1 + resultados.length) % resultados.length; pintar(); }
      } else if (e.key === 'Enter') {
        if (!lista.hidden && activo >= 0) { e.preventDefault(); elegir(activo); }
      } else if (e.key === 'Escape') {
        if (!lista.hidden) { e.preventDefault(); e.stopPropagation(); cerrar(); }
        else if (input.value) { input.value = ''; }
      }
    });
    input.addEventListener('blur', () => setTimeout(cerrar, 150));
    lista.addEventListener('mousedown', e => e.preventDefault());
    lista.addEventListener('click', e => {
      const o = e.target.closest('[data-i]');
      if (o) elegir(+o.dataset.i);
    });
  }

  /* ====================================================================
   * Filtros: tipo de destino y forma de ver
   * ==================================================================== */
  function configurarFiltros() {
    $$('input[name="tipo"]').forEach(r => r.addEventListener('change', () => {
      E.tipo = r.value;
      renderMapa();
      renderRanking();
      renderSitios({ reiniciar: true });
      renderEventos({ reiniciar: true });
      if (E.vista === 'lista') renderLista();
      anunciar(E.tipo === 'todos' ? 'Mostrando todas las zonas.' : `Mostrando solo zonas de ${TIPO_NOMBRE[E.tipo].toLowerCase()}.`);
    }));
    $$('[data-vista]').forEach(b => b.addEventListener('click', () => {
      E.vista = b.dataset.vista;
      $$('[data-vista]').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
      $('#mapa-marco').hidden = E.vista !== 'mapa';
      $('#nota-mapa').hidden = E.vista !== 'mapa';
      $('#lista-zonas').hidden = E.vista !== 'lista';
      if (E.vista === 'lista') renderLista();
      else if (E.mapa) E.mapa.redimensionar();
    }));
    $('#lista-zonas').addEventListener('click', e => {
      const b = e.target.closest('[data-zona]');
      if (b) abrirZona(b.dataset.zona, { foco: true });
    });
    const bf = $('#btn-filtros');
    const resumirFiltros = () => {
      const partes = [];
      if (E.tipo !== 'todos') partes.push(TIPO_NOMBRE[E.tipo]);
      if (E.vista === 'lista') partes.push('Lista');
      bf.textContent = partes.length ? 'Filtros · ' + partes.join(', ') : 'Filtros';
    };
    bf.addEventListener('click', () => {
      const abierto = !$('.filtros').classList.contains('abiertos');
      $('.filtros').classList.toggle('abiertos', abierto);
      bf.setAttribute('aria-expanded', String(abierto));
    });
    $$('input[name="tipo"]').forEach(r => r.addEventListener('change', resumirFiltros));
    $$('[data-vista]').forEach(b => b.addEventListener('click', resumirFiltros));
  }

  /* ====================================================================
   * Mapa
   * ==================================================================== */
  // Cada zona y concejo del mapa: nivel, etiqueta (icono + porcentaje) y texto accesible
  function estadoArea(nombre, p, visible) {
    const n = p ? p.nivel : 'gris';
    return {
      nivel: n, atenuada: !visible,
      etiqueta: ICONO[n] + `<span>${p && p.ratio != null ? pct(p.ratio) : 'sin datos'}</span>`,
      aria: `${nombre}. ${NIVEL[n].nombre}. ${p && p.ratio != null ? delta(p.ratio, esPeriodo()) : 'Sin datos suficientes'}.` +
        (visible ? '' : ' No coincide con el filtro.'),
    };
  }

  function construirMapa() {
    E.mapa = window.MapaAsturias.crear($('#mapa'), {
      zonas: E.zonas,
      concejos: E.concejos,
      sitios: E.sitios,
      popupSitio: htmlSitio,
      tooltip: htmlTip,
      alElegir: (tipo, id, porTeclado) => {
        if (tipo === 'concejo') { abrirConcejo(id, { foco: porTeclado }); return; }
        abrirZona(id, { foco: porTeclado });
        encuadrar('zona', id);
      },
    });
  }

  function renderMapa() {
    if (!E.mapa) return;
    const zonas = {}, concejos = {};
    E.zonas.forEach(z => { zonas[z.id] = estadoArea(z.nombre, E.prevPorZona[z.id], coincideTipo(z)); });
    E.concejos.forEach(c => {
      concejos[c.id] = estadoArea(`${c.nombre}, en ${nombreZ(c.zonaId)}`, E.prevPorConcejo[c.id], coincideTipo(E.zonasPorId[c.zonaId]));
    });
    E.mapa.actualizar({ zonas, concejos, zonaSel: E.zona, concejoSel: E.concejo });
  }

  // Solo se mueve el mapa si está a la vista (en la vista de lista no tiene tamaño)
  function encuadrar(tipo, id) {
    if (E.mapa && E.vista === 'mapa') E.mapa.encuadrar(tipo, id);
  }

  function htmlTip(tipo, id) {
    const esZona = tipo === 'zona';
    if (!esZona && !E.concejosPorId[id].zonaId) {
      return `<div class="tip-in"><strong class="tip-nombre">${esc(nombreC(id))}</strong><span>Fuera de las zonas del modelo: sin previsión.</span></div>`;
    }
    const p = esZona ? E.prevPorZona[id] : E.prevPorConcejo[id];
    const n = p ? p.nivel : 'gris', periodo = esPeriodo();
    return `<div class="tip-in"><strong class="tip-nombre">${esc(esZona ? nombreZ(id) : nombreC(id))}</strong>` +
      (esZona ? '' : `<span class="tip-sub">Concejo · ${esc(nombreZ(E.concejosPorId[id].zonaId))}</span>`) +
      pill(n) +
      `<span>${p && p.ratio != null ? delta(p.ratio, periodo) : 'Sin datos suficientes'}</span>` +
      (p && p.visitantes != null ? `<span class="tip-cifra">Unos ${num(p.visitantes)} visitantes${periodo ? ' al día' : ''}</span>` : '') +
      (periodo && p && p.pico ? `<span class="tip-cifra">Día con más gente: ${esc(fechaCorta(p.pico.fecha))}, ${pct(p.pico.ratio)}</span>` : '') +
      `<span class="tip-acc">${esZona ? 'Pulsa para ver el detalle y sus concejos' : 'Pulsa para ver el detalle'}</span></div>`;
  }

  function pintarLeyendas() {
    const t = textosNivel();
    const html = ['verde', 'ambar', 'rojo', 'gris'].map(n =>
      `<li><span class="sw-mapa nivel-${n}" aria-hidden="true"></span>${ICONO[n]}<span class="ley-txt"><strong>${NIVEL[n].nombre}</strong><span>${t[n]}</span></span></li>`).join('');
    const sinZona = E.concejos.some(c => !c.zonaId);
    const extra = sinZona ? '<li><span class="sw-mapa sin-zona" aria-hidden="true"></span><span class="ley-txt"><strong>Sin previsión</strong><span>Concejo fuera de las zonas del modelo</span></span></li>' : '';
    $('#leyenda').innerHTML = html + extra;
    $('#leyenda-mini').innerHTML = ['verde', 'ambar', 'rojo', 'gris'].map(n =>
      `<li><span class="sw-mapa nivel-${n}"></span>${ICONO[n]}${NIVEL[n].nombre}</li>`).join('') +
      (sinZona ? '<li><span class="sw-mapa sin-zona"></span>Sin previsión</li>' : '');
  }

  /* ====================================================================
   * Columna lateral: ranking y lista
   * ==================================================================== */
  function renderRanking() {
    const visibles = E.prevDia.filter(p => p.nivel !== 'gris' && coincideTipo(E.zonasPorId[p.zonaId]));
    const top = visibles.slice().sort((a, b) => b.ratio - a.ratio).slice(0, 5);
    const enTop = new Set(top.map(p => p.zonaId));
    const tranquilas = visibles.filter(p => p.nivel === 'verde' && !enTop.has(p.zonaId)).sort((a, b) => a.ratio - b.ratio).slice(0, 3);
    const filtro = E.tipo === 'todos' ? '' : ' · Solo ' + TIPO_NOMBRE[E.tipo].toLowerCase();
    const periodo = esPeriodo(), media = periodo ? ', de media' : '';

    $('#ranking').innerHTML = `
      <h2 class="lat-titulo">Dónde habrá más presión</h2>
      <p class="lat-sub">${esc(textoSel())}${periodo ? ' · Media por día' : ''}${esc(filtro)}</p>
      <p class="lat-sub">Comparado con un día normal en cada zona.</p>
      <ol class="ranking">${top.map((p, i) => `<li><button type="button" class="rk" data-zona="${p.zonaId}">
        <span class="rk-n" aria-hidden="true">${i + 1}</span>
        <span class="rk-nombre" title="${esc(nombreZ(p.zonaId))}">${esc(nombreZ(p.zonaId))}</span>
        <span class="rk-dato">${pill(p.nivel)}<span class="rk-pct"><span aria-hidden="true">${pct(p.ratio)}</span><span class="sr">${esc(delta(p.ratio, periodo))}</span></span></span>
      </button></li>`).join('') || '<li class="vacio">No hay zonas con este filtro.</li>'}</ol>
      ${tranquilas.length ? `<h3 class="lat-titulo2">Con menos presión ${periodo ? 'esos días' : 'ese día'}</h3>
      <ul class="tranquilas">${tranquilas.map(p => `<li><button type="button" class="tq" data-zona="${p.zonaId}">
        <span class="rk-nombre" title="${esc(nombreZ(p.zonaId))}">${esc(nombreZ(p.zonaId))}</span>
        <span class="rk-dato">${pill(p.nivel)}<span class="rk-pct"><span aria-hidden="true">${pct(p.ratio)}</span><span class="sr">${esc(delta(p.ratio, periodo))}</span></span></span>
      </button></li>`).join('')}</ul>` : ''}
      <p class="lat-ayuda">Elige una zona en el mapa para ver la previsión de los próximos días, las causas y alternativas con menos gente.</p>`;
  }

  function renderLista() {
    const filas = E.prevDia
      .filter(p => coincideTipo(E.zonasPorId[p.zonaId]))
      .sort((a, b) => (b.ratio == null ? -1 : b.ratio) - (a.ratio == null ? -1 : a.ratio));
    const periodo = esPeriodo();
    $('#lista-zonas').innerHTML = `<div class="tabla-marco"><table class="tabla">
      <caption class="sr">Previsión por zona (${esc(textoSel())}), ordenada de más a menos gente</caption>
      <thead><tr><th scope="col">Zona</th><th scope="col">Tipo</th><th scope="col">Nivel</th>
        <th scope="col" class="num">Sobre un día normal${periodo ? ' (media)' : ''}</th>
        <th scope="col" class="num">${periodo ? 'Visitantes al día (media)' : 'Visitantes previstos'}</th>
        ${periodo ? '<th scope="col">Día con más gente</th><th scope="col" class="num">Días en saturación</th>' : ''}</tr></thead>
      <tbody>${filas.map(p => {
        const z = E.zonasPorId[p.zonaId];
        return `<tr><th scope="row"><button type="button" class="enlace" data-zona="${p.zonaId}">${esc(z.nombre)}</button></th>
          <td>${esc(z.tipos.map(t => TIPO_NOMBRE[t]).join(', '))}</td>
          <td>${pill(p.nivel)}</td>
          <td class="num">${pct(p.ratio)}</td>
          <td class="num">${p.visitantes != null ? num(p.visitantes) + ` <span class="rango-txt">(${num(p.min)}–${num(p.max)})</span>` : '—'}</td>
          ${periodo ? `<td>${p.pico ? esc(fechaCorta(p.pico.fecha)) + ' · ' + pct(p.pico.ratio) : '—'}</td>
          <td class="num">${p.diasPorNivel ? p.diasPorNivel.rojo + ' de ' + p.dias : '—'}</td>` : ''}</tr>`;
      }).join('')}</tbody></table></div>`;
  }

  function configurarLateral() {
    $('#lateral').addEventListener('click', e => {
      if (e.target.closest('#pz-cerrar')) { cerrarZona(); return; }
      const bs = e.target.closest('[data-sitio]');
      if (bs) { verSitio(bs.dataset.sitio); return; }
      const bc = e.target.closest('[data-concejo]');
      if (bc) { abrirConcejo(bc.dataset.concejo, { foco: false, encuadrar: true }); return; }
      if (e.target.closest('[data-ver-zona]')) { abrirZona(E.zona, { foco: true }); encuadrar('zona', E.zona); return; }
      const bz = e.target.closest('[data-zona]');
      if (bz) { abrirZona(bz.dataset.zona, { foco: true }); return; }
      const bf = e.target.closest('[data-fecha]');
      if (bf) cambiarSeleccion(bf.dataset.fecha, bf.dataset.fecha);
    });
    document.addEventListener('keydown', e => {
      if (e.key !== 'Escape' || !E.zona || E.tab !== 'inicio') return;
      // Escape en el buscador, el calendario o una viñeta del mapa solo cierra eso
      if (e.target.closest && e.target.closest('.buscador, #calendario, .sitio-icono, .leaflet-popup')) return;
      if (document.querySelector('dialog[open]')) return;
      cerrarZona();
    });
  }

  /* ====================================================================
   * Panel de zona
   * ==================================================================== */
  async function abrirZona(id, opts) {
    opts = opts || {};
    if (!E.zonasPorId[id]) return;
    if (E.tab !== 'inicio') irPestana('inicio', true);
    E.zona = id;
    E.concejo = opts.concejo || null;
    E.lugarBuscado = opts.lugar || null;
    $('#ranking').hidden = true;
    $('#panel-zona').hidden = false;
    $('#lateral').classList.add('con-panel');
    if (E.zona !== E.zonaPanelAnterior) $('#lateral').scrollTop = 0; // otra zona: el lateral empieza arriba
    E.zonaPanelAnterior = E.zona;
    renderMapa();
    await renderPanel();
    if (opts.foco !== false) { const h = $('#pz-titulo'); if (h) h.focus(); }
    else if (opts.mostrar !== false && estrecho()) {
      const panel = $('#panel-zona');
      if (panel.getBoundingClientRect().top > innerHeight * 0.6) panel.scrollIntoView({ block: 'start' });
    }
    else if (opts.concejo) anunciar(`Concejo de ${nombreC(opts.concejo)}, en ${nombreZ(id)}.`);
    else anunciar(`${nombreZ(id)}.`);
  }

  // Un concejo se muestra dentro del panel de su zona
  function abrirConcejo(id, opts) {
    opts = opts || {};
    const c = E.concejosPorId[id];
    if (!c) return;
    if (opts.encuadrar || !c.zonaId) encuadrar('concejo', id);
    if (!c.zonaId) { anunciar(`${c.nombre} no está en ninguna zona del modelo: no hay previsión.`); return; }
    abrirZona(c.zonaId, { foco: opts.foco, concejo: id });
  }

  function cerrarZona() {
    const id = E.zona, cid = E.concejo;
    E.zona = null;
    E.concejo = null;
    E.lugarBuscado = null;
    const panel = $('#panel-zona');
    panel.hidden = true;
    panel.innerHTML = '';
    $('#ranking').hidden = false;
    $('#lateral').classList.remove('con-panel');
    $('#lateral').scrollTop = 0;
    E.zonaPanelAnterior = null;
    renderMapa();
    // En una sola columna, al cerrar se vuelve al mapa (el panel estaba debajo)
    if (estrecho() && E.vista === 'mapa') $('.mapa-marco').scrollIntoView({ block: 'start' });
    const enMapa = E.vista === 'mapa' && E.mapa && ((cid && E.mapa.enfocar('concejo', cid)) || (id && E.mapa.enfocar('zona', id)));
    if (!enMapa) { const t = $('#ranking .lat-titulo'); if (t) { t.tabIndex = -1; t.focus(); } }
    anunciar('Detalle cerrado.');
  }

  let seqPanel = 0;
  async function renderPanel() {
    const id = E.zona;
    if (!id) return;
    const s = ++seqPanel;
    const z = E.zonasPorId[id];
    const p = E.prevPorZona[id] || { nivel: 'gris' };
    const periodo = esPeriodo();
    const v = ventanaSerie();
    // En un periodo, las causas se explican con el día con más gente y el mejor día se busca dentro del periodo
    const fechaFactores = periodo && p.pico ? p.pico.fecha : E.desde;

    let serie, factores, mejor, alts, perfil, fiab, mejorDia;
    try {
      [serie, factores, mejor, alts, perfil, fiab, mejorDia] = await Promise.all([
        D.getSerieZona(id, v.desde, v.dias),
        D.getFactores(id, fechaFactores),
        periodo ? D.getMejorMomento(id, E.desde, nDias()) : D.getMejorMomento(id, v.desde, v.dias),
        periodo ? D.getAlternativas(id, E.desde, E.hasta) : D.getAlternativas(id, E.desde),
        D.getPerfil(id, E.desde), // media del mes (en un periodo, el del primer día)
        D.getFiabilidad(id),
        periodo ? Promise.resolve(null) : D.getMejorDia(id, E.desde),
      ]);
    } catch (err) {
      if (s === seqPanel) avisarError(err);
      return;
    }
    if (s !== seqPanel || E.zona !== id) return;

    // Tras repintar, el foco vuelve al mismo día o concejo si estaba en el panel
    const activo = document.activeElement;
    let selFoco = null;
    if (activo && activo.closest && activo.closest('#panel-zona')) {
      if (activo.classList.contains('dc')) selFoco = `.dc[data-fecha="${activo.dataset.fecha}"]`;
      else if (activo.dataset.concejo) selFoco = `[data-concejo="${activo.dataset.concejo}"]`;
    }

    const c = E.concejo ? E.concejosPorId[E.concejo] : null;
    const pc = c ? (E.prevPorConcejo[c.id] || { nivel: 'gris' }) : null;
    const tarjetaConcejo = c ? `<div class="pz-estado pz-concejo estado-${pc.nivel}">
        <p class="pz-fecha">Concejo de ${esc(c.nombre)} · ${esc(textoSel())}</p>
        <div class="pz-estado-fila">${pill(pc.nivel, 'pill-grande')}<p class="pz-delta">${pc.ratio != null ? delta(pc.ratio, periodo) : 'Sin datos suficientes'}</p></div>
        ${pc.visitantes != null ? `<details class="detalles"><summary>Ver más cifras</summary><p class="pz-cifra">Unos <strong>${num(pc.visitantes)}</strong> visitantes${periodo ? ' al día de media' : ''} en el concejo. Un día normal vienen unos ${num(pc.normal)}.</p></details>` : ''}
        ${periodo && pc.pico ? `<p class="pz-cifra">Día con más gente: <strong>${esc(fechaLarga(pc.pico.fecha))}</strong>, ${pct(pc.pico.ratio)}.</p>` : ''}
        <button type="button" class="btn-mini" data-ver-zona>Ver la zona entera</button>
      </div>` : '';

    const tipos = z.tipos.map(t => TIPO_NOMBRE[t]).join(' y ');
    let html = `<div class="pz-fija">
      <div class="pz-cab-fila">
        <p class="eyebrow">${esc(tipos)}</p>
        <button type="button" class="btn-cerrar" id="pz-cerrar">${ICONO_CERRAR}Cerrar<span class="sr"> el detalle de ${esc(z.nombre)}</span></button>
      </div>
      <h2 id="pz-titulo" tabindex="-1">${esc(z.nombre)}</h2>
    </div>
    <div class="pz-cab">
      <p class="pz-concejos">${esc(z.concejos.join(', '))}</p>
      ${E.lugarBuscado ? `<p class="pz-nota-lugar">Has buscado <strong>${esc(E.lugarBuscado)}</strong>. Mostramos los datos de toda la zona: no tenemos cifras de puntos concretos.</p>` : ''}
      ${tarjetaConcejo}
      <div class="pz-estado estado-${p.nivel}">
        <p class="pz-fecha">${c ? 'Toda la zona · ' : ''}${esc(textoSel())}</p>
        <div class="pz-estado-fila">${pill(p.nivel, 'pill-grande')}<p class="pz-delta">${p.ratio != null ? delta(p.ratio, periodo) : 'Sin datos suficientes'}</p></div>
        ${p.visitantes != null ? `<details class="detalles"><summary>Ver más cifras</summary>
          <p class="pz-cifra">Unos <strong>${num(p.visitantes)}</strong> visitantes${periodo ? ' al día de media' : ''}, probablemente entre ${num(p.min)} y ${num(p.max)}. Un día normal vienen unos ${num(p.normal)}.</p>
          ${!periodo && p.incierto ? '<p class="pz-cifra"><span class="etq etq-aviso">Incierto</span> El rango probable cae en colores distintos del semáforo.</p>' : ''}
        </details>` : ''}
        ${!periodo && p.nivelObservado ? `<p class="pz-cifra">Lo que pasó de verdad: ${pill(p.nivelObservado)} ${esc(delta(p.ratioObservado))} (unos ${num(p.observado)} visitantes).</p>` : ''}
        ${periodo && p.pico ? resumenPeriodo(p) : ''}
      </div>
    </div>`;

    if (p.nivel === 'gris') {
      html += `<section class="pz-sec" aria-labelledby="pz-s-g"><h3 id="pz-s-g">Por qué no hay previsión</h3>
        <p class="pz-ayuda">${esc(p.motivo || 'No hay datos suficientes para esta zona.')}</p></section>`;
      html += seccionSitios(id);
      html += seccionAlternativas(alts, true);
    } else {
      html += seccionSerie(serie, v);
      html += seccionFactores(factores, periodo ? fechaFactores : null);
      html += seccionMejor(mejor, v, mejorDia);
      html += seccionAlternativas(alts, false);
      html += seccionConcejos(id);
      html += seccionEventosPanel(id);
      html += seccionPerfil(perfil);
      html += seccionSitios(id);
      html += seccionFiabilidad(periodo && p.pico ? p.pico : p, fiab); // aviso de predicción, al final
    }

    const panel = $('#panel-zona');
    panel.setAttribute('aria-label', 'Detalle de ' + z.nombre);
    panel.innerHTML = html;
    if (selFoco) {
      const b = panel.querySelector(selFoco);
      if (b) b.focus();
    }
  }

  function seccionConcejos(zonaId) {
    const lista = E.concejos.filter(c => c.zonaId === zonaId);
    if (lista.length < 2) return '';
    const periodo = esPeriodo();
    const filas = lista.map(c => ({ c, p: E.prevPorConcejo[c.id] || { nivel: 'gris' } }))
      .sort((a, b) => (b.p.ratio == null ? -1 : b.p.ratio) - (a.p.ratio == null ? -1 : a.p.ratio));
    return plegable(`<section class="pz-sec" aria-labelledby="pz-s-f">
      <h3 id="pz-s-f">Por concejos</h3>
      <p class="pz-ayuda">${periodo ? 'Media por día de las fechas elegidas. ' : ''}Pulsa un concejo para verlo en el mapa.</p>
      <ul class="cj-lista">${filas.map(({ c, p }) => `<li><button type="button" class="tq cj" data-concejo="${c.id}" aria-pressed="${c.id === E.concejo}">
        <span class="rk-nombre">${esc(c.nombre)}</span>
        <span class="rk-dato">${pill(p.nivel)}<span class="rk-pct"><span aria-hidden="true">${pct(p.ratio)}</span><span class="sr">${esc(delta(p.ratio, periodo))}</span></span></span>
      </button></li>`).join('')}</ul>
    </section>`, !!E.concejo);
  }

  // Secciones secundarias del panel: se pliegan (el panel es largo) y recuerdan si estaban abiertas
  function plegable(html, abierta) {
    const id = (html.match(/<h3 id="([^"]+)"/) || [])[1];
    const abrir = abierta || (id && E.plegablesAbiertos[id]);
    return html
      .replace(/^<section class="pz-sec" aria-labelledby="([^"]+)">\s*(<h3[^>]*>[\s\S]*?<\/h3>)/,
        `<details class="pz-sec pz-plegable"${abrir ? ' open' : ''}><summary>$2<svg class="ico desp-flecha" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" class="ico-trazo"/></svg></summary>`)
      .replace(/<\/section>\s*$/, '</details>');
  }

  // Días que muestra la gráfica del panel: al menos 14 alrededor de la selección y como mucho 31
  const MIN_SERIE = 14, MAX_SERIE = 31;
  function ventanaSerie() {
    const n = nDias();
    if (n > MAX_SERIE) return { desde: E.desde, dias: MAX_SERIE, recortado: true };
    const dias = Math.max(n, MIN_SERIE);
    let desde = sumar(E.desde, -Math.floor((dias - n) / 2));
    if (sumar(desde, dias - 1) > E.maxFecha) desde = sumar(E.maxFecha, -(dias - 1));
    if (desde < E.info.hoy) desde = E.info.hoy;
    // No se enseñan días fuera del horizonte con predicción
    const caben = diasEntre(desde, E.maxFecha) + 1;
    return { desde, dias: Math.max(1, Math.min(dias, caben)), recortado: false };
  }

  function resumenPeriodo(p) {
    const d = p.diasPorNivel, partes = [];
    if (d.rojo) partes.push(`${d.rojo} en saturación`);
    if (d.ambar) partes.push(`${d.ambar} con afluencia alta`);
    const reparto = partes.length ? `De los ${p.dias} días, ${listaNatural(partes)}.` : `Los ${p.dias} días, con afluencia normal.`;
    return `<p class="pz-cifra">${esc(reparto)} Día con más gente: <strong>${esc(fechaLarga(p.pico.fecha))}</strong>, ${pct(p.pico.ratio)}.</p>
      <button type="button" class="btn-mini" data-fecha="${p.pico.fecha}">Ver solo ese día</button>`;
  }

  function seccionSerie(serie, v) {
    const conDatos = serie.filter(x => x.ratio != null);
    if (!conDatos.length) return '';
    const periodo = esPeriodo();
    const maxR = Math.max(1.7, ...conDatos.map(x => x.max / x.normal)) * 1.06;
    const cols = serie.map(x => {
      const d = deISO(x.fecha), sel = x.fecha >= E.desde && x.fecha <= E.hasta;
      if (x.ratio == null) return `<li><button type="button" class="dc nivel-gris" data-fecha="${x.fecha}" aria-label="${esc(fechaLarga(x.fecha))}: sin datos"><span class="dc-area"></span><span class="dc-et" aria-hidden="true"><span>${LETRA[d.getDay()]}</span><span>${d.getDate()}</span></span></button></li>`;
      const h = x.ratio / maxR * 100;
      const lo = x.min / x.normal / maxR * 100, hi = x.max / x.normal / maxR * 100;
      const etiqueta = `${fechaLarga(x.fecha)}: ${NIVEL[x.nivel].nombre}, ${delta(x.ratio)}. Entre ${num(x.min)} y ${num(x.max)} visitantes.${x.conMeteo ? '' : ' Sin meteorología.'}`;
      return `<li><button type="button" class="dc nivel-${x.nivel}${sel ? ' sel' : ''}${x.conMeteo ? '' : ' sin-meteo'}" data-fecha="${x.fecha}" aria-pressed="${sel}" aria-label="${esc(etiqueta)}">` +
        `<span class="dc-area"><span class="dc-barra" style="height:${h.toFixed(1)}%"></span>` +
        `<span class="dc-rango" style="bottom:${lo.toFixed(1)}%;height:${(hi - lo).toFixed(1)}%"></span></span>` +
        `<span class="dc-et" aria-hidden="true"><span>${LETRA[d.getDay()]}</span><span>${d.getDate()}</span></span></button></li>`;
    }).join('');
    return `<section class="pz-sec" aria-labelledby="pz-s-a">
      <h3 id="pz-s-a">Día a día</h3>
      <p class="pz-ayuda">Del ${esc(diaMes(serie[0].fecha))} al ${esc(diaMes(serie[serie.length - 1].fecha))}.
        ${v.recortado ? `Mostramos los primeros ${serie.length} días del periodo.` : ''}
        ${periodo ? 'Los días elegidos van recuadrados. Pulsa un día para verlo solo en el mapa.' : 'Pulsa un día para verlo también en el mapa.'}</p>
      <div class="dc-marco"><ul class="dc-lista" style="--n:${serie.length};--base:${(1 / maxR).toFixed(4)}">${cols}<li class="dc-normal" aria-hidden="true"><span>Día normal</span></li></ul></div>
      <p class="dc-leyenda"><span><i class="ley-linea"></i>Día normal</span><span><i class="ley-rango"></i>Rango probable</span><span><i class="ley-claro"></i>Más de ${E.info.diasConMeteo} días: sin meteorología</span></p>
    </section>`;
  }

  // fechaPico: en un periodo, el día con más gente con el que se explican las causas
  function seccionFactores(factores, fechaPico) {
    if (!factores || !factores.length) return '';
    const maxAbs = Math.max(10, ...factores.map(f => Math.abs(f.efecto)));
    const filas = factores.map(f => {
      const sube = f.efecto >= 0, abs = Math.abs(f.efecto);
      return `<li class="fx"><span class="fx-texto">${esc(f.texto)}</span>
        <span class="fx-barra" aria-hidden="true"><span class="fx-eje"></span><span class="fx-val ${sube ? 'sube' : 'baja'}" style="width:${(abs / maxAbs * 50).toFixed(1)}%"></span></span>
        <span class="fx-num"><span aria-hidden="true">${sube ? '▲' : '▼'} </span>${sube ? '+' : MENOS}${abs}${NBSP}%<span class="sr">${sube ? ' más visitantes' : ' menos visitantes'}</span></span></li>`;
    }).join('');
    return `<section class="pz-sec" aria-labelledby="pz-s-b">
      <h3 id="pz-s-b">¿Por qué?</h3>
      <p class="pz-ayuda">${fechaPico ? `Lo que más pesa el día con más gente del periodo: ${esc(fechaLarga(fechaPico).toLowerCase())}.` : 'Lo que más sube o baja la previsión de ese día.'}</p>
      <ul class="fx-lista">${filas}</ul>
      <p class="pz-nota">Cada efecto se mide frente a un día medio del modelo, no frente al día normal, y se multiplican entre sí: no se suman para dar la cifra de arriba.</p>
    </section>`;
  }

  // mejorDia: propuesta del modelo (alternativas.json) si el día está en alerta; si no, el día más tranquilo de la gráfica
  function seccionMejor(mejor, v, mejorDia) {
    const periodo = esPeriodo();
    let tarjeta = '';
    if (mejorDia && mejorDia.fecha) {
      const dif = mejorDia.diferenciaPct != null ? `: ${Math.abs(Math.round(mejorDia.diferenciaPct))}${NBSP}% ${mejorDia.diferenciaPct < 0 ? 'menos' : 'más'} gente que el día elegido` : '';
      tarjeta = `<div class="mm"><p class="eyebrow">Mejor día alternativo</p><p class="mm-valor">${esc(fechaLarga(mejorDia.fecha))}</p>
        <p>${pill(mejorDia.nivel)}</p><p class="mm-nota">${esc(delta(mejorDia.ratio))}${dif}.</p>
        <p class="mm-nota">El día con menos presión a ±${mejorDia.margen} días en la misma zona, según el modelo.</p>
        <button type="button" class="btn-mini" data-fecha="${mejorDia.fecha}">Ver ese día</button></div>`;
    } else if (mejorDia) {
      tarjeta = `<div class="mm"><p class="eyebrow">Mejor día alternativo</p><p class="mm-nota">Ningún día a ±${mejorDia.margen} días tiene menos presión en esta zona.</p></div>`;
    } else if (mejor) {
      const d = mejor.dia;
      const donde = periodo ? 'Dentro de las fechas elegidas.' : `Entre el ${diaMes(v.desde)} y el ${diaMes(sumar(v.desde, v.dias - 1))}.`;
      tarjeta = `<div class="mm"><p class="eyebrow">Día más tranquilo</p><p class="mm-valor">${esc(fechaLarga(d.fecha))}</p>
        <p>${pill(d.nivel)}</p><p class="mm-nota">${esc(delta(d.ratio))}</p><p class="mm-nota">${esc(donde)}</p>
        ${periodo || d.fecha !== E.desde ? `<button type="button" class="btn-mini" data-fecha="${d.fecha}">${periodo ? 'Ver solo ese día' : 'Ver ese día'}</button>` : '<p class="mm-nota"><strong>Es el día que estás viendo.</strong></p>'}</div>`;
    }
    if (!tarjeta) return '';
    return `<section class="pz-sec" aria-labelledby="pz-s-c">
      <h3 id="pz-s-c">Mejor momento para ir</h3>
      <div class="mm-grid">${tarjeta}</div>
    </section>`;
  }

  function seccionAlternativas(alts, sinDatos) {
    const titulo = sinDatos ? 'Zonas cercanas con previsión' : 'Alternativas cercanas con menos gente';
    alts = (alts || []).slice().sort((a, b) => (a.km == null ? 1e9 : a.km) - (b.km == null ? 1e9 : b.km)).slice(0, 3); // las 3 más cercanas
    const cuerpo = alts && alts.length
      ? `<ul class="alt-lista">${alts.map(a => `<li><button type="button" class="alt" data-zona="${a.zonaId}">
          <span class="alt-nombre">${esc(a.nombre)}</span>
          <span class="alt-dato">${pill(a.nivel)}<span>${pct(a.ratio)}</span></span>
          <span class="alt-dist">${a.minutos != null ? `A unos ${a.minutos} min en coche` : `A unos ${a.km} km${a.delModelo ? ' · la menos saturada cerca, según el modelo' : ''}`}</span></button></li>`).join('')}</ul>`
      : `<p class="pz-ayuda">${esPeriodo() ? 'En esas fechas no hay zonas cercanas con menos gente. Prueba con otras.' : 'Ese día no hay zonas cercanas con menos gente. Prueba con otro día.'}</p>`;
    return `<section class="pz-sec" aria-labelledby="pz-s-d"><h3 id="pz-s-d">${titulo}</h3>${cuerpo}</section>`;
  }

  function barraReparto(titulo, a, b) {
    return `<div class="rp"><p class="rp-tit">${titulo}</p>
      <div class="rp-barra" aria-hidden="true"><span class="rp-a" style="width:${a.v}%"></span><span class="rp-b" style="width:${b.v}%"></span></div>
      <p class="rp-ley"><span><i class="sw sw-a" aria-hidden="true"></i>${a.t} <strong>${a.v}${NBSP}%</strong></span><span><i class="sw sw-b" aria-hidden="true"></i>${b.t} <strong>${b.v}${NBSP}%</strong></span></p></div>`;
  }
  function seccionPerfil(perfil) {
    if (!perfil) return '';
    return plegable(`<section class="pz-sec" aria-labelledby="pz-s-e">
      <h3 id="pz-s-e">Quién viene</h3>
      ${perfil.deUnDia != null ? barraReparto('Tipo de visita (aproximado)', { t: 'De un día', v: perfil.deUnDia }, { t: 'Con pernoctación', v: perfil.conPernocta }) : ''}
      ${barraReparto('Procedencia', { t: 'De Asturias', v: perfil.asturias }, { t: 'Resto de España', v: perfil.restoEspana })}
      <p class="pz-nota">Media de ${MES[perfil.mes - 1]} en años anteriores (llegadas de ocio). Sin extranjeros: los datos de movilidad solo cubren residentes en España. El tipo de visita es aproximado, porque una persona puede pasar varias noches.</p>
    </section>`);
  }

  function seccionFiabilidad(p, fiab) {
    const h = p.horizonte == null ? null : p.horizonte >= 8 ? '8+' : String(p.horizonte);
    const fila = fiab && h && fiab.porHorizonte[h];
    const antelacion = p.horizonte != null ? ` Hecha con ${p.horizonte} ${p.horizonte === 1 ? 'día' : 'días'} de antelación.` : '';
    const nota = fila ? ' ' + fila.nota : '';
    const meteo = !p.conMeteo && p.ratio != null ? ' Sin previsión del tiempo para este día: usa calendario y eventos.' : '';
    return `<p class="pz-fiab">${ICONO_INFO}<span><strong>Predicción</strong>, no es un dato medido.${antelacion}${esc(nota)}${meteo}</span></p>`;
  }

  /* ====================================================================
   * Sitios de interés
   * No tienen previsión propia: se muestra la de su concejo principal (concejos[0]).
   * ==================================================================== */
  const prevSitio = s => E.prevPorConcejo[s.concejos[0]] || { nivel: 'gris' };
  const concejosSitio = s => s.concejos.map(nombreC).join(', ');
  // Para ordenar: los que no tienen datos van siempre al final
  const ratioOrden = (s, signo) => { const p = prevSitio(s); return p.ratio == null ? Infinity : signo * p.ratio; };

  function creditoFoto(f) {
    if (!f) return '';
    const autor = f.autor ? esc(f.autor) : 'Autor en Wikimedia Commons';
    return `<a class="credito" href="${esc(f.pagina)}" target="_blank" rel="noopener">Foto: ${autor}${f.licencia ? ' · ' + esc(f.licencia) : ''}</a>`;
  }

  // Viñeta del mapa al pulsar un sitio
  function htmlSitio(id) {
    const s = E.sitiosPorId[id];
    if (!s) return '';
    const p = prevSitio(s), principal = nombreC(s.concejos[0]);
    return `<div class="ps">
      ${s.foto ? `<img class="ps-foto" src="${esc(s.foto.src)}" alt="" width="480" height="360">` : ''}
      <div class="ps-cuerpo">
        <h3 class="ps-nombre">${esc(s.nombre)}</h3>
        <p class="ps-concejo">Concejo: ${esc(concejosSitio(s))}</p>
        <div class="ps-af">${pill(p.nivel)}<span>${p.ratio != null ? esc(delta(p.ratio, esPeriodo())) : 'Sin datos suficientes'}</span></div>
        <p class="ps-nota">Previsión del concejo de ${esc(principal)}; no hay cifras de cada sitio.${s.ubicacionAproximada ? ' Ubicación aproximada.' : ''}</p>
        <button type="button" class="btn-mini" data-concejo="${s.concejos[0]}">Ver el concejo</button>
        ${creditoFoto(s.foto)}
      </div>
    </div>`;
  }

  // Muestra el sitio en el mapa (cambia a la vista de mapa si hace falta) y abre su viñeta
  function verSitio(id) {
    if (!E.sitiosPorId[id] || !E.mapa) return;
    if (E.tab !== 'inicio') irPestana('inicio', true);
    if (E.vista !== 'mapa') $('[data-vista="mapa"]').click();
    const marco = $('#mapa-marco'), r = marco.getBoundingClientRect();
    if (r.top < 0 || r.bottom > window.innerHeight) marco.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    E.mapa.abrirSitio(id);
    anunciar(`${E.sitiosPorId[id].nombre}, abierto en el mapa.`);
  }

  // Sección del panel: los sitios del concejo elegido o, si no hay concejo, los de toda la zona
  function seccionSitios(zonaId) {
    const c = E.concejo ? E.concejosPorId[E.concejo] : null;
    const lista = E.sitios.filter(s => c ? s.concejos.indexOf(c.id) !== -1
      : E.concejosPorId[s.concejos[0]] && E.concejosPorId[s.concejos[0]].zonaId === zonaId);
    if (!lista.length) return '';
    const titulo = c ? `Qué ver en ${c.nombre}` : 'Qué ver en la zona';
    return plegable(`<section class="pz-sec" aria-labelledby="pz-s-h">
      <h3 id="pz-s-h">${esc(titulo)}</h3>
      <p class="pz-ayuda">Pulsa un sitio para verlo en el mapa.${c ? '' : ' Elige un concejo para ver solo los suyos.'}</p>
      <ul class="ss-lista">${lista.map(s => `<li><button type="button" class="ss" data-sitio="${s.id}">
        ${s.foto ? `<img src="${esc(s.foto.src)}" alt="" loading="lazy" width="64" height="48">` : '<span class="ss-sin"></span>'}
        <span class="ss-txt"><span class="ss-nombre">${esc(s.nombre)}</span>${c ? '' : `<span class="ss-concejo">${esc(nombreC(s.concejos[0]))}</span>`}</span>
      </button></li>`).join('')}</ul>
    </section>`);
  }

  /* ---------- Sección propia en Inicio, ordenable por la afluencia del concejo ---------- */
  const PASO_SITIOS = 24;
  function configurarSitios() {
    $('#sitios-total').textContent = String(E.sitios.length);
    $('#sitios-orden').addEventListener('change', e => {
      E.sitiosOrden = e.target.value;
      renderSitios({ reiniciar: true });
      anunciar('Sitios ordenados: ' + e.target.selectedOptions[0].textContent.toLowerCase() + '.');
    });
    $('#sitios-mas').addEventListener('click', () => {
      const antes = E.sitiosVisibles;
      E.sitiosVisibles += PASO_SITIOS;
      renderSitios();
      const primero = $$('#sitios-lista .sc-nombre')[antes];
      if (primero) { primero.tabIndex = -1; primero.focus(); }
    });
    $('#sitios').addEventListener('click', e => {
      const bs = e.target.closest('[data-sitio]');
      if (bs) { verSitio(bs.dataset.sitio); return; }
      const bc = e.target.closest('[data-concejo]');
      if (bc) abrirConcejo(bc.dataset.concejo, { foco: true, encuadrar: true });
    });
  }

  function renderSitios(opts) {
    opts = opts || {};
    if (opts.reiniciar || !E.sitiosVisibles) E.sitiosVisibles = PASO_SITIOS;
    const periodo = esPeriodo();
    const filtrados = E.sitios.filter(s => coincideTipo(E.zonasPorId[(E.concejosPorId[s.concejos[0]] || {}).zonaId]));
    const orden = E.sitiosOrden;
    filtrados.sort((a, b) => orden === 'concejo'
      ? nombreC(a.concejos[0]).localeCompare(nombreC(b.concejos[0]), 'es') || a.nombre.localeCompare(b.nombre, 'es')
      : (ratioOrden(a, orden === 'mas' ? -1 : 1) - ratioOrden(b, orden === 'mas' ? -1 : 1)) || a.nombre.localeCompare(b.nombre, 'es'));
    const vis = filtrados.slice(0, E.sitiosVisibles);
    $('#sitios-sub').textContent = `${textoSel()}${periodo ? ' · media por día' : ''}${E.tipo === 'todos' ? '' : ' · Solo ' + TIPO_NOMBRE[E.tipo].toLowerCase()}`;
    $('#sitios-lista').innerHTML = vis.map(s => {
      const p = prevSitio(s);
      return `<li><article class="sc">
        ${s.foto ? `<img class="sc-foto" src="${esc(s.foto.src)}" alt="" loading="lazy" width="480" height="360">` : ''}
        <div class="sc-cuerpo">
          <h3 class="sc-nombre">${esc(s.nombre)}</h3>
          <p class="sc-concejo">${esc(concejosSitio(s))}</p>
          <div class="sc-dato">${pill(p.nivel)}<span class="sc-pct">${p.ratio != null ? pct(p.ratio) : ''}<span class="sr"> en el concejo${periodo ? ', de media' : ''}</span></span></div>
          <div class="sc-acc">
            <button type="button" class="btn-mini" data-sitio="${s.id}">Ver en el mapa<span class="sr">: ${esc(s.nombre)}</span></button>
            <button type="button" class="btn-mini" data-concejo="${s.concejos[0]}">Ver el concejo<span class="sr"> de ${esc(nombreC(s.concejos[0]))}</span></button>
          </div>
          ${creditoFoto(s.foto)}
        </div>
      </article></li>`;
    }).join('') || '<li class="vacio">No hay sitios con este filtro.</li>';
    $('#sitios-cuenta').textContent = `Mostrando ${vis.length} de ${filtrados.length}`;
    $('#sitios-mas').hidden = vis.length >= filtrados.length;
  }

  /* ====================================================================
   * Eventos: agenda de las salidas del modelo (festivos, partidos y grandes eventos
   * de fuentes públicas). La asistencia, cuando la hay, es la que publica la fuente.
   * ==================================================================== */
  const PASO_EVENTOS = 20;
  const ICONO_EVENTO = '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><rect x="1.8" y="3" width="12.4" height="11" rx="2" class="ico-trazo"/><path d="M1.8 6.6h12.4M5 1.6v2.8M11 1.6v2.8" class="ico-trazo"/></svg>';
  const zonaDeConcejo = ine => (E.concejosPorId[ine] || {}).zonaId;
  const fechaEvento = e => (e.inicio === e.fin ? fechaCorta(e.inicio) : `${fechaCorta(e.inicio)} – ${fechaCorta(e.fin)}`) + (e.hora ? ', ' + e.hora : '');

  function htmlEvento(e, conConcejo) {
    return `<li class="ev">
      <div class="ev-fecha" aria-hidden="true"><span class="ev-dia">${deISO(e.inicio).getDate()}</span><span class="ev-mes">${esc(MES[deISO(e.inicio).getMonth()].slice(0, 3))}</span></div>
      <div class="ev-txt">
        <p class="ev-titulo">${esc(e.titulo)}</p>
        <p class="ev-meta"><span class="sr">${esc(fechaLarga(e.inicio))}. </span><span class="ev-cat">${esc(e.categoria)}</span>
          ${esc(fechaEvento(e))}${e.lugar ? ' · ' + esc(e.lugar) : ''}${conConcejo && e.concejo ? ' · ' + esc(nombreC(e.concejo)) : ''}</p>
        ${e.asistencia ? `<p class="ev-asis">Unas ${num(e.asistencia)} personas, según la fuente${e.impacto ? `<span class="ev-imp">: ${e.impacto >= 1 ? `${String(Math.round(e.impacto * 10) / 10).replace('.', ',')} veces` : `el ${Math.round(e.impacto * 100)}${NBSP}% de`} los visitantes de un día normal en ${esc(nombreC(e.concejo))}</span>` : ''}</p>` : ''}
      </div>
      ${conConcejo && e.concejo ? `<button type="button" class="btn-mini" data-concejo="${e.concejo}">Ver el concejo<span class="sr"> de ${esc(nombreC(e.concejo))}</span></button>` : ''}
    </li>`;
  }

  async function configurarEventos() {
    // Las categorías del filtro salen de todos los eventos disponibles
    const todo = await D.getEventos(E.info.hoy, E.maxFecha);
    const cats = Array.from(new Set(todo.eventos.map(e => e.categoria))).sort((a, b) => a.localeCompare(b, 'es'));
    $('#eventos-cat').innerHTML = '<option value="todas">Todos</option>' + cats.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('');
    $('#eventos-cat').addEventListener('change', e => { E.eventosCat = e.target.value; renderEventos({ reiniciar: true }); });
    $('#eventos-mas').addEventListener('click', () => {
      const antes = E.eventosVisibles;
      E.eventosVisibles += PASO_EVENTOS;
      renderEventos();
      const t = $$('#eventos-lista .ev-titulo')[antes];
      if (t) { t.tabIndex = -1; t.focus(); }
    });
    $('#eventos').addEventListener('click', e => {
      const bc = e.target.closest('[data-concejo]');
      if (bc) abrirConcejo(bc.dataset.concejo, { foco: true, encuadrar: true });
    });
  }

  function renderEventos(opts) {
    opts = opts || {};
    if (opts.reiniciar || !E.eventosVisibles) E.eventosVisibles = PASO_EVENTOS;
    const d = E.eventos, cat = E.eventosCat;
    const lista = d.eventos.filter(e => (cat === 'todas' || e.categoria === cat) && (!e.concejo || coincideTipo(E.zonasPorId[zonaDeConcejo(e.concejo)])));
    const vis = lista.slice(0, E.eventosVisibles);
    $('#eventos-sub').textContent = textoSel() + (E.tipo === 'todos' ? '' : ' · Solo ' + TIPO_NOMBRE[E.tipo].toLowerCase());
    $('#eventos-nota').textContent = 'Festivos de Asturias y de cada concejo (BOE y BOPA), partidos del Real Oviedo y del Sporting en su estadio, y grandes fiestas, festivales, ferias y pruebas deportivas recopilados de sus webs oficiales y de prensa. Son días en los que puede venir más gente de lo normal.';
    let vacio = '';
    if (!lista.length) {
      vacio = d.hastaDatos && E.desde > d.hastaDatos
        ? 'Todavía no hay eventos publicados para estas fechas.'
        : `No hay eventos ni festivos ${esPeriodo() ? 'en estas fechas' : 'este día'}${cat === 'todas' ? '' : ' de este tipo'}.`;
    }
    // Agrupados por día de inicio
    const grupos = [];
    vis.forEach(e => { const g = grupos[grupos.length - 1]; if (g && g.f === e.inicio) g.ev.push(e); else grupos.push({ f: e.inicio, ev: [e] }); });
    $('#eventos-lista').innerHTML = vacio ? `<p class="vacio">${esc(vacio)}</p>` : grupos.map(g => `<div class="ev-grupo">
      <h3 class="ev-grupo-t">${ICONO_EVENTO}${esc(fechaLarga(g.f))}</h3>
      <ul>${g.ev.map(e => htmlEvento(e, true)).join('')}</ul></div>`).join('');
    $('#eventos-cuenta').textContent = lista.length ? `Mostrando ${vis.length} de ${lista.length}` : '';
    // Resumen visible con la sección cerrada
    $('#eventos-resumen').textContent = lista.length
      ? `${lista.length} ${lista.length === 1 ? 'evento' : 'eventos'} ${esPeriodo() ? 'en las fechas elegidas' : 'ese día'}`
      : `Ninguno ${esPeriodo() ? 'en las fechas elegidas' : 'ese día'}`;
    $('#eventos-mas').hidden = vis.length >= lista.length;
  }

  // Panel: eventos en las fechas elegidas dentro del concejo elegido o de toda la zona
  function seccionEventosPanel(zonaId) {
    const c = E.concejo;
    const lista = E.eventos.eventos.filter(e => (c ? e.concejo === c : zonaDeConcejo(e.concejo) === zonaId));
    if (!lista.length) return '';
    const max = 6;
    return `<section class="pz-sec" aria-labelledby="pz-s-i">
      <h3 id="pz-s-i">Eventos ${esPeriodo() ? 'en estas fechas' : 'ese día'}</h3>
      <p class="pz-ayuda">Eventos, partidos y festivos locales ${c ? 'en el concejo' : 'en la zona'}. Pueden atraer más gente de lo normal.</p>
      <ul class="ev-panel">${lista.slice(0, max).map(e => htmlEvento(e, false)).join('')}</ul>
      ${lista.length > max ? `<p class="pz-nota">Y ${lista.length - max} más en la sección «Eventos».</p>` : ''}
    </section>`;
  }

  /* ====================================================================
   * Pestañas Funciones avanzadas y Sobre los datos (pestanas/gestion/, pestanas/sobre/)
   * Se montan la primera vez que se abren, con el objeto del módulo «datos».
   * ==================================================================== */
  const COMPONENTE = { gestion: 'gestion', datos: 'sobre' };
  const montadas = {};
  function mostrarComponente(t) {
    const nombre = COMPONENTE[t];
    const comp = nombre && window.Pestanas && window.Pestanas[nombre];
    if (!comp) return;
    const cont = $('#panel-' + t);
    if (montadas[t]) { if (comp.mostrar) comp.mostrar(); return; }
    montadas[t] = true;
    window.DatosModelo.cargar()
      .then(datos => comp.montar(cont, datos, window.UtilWeb))
      .catch(err => {
        console.error(err);
        montadas[t] = false; // al volver a la pestaña se reintenta
        cont.innerHTML = `<div class="tarjeta"><p><strong>No se han podido cargar las salidas del modelo.</strong></p><p class="error-datos">${esc(err.message)}</p></div>`;
      });
  }

  /* ---------- Aviso de datos sintéticos ---------- */
  function avisoSintetico() {
    window.DatosModelo.cargarInicio().then(d => {
      if (!d.sintetico) return;
      $('#aviso-sintetico').hidden = false;
    }).catch(err => {
      console.error(err);
      const a = $('#aviso-sintetico');
      a.querySelector('p').innerHTML = `<strong>No se han podido cargar las salidas del modelo.</strong> <span class="error-datos">${esc(err.message)}</span>`;
      a.hidden = false;
    });
  }

  /* ---------- Utilidades para las pestañas de pestanas/ ---------- */
  window.UtilWeb = Object.freeze({
    $, $$, esc, num, pct, delta, pill, anunciar, listaNatural,
    fechaLarga: f => fechaLarga(f), fechaCorta: f => fechaCorta(f),
    deISO, aISO, sumar, diasEntre, NIVEL, ICONO, NBSP, MENOS,
  });

  /* ---------- Arranque ---------- */
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
