/* ==========================================================================
 * PESTAÑA «Funciones avanzadas» (antes «Gestión») — PROPIEDAD DE LA PERSONA 2 (rama web-gestion)
 * --------------------------------------------------------------------------
 * interfaz/app.js llama a montar() la primera vez que se abre la pestaña, y a
 * mostrar() cada vez que se vuelve a ella.
 *
 *   contenedor  <section id="panel-gestion"> (vacío)
 *   datos       objeto de window.DatosModelo.cargar() (ver notas/coordinacion_web.md)
 *   util        window.UtilWeb (pill, num, pct, esc, anunciar…)
 *
 * Aspecto: marcado y clases del piloto (estilos/estilos.css). Los números salen
 * de GestionLogica (pestanas/gestion/logica.js) y esta, de las salidas del modelo.
 * Textos editables de acciones y criterios: pestanas/gestion/config-gestion.js.
 * ========================================================================== */
window.Pestanas = window.Pestanas || {};
(function () {
  'use strict';

  const SCRIPTS = ['pestanas/gestion/config-gestion.js', 'pestanas/gestion/logica.js'];
  const LETRA = ['D', 'L', 'M', 'X', 'J', 'V', 'S'];
  const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

  function cargarScripts(lista) {
    return lista.reduce((p, src) => p.then(() => new Promise((ok, ko) => {
      if (document.querySelector('script[data-g="' + src + '"]')) return ok();
      const s = document.createElement('script');
      s.src = src; s.dataset.g = src;
      s.onload = ok; s.onerror = () => ko(new Error('No se ha podido cargar ' + src));
      document.head.appendChild(s);
    })), Promise.resolve());
  }

  window.Pestanas.gestion = {
    montar(contenedor, datos, util) {
      return cargarScripts(SCRIPTS).then(() => pintar(contenedor, datos, util)).catch(err => {
        console.error(err);
        contenedor.innerHTML = '<div class="tarjeta"><p><strong>No se ha podido montar la pestaña Funciones avanzadas.</strong></p><p class="error-datos">' + util.esc(err.message) + '</p></div>';
      });
    },
    mostrar() {},
  };

  function pintar(cont, datos, util) {
    const L = window.GestionLogica, C = window.GestionConfig;
    const { esc, num, pct, pill, NBSP, ICONO, NIVEL } = util;
    const pc100 = x => (x == null ? '—' : Math.round(x * 100) + NBSP + '%');
    const zonas = L.zonas(datos);
    const principal = zonas[0];
    const umbrales = L.umbralesDisponibles(datos);
    const umb = datos.regulacion.umbrales || datos.predicciones.umbrales;
    const porZona = L.hayUmbralesPorZona(datos);
    const estado = { umbralIdx: Math.max(0, umbrales.indexOf(umb.rojo)), modoU: porZona ? 'zona' : 'manual', sel: null, filtro: 'rojo', csv: null, csvOrigen: null,
      al: { modo: 'comarcas', comarca: null, elegidos: new Set() } };
    const opcionesZona = zonas.map(z => `<option value="${esc(z.zona_mitma_id)}">${esc(z.nombre_zona)}</option>`).join('');
    const alertas = L.alertasProximas(datos);
    const mesHoy = +datos.predicciones.fecha_hoy.slice(5, 7);
    const prev = L.prevision(datos);
    const desdeP = prev.length ? prev[0].fecha : null, hastaP = prev.length ? prev[prev.length - 1].fecha : null;
    const concejos = L.concejos(datos);
    const comarcas = L.comarcas(datos);
    estado.al.comarca = comarcas.indexOf('Oriente') !== -1 ? 'Oriente' : comarcas[0];
    const concejoPorIne = {};
    concejos.forEach(c => { concejoPorIne[c.ine] = c; });
    const concejosDeZona = id => concejos.filter(c => c.zona_mitma_id === id);
    const zonasDeComarca = nombre => Array.from(new Set(concejos.filter(c => c.comarca === nombre && c.zona_mitma_id).map(c => c.zona_mitma_id)));
    const periodo = desdeP ? `del ${util.fechaLarga(desdeP).toLowerCase()} al ${util.fechaLarga(hastaP).toLowerCase()}` : '';

    cont.innerHTML = `
    <div class="g-intro">
      <h1 class="titulo-pagina">Funciones avanzadas</h1>
      <p class="g-lead">Herramientas para ayuntamientos, el Principado y el Parque Nacional: qué días se espera saturación, qué viene en las próximas semanas y cuánto podemos fiarnos del modelo.</p>
      <nav aria-label="Apartados de funciones avanzadas" class="g-indice">
        <button type="button" class="chip-btn" data-panel="g-saturacion" aria-controls="g-saturacion">Previsión de saturación</button>
        <button type="button" class="chip-btn" data-panel="g-lagos" aria-controls="g-lagos">Regulación actual</button>
        <button type="button" class="chip-btn" data-panel="g-alertas" aria-controls="g-alertas">Alertas</button>
        <button type="button" class="chip-btn" data-panel="g-fiabilidad" aria-controls="g-fiabilidad">Fiabilidad</button>
        <button type="button" class="chip-btn" data-panel="g-perfil" aria-controls="g-perfil">Perfil del visitante</button>
        <button type="button" class="chip-btn" data-panel="g-exportar" aria-controls="g-exportar">Exportar datos</button>
      </nav>
    </div>

    <section class="tarjeta g-sec" id="g-saturacion" aria-labelledby="g-saturacion-t">
      <h2 id="g-saturacion-t">Previsión de saturación</h2>
      <p class="g-desc">Días de los próximos 12 meses (${esc(periodo)}) en los que el modelo prevé más visitantes que el umbral que elijas, comparados con un día normal. Busca un concejo o una comarca para ver qué días son.</p>
      <div class="g-dos">
        <div class="buscador">
          <label for="sat-buscar" class="filtro-et">Buscar un concejo o una comarca</label>
          <div class="buscador-caja">
            <svg class="ico lupa" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="4.8" class="ico-trazo"/><path d="M10.6 10.6 14 14" class="ico-trazo"/></svg>
            <input id="sat-buscar" type="text" role="combobox" autocomplete="off" spellcheck="false" aria-autocomplete="list" aria-expanded="false" aria-controls="sat-lista" placeholder="Llanes, Cabrales, Oriente…">
            <ul id="sat-lista" role="listbox" aria-label="Concejos y comarcas encontrados" hidden></ul>
          </div>
          <button type="button" class="btn-mini" id="sat-todas" hidden>Ver todas las zonas</button>
        </div>
        <div class="umbral">
          ${porZona ? `<fieldset class="segmentado" style="margin-bottom:.7rem"><legend class="filtro-et">Umbral</legend><div class="seg-opciones"><label><input type="radio" name="sat-modo" value="zona" checked><span>El de saturación de cada zona</span></label><label><input type="radio" name="sat-modo" value="manual"><span>Elegir un umbral</span></label></div></fieldset>` : ''}
          <label for="umbral" class="umbral-et">Contar los días con más de <strong id="umbral-valor"></strong> de visitantes sobre un día normal</label>
          <input type="range" id="umbral" min="0" max="${umbrales.length - 1}" step="1" value="${estado.umbralIdx}">
          <div class="umbral-escala" aria-hidden="true"><span>${esc(pct(umbrales[0]))}</span><span>${esc(pct(umbrales[umbrales.length - 1]))}</span></div>
        </div>
      </div>
      <p class="g-resumen" id="sat-resumen" aria-live="polite"></p>
      <ul class="rg-lista" id="reg-lista"></ul>
      <div id="sat-dias" class="al-lista"></div>
      <p class="g-nota">Previsión del modelo, no datos medidos: a 1-7 días, el de corto plazo (con el tiempo a 1-3 días); después, el de largo plazo (calendario y eventos). Entre paréntesis, el intervalo probable: días que superan el umbral incluso en el escenario bajo y en el alto. Criterio orientativo del equipo, no un dato oficial: <strong>${C.criterio.estudiar} días o más</strong>, estudiar regulación; <strong>entre ${C.criterio.vigilar} y ${C.criterio.estudiar - 1}</strong>, vigilar. ${porZona ? 'Cada zona tiene sus umbrales de alta y saturación, calculados con su propia historia (ver «Sobre los datos»).' : `Los umbrales del semáforo son ${esc(pct(umb.ambar))} (alta) y ${esc(pct(umb.rojo))} (saturación).`} Cada concejo usa la previsión de su zona del modelo (zonas del MITMA, algunas con varios concejos).</p>
    </section>

    <section class="tarjeta g-sec" id="g-lagos" aria-labelledby="g-lagos-t">
      <h2 id="g-lagos-t">Comparación con el acceso regulado a los Lagos</h2>
      <p class="g-desc" id="lagos-desc"></p>
      <div class="tabla-marco" id="lagos-tabla"></div>
      <p class="g-nota" id="lagos-nota"></p>
    </section>

    <section class="tarjeta g-sec" id="g-alertas" aria-labelledby="g-alertas-t">
      <h2 id="g-alertas-t">Alertas de las próximas ${Math.round(C.diasAlertas / 7)} semanas</h2>
      <p class="g-desc">Nivel previsto por día. Elige una comarca y añade sus concejos a la tabla, o mira todas las comarcas a la vez (cada comarca muestra el peor nivel de sus concejos). A 1-3 días la previsión incluye el tiempo; a partir de 8 días usa solo calendario y eventos y es más incierta. Comarcas: las 8 del Decreto 11/1991 del Principado de Asturias.</p>
      <div class="g-dos">
        <div>
          <label for="al-comarca" class="filtro-et">Comarca</label>
          <select id="al-comarca" class="select">${comarcas.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('')}</select>
        </div>
        <div>
          <p class="filtro-et" id="al-concejos-et">Concejos</p>
          <details class="g-multi" id="al-concejos">
            <summary class="select" aria-describedby="al-concejos-et"><span id="al-concejos-txt"></span></summary>
            <div class="g-multi-panel">
              <button type="button" class="btn-mini" id="al-todos-comarca"></button>
              <div class="g-multi-ops" id="al-concejos-ops" role="group" aria-labelledby="al-concejos-et"></div>
            </div>
          </details>
        </div>
      </div>
      <div class="exp-botones">
        <button type="button" class="btn" id="al-todas">Ver todas las comarcas</button>
        <button type="button" class="btn btn-sec" id="al-quitar">Quitar los concejos</button>
      </div>
      <div class="tabla-marco"><table class="matriz" id="matriz"></table></div>
      <fieldset class="segmentado g-filtro">
        <legend class="filtro-et">Mostrar</legend>
        <div class="seg-opciones">
          <label><input type="radio" name="filtro-alerta" value="rojo" checked><span>Solo saturación</span></label>
          <label><input type="radio" name="filtro-alerta" value="todas"><span>Alta y saturación</span></label>
        </div>
      </fieldset>
      <div id="alertas-lista" class="al-lista"></div>
    </section>

    <section class="tarjeta g-sec" id="g-fiabilidad" aria-labelledby="g-fiabilidad-t">
      <h2 id="g-fiabilidad-t">Fiabilidad del modelo</h2>
      <p class="g-desc">Cuánto acierta el modelo en días que no ha visto al entrenar, según con cuánta antelación se hace la previsión.</p>
      <label for="fiab-zona" class="filtro-et">Zona</label>
      <select id="fiab-zona" class="select">${opcionesZona}</select>
      <div class="metricas" id="fiab-metricas"></div>
      <p class="g-nota" id="fiab-nota"></p>
      <details class="detalles"><summary>Ver el detalle por días de antelación</summary><div class="tabla-marco" id="fiab-tabla"></div></details>
    </section>

    <section class="tarjeta g-sec" id="g-perfil" aria-labelledby="g-perfil-t">
      <h2 id="g-perfil-t">Perfil del visitante</h2>
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

    <section class="tarjeta g-sec" id="g-exportar" aria-labelledby="g-exportar-t">
      <h2 id="g-exportar-t">Exportar datos</h2>
      <p class="g-desc">Tablas en CSV (separadas por punto y coma, decimales con coma) para abrir en Excel o LibreOffice.</p>
      <div class="exp-botones">
        <button type="button" class="btn" data-exportar="prevision">Previsión de las próximas semanas (alertas)</button>
        <button type="button" class="btn" data-exportar="umbral">Días previstos sobre el umbral</button>
      </div>
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

    /* ---------- Previsión de saturación ---------- */
    const VER = { estudiar: { t: 'Estudiar regulación', n: 'rojo' }, vigilar: { t: 'Vigilar', n: 'ambar' }, ok: { t: 'Sin presión', n: 'verde' } };
    const umbralActual = () => umbrales[+q('#umbral').value];
    const umbralUso = () => (estado.modoU === 'zona' ? (id => L.umbralesZona(datos, id).rojo) : umbralActual());
    // «más de +100 %» o «su umbral de saturación (+188 %)»
    const txtU = id => (estado.modoU === 'zona' ? `su umbral de saturación (${pct(L.umbralesZona(datos, id).rojo)})` : `más de ${pct(umbralActual())}`);
    const veredicto = d => (d >= C.criterio.estudiar ? 'estudiar' : d >= C.criterio.vigilar ? 'vigilar' : 'ok');
    const diasTxt = n => n + NBSP + (n === 1 ? 'día' : 'días');
    const idsSeleccion = () => {
      const s = estado.sel;
      if (!s) return zonas.map(z => z.zona_mitma_id);
      if (s.tipo === 'concejo') return concejoPorIne[s.id] && concejoPorIne[s.id].zona_mitma_id ? [concejoPorIne[s.id].zona_mitma_id] : [];
      return zonasDeComarca(s.id);
    };
    const filasSaturacion = u => L.saturacionPrevista(prev, idsSeleccion(), u)
      .sort((a, b) => b.dias.length - a.dias.length || L.nombreZona(datos, a.zona_mitma_id).localeCompare(L.nombreZona(datos, b.zona_mitma_id), 'es'));

    function pintarRegulacion() {
      const um = umbralActual(), u = umbralUso(), zonaM = estado.modoU === 'zona';
      q('#umbral-valor').textContent = pct(um);
      q('#umbral').setAttribute('aria-valuetext', `Más de ${Math.round((um - 1) * 100)} por ciento sobre un día normal`);
      q('#umbral').disabled = zonaM;
      q('.umbral-et').style.opacity = zonaM ? '.55' : '';
      const filas = filasSaturacion(u);
      const s = estado.sel;
      const maxD = Math.max(40, ...filas.map(f => f.max));
      // Resumen
      if (!s) {
        const con = filas.filter(f => f.dias.length);
        const est = filas.filter(f => veredicto(f.dias.length) === 'estudiar').map(f => L.nombreZona(datos, f.zona_mitma_id));
        q('#sat-resumen').textContent = `${zonaM ? 'Con el umbral de saturación de cada zona' : 'Con este umbral'}, ${con.length} de ${filas.length} zonas tienen algún día por encima en los próximos 12 meses`
          + (est.length ? `; en ${est.length === 1 ? 'una' : est.length} se superan ${C.criterio.estudiar} días: ${est.join(', ')}.` : '.')
          + ' Busca un concejo o una comarca para ver qué días son.';
      } else if (s.tipo === 'concejo') {
        const c = concejoPorIne[s.id], f = filas[0];
        const otros = c && c.zona_mitma_id ? concejosDeZona(c.zona_mitma_id).filter(x => x.ine !== c.ine).map(x => x.nombre) : [];
        q('#sat-resumen').textContent = !f ? `${s.nombre}: sin previsión.`
          : `${s.nombre} (comarca de ${c.comarca}): ${diasTxt(f.dias.length)} por encima de ${txtU(f.zona_mitma_id)} en los próximos 12 meses (entre ${f.min} y ${f.max} según el rango probable).`
            + (otros.length ? ` Las cifras son de su zona del modelo, «${L.nombreZona(datos, c.zona_mitma_id)}», que también incluye ${otros.join(', ')}.` : '');
      } else {
        const fechas = new Set();
        filas.forEach(f => f.dias.forEach(p => fechas.add(p.fecha)));
        const nC = concejos.filter(c => c.comarca === s.id).length;
        q('#sat-resumen').textContent = `Comarca de ${s.id} (${nC} concejos, ${filas.length} ${filas.length === 1 ? 'zona' : 'zonas'} del modelo): ${diasTxt(fechas.size)} en los próximos 12 meses con al menos una zona por encima de ${zonaM ? 'su umbral de saturación' : pct(um)}.`;
      }
      // Barras por zona
      q('#reg-lista').innerHTML = filas.map(f => {
        const n = f.dias.length, v = VER[veredicto(n)], z = zonas.find(x => x.zona_mitma_id === f.zona_mitma_id);
        return `<li class="rg">
          <span class="rg-zona">${esc(L.nombreZona(datos, f.zona_mitma_id))}${z && z.es_principal ? ' · zona principal' : ''}</span>
          <span class="rg-barra" aria-hidden="true"><span class="rg-val v-${veredicto(n)}" style="width:${(n / maxD * 100).toFixed(1)}%"></span>
            <span class="rg-ref" style="left:${(C.criterio.vigilar / maxD * 100).toFixed(1)}%"></span><span class="rg-ref" style="left:${(C.criterio.estudiar / maxD * 100).toFixed(1)}%"></span></span>
          <span class="rg-num">${diasTxt(n)}</span>
          <span class="rg-ver"><span class="pill pill-${v.n}">${ICONO[v.n]}<span>${v.t}</span></span></span>
          <span class="rg-pico">(${f.min}–${f.max})</span>
        </li>`;
      }).join('');
      // Detalle de los días (solo al buscar)
      if (!s) { q('#sat-dias').innerHTML = ''; return; }
      const porFecha = {};
      filas.forEach(f => f.dias.forEach(p => { (porFecha[p.fecha] = porFecha[p.fecha] || []).push(p); }));
      const fechas = Object.keys(porFecha).sort();
      if (!fechas.length) { q('#sat-dias').innerHTML = `<p class="pz-ayuda">Ningún día previsto por encima de ${esc(zonaM ? 'su umbral de saturación' : pct(um))} en los próximos 12 meses.</p>`; return; }
      const porMes = {};
      fechas.forEach(f => { (porMes[f.slice(0, 7)] = porMes[f.slice(0, 7)] || []).push(f); });
      const varias = filas.length > 1;
      q('#sat-dias').innerHTML = Object.keys(porMes).map(m => {
        const d0 = util.deISO(porMes[m][0]);
        return `<div class="al-dia">
          <h3>${esc(MESES[d0.getMonth()].charAt(0).toUpperCase() + MESES[d0.getMonth()].slice(1))} de ${d0.getFullYear()} · ${diasTxt(porMes[m].length)}</h3>
          <ul>${porMes[m].map(f => {
            const ps = porFecha[f].sort((a, b) => b.cociente - a.cociente), peor = ps[0];
            const quien = varias ? ps.map(p => `${esc(L.nombreZona(datos, p.zona_mitma_id))} ${esc(pct(p.cociente))}`).join(', ') : esc(util.delta(peor.cociente)) + (peor.incierto ? ' · previsión incierta' : '');
            return `<li class="al"><span>${pill(peor.color)}</span><div><p class="al-zona"><strong>${esc(util.fechaLarga(f))}</strong> · ${quien}</p></div></li>`;
          }).join('')}</ul></div>`;
      }).join('');
    }
    q('#umbral').addEventListener('input', pintarRegulacion);
    qa('input[name="sat-modo"]').forEach(r => r.addEventListener('change', () => { estado.modoU = r.value; pintarRegulacion(); }));

    // Buscador de concejos y comarcas
    const normT = t => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
    const opcionesSat = comarcas.map(c => ({ tipo: 'comarca', id: c, nombre: 'Comarca de ' + c, sub: concejos.filter(x => x.comarca === c).length + ' concejos', clave: normT(c + ' comarca') }))
      .concat(concejos.map(c => ({ tipo: 'concejo', id: c.ine, nombre: c.nombre, sub: 'Concejo · comarca de ' + c.comarca, clave: normT(c.nombre) })));
    const inp = q('#sat-buscar'), lst = q('#sat-lista');
    let encontrados = [], activo = -1;
    function cerrarLista() { lst.hidden = true; inp.setAttribute('aria-expanded', 'false'); inp.removeAttribute('aria-activedescendant'); activo = -1; }
    function pintarLista() {
      const t = normT(inp.value);
      encontrados = t ? opcionesSat.filter(o => o.clave.includes(t)).slice(0, 12) : opcionesSat.slice(0, comarcas.length);
      lst.innerHTML = encontrados.length
        ? encontrados.map((o, i) => `<li role="option" id="sat-op-${i}" data-i="${i}" aria-selected="${i === activo}"><span>${esc(o.nombre)}</span><span class="op-zona">${esc(o.sub)}</span></li>`).join('')
        : '<li class="sin-res">Ningún concejo ni comarca con ese nombre.</li>';
      lst.hidden = false; inp.setAttribute('aria-expanded', 'true');
      if (activo >= 0) inp.setAttribute('aria-activedescendant', 'sat-op-' + activo); else inp.removeAttribute('aria-activedescendant');
    }
    function elegir(o) {
      estado.sel = { tipo: o.tipo, id: o.id, nombre: o.nombre };
      inp.value = o.nombre; cerrarLista();
      q('#sat-todas').hidden = false;
      pintarRegulacion();
      util.anunciar(q('#sat-resumen').textContent);
    }
    inp.addEventListener('input', () => { activo = -1; pintarLista(); });
    inp.addEventListener('focus', pintarLista);
    inp.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (lst.hidden) pintarLista();
        if (!encontrados.length) return;
        activo = (activo + (e.key === 'ArrowDown' ? 1 : -1) + encontrados.length) % encontrados.length;
        pintarLista();
      } else if (e.key === 'Enter') {
        if (encontrados.length) { e.preventDefault(); elegir(encontrados[Math.max(activo, 0)]); }
      } else if (e.key === 'Escape') cerrarLista();
    });
    lst.addEventListener('mousedown', e => { const li = e.target.closest('[data-i]'); if (li) { e.preventDefault(); elegir(encontrados[+li.dataset.i]); } });
    inp.addEventListener('blur', () => setTimeout(cerrarLista, 100));
    q('#sat-todas').addEventListener('click', () => { estado.sel = null; inp.value = ''; q('#sat-todas').hidden = true; pintarRegulacion(); inp.focus(); });

    /* ---------- Lagos ---------- */
    (function pintarLagos() {
      const l = L.compararLagos(datos);
      if (!l) { q('#g-lagos').hidden = true; return; }
      q('#lagos-desc').textContent = `${l.nombre_zona}: cuántos días de alerta (alta o saturación, con los umbrales del semáforo) caen en días con acceso regulado a los Lagos y cuántos fuera.`;
      q('#lagos-tabla').innerHTML = `<table class="tabla"><caption class="sr">Días de alerta dentro y fuera de los días con acceso regulado</caption>
        <thead><tr><th scope="col">Año</th><th scope="col" class="num">Días regulados</th><th scope="col" class="num">Alertas en días regulados</th><th scope="col" class="num">Alertas fuera</th><th scope="col" class="num">Saturación en días regulados</th><th scope="col" class="num">Saturación fuera</th></tr></thead>
        <tbody>${l.anios.map(a => `<tr><th scope="row">${a.anio} <span class="rg-pico">${a.tipo === 'previsto' ? 'previsto' : 'observado'}${a.supuesta ? ', calendario supuesto' : ''}</span></th>
          <td class="num">${num(a.dias_regulados)}</td><td class="num">${num(a.alerta_en_regulados)}</td><td class="num">${num(a.alerta_fuera)}</td><td class="num">${num(a.rojos_en_regulados)}</td><td class="num">${num(a.rojos_fuera)}</td></tr>`).join('')}</tbody></table>`;
      const cal = l.calibracion;
      q('#lagos-nota').innerHTML = (cal ? `El umbral que mejor reproduce los días regulados en 2023 y 2024 es <strong>${esc(pct(cal.mejor_umbral))}</strong> sobre un día normal (precisión ${pc100(cal.precision)}, cobertura ${pc100(cal.recall)}). ` : '') +
        (l.nota ? esc(l.nota) + ' ' : '') + 'En 2027 aún no se ha publicado la regulación de los Lagos: se supone igual que 364 días antes.';
    })();

    /* ---------- Alertas: tabla dinámica por comarca y concejos ---------- */
    const ORDEN = { gris: 0, verde: 1, ambar: 2, rojo: 3 };
    const fechasAl = Array.from(new Set(alertas.map(a => a.fecha))).sort();
    const alPorClave = new Map(alertas.map(a => [a.fecha + '|' + a.zona_mitma_id, a]));
    const celda = (n, t) => `<td class="cel cel-${n}" title="${esc(t)}">${ICONO[n]}<span class="sr">${esc(t)}</span></td>`;

    function pintarMatriz() {
      const al = estado.al;
      const cabecera = '<thead><tr><th scope="col"><span class="sr">' + (al.modo === 'comarcas' ? 'Comarca' : 'Concejo') + '</span></th>' + fechasAl.map(f => {
        const d = util.deISO(f), finde = d.getDay() === 0 || d.getDay() === 6;
        return `<th scope="col" class="${finde ? 'finde' : ''}" title="${esc(util.fechaLarga(f))}"><span aria-hidden="true">${LETRA[d.getDay()]}<br>${d.getDate()}</span><span class="sr">${esc(util.fechaLarga(f))}</span></th>`;
      }).join('') + '</tr></thead>';
      let filas;
      if (al.modo === 'comarcas') {
        filas = comarcas.map(cm => {
          const ids = zonasDeComarca(cm);
          return '<tr><th scope="row">' + esc(cm) + '</th>' + fechasAl.map(f => {
            const as = ids.map(id => alPorClave.get(f + '|' + id)).filter(Boolean);
            const peor = as.reduce((x, a) => (ORDEN[a.color] > ORDEN[x] ? a.color : x), 'gris');
            const en = as.filter(a => a.color === peor).map(a => a.nombre_zona);
            const t = `${cm}, ${util.fechaLarga(f).toLowerCase()}: ${NIVEL[peor].nombre}` + (peor === 'ambar' || peor === 'rojo' ? ` en ${en.join(', ')}` : '');
            return celda(peor, t);
          }).join('') + '</tr>';
        });
      } else {
        const elegidos = Array.from(al.elegidos).map(i => concejoPorIne[i]).filter(Boolean)
          .sort((a, b) => a.comarca.localeCompare(b.comarca, 'es') || a.nombre.localeCompare(b.nombre, 'es'));
        filas = elegidos.map(c => {
          const zn = c.zona_mitma_id ? L.nombreZona(datos, c.zona_mitma_id) : null;
          const varios = c.zona_mitma_id && concejosDeZona(c.zona_mitma_id).length > 1;
          return `<tr><th scope="row">${esc(c.nombre)}${varios ? ` <span class="rg-pico">(zona ${esc(zn)})</span>` : ''}</th>` + fechasAl.map(f => {
            const a = c.zona_mitma_id && alPorClave.get(f + '|' + c.zona_mitma_id), n = a ? a.color : 'gris';
            return celda(n, `${c.nombre}, ${util.fechaLarga(f).toLowerCase()}: ${NIVEL[n].nombre}` + (a && a.cociente != null ? ', ' + pct(a.cociente) : ''));
          }).join('') + '</tr>';
        });
      }
      q('#matriz').innerHTML = filas.length
        ? `<caption class="sr">Nivel previsto por ${al.modo === 'comarcas' ? 'comarca' : 'concejo'} para los próximos ${fechasAl.length} días</caption>` + cabecera + '<tbody>' + filas.join('') + '</tbody>'
        : '<caption class="pz-ayuda">Elige una comarca y marca sus concejos para añadirlos a la tabla, o pulsa «Ver todas las comarcas».</caption>';
      q('#al-todas').setAttribute('aria-pressed', String(al.modo === 'comarcas'));
      q('#al-quitar').hidden = al.modo === 'comarcas' || !al.elegidos.size;
    }

    function pintarConcejosComarca() {
      const al = estado.al, lista = concejos.filter(c => c.comarca === al.comarca);
      const marcados = lista.filter(c => al.elegidos.has(c.ine)).length;
      q('#al-concejos-txt').textContent = marcados ? `${marcados} de ${lista.length} concejos de ${al.comarca} en la tabla` : `Elegir concejos de ${al.comarca} (${lista.length})`;
      q('#al-todos-comarca').textContent = marcados === lista.length ? `Quitar todos los de ${al.comarca}` : `Todos los concejos de ${al.comarca}`;
      q('#al-concejos-ops').innerHTML = lista.map(c => `<button type="button" class="chip-btn" data-ine="${esc(c.ine)}" aria-pressed="${al.elegidos.has(c.ine)}">${esc(c.nombre)}</button>`).join('');
    }
    const cambiarConcejos = (ines, poner) => {
      const al = estado.al;
      ines.forEach(i => (poner ? al.elegidos.add(i) : al.elegidos.delete(i)));
      al.modo = 'concejos';
      pintarConcejosComarca(); pintarMatriz();
    };
    q('#al-comarca').value = estado.al.comarca;
    q('#al-comarca').addEventListener('change', e => { estado.al.comarca = e.target.value; pintarConcejosComarca(); q('#al-concejos').open = true; });
    q('#al-concejos-ops').addEventListener('click', e => {
      const b = e.target.closest('[data-ine]');
      if (b) cambiarConcejos([b.dataset.ine], !estado.al.elegidos.has(b.dataset.ine));
    });
    q('#al-todos-comarca').addEventListener('click', () => {
      const ines = concejos.filter(c => c.comarca === estado.al.comarca).map(c => c.ine);
      cambiarConcejos(ines, !ines.every(i => estado.al.elegidos.has(i)));
    });
    q('#al-todas').addEventListener('click', () => { estado.al.modo = 'comarcas'; q('#al-concejos').open = false; pintarMatriz(); });
    q('#al-quitar').addEventListener('click', () => { estado.al.elegidos.clear(); pintarConcejosComarca(); pintarMatriz(); });
    document.addEventListener('click', e => { const d = q('#al-concejos'); if (d && d.open && !d.contains(e.target)) d.open = false; });

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
      pintarHoras(id, mes);
    }
    // Patrón horario: hora con más llegadas de ocio (data/clean/llegadas_por_hora.parquet vía datos.horas)
    function pintarHoras(id, mes) {
      if (!datos.horas) return; // sin datos: queda el texto «Pendiente de datos»
      const tipos = [['laborable', 'los laborables'], ['fin_de_semana_o_festivo', 'los fines de semana y festivos']];
      const partes = tipos.map(([t, et]) => {
        const f = datos.horas.filas.filter(x => x.zona_mitma_id === id && x.mes === mes && x.tipo_dia === t);
        if (!f.length) return null;
        const pico = f.reduce((a, b) => (b.llegadas_ocio_media > a.llegadas_ocio_media ? b : a));
        return `${et}, de ${pico.hora} a ${pico.hora + 1} h (unas ${num(pico.llegadas_ocio_media)} llegadas de ocio en esa hora; ${pico.n_dias} días de muestra)`;
      }).filter(Boolean);
      q('#perfil-horas').textContent = partes.length
        ? `Hora con más llegadas, media de ${MESES[mes - 1]}: ${partes.join('; ')}. Hora local; festivos de Asturias, sin los locales.`
        : 'Sin datos de llegadas por hora para esta zona y mes.';
    }
    q('#perfil-zona').addEventListener('change', pintarPerfil);
    q('#perfil-mes').addEventListener('change', pintarPerfil);

    /* ---------- Exportar CSV ---------- */
    function exportar(tipo, boton) {
      let nombre, desc, csv;
      const sint = !!datos.sintetico;
      if (tipo === 'prevision') {
        csv = L.csvPrevision(alertas, sint);
        nombre = `prevision_${datos.predicciones.fecha_hoy}.csv`;
        desc = `Previsión de las ${zonas.length} zonas para los próximos ${C.diasAlertas} días, con el color, el rango probable y la acción sugerida.`;
      } else {
        const u = umbralUso(), s = estado.sel, zonaM = estado.modoU === 'zona';
        csv = L.csvSaturacion(datos, filasSaturacion(u), u, sint);
        nombre = `dias_previstos_${zonaM ? 'saturacion' : 'sobre_' + String(umbralActual()).replace('.', '_')}${s ? '_' + s.nombre.replace(/\s+/g, '_') : ''}.csv`;
        desc = `Días de los próximos 12 meses en los que el modelo prevé ${zonaM ? 'saturación (el umbral de cada zona)' : 'más de ' + pct(umbralActual()) + ' sobre un día normal'}, ${s ? 'en ' + s.nombre : 'en todas las zonas'} (lo que muestra «Previsión de saturación»), con el rango probable.`;
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

    /* ---------- Índice: un panel a la vista, el del botón pulsado ---------- */
    function mostrarPanel(id, foco) {
      qa('.g-indice [data-panel]').forEach(b => {
        const on = b.dataset.panel === id;
        b.setAttribute('aria-pressed', String(on));
        q('#' + b.dataset.panel).hidden = !on;
      });
      if (foco) { const t = q('#' + id + ' h2'); if (t) { t.tabIndex = -1; t.focus(); } }
    }
    qa('.g-indice [data-panel]').forEach(b => b.addEventListener('click', () => mostrarPanel(b.dataset.panel, false)));

    pintarRegulacion();
    pintarConcejosComarca();
    pintarMatriz();
    pintarListaAlertas();
    pintarFiabilidad();
    pintarPerfil();
    mostrarPanel('g-saturacion', false);
  }
})();
