/* ==========================================================================
 * PESTAÑA «Funciones avanzadas» (antes «Gestión») — PROPIEDAD DE LA PERSONA 2
 * --------------------------------------------------------------------------
 * interfaz/app.js llama a montar() la primera vez que se abre la pestaña, y a
 * mostrar() cada vez que se vuelve a ella.
 *
 *   contenedor  <section id="panel-gestion"> (vacío)
 *   datos       objeto de window.DatosModelo.cargar() (ver notas/coordinacion_web.md)
 *   util        window.UtilWeb (pill, num, pct, esc, anunciar…)
 *
 * Las secciones son paneles: una fila de botones (pestañas) arriba y solo se ve
 * el panel elegido. Los números salen de GestionLogica (pestanas/gestion/logica.js)
 * y esta, de las salidas del modelo. Textos editables: config-gestion.js.
 * Los nombres de los concejos llegan de window.Datos.getConcejos() (fachada de Inicio).
 * ========================================================================== */
window.Pestanas = window.Pestanas || {};
(function () {
  'use strict';

  const SCRIPTS = ['pestanas/gestion/config-gestion.js', 'pestanas/gestion/logica.js'];
  const LETRA = ['D', 'L', 'M', 'X', 'J', 'V', 'S'];
  const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const LUPA = '<svg class="ico lupa" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="4.8" class="ico-trazo"/><path d="M10.6 10.6 14 14" class="ico-trazo"/></svg>';
  const CERRAR = '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9" class="ico-trazo"/></svg>';
  const PANELES = [
    { id: 'saturacion', t: 'Previsión de saturación' },
    { id: 'alertas', t: 'Alertas' },
    { id: 'lagos', t: 'Lagos de Covadonga' },
    { id: 'fiabilidad', t: 'Fiabilidad del modelo' },
    { id: 'perfil', t: 'Perfil del visitante' },
    { id: 'exportar', t: 'Exportar datos' },
  ];

  function cargarScripts(lista) {
    return lista.reduce((p, src) => p.then(() => new Promise((ok, ko) => {
      if (document.querySelector('script[data-g="' + src + '"]')) return ok();
      const s = document.createElement('script');
      s.src = src; s.dataset.g = src;
      s.onload = ok; s.onerror = () => ko(new Error('No se ha podido cargar ' + src));
      document.head.appendChild(s);
    })), Promise.resolve());
  }

  // Nombres de los concejos (código INE → nombre). Si la fachada no está, se usa el código.
  function nombresConcejos() {
    if (!window.Datos || typeof window.Datos.getConcejos !== 'function') return Promise.resolve({});
    return window.Datos.getConcejos().then(lista => {
      const m = {};
      lista.forEach(c => { m[c.id] = c.nombre; });
      return m;
    }).catch(() => ({}));
  }

  window.Pestanas.gestion = {
    montar(contenedor, datos, util) {
      return Promise.all([cargarScripts(SCRIPTS), nombresConcejos()])
        .then(([, nombres]) => pintar(contenedor, datos, util, nombres)).catch(err => {
          console.error(err);
          contenedor.innerHTML = '<div class="tarjeta"><p><strong>No se ha podido montar la pestaña Funciones avanzadas.</strong></p><p class="error-datos">' + util.esc(err.message) + '</p></div>';
        });
    },
    mostrar() {},
  };

  function pintar(cont, datos, util, nombresIne) {
    const L = window.GestionLogica, C = window.GestionConfig;
    const { esc, num, pct, pill, NBSP, ICONO, NIVEL } = util;
    const pc100 = x => (x == null ? '—' : Math.round(x * 100) + NBSP + '%');
    const zonas = L.zonas(datos);
    const principal = zonas[0];
    const zonaPorId = {};
    zonas.forEach(z => { zonaPorId[z.zona_mitma_id] = z; });
    const nombreZ = id => (zonaPorId[id] ? zonaPorId[id].nombre_zona : id);
    const nombreC = ine => nombresIne[ine] || 'Concejo ' + ine;
    const umbrales = L.umbralesDisponibles(datos);
    const umb = datos.regulacion.umbrales || datos.predicciones.umbrales;
    const hoy = datos.predicciones.fecha_hoy;
    const finPrev = L.finPrevision(datos);
    const calendario = {};
    ((datos.calendario && datos.calendario.dias) || []).forEach(d => { calendario[d.fecha] = d; });
    const alertas = L.alertasProximas(datos);
    const mesHoy = +hoy.slice(5, 7);
    const opcionesZona = zonas.map(z => `<option value="${esc(z.zona_mitma_id)}">${esc(z.nombre_zona)}</option>`).join('');
    const lagos = L.compararLagos(datos);
    const paneles = PANELES.filter(p => p.id !== 'lagos' || lagos);

    // Periodos de la previsión de saturación (todos desde hoy y dentro de lo que cubre el modelo)
    const anioHoy = +hoy.slice(0, 4), anioFin = +finPrev.slice(0, 4);
    const limitar = f => (f > finPrev ? finPrev : f);
    const periodos = [
      { v: 'p28', t: 'Próximas 4 semanas', desde: hoy, hasta: limitar(L.sumarDias(hoy, 27)) },
      { v: 'p91', t: 'Próximos 3 meses', desde: hoy, hasta: limitar(L.sumarDias(hoy, 90)) },
    ];
    if (anioFin > anioHoy) periodos.push({ v: 'fin', t: `Lo que queda de ${anioHoy}`, desde: hoy, hasta: anioHoy + '-12-31' });
    for (let a = anioHoy + 1; a <= anioFin; a++) periodos.push({ v: 'a' + a, t: `Todo ${a}`, desde: a + '-01-01', hasta: limitar(a + '-12-31') });
    periodos.push({ v: 'todo', t: `Toda la previsión (hasta el ${util.fechaLarga(finPrev).replace(/^\S+ /, '')})`, desde: hoy, hasta: finPrev });

    const estado = {
      panel: paneles[0].id,
      umbralIdx: Math.max(0, umbrales.indexOf(umb.rojo)),
      periodo: 'p91', sel: null, satActiva: -1, satOpciones: [],
      alZona: '', todasZonas: false, concejos: [], // concejos = [{ ine, zona }] en el orden en que se eligen
      filtro: 'rojo', csv: null, csvOrigen: null,
    };

    cont.innerHTML = `
    <div class="g-intro">
      <h1 class="titulo-pagina">Funciones avanzadas</h1>
      <p class="g-lead">Herramientas para ayuntamientos, el Principado y el Parque Nacional: qué días se espera saturación, qué viene en las próximas semanas y cuánto podemos fiarnos del modelo.</p>
      <div class="g-paneles" role="tablist" aria-label="Funciones avanzadas">
        ${paneles.map((p, i) => `<button type="button" role="tab" id="gt-${p.id}" aria-controls="g-${p.id}" aria-selected="${i === 0}" tabindex="${i === 0 ? 0 : -1}">${esc(p.t)}</button>`).join('')}
      </div>
    </div>

    <section class="tarjeta g-sec" id="g-saturacion" role="tabpanel" aria-labelledby="gt-saturacion" tabindex="-1">
      <h2>Previsión de saturación</h2>
      <p class="g-desc">Días en los que el modelo prevé más visitantes que el umbral elegido. Busca una zona o un concejo para ver los días uno a uno. Se basa solo en la previsión del modelo, no en lo que pasó años anteriores.</p>
      <div class="sat-controles">
        <div class="g-buscador">
          <label for="sat-buscar" class="filtro-et">Buscar una zona o un concejo</label>
          <div class="buscador-caja">
            ${LUPA}
            <input id="sat-buscar" class="g-buscar-in" type="text" role="combobox" autocomplete="off" spellcheck="false"
                   aria-autocomplete="list" aria-expanded="false" aria-controls="sat-lista" aria-describedby="sat-buscar-ayuda"
                   placeholder="Cangas de Onís, Llanes, una zona…">
            <ul id="sat-lista" class="g-buscar-lista" role="listbox" aria-label="Zonas y concejos encontrados" hidden></ul>
          </div>
          <p id="sat-buscar-ayuda" class="sr">Escribe el nombre de una zona o de un concejo. Usa las flechas para moverte por los resultados e Intro para elegir.</p>
        </div>
        <div>
          <label for="sat-periodo" class="filtro-et">Periodo</label>
          <select id="sat-periodo" class="select">${periodos.map(p => `<option value="${p.v}"${p.v === estado.periodo ? ' selected' : ''}>${esc(p.t)}</option>`).join('')}</select>
        </div>
      </div>
      <div class="umbral">
        <label for="umbral" class="umbral-et">Contar como saturación los días con más de <strong id="umbral-valor"></strong> de visitantes sobre un día normal</label>
        <input type="range" id="umbral" min="0" max="${umbrales.length - 1}" step="1" value="${estado.umbralIdx}">
        <div class="umbral-escala" aria-hidden="true"><span>${esc(pct(umbrales[0]))}</span><span>${esc(pct(umbrales[umbrales.length - 1]))}</span></div>
      </div>
      <div id="sat-detalle" class="sat-detalle"></div>
      <h3 class="sat-sub" id="sat-zonas-t">Todas las zonas en este periodo</h3>
      <ul class="rg-lista sat-zonas" id="sat-zonas" aria-labelledby="sat-zonas-t"></ul>
      <p class="g-nota">Hasta 7 días vista la previsión incluye el tiempo; hasta unos 2 meses usa calendario y eventos; más allá solo tiene en cuenta el calendario (festivos, puentes, vacaciones) y es orientativa. Por defecto, saturación es ${esc(pct(umb.rojo))} sobre un día normal, el rojo del semáforo (alta: ${esc(pct(umb.ambar))}). Un concejo muestra la previsión de su zona.</p>
    </section>

    <section class="tarjeta g-sec" id="g-alertas" role="tabpanel" aria-labelledby="gt-alertas" tabindex="-1" hidden>
      <h2>Alertas de las próximas ${Math.round(C.diasAlertas / 7)} semanas</h2>
      <p class="g-desc">Nivel previsto por día. Elige una zona y añade sus concejos a la tabla, o muestra todas las zonas. Hasta una semana vista la previsión incluye el tiempo; después usa solo calendario y eventos y es más incierta.</p>
      <div class="al-controles">
        <div>
          <label for="al-zona" class="filtro-et">Zona</label>
          <div class="al-fila">
            <select id="al-zona" class="select"><option value="">Elige una zona…</option>${opcionesZona}</select>
            <button type="button" class="btn" id="al-todas-zonas" aria-pressed="false">Todas las zonas</button>
          </div>
        </div>
        <div>
          <span class="filtro-et" id="al-concejos-et">Concejos de la zona</span>
          <div class="al-fila">
            <div class="multi">
              <button type="button" class="select multi-btn" id="al-concejos-btn" aria-expanded="false" aria-controls="al-concejos-pop" aria-labelledby="al-concejos-et al-concejos-btn" disabled>Elige primero una zona</button>
              <div class="multi-pop" id="al-concejos-pop" hidden></div>
            </div>
            <button type="button" class="btn" id="al-todos-concejos" aria-pressed="false" disabled>Todos los concejos</button>
          </div>
        </div>
      </div>
      <div class="al-chips" id="al-chips" aria-label="Concejos en la tabla"></div>
      <p class="pz-ayuda al-vacia" id="al-vacia">La tabla está vacía. Elige una zona y marca uno o varios concejos, o pulsa «Todas las zonas».</p>
      <div class="tabla-marco" id="matriz-marco" hidden><table class="matriz" id="matriz"></table></div>
      <h3 class="sat-sub">Resumen de los días con alerta</h3>
      <fieldset class="segmentado g-filtro">
        <legend class="filtro-et">Mostrar</legend>
        <div class="seg-opciones">
          <label><input type="radio" name="filtro-alerta" value="rojo" checked><span>Solo saturación</span></label>
          <label><input type="radio" name="filtro-alerta" value="todas"><span>Alta y saturación</span></label>
        </div>
      </fieldset>
      <div id="alertas-lista" class="al-lista"></div>
    </section>

    <section class="tarjeta g-sec" id="g-lagos" role="tabpanel" aria-labelledby="gt-lagos" tabindex="-1" hidden>
      <h2>Comparación con el acceso regulado a los Lagos</h2>
      <p class="g-desc" id="lagos-desc"></p>
      <div class="tabla-marco" id="lagos-tabla"></div>
      <p class="g-nota" id="lagos-nota"></p>
    </section>

    <section class="tarjeta g-sec" id="g-fiabilidad" role="tabpanel" aria-labelledby="gt-fiabilidad" tabindex="-1" hidden>
      <h2>Fiabilidad del modelo</h2>
      <p class="g-desc">Cuánto acierta el modelo en días que no ha visto al entrenar, según con cuánta antelación se hace la previsión.</p>
      <label for="fiab-zona" class="filtro-et">Zona</label>
      <select id="fiab-zona" class="select">${opcionesZona}</select>
      <div class="metricas" id="fiab-metricas"></div>
      <p class="g-nota" id="fiab-nota"></p>
      <details class="detalles"><summary>Ver el detalle por días de antelación</summary><div class="tabla-marco" id="fiab-tabla"></div></details>
    </section>

    <section class="tarjeta g-sec" id="g-perfil" role="tabpanel" aria-labelledby="gt-perfil" tabindex="-1" hidden>
      <h2>Perfil del visitante</h2>
      <p class="g-desc">De dónde llega quien viene a la zona por ocio y cuánto se queda. Media histórica del mes elegido.</p>
      <div class="sim-form">
        <div><label for="perfil-zona" class="filtro-et">Zona</label><select id="perfil-zona" class="select">${opcionesZona}</select></div>
        <div><label for="perfil-mes" class="filtro-et">Mes</label><select id="perfil-mes" class="select">${MESES.map((m, i) => `<option value="${i + 1}"${i + 1 === mesHoy ? ' selected' : ''}>${m.charAt(0).toUpperCase() + m.slice(1)}</option>`).join('')}</select></div>
      </div>
      <div class="metricas" id="perfil-metricas"></div>
      <p class="g-nota" id="perfil-nota"></p>
      <h3 class="filtro-et" style="margin-top:1rem">Patrón horario</h3>
      <p class="g-desc" id="perfil-horas">Pendiente de datos: aún no hay llegadas por hora (data/clean/llegadas_por_hora.parquet). Cuando lleguen, aquí saldrá la hora a la que suele llegar la gente.</p>
    </section>

    <section class="tarjeta g-sec" id="g-exportar" role="tabpanel" aria-labelledby="gt-exportar" tabindex="-1" hidden>
      <h2>Exportar datos</h2>
      <p class="g-desc">Tablas en CSV (separadas por punto y coma, decimales con coma) para abrir en Excel o LibreOffice.</p>
      <div class="exp-botones">
        <button type="button" class="btn" data-exportar="saturacion">Días con saturación prevista</button>
        <button type="button" class="btn" data-exportar="prevision">Alertas de las próximas ${Math.round(C.diasAlertas / 7)} semanas</button>
        <button type="button" class="btn" data-exportar="umbral">Días al año sobre el umbral</button>
      </div>
      <p class="g-nota">«Días con saturación prevista» usa el periodo y el umbral elegidos en «Previsión de saturación» (ahora: <span id="exp-sat-txt"></span>) e incluye todas las zonas.</p>
    </section>

    <dialog id="dlg-csv" aria-labelledby="dlg-titulo" aria-describedby="dlg-desc">
      <div class="dlg-in">
        <h2 id="dlg-titulo">Exportar <span id="dlg-nombre"></span></h2>
        <p id="dlg-desc" class="g-desc"></p>
        <label for="dlg-texto" class="filtro-et">Contenido del archivo</label>
        <textarea id="dlg-texto" rows="9" readonly spellcheck="false"></textarea>
        <p class="ayuda" id="dlg-estado" role="status"></p>
        <div class="dlg-botones">
          <button type="button" class="btn btn-prim" id="dlg-copiar">Copiar</button>
          <button type="button" class="btn" id="dlg-descargar">Descargar archivo</button>
          <button type="button" class="btn btn-sec" id="dlg-cerrar">Cerrar</button>
        </div>
      </div>
    </dialog>`;

    const q = (s) => cont.querySelector(s);
    const qa = (s) => Array.from(cont.querySelectorAll(s));
    q('#fiab-zona').value = principal.zona_mitma_id;
    q('#perfil-zona').value = principal.zona_mitma_id;

    /* ---------- Paneles (pestañas internas) ---------- */
    const botonesPanel = qa('.g-paneles [role="tab"]');
    function abrirPanel(id, enfocar) {
      estado.panel = id;
      botonesPanel.forEach(b => {
        const on = b.id === 'gt-' + id;
        b.setAttribute('aria-selected', String(on));
        b.tabIndex = on ? 0 : -1;
        q('#' + b.getAttribute('aria-controls')).hidden = !on;
      });
      if (id === 'exportar') q('#exp-sat-txt').textContent = textoSatActual();
      if (enfocar) q('#gt-' + id).focus();
    }
    botonesPanel.forEach((b, i) => {
      b.addEventListener('click', () => abrirPanel(paneles[i].id));
      b.addEventListener('keydown', e => {
        let j = null;
        if (e.key === 'ArrowRight') j = (i + 1) % paneles.length;
        else if (e.key === 'ArrowLeft') j = (i - 1 + paneles.length) % paneles.length;
        else if (e.key === 'Home') j = 0;
        else if (e.key === 'End') j = paneles.length - 1;
        if (j !== null) { e.preventDefault(); abrirPanel(paneles[j].id, true); }
      });
    });

    /* ---------- Previsión de saturación ---------- */
    const umbralActual = () => umbrales[+q('#umbral').value];
    const periodoActual = () => periodos.find(p => p.v === estado.periodo) || periodos[0];
    // Si el periodo cruza de año, las dos fechas llevan el año
    const sinDia = f => util.fechaLarga(f).replace(/^\S+ /, '');
    const conAnio = f => (/\d{4}$/.test(sinDia(f)) ? sinDia(f) : sinDia(f) + ' de ' + f.slice(0, 4));
    const rangoTxt = p => (p.desde.slice(0, 4) !== p.hasta.slice(0, 4)
      ? `del ${conAnio(p.desde)} al ${conAnio(p.hasta)}` : `del ${sinDia(p.desde)} al ${sinDia(p.hasta)}`);
    const textoSatActual = () => `${periodoActual().t.toLowerCase()}, más de ${pct(umbralActual())}`;
    const diaMes = f => { const d = util.deISO(f); return d.getDate() + ' de ' + MESES[d.getMonth()]; };
    const textoRacha = r => (r.dias === 1 ? diaMes(r.desde) : `del ${diaMes(r.desde)} al ${diaMes(r.hasta)} (${r.dias} días)`);

    // Índice del buscador: zonas del modelo y concejos (con las zonas que los incluyen)
    const indice = zonas.map(z => {
      const cs = L.concejosDeZona(datos, z.zona_mitma_id).map(nombreC);
      return { tipo: 'zona', id: z.zona_mitma_id, nombre: z.nombre_zona,
        sub: 'Zona' + (cs.length ? ' · ' + (cs.length === 1 ? '1 concejo: ' : cs.length + ' concejos: ') + util.listaNatural(cs) : '') };
    });
    const ines = new Set(Object.keys(nombresIne));
    ((datos.mapeo && datos.mapeo.zonas) || []).forEach(z => z.concejos_ine.forEach(i => ines.add(i)));
    ines.forEach(ine => {
      const zs = L.zonasDeConcejo(datos, ine).filter(id => zonaPorId[id]);
      indice.push({ tipo: 'concejo', id: ine, nombre: nombreC(ine), zonas: zs,
        sub: zs.length ? 'Concejo · zona ' + util.listaNatural(zs.map(nombreZ)) : 'Concejo · sin previsión (fuera de las zonas del modelo)' });
    });

    let resultadoSat = [];
    function calcularSat() {
      const p = periodoActual();
      resultadoSat = L.previsionSaturacion(datos, { desde: p.desde, hasta: p.hasta, umbral: umbralActual() });
    }

    function htmlDia(d) {
      const cal = calendario[d.fecha] || {};
      const extra = [];
      if (d.p10 != null && d.p90 != null && d.normal) extra.push(`probable entre ${pct(d.p10 / d.normal)} y ${pct(d.p90 / d.normal)}`);
      if (cal.festivo) extra.push(cal.festivo);
      else if (cal.puente) extra.push('puente');
      if (d.lagos_regulado && lagos && d.zona_mitma_id === lagos.zona_mitma_id) extra.push('acceso a los Lagos regulado');
      if (d.lejana) extra.push('previsión solo de calendario');
      else if (d.incierto) extra.push('previsión incierta');
      return `<li class="sat-dia">
        <span class="sat-fecha"><span aria-hidden="true">${esc(util.fechaCorta(d.fecha))}</span><span class="sr">${esc(util.fechaLarga(d.fecha))}</span></span>
        <span>${pill(d.color)}</span>
        <span class="sat-val"><strong>${esc(util.delta(d.cociente))}</strong>${d.prediccion != null ? ` · unas ${num(d.prediccion)} llegadas` : ''}${extra.length ? `<span class="rg-pico"> · ${esc(extra.join(' · '))}</span>` : ''}</span>
      </li>`;
    }

    function htmlZonaDetalle(r, titulo, intro) {
      const p = periodoActual();
      const n = r.dias.length;
      const cab = `<div class="sat-cab"><h3>${esc(titulo)}</h3>${intro ? `<p class="g-desc">${esc(intro)}</p>` : ''}</div>`;
      if (!n) return `<div class="sat-bloque">${cab}<p class="g-resumen">No se espera ningún día con más de ${esc(pct(umbralActual()))} sobre un día normal ${esc(rangoTxt(p))}.</p></div>`;
      const m = (v, et) => `<div class="met"><span class="met-valor">${v}</span><span class="met-et">${et}</span></div>`;
      const meses = [];
      r.dias.forEach(d => {
        const k = d.fecha.slice(0, 7);
        if (!meses.length || meses[meses.length - 1].k !== k) meses.push({ k, dias: [] });
        meses[meses.length - 1].dias.push(d);
      });
      const largas = r.rachas.filter(x => x.dias > 1);
      return `<div class="sat-bloque">${cab}
        <p class="g-resumen">${n === 1 ? 'Se espera saturación 1 día' : `Se espera saturación ${n} días`} ${esc(rangoTxt(p))}.</p>
        <div class="metricas">
          ${m(num(n), n === 1 ? 'día con saturación prevista' : 'días con saturación prevista')}
          ${m(num(largas.length), largas.length === 1 ? 'racha de varios días seguidos' : 'rachas de varios días seguidos')}
          ${m(esc(pct(r.pico.cociente)), 'el día más cargado: ' + esc(util.fechaLarga(r.pico.fecha)))}
        </div>
        ${largas.length ? `<p class="g-nota"><strong>Días seguidos:</strong> ${esc(largas.slice(0, 8).map(textoRacha).join('; '))}${largas.length > 8 ? ` y ${largas.length - 8} más` : ''}.</p>` : ''}
        <div class="sat-meses">${meses.map(mm => {
          const d0 = util.deISO(mm.k + '-01');
          return `<section class="sat-mes" aria-label="${esc(MESES[d0.getMonth()] + ' de ' + d0.getFullYear())}">
            <h4>${esc(MESES[d0.getMonth()].charAt(0).toUpperCase() + MESES[d0.getMonth()].slice(1))} de ${d0.getFullYear()} <span class="sat-mes-n">· ${mm.dias.length} ${mm.dias.length === 1 ? 'día' : 'días'}</span></h4>
            <ul class="sat-dias">${mm.dias.map(htmlDia).join('')}</ul>
          </section>`;
        }).join('')}</div>
      </div>`;
    }

    function pintarDetalle() {
      const s = estado.sel, det = q('#sat-detalle');
      if (!s) { det.innerHTML = `<p class="pz-ayuda">Busca una zona o un concejo, o pulsa «Ver días» en la lista de zonas, para ver qué días se espera saturación.</p>`; return; }
      const porZona = id => resultadoSat.find(r => r.zona_mitma_id === id);
      let html;
      if (s.tipo === 'zona') {
        const cs = L.concejosDeZona(datos, s.id).map(nombreC);
        html = htmlZonaDetalle(porZona(s.id), s.nombre, cs.length ? 'Zona con ' + (cs.length === 1 ? 'el concejo ' : 'los concejos ') + util.listaNatural(cs) + '.' : '');
      } else if (!s.zonas.length) {
        html = `<div class="sat-bloque"><div class="sat-cab"><h3>${esc(s.nombre)}</h3></div><p class="pz-ayuda">Este concejo no está en ninguna zona del modelo, así que no hay previsión para él.</p></div>`;
      } else {
        html = s.zonas.map(id => htmlZonaDetalle(porZona(id), s.nombre,
          `Concejo de la zona ${nombreZ(id)}. Se muestra la previsión de toda la zona.`)).join('');
      }
      det.innerHTML = `<div class="sat-sel"><button type="button" class="btn-mini" id="sat-quitar">Quitar selección</button></div>` + html;
      q('#sat-quitar').addEventListener('click', () => { estado.sel = null; q('#sat-buscar').value = ''; pintarDetalle(); q('#sat-buscar').focus(); });
    }

    function pintarZonasSat() {
      const maxD = Math.max(1, ...resultadoSat.map(r => r.dias.length));
      q('#sat-zonas').innerHTML = resultadoSat.map(r => {
        const n = r.dias.length, prox = r.dias[0];
        return `<li class="rg">
          <span class="rg-zona">${esc(r.nombre_zona)}${r.es_principal ? ' · zona principal' : ''}</span>
          <span class="rg-barra" aria-hidden="true"><span class="rg-val v-estudiar" style="width:${(n / maxD * 100).toFixed(1)}%"></span></span>
          <span class="rg-num">${n} ${n === 1 ? 'día' : 'días'}</span>
          <span class="rg-ver"><button type="button" class="btn-mini" data-ver-zona="${esc(r.zona_mitma_id)}" aria-label="Ver los días de ${esc(r.nombre_zona)}">Ver días</button></span>
          <span class="rg-pico">${prox ? 'Primero: ' + esc(util.fechaLarga(prox.fecha)) : 'Ninguno en este periodo'}</span>
        </li>`;
      }).join('');
    }

    function pintarSaturacion() {
      const u = umbralActual();
      q('#umbral-valor').textContent = pct(u);
      q('#umbral').setAttribute('aria-valuetext', `Más de ${Math.round((u - 1) * 100)} por ciento sobre un día normal`);
      calcularSat();
      pintarDetalle();
      pintarZonasSat();
    }
    q('#umbral').addEventListener('input', pintarSaturacion);
    q('#sat-periodo').addEventListener('change', () => { estado.periodo = q('#sat-periodo').value; pintarSaturacion(); });
    q('#sat-zonas').addEventListener('click', e => {
      const b = e.target.closest('[data-ver-zona]');
      if (!b) return;
      elegirLugar(indice.find(x => x.tipo === 'zona' && x.id === b.dataset.verZona));
      q('#sat-detalle').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    // Buscador (combobox con lista)
    const entrada = q('#sat-buscar'), listaSat = q('#sat-lista');
    function cerrarLista() { listaSat.hidden = true; entrada.setAttribute('aria-expanded', 'false'); entrada.removeAttribute('aria-activedescendant'); estado.satActiva = -1; }
    function marcarActiva(i) {
      estado.satActiva = i;
      qa('#sat-lista [role="option"]').forEach((li, j) => li.setAttribute('aria-selected', String(j === i)));
      const li = q('#sat-op-' + i);
      if (li) { entrada.setAttribute('aria-activedescendant', li.id); li.scrollIntoView({ block: 'nearest' }); } else entrada.removeAttribute('aria-activedescendant');
    }
    function abrirLista() {
      estado.satOpciones = L.buscar(indice, entrada.value, 15);
      listaSat.innerHTML = estado.satOpciones.length
        ? estado.satOpciones.map((x, i) => `<li role="option" id="sat-op-${i}" aria-selected="false" data-i="${i}"><span>${esc(x.nombre)}</span><span class="op-zona">${esc(x.sub)}</span></li>`).join('')
        : '<li class="sin-res" role="option" aria-disabled="true">No hay ninguna zona ni concejo con ese nombre</li>';
      listaSat.hidden = false;
      entrada.setAttribute('aria-expanded', 'true');
      marcarActiva(-1);
      util.anunciar(estado.satOpciones.length ? `${estado.satOpciones.length} resultados` : 'Sin resultados');
    }
    function elegirLugar(x) {
      if (!x) return;
      estado.sel = x;
      entrada.value = x.nombre;
      cerrarLista();
      pintarDetalle();
      const n = x.tipo === 'zona' ? (resultadoSat.find(r => r.zona_mitma_id === x.id) || { dias: [] }).dias.length : null;
      util.anunciar(x.nombre + (n != null ? `: ${n} ${n === 1 ? 'día' : 'días'} con saturación prevista` : ''));
    }
    entrada.addEventListener('input', abrirLista);
    entrada.addEventListener('focus', () => { if (!entrada.value) abrirLista(); });
    entrada.addEventListener('keydown', e => {
      const n = estado.satOpciones.length;
      if (e.key === 'ArrowDown') { e.preventDefault(); if (listaSat.hidden) abrirLista(); else if (n) marcarActiva((estado.satActiva + 1) % n); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); if (n && !listaSat.hidden) marcarActiva((estado.satActiva - 1 + n) % n); }
      else if (e.key === 'Enter') {
        if (listaSat.hidden) return;
        e.preventDefault();
        elegirLugar(estado.satOpciones[estado.satActiva >= 0 ? estado.satActiva : 0]);
      } else if (e.key === 'Escape') { if (!listaSat.hidden) { e.preventDefault(); cerrarLista(); } }
    });
    listaSat.addEventListener('mousedown', e => e.preventDefault()); // que el input no pierda el foco antes del clic
    listaSat.addEventListener('click', e => {
      const li = e.target.closest('[data-i]');
      if (li) elegirLugar(estado.satOpciones[+li.dataset.i]);
    });
    entrada.addEventListener('blur', () => setTimeout(cerrarLista, 120));

    /* ---------- Lagos ---------- */
    (function pintarLagos() {
      const l = lagos;
      if (!l) return;
      q('#lagos-desc').textContent = `${l.nombre_zona}: cuántos días de alerta (alta o saturación, con los umbrales del semáforo) caen en días con acceso regulado a los Lagos y cuántos fuera.`;
      q('#lagos-tabla').innerHTML = `<table class="tabla"><caption class="sr">Días de alerta dentro y fuera de los días con acceso regulado</caption>
        <thead><tr><th scope="col">Año</th><th scope="col" class="num">Días regulados</th><th scope="col" class="num">Alertas en días regulados</th><th scope="col" class="num">Alertas fuera</th><th scope="col" class="num">Saturación en días regulados</th><th scope="col" class="num">Saturación fuera</th></tr></thead>
        <tbody>${l.anios.map(a => `<tr><th scope="row">${a.anio} <span class="rg-pico">${a.tipo === 'previsto' ? 'previsto' : 'observado'}${a.supuesta ? ', calendario supuesto' : ''}</span></th>
          <td class="num">${num(a.dias_regulados)}</td><td class="num">${num(a.alerta_en_regulados)}</td><td class="num">${num(a.alerta_fuera)}</td><td class="num">${num(a.rojos_en_regulados)}</td><td class="num">${num(a.rojos_fuera)}</td></tr>`).join('')}</tbody></table>`;
      const cal = l.calibracion;
      q('#lagos-nota').innerHTML = (cal ? `El umbral que mejor reproduce los días regulados en 2023 y 2024 es <strong>${esc(pct(cal.mejor_umbral))}</strong> sobre un día normal (precisión ${pc100(cal.precision)}, cobertura ${pc100(cal.recall)}). ` : '') +
        (l.nota ? esc(l.nota) + ' ' : '') + 'En 2027 aún no se ha publicado la regulación de los Lagos: se supone igual que 364 días antes.';
    })();

    /* ---------- Alertas: tabla dinámica (zona → concejos) ---------- */
    const fechasAl = Array.from(new Set(alertas.map(a => a.fecha))).sort();
    const alPorClave = new Map(alertas.map(a => [a.fecha + '|' + a.zona_mitma_id, a]));
    const claveC = c => c.ine + '|' + c.zona;
    const elegido = (ine, zona) => estado.concejos.some(c => c.ine === ine && c.zona === zona);

    function filaMatriz(etiqueta, zonaId) {
      return '<tr><th scope="row">' + etiqueta + '</th>' + fechasAl.map(f => {
        const a = alPorClave.get(f + '|' + zonaId), n = a ? a.color : 'gris';
        const t = NIVEL[n].nombre + (a && a.cociente != null ? ', ' + pct(a.cociente) : '');
        return `<td class="cel cel-${n}" title="${esc(t)}">${ICONO[n]}<span class="sr">${esc(t)}</span></td>`;
      }).join('') + '</tr>';
    }

    function pintarMatriz() {
      const filas = [];
      if (estado.todasZonas) zonas.forEach(z => filas.push(filaMatriz(`${esc(z.nombre_zona)}<span class="mz-zona">Zona completa</span>`, z.zona_mitma_id)));
      estado.concejos.forEach(c => filas.push(filaMatriz(`${esc(nombreC(c.ine))}<span class="mz-zona">${esc(nombreZ(c.zona))}</span>`, c.zona)));
      q('#al-vacia').hidden = filas.length > 0;
      q('#matriz-marco').hidden = !filas.length;
      if (!filas.length) { q('#matriz').innerHTML = ''; return; }
      const cabecera = '<thead><tr><th scope="col"><span class="sr">Zona o concejo</span></th>' + fechasAl.map(f => {
        const d = util.deISO(f), finde = d.getDay() === 0 || d.getDay() === 6;
        return `<th scope="col" class="${finde ? 'finde' : ''}" title="${esc(util.fechaLarga(f))}"><span aria-hidden="true">${LETRA[d.getDay()]}<br>${d.getDate()}</span><span class="sr">${esc(util.fechaLarga(f))}</span></th>`;
      }).join('') + '</tr></thead>';
      q('#matriz').innerHTML = `<caption class="sr">Nivel previsto para los próximos ${fechasAl.length} días</caption>` + cabecera + '<tbody>' + filas.join('') + '</tbody>';
    }

    function pintarChips() {
      const chips = estado.concejos.map(c => `<button type="button" class="al-chip" data-quitar="${esc(claveC(c))}" aria-label="Quitar ${esc(nombreC(c.ine))} de la tabla">${esc(nombreC(c.ine))} ${CERRAR}</button>`);
      if (estado.concejos.length > 1 || (estado.concejos.length && estado.todasZonas)) chips.push('<button type="button" class="btn-mini" id="al-quitar-todo">Vaciar la tabla</button>');
      q('#al-chips').innerHTML = chips.join('');
    }

    function concejosZonaSel() { return estado.alZona ? L.concejosDeZona(datos, estado.alZona) : []; }

    function pintarControlesConcejo() {
      const btn = q('#al-concejos-btn'), todos = q('#al-todos-concejos'), cs = concejosZonaSel();
      btn.disabled = !estado.alZona;
      todos.disabled = !cs.length;
      if (!estado.alZona) { btn.textContent = 'Elige primero una zona'; todos.setAttribute('aria-pressed', 'false'); return; }
      const n = cs.filter(i => elegido(i, estado.alZona)).length;
      btn.textContent = !cs.length ? 'Esta zona no tiene concejos' : n === 0 ? 'Elige uno o varios concejos' : n === cs.length ? `Todos (${n})` : `${n} de ${cs.length} concejos`;
      const all = cs.length > 0 && n === cs.length;
      todos.setAttribute('aria-pressed', String(all));
      todos.textContent = all ? 'Quitar todos los concejos' : 'Todos los concejos';
      q('#al-concejos-pop').innerHTML = cs.length ? `<fieldset class="multi-campo"><legend class="sr">Concejos de ${esc(nombreZ(estado.alZona))}</legend>${
        cs.map(i => `<label class="multi-op"><input type="checkbox" value="${esc(i)}"${elegido(i, estado.alZona) ? ' checked' : ''}><span>${esc(nombreC(i))}</span></label>`).join('')}</fieldset>` : '';
    }

    function actualizarAlertas() { pintarControlesConcejo(); pintarChips(); pintarMatriz(); }

    function cerrarPop(enfocar) {
      const pop = q('#al-concejos-pop');
      if (pop.hidden) return;
      pop.hidden = true;
      q('#al-concejos-btn').setAttribute('aria-expanded', 'false');
      if (enfocar) q('#al-concejos-btn').focus();
    }
    q('#al-zona').addEventListener('change', () => { estado.alZona = q('#al-zona').value; cerrarPop(); actualizarAlertas(); });
    q('#al-todas-zonas').addEventListener('click', () => {
      estado.todasZonas = !estado.todasZonas;
      q('#al-todas-zonas').setAttribute('aria-pressed', String(estado.todasZonas));
      actualizarAlertas();
      util.anunciar(estado.todasZonas ? 'Todas las zonas añadidas a la tabla' : 'Zonas quitadas de la tabla');
    });
    q('#al-concejos-btn').addEventListener('click', () => {
      const pop = q('#al-concejos-pop');
      if (!pop.hidden) { cerrarPop(); return; }
      pop.hidden = false;
      q('#al-concejos-btn').setAttribute('aria-expanded', 'true');
      const primero = pop.querySelector('input');
      if (primero) primero.focus();
    });
    q('#al-concejos-pop').addEventListener('change', e => {
      const cb = e.target.closest('input[type="checkbox"]');
      if (!cb) return;
      const ine = cb.value, zona = estado.alZona;
      if (cb.checked) { if (!elegido(ine, zona)) estado.concejos.push({ ine, zona }); }
      else estado.concejos = estado.concejos.filter(c => !(c.ine === ine && c.zona === zona));
      // Solo el botón, las fichas y la tabla: la lista sigue abierta y con el foco donde estaba
      const btn = q('#al-concejos-btn'), cs = concejosZonaSel(), n = cs.filter(i => elegido(i, zona)).length;
      btn.textContent = n === 0 ? 'Elige uno o varios concejos' : n === cs.length ? `Todos (${n})` : `${n} de ${cs.length} concejos`;
      const all = n === cs.length;
      q('#al-todos-concejos').setAttribute('aria-pressed', String(all));
      q('#al-todos-concejos').textContent = all ? 'Quitar todos los concejos' : 'Todos los concejos';
      pintarChips(); pintarMatriz();
      util.anunciar(`${nombreC(ine)} ${cb.checked ? 'añadido a' : 'quitado de'} la tabla`);
    });
    q('#al-concejos-pop').addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); cerrarPop(true); } });
    document.addEventListener('click', e => { if (!e.target.closest('.multi')) cerrarPop(); });
    q('#al-todos-concejos').addEventListener('click', () => {
      const cs = concejosZonaSel(), zona = estado.alZona;
      const all = cs.every(i => elegido(i, zona));
      if (all) estado.concejos = estado.concejos.filter(c => c.zona !== zona || cs.indexOf(c.ine) === -1);
      else cs.forEach(i => { if (!elegido(i, zona)) estado.concejos.push({ ine: i, zona }); });
      actualizarAlertas();
      util.anunciar(all ? 'Concejos de la zona quitados de la tabla' : `${cs.length} concejos añadidos a la tabla`);
    });
    q('#al-chips').addEventListener('click', e => {
      const b = e.target.closest('[data-quitar]');
      if (b) {
        const [ine, zona] = b.dataset.quitar.split('|');
        estado.concejos = estado.concejos.filter(c => !(c.ine === ine && c.zona === zona));
        actualizarAlertas();
        util.anunciar(nombreC(ine) + ' quitado de la tabla');
        const otro = q('#al-chips [data-quitar]') || q('#al-zona');
        otro.focus();
      } else if (e.target.closest('#al-quitar-todo')) {
        estado.concejos = []; estado.todasZonas = false;
        q('#al-todas-zonas').setAttribute('aria-pressed', 'false');
        actualizarAlertas();
        util.anunciar('Tabla vacía');
        q('#al-zona').focus();
      }
    });

    function pintarListaAlertas() {
      const todas = estado.filtro === 'todas';
      const lista = alertas.filter(a => a.color === 'rojo' || (todas && a.color === 'ambar'));
      if (!lista.length) {
        q('#alertas-lista').innerHTML = `<p class="pz-ayuda">No hay alertas de ${todas ? 'afluencia alta ni de saturación' : 'saturación'} en este periodo.</p>`;
        return;
      }
      const porDia = {};
      lista.forEach(a => { (porDia[a.fecha] = porDia[a.fecha] || []).push(a); });
      q('#alertas-lista').innerHTML = Object.keys(porDia).sort().map(f => `<div class="al-dia">
        <h3>${esc(util.fechaLarga(f))}</h3>
        <ul>${porDia[f].map(a => `<li class="al">
          <span>${pill(a.color)}</span>
          <div><p class="al-zona"><strong>${esc(a.nombre_zona)}</strong> · ${esc(util.delta(a.cociente))}${a.incierto ? ' · previsión incierta' : ''}${a.lagos_regulado ? ' · acceso a los Lagos regulado' : ''}</p>
          <p class="al-accion"><span class="al-etq">Acción sugerida:</span> ${esc(a.accion.texto)}</p></div>
        </li>`).join('')}</ul></div>`).join('');
    }
    qa('input[name="filtro-alerta"]').forEach(r => r.addEventListener('change', () => { estado.filtro = r.value; pintarListaAlertas(); }));

    /* ---------- Fiabilidad ---------- */
    function pintarFiabilidad() {
      const id = q('#fiab-zona').value;
      const f = L.fiabilidad(datos, id);
      const g = f.grupos;
      const corto = g.find(x => x.horizontes[0] === '1'), largo = g.find(x => x.horizontes[0] === '8+');
      const met = (x, tit) => x ? `<div class="met"><span class="met-valor">${pc100(x.acierto_color)}</span><span class="met-et">${esc(tit)}: días en que el semáforo acertó el color</span></div>` : '';
      q('#fiab-metricas').innerHTML = met(corto, 'A 1-3 días') + met(g.find(x => x.horizontes[0] === '4'), 'A 4-7 días') + met(largo, 'A 8 días o más');
      const rojos = largo && largo.rojos_obs ? `A 8 días o más detecta ${largo.rojos_detectados} de ${largo.rojos_obs} días de saturación reales.` : '';
      q('#fiab-nota').textContent = `${f.nombre_zona}. ${rojos}`.trim();
      q('#fiab-tabla').innerHTML = `<table class="tabla"><caption class="sr">Fiabilidad por días de antelación</caption>
        <thead><tr><th scope="col">Antelación</th><th scope="col">Qué significa</th></tr></thead>
        <tbody>${f.filas.map(x => `<tr><td>${x.horizonte_txt === '8+' ? '8 días o más' : x.horizonte_txt + (x.horizonte_txt === '1' ? ' día' : ' días')}</td><td>${esc(x.nota)}</td></tr>`).join('')}</tbody></table>`;
    }
    q('#fiab-zona').addEventListener('change', pintarFiabilidad);

    /* ---------- Perfil del visitante ---------- */
    function pintarPerfil() {
      const id = q('#perfil-zona').value, mes = +q('#perfil-mes').value;
      const p = datos.perfil.perfil.find(x => x.zona_mitma_id === id && x.mes === mes);
      if (!p) { q('#perfil-metricas').innerHTML = ''; q('#perfil-nota').textContent = 'Sin datos de perfil para esta zona y mes.'; return; }
      const m = (v, et) => `<div class="met"><span class="met-valor">${v}</span><span class="met-et">${et}</span></div>`;
      q('#perfil-metricas').innerHTML =
        m(Math.round(p.pct_desde_asturias) + NBSP + '%', 'Llegan desde Asturias') +
        m(Math.round(p.pct_resto_espana) + NBSP + '%', 'Llegan del resto de España') +
        m(Math.round(p.pct_excursionistas_aprox) + NBSP + '%', 'Vienen solo por el día (aprox.)');
      q('#perfil-nota').textContent = `${p.nombre_zona}, ${MESES[mes - 1]}: unas ${num(p.llegadas_ocio_media_dia)} llegadas de ocio al día (${p.dias} días de muestra); ${Math.round(p.pernoctaciones_por_100_llegadas)} pernoctaciones de no residentes por cada 100 llegadas. Sin visitantes extranjeros.`;
    }
    q('#perfil-zona').addEventListener('change', pintarPerfil);
    q('#perfil-mes').addEventListener('change', pintarPerfil);

    /* ---------- Exportar CSV ---------- */
    function exportar(tipo, boton) {
      let nombre, desc, csv;
      const sint = !!datos.sintetico;
      const u = umbralActual();
      if (tipo === 'saturacion') {
        const p = periodoActual();
        csv = L.csvSaturacion(resultadoSat, u, sint);
        nombre = `saturacion_prevista_${p.desde}_${p.hasta}.csv`;
        desc = `Días con más de ${pct(u)} sobre un día normal ${rangoTxt(p)}, por zona, con el rango probable y la acción sugerida.`;
      } else if (tipo === 'prevision') {
        csv = L.csvPrevision(alertas, sint);
        nombre = `prevision_${hoy}.csv`;
        desc = `Previsión de las ${zonas.length} zonas para los próximos ${C.diasAlertas} días, con el color, el rango probable y la acción sugerida.`;
      } else {
        csv = L.csvRegulacion(L.tablaRegulacion(datos, u), u, sint);
        nombre = `dias_sobre_umbral_${String(u).replace('.', '_')}.csv`;
        desc = `Días por año que cada zona supera ${pct(u)} sobre un día normal (en los años previstos, con el mínimo y el máximo probables).`;
      }
      estado.csv = { nombre, csv }; estado.csvOrigen = boton;
      q('#dlg-nombre').textContent = nombre;
      q('#dlg-desc').textContent = desc + (sint ? ' Datos sintéticos: no son reales.' : '');
      q('#dlg-texto').value = csv;
      q('#dlg-estado').textContent = '';
      const dlg = q('#dlg-csv');
      if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
      q('#dlg-copiar').focus();
    }
    qa('[data-exportar]').forEach(b => b.addEventListener('click', () => exportar(b.dataset.exportar, b)));
    const dlg = q('#dlg-csv');
    q('#dlg-cerrar').addEventListener('click', () => dlg.close());
    dlg.addEventListener('close', () => { if (estado.csvOrigen) estado.csvOrigen.focus(); });
    q('#dlg-copiar').addEventListener('click', () => {
      const ta = q('#dlg-texto'), est = q('#dlg-estado');
      const seleccionar = () => { ta.focus(); ta.select(); est.textContent = 'No se ha podido copiar automáticamente. El texto está seleccionado: cópialo con Ctrl+C.'; };
      try { navigator.clipboard.writeText(estado.csv.csv).then(() => { est.textContent = 'Copiado. Pégalo en una hoja de cálculo o en un archivo de texto.'; }).catch(seleccionar); } catch (e) { seleccionar(); }
    });
    q('#dlg-descargar').addEventListener('click', () => {
      const est = q('#dlg-estado');
      try {
        const url = URL.createObjectURL(new Blob(['﻿' + estado.csv.csv], { type: 'text/csv;charset=utf-8' }));
        const a = document.createElement('a');
        a.href = url; a.download = estado.csv.nombre;
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        est.textContent = 'Descarga iniciada.';
      } catch (e) { est.textContent = 'No se ha podido descargar. Usa «Copiar».'; }
    });

    pintarSaturacion();
    actualizarAlertas();
    pintarListaAlertas();
    pintarFiabilidad();
    pintarPerfil();
  }
})();
