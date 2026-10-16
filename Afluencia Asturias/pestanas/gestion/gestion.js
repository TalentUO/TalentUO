/* ==========================================================================
 * PESTAÑA «Gestión» — PROPIEDAD DE LA PERSONA 2 (rama web-gestion)
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
        contenedor.innerHTML = '<div class="tarjeta"><p><strong>No se ha podido montar la pestaña Gestión.</strong></p><p class="error-datos">' + util.esc(err.message) + '</p></div>';
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
    const nombreZ = id => esc(L.nombreZona(datos, id));
    const umbrales = L.umbralesDisponibles(datos);
    const umb = datos.regulacion.umbrales || datos.predicciones.umbrales;
    const aniosInfo = L.aniosDisponibles(datos);
    const etiquetaAnio = a => a.anio + (a.tipo === 'previsto' ? ' (previsto)' : ' (observado)');
    const estado = { umbralIdx: Math.max(0, umbrales.indexOf(umb.ambar)), anio: aniosInfo.filter(a => a.tipo === 'previsto')[0] || aniosInfo[0], filtro: 'rojo', csv: null, csvOrigen: null };
    const opcionesZona = zonas.map(z => `<option value="${esc(z.zona_mitma_id)}">${esc(z.nombre_zona)}</option>`).join('');
    const alertas = L.alertasProximas(datos);
    const mesHoy = +datos.predicciones.fecha_hoy.slice(5, 7);

    cont.innerHTML = `
    <div class="g-intro">
      <h1 class="titulo-pagina">Gestión</h1>
      <p class="g-lead">Herramientas para ayuntamientos, el Principado y el Parque Nacional: cuántos días al año hay presión, qué viene en las próximas semanas y cuánto podemos fiarnos del modelo.</p>
      <nav aria-label="Apartados de gestión" class="g-indice">
        <a href="#g-regular">¿Hace falta regular?</a>
        <a href="#g-lagos">Lagos de Covadonga</a>
        <a href="#g-alertas">Alertas</a>
        <a href="#g-fiabilidad">Fiabilidad</a>
        <a href="#g-perfil">Perfil del visitante</a>
        <a href="#g-exportar">Exportar</a>
      </nav>
    </div>

    <section class="tarjeta g-sec" id="g-regular" aria-labelledby="g-regular-t">
      <h2 id="g-regular-t">¿Hace falta regular?</h2>
      <p class="g-desc">Días al año en los que cada zona supera el umbral que elijas, comparados con un día normal. Si una zona lo supera muchos días, conviene estudiar medidas. Los años 2023 y 2024 son observados; 2026 y 2027, previstos por el modelo.</p>
      <div class="g-dos">
        <div class="umbral">
          <label for="umbral" class="umbral-et">Contar los días con más de <strong id="umbral-valor"></strong> de visitantes sobre un día normal</label>
          <input type="range" id="umbral" min="0" max="${umbrales.length - 1}" step="1" value="${estado.umbralIdx}">
          <div class="umbral-escala" aria-hidden="true"><span>${esc(pct(umbrales[0]))}</span><span>${esc(pct(umbrales[umbrales.length - 1]))}</span></div>
        </div>
        <div>
          <label for="reg-anio" class="filtro-et">Año de referencia para el veredicto</label>
          <select id="reg-anio" class="select">${aniosInfo.map(a => `<option value="${a.anio}"${a.anio === estado.anio.anio ? ' selected' : ''}>${etiquetaAnio(a)}</option>`).join('')}</select>
        </div>
      </div>
      <p class="g-resumen" id="reg-resumen" aria-live="polite"></p>
      <ul class="rg-lista" id="reg-lista"></ul>
      <p class="g-nota">Criterio orientativo del equipo, no un dato oficial: <strong>${C.criterio.estudiar} días o más</strong>, estudiar regulación; <strong>entre ${C.criterio.vigilar} y ${C.criterio.estudiar - 1}</strong>, vigilar. Las líneas finas de cada barra marcan ${C.criterio.vigilar} y ${C.criterio.estudiar} días. Los umbrales del semáforo son ${esc(pct(umb.ambar))} (alta) y ${esc(pct(umb.rojo))} (saturación). Los años observados solo admiten los valores de la barra deslizante. En los años previstos, el intervalo probable va entre paréntesis.</p>
    </section>

    <section class="tarjeta g-sec" id="g-lagos" aria-labelledby="g-lagos-t">
      <h2 id="g-lagos-t">Comparación con el acceso regulado a los Lagos</h2>
      <p class="g-desc" id="lagos-desc"></p>
      <div class="tabla-marco" id="lagos-tabla"></div>
      <p class="g-nota" id="lagos-nota"></p>
    </section>

    <section class="tarjeta g-sec" id="g-alertas" aria-labelledby="g-alertas-t">
      <h2 id="g-alertas-t">Alertas de las próximas ${Math.round(C.diasAlertas / 7)} semanas</h2>
      <p class="g-desc">Nivel previsto por zona y día. Debajo, las acciones sugeridas por nivel. A 1-3 días la previsión incluye el tiempo; a partir de 8 días usa solo calendario y eventos y es más incierta.</p>
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

    <div class="g-dos">
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
    </div>

    <section class="tarjeta g-sec" id="g-exportar" aria-labelledby="g-exportar-t">
      <h2 id="g-exportar-t">Exportar datos</h2>
      <p class="g-desc">Tablas en CSV (separadas por punto y coma, decimales con coma) para abrir en Excel o LibreOffice.</p>
      <div class="exp-botones">
        <button type="button" class="btn" data-exportar="prevision">Previsión mostrada (alertas)</button>
        <button type="button" class="btn" data-exportar="umbral">Días sobre el umbral</button>
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

    /* ---------- ¿Hace falta regular? ---------- */
    const VER = { estudiar: { t: 'Estudiar regulación', n: 'rojo' }, vigilar: { t: 'Vigilar', n: 'ambar' }, ok: { t: 'Sin presión', n: 'verde' } };
    const umbralActual = () => umbrales[+q('#umbral').value];
    const textoDias = d => (d.dias == null ? '—' : d.dias + (d.tipo === 'previsto' && d.min != null ? ` (${d.min}–${d.max})` : ''));

    function pintarRegulacion() {
      const u = umbralActual();
      q('#umbral-valor').textContent = pct(u);
      q('#umbral').setAttribute('aria-valuetext', `Más de ${Math.round((u - 1) * 100)} por ciento sobre un día normal`);
      const tabla = L.tablaRegulacion(datos, u, { anioReferencia: estado.anio.anio });
      const maxD = Math.max(40, ...tabla.map(t => t.dias || 0));
      const estudiar = tabla.filter(t => t.veredicto === 'estudiar').map(t => t.nombre_zona);
      q('#reg-resumen').textContent = estudiar.length
        ? `Con este umbral, en ${estudiar.length === 1 ? 'una zona' : estudiar.length + ' zonas'} se superan ${C.criterio.estudiar} días en ${estado.anio.anio}: ${estudiar.join(', ')}.`
        : `Con este umbral, ninguna zona llega a ${C.criterio.estudiar} días en ${estado.anio.anio}.`;
      q('#reg-lista').innerHTML = tabla.map(t => {
        if (t.dias == null) return `<li class="rg"><span class="rg-zona">${esc(t.nombre_zona)}</span><span class="rg-sin">Sin datos suficientes</span></li>`;
        const v = VER[t.veredicto];
        const otros = t.anios.map(a => `${a.anio}: ${textoDias(a)}`).join(' · ');
        return `<li class="rg">
          <span class="rg-zona">${esc(t.nombre_zona)}${t.es_principal ? ' · zona principal' : ''}</span>
          <span class="rg-barra" aria-hidden="true"><span class="rg-val v-${t.veredicto}" style="width:${(t.dias / maxD * 100).toFixed(1)}%"></span>
            <span class="rg-ref" style="left:${(C.criterio.vigilar / maxD * 100).toFixed(1)}%"></span><span class="rg-ref" style="left:${(C.criterio.estudiar / maxD * 100).toFixed(1)}%"></span></span>
          <span class="rg-num">${t.dias} ${t.dias === 1 ? 'día' : 'días'}</span>
          <span class="rg-ver"><span class="pill pill-${v.n}">${ICONO[v.n]}<span>${v.t}</span></span></span>
          <span class="rg-pico">${esc(otros)}</span>
        </li>`;
      }).join('');
    }
    q('#umbral').addEventListener('input', pintarRegulacion);
    q('#reg-anio').addEventListener('change', () => { estado.anio = aniosInfo.find(a => a.anio === +q('#reg-anio').value); pintarRegulacion(); });

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

    /* ---------- Alertas ---------- */
    (function pintarMatriz() {
      const fechas = Array.from(new Set(alertas.map(a => a.fecha))).sort();
      const porClave = new Map(alertas.map(a => [a.fecha + '|' + a.zona_mitma_id, a]));
      const cabecera = '<thead><tr><th scope="col"><span class="sr">Zona</span></th>' + fechas.map(f => {
        const d = util.deISO(f), finde = d.getDay() === 0 || d.getDay() === 6;
        return `<th scope="col" class="${finde ? 'finde' : ''}" title="${esc(util.fechaLarga(f))}"><span aria-hidden="true">${LETRA[d.getDay()]}<br>${d.getDate()}</span><span class="sr">${esc(util.fechaLarga(f))}</span></th>`;
      }).join('') + '</tr></thead>';
      const cuerpo = '<tbody>' + zonas.map(z => '<tr><th scope="row">' + esc(z.nombre_zona) + '</th>' + fechas.map(f => {
        const a = porClave.get(f + '|' + z.zona_mitma_id), n = a ? a.color : 'gris';
        const t = NIVEL[n].nombre + (a && a.cociente != null ? ', ' + pct(a.cociente) : '');
        return `<td class="cel cel-${n}" title="${esc(t)}">${ICONO[n]}<span class="sr">${esc(t)}</span></td>`;
      }).join('') + '</tr>').join('') + '</tbody>';
      q('#matriz').innerHTML = `<caption class="sr">Nivel previsto por zona para los próximos ${fechas.length} días</caption>` + cabecera + cuerpo;
    })();

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
        const u = umbralActual();
        csv = L.csvRegulacion(L.tablaRegulacion(datos, u, { anioReferencia: estado.anio.anio }), u, sint);
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

    /* ---------- Índice: desplaza sin tocar el hash (lo usa la navegación) ---------- */
    qa('.g-indice a').forEach(a => a.addEventListener('click', ev => {
      ev.preventDefault();
      const destino = q(a.getAttribute('href'));
      if (destino) { destino.scrollIntoView({ behavior: 'smooth', block: 'start' }); destino.setAttribute('tabindex', '-1'); destino.focus({ preventScroll: true }); }
    }));

    pintarRegulacion();
    pintarListaAlertas();
    pintarFiabilidad();
    pintarPerfil();
  }
})();
