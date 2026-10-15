/* ==========================================================================
 * MAPA (Leaflet)
 * --------------------------------------------------------------------------
 * Mapa real de Asturias, aislado y sobre fondo liso. Con poco zoom se ven
 * las zonas (unión de sus concejos); al acercarse, cada concejo por separado.
 * Este archivo solo dibuja: no sabe de previsiones. app.js le pasa, para cada
 * zona y concejo, el nivel, la etiqueta y el texto accesible (actualizar()).
 *
 * Necesita: window.L (Leaflet), window.topojson (topojson-client) y
 * window.GeoAsturias (interfaz/geo-asturias.js).
 * ========================================================================== */
window.MapaAsturias = (function () {
  'use strict';

  const ZOOM_CONCEJOS = 9.5;   // a partir de aquí se ven los concejos
  const TAM_CLIC = 22;         // px del área pulsable de cada sitio (el punto visible es más pequeño)
  const SEP_PUNTOS = 16;       // px mínimos entre puntos de sitios
  const COS_LAT = Math.cos(43.3 * Math.PI / 180); // para medir distancias en grados sin deformar

  /* ---------- Punto interior para las etiquetas (algoritmo «polylabel» simplificado) ---------- */
  function distSeg2(px, py, a, b) {
    let x = a[0], y = a[1], dx = b[0] - x, dy = b[1] - y;
    if (dx || dy) {
      const t = ((px - x) * dx + (py - y) * dy) / (dx * dx + dy * dy);
      if (t > 1) { x = b[0]; y = b[1]; } else if (t > 0) { x += dx * t; y += dy * t; }
    }
    dx = px - x; dy = py - y;
    return dx * dx + dy * dy;
  }
  // Distancia al borde más cercano: positiva dentro del polígono, negativa fuera
  function distancia(x, y, anillos) {
    let dentro = false, min = Infinity;
    anillos.forEach(a => {
      for (let i = 0, j = a.length - 1; i < a.length; j = i++) {
        const p = a[i], q = a[j];
        if ((p[1] > y) !== (q[1] > y) && x < (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1]) + p[0]) dentro = !dentro;
        min = Math.min(min, distSeg2(x, y, p, q));
      }
    });
    return (dentro ? 1 : -1) * Math.sqrt(min);
  }
  function areaAnillo(a) {
    let s = 0;
    for (let i = 0, j = a.length - 1; i < a.length; j = i++) s += a[j][0] * a[i][1] - a[i][0] * a[j][1];
    return s / 2;
  }
  function centroide(a) {
    let area = 0, x = 0, y = 0;
    for (let i = 0, j = a.length - 1; i < a.length; j = i++) {
      const p = a[i], q = a[j], f = p[0] * q[1] - q[0] * p[1];
      x += (p[0] + q[0]) * f; y += (p[1] + q[1]) * f; area += f * 3;
    }
    return area ? [x / area, y / area] : a[0];
  }
  function polylabel(anillos, precision) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    anillos[0].forEach(([x, y]) => { minX = Math.min(minX, x); minY = Math.min(minY, y); maxX = Math.max(maxX, x); maxY = Math.max(maxY, y); });
    const ancho = maxX - minX, alto = maxY - minY, tam = Math.min(ancho, alto);
    if (!tam) return [minX, minY];
    const celda = (x, y, h) => { const d = distancia(x, y, anillos); return { x, y, h, d, max: d + h * Math.SQRT2 }; };
    const cola = [];
    for (let x = minX; x < maxX; x += tam) for (let y = minY; y < maxY; y += tam) cola.push(celda(x + tam / 2, y + tam / 2, tam / 2));
    const c0 = centroide(anillos[0]);
    let mejor = celda(c0[0], c0[1], 0);
    const caja = celda(minX + ancho / 2, minY + alto / 2, 0);
    if (caja.d > mejor.d) mejor = caja;
    while (cola.length) {
      let i = 0;
      for (let j = 1; j < cola.length; j++) if (cola[j].max > cola[i].max) i = j;
      const c = cola[i];
      cola[i] = cola[cola.length - 1];
      cola.pop();
      if (c.d > mejor.d) mejor = c;
      if (c.max - mejor.d <= precision) continue;
      const h = c.h / 2;
      cola.push(celda(c.x - h, c.y - h, h), celda(c.x + h, c.y - h, h), celda(c.x - h, c.y + h, h), celda(c.x + h, c.y + h, h));
    }
    return [mejor.x, mejor.y];
  }
  // Devuelve [lat, lon] dentro del polígono más grande de la geometría
  function puntoEtiqueta(geom) {
    const polis = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
    let mayor = polis[0], area = -1;
    polis.forEach(p => { const a = Math.abs(areaAnillo(p[0])); if (a > area) { area = a; mayor = p; } });
    const plano = mayor.map(anillo => anillo.map(([lon, lat]) => [lon * COS_LAT, lat]));
    const [x, y] = polylabel(plano, 0.002);
    return [y, x / COS_LAT];
  }

  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const movimientoReducido = () => window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ====================================================================
   * crear(contenedor, opciones)
   *   opciones.zonas:    [{ id, nombre }]
   *   opciones.concejos: [{ id (INE), nombre, zonaId }]
   *   opciones.tooltip(tipo, id)               -> HTML del recuadro al pasar el ratón
   *   opciones.alElegir(tipo, id, porTeclado)  -> al pulsar una zona o un concejo
   *   tipo es 'zona' o 'concejo'
   * ==================================================================== */
  function crear(contenedor, op) {
    const L = window.L, topo = window.GeoAsturias;
    if (!L || !window.topojson || !topo) throw new Error('Faltan Leaflet, topojson-client o la geometría de Asturias.');

    const geomPorId = {};
    topo.objects.concejos.geometries.forEach(g => { geomPorId[g.id] = g; });
    const enDatos = new Set(op.concejos.map(c => c.id));
    Object.keys(geomPorId).forEach(id => { if (!enDatos.has(id)) console.warn('Concejo con geometría pero sin datos:', id); });
    const concejos = op.concejos.filter(c => geomPorId[c.id] || (console.warn('Concejo sin geometría:', c.id, c.nombre), false));

    const fConcejos = concejos.map(c => ({
      type: 'Feature', properties: { tipo: 'concejo', id: c.id, nombre: c.nombre },
      geometry: window.topojson.feature(topo, geomPorId[c.id]).geometry,
    }));
    const fZonas = op.zonas.map(z => {
      const gs = concejos.filter(c => c.zonaId === z.id).map(c => geomPorId[c.id]);
      if (!gs.length) { console.warn('Zona sin concejos en el mapa:', z.id); return null; }
      return { type: 'Feature', properties: { tipo: 'zona', id: z.id, nombre: z.nombre }, geometry: window.topojson.merge(topo, gs) };
    }).filter(Boolean);

    /* ---------- Mapa: solo Asturias, sobre fondo liso (sin mapa base ni nombres de pueblos) ---------- */
    const map = L.map(contenedor, {
      zoomSnap: 0.25, zoomDelta: 0.5, wheelPxPerZoomLevel: 90, maxZoom: 13, zoomControl: false, maxBoundsViscosity: 1,
    });
    map.attributionControl.setPrefix(false);
    map.attributionControl.addAttribution('Límites: <a href="https://www.ign.es">© IGN</a> (CC BY 4.0)');
    // La vista inicial va antes que las capas: Leaflet no crea los polígonos hasta que el mapa tiene vista
    const limites = L.geoJSON({ type: 'FeatureCollection', features: fZonas }).getBounds();
    // No se puede alejar más allá de Asturias entera ni salirse de ella
    const zoomInicial = () => map.getBoundsZoom(limites, false, L.point(16, 16));
    map.setView(limites.getCenter(), zoomInicial(), { animate: false });
    map.setMinZoom(map.getZoom());
    map.setMaxBounds(limites.pad(0.08));
    // Si el contenedor cambia de tamaño (carga de fuentes, giro de pantalla…) se recalcula el encuadre;
    // mientras el usuario no haya movido el mapa, se vuelve a ajustar Asturias entera
    let sinTocar = true;
    ['pointerdown', 'wheel', 'keydown'].forEach(ev => contenedor.addEventListener(ev, () => { sinTocar = false; }, { passive: true }));
    function reajustar() {
      // Con el mapa oculto (otra pestaña o la vista de lista) el tamaño es 0 y el zoom mínimo saldría
      // disparado, bloqueando el alejamiento al volver: se espera a que vuelva a verse
      if (!contenedor.clientWidth || !contenedor.clientHeight) return;
      map.invalidateSize();
      const z = zoomInicial();
      map.setMinZoom(z);
      if (sinTocar) map.setView(limites.getCenter(), z, { animate: false });
    }
    if (window.ResizeObserver) new ResizeObserver(reajustar).observe(contenedor);
    else map.on('resize', reajustar);
    L.control.zoom({ position: 'topright', zoomInTitle: 'Acercar', zoomOutTitle: 'Alejar' }).addTo(map);

    map.createPane('contornos').style.zIndex = 410;
    map.createPane('resalte').style.zIndex = 415;
    map.createPane('etiquetas').style.zIndex = 450;
    ['contornos', 'resalte', 'etiquetas'].forEach(p => { map.getPane(p).style.pointerEvents = 'none'; });

    /* ---------- Polígonos ---------- */
    const capas = { zona: {}, concejo: {} };
    function preparar(tipo) {
      return {
        style: { className: 'area area-' + tipo + ' nivel-gris', weight: tipo === 'zona' ? 2 : 1 },
        onEachFeature: (f, capa) => {
          capas[tipo][f.properties.id] = capa;
          capa.bindTooltip(() => op.tooltip(tipo, f.properties.id), {
            sticky: true, direction: 'top', offset: [0, -14], opacity: 1, className: 'tip-mapa',
          });
          capa.on('mouseover', () => resaltar('hover', tipo, f.properties.id));
          capa.on('mouseout', () => resaltar('hover', null));
          capa.on('click', () => { capa.closeTooltip(); op.alElegir(tipo, f.properties.id, false); });
        },
      };
    }
    L.geoJSON({ type: 'FeatureCollection', features: fZonas }, preparar('zona')).addTo(map);
    L.geoJSON({ type: 'FeatureCollection', features: fConcejos }, preparar('concejo')).addTo(map);
    // Límites de zona encima de los concejos, para no perder la referencia al acercarse
    L.geoJSON({ type: 'FeatureCollection', features: fZonas }, {
      pane: 'contornos', interactive: false, style: { className: 'contorno-zona', fill: false },
    }).addTo(map);

    // Teclado: cada polígono visible es un botón. Intro o Espacio lo elige; al enfocarlo se ve su recuadro.
    ['zona', 'concejo'].forEach(tipo => Object.keys(capas[tipo]).forEach(id => {
      const capa = capas[tipo][id], el = capa.getElement();
      el.setAttribute('tabindex', '0');
      el.setAttribute('role', 'button');
      el.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); op.alElegir(tipo, id, true); }
      });
      el.addEventListener('focus', () => { capa.openTooltip(etiquetas[tipo][id].punto); resaltar('hover', tipo, id); });
      el.addEventListener('blur', () => { capa.closeTooltip(); resaltar('hover', null); });
    }));

    /* ---------- Resaltes (selección y ratón) ---------- */
    const resaltes = {
      sel: L.geoJSON(null, { pane: 'resalte', interactive: false, style: { className: 'resalte resalte-sel', fill: false } }).addTo(map),
      hover: L.geoJSON(null, { pane: 'resalte', interactive: false, style: { className: 'resalte resalte-hover', fill: false } }).addTo(map),
    };
    function resaltar(cual, tipo, id) {
      resaltes[cual].clearLayers();
      if (tipo && capas[tipo][id]) resaltes[cual].addData(capas[tipo][id].feature);
    }

    /* ---------- Etiquetas ---------- */
    const etiquetas = { zona: {}, concejo: {} };
    function crearEtiquetas(features, tipo) {
      features.forEach(f => {
        const punto = puntoEtiqueta(f.geometry);
        const icono = L.divIcon({
          className: 'et-icono', iconSize: null,
          html: `<span class="et-mapa et-${tipo}" aria-hidden="true"><span class="et-nombre">${esc(f.properties.nombre)}</span><span class="et-dato"></span></span>`,
        });
        const marca = L.marker(punto, { icon: icono, pane: 'etiquetas', interactive: false, keyboard: false }).addTo(map);
        const caja = capas[tipo][f.properties.id].getBounds();
        const area = (caja.getNorth() - caja.getSouth()) * (caja.getEast() - caja.getWest());
        etiquetas[tipo][f.properties.id] = { punto, marca, area, caja, el: marca.getElement().firstChild };
      });
    }
    crearEtiquetas(fZonas, 'zona');
    crearEtiquetas(fConcejos, 'concejo');

    // Etiquetas sin saturar: siempre nombre + porcentaje. Si una choca con otra ya puesta (dejando
    // AIRE px de margen) o es mucho más grande que su concejo, se oculta entera; al acercar el mapa
    // van apareciendo más. Tienen prioridad la seleccionada y las áreas más grandes.
    let prioridad = null;
    const AIRE = 6; // px mínimos entre etiquetas
    function colocarEtiquetas() {
      const tipo = modo === 'zonas' ? 'zona' : 'concejo';
      const lista = Object.keys(etiquetas[tipo]).map(id => Object.assign({ id }, etiquetas[tipo][id]))
        .sort((a, b) => (b.id === prioridad) - (a.id === prioridad) || b.area - a.area);
      lista.forEach(e => e.el.classList.remove('oculta'));
      const puestas = [];
      const choca = r => puestas.some(q => !(r.right + AIRE < q.left || r.left - AIRE > q.right || r.bottom + AIRE < q.top || r.top - AIRE > q.bottom));
      // Un concejo diminuto no se tapa con una etiqueta que lo desborda mucho
      const cabe = (r, e) => {
        if (tipo === 'zona') return true;
        const a = map.latLngToContainerPoint(e.caja.getNorthWest()), b = map.latLngToContainerPoint(e.caja.getSouthEast());
        return r.width <= (b.x - a.x) * 1.4 && r.height <= (b.y - a.y);
      };
      lista.forEach(e => {
        const r = e.el.getBoundingClientRect();
        if (!r.width) return;
        if (choca(r) || (e.id !== prioridad && !cabe(r, e))) e.el.classList.add('oculta');
        else puestas.push(r);
      });
      colocarSitios();
    }

    /* ---------- Sitios de interés: puntos con viñeta (solo en la vista de concejos) ---------- */
    // Por debajo de los carteles (pane 'etiquetas', 450): un punto nunca tapa el nombre de un concejo
    map.createPane('sitios').style.zIndex = 440;
    const sitios = {};
    (op.sitios || []).forEach(s => {
      const icono = L.divIcon({
        className: 'sitio-icono', iconSize: [TAM_CLIC, TAM_CLIC], iconAnchor: [TAM_CLIC / 2, TAM_CLIC / 2], popupAnchor: [0, -4],
        html: '<span class="sitio-punto"></span>',
      });
      const marca = L.marker([s.lat, s.lon], { icon: icono, pane: 'sitios', keyboard: true, title: s.nombre }).addTo(map);
      marca.origen = L.latLng(s.lat, s.lon);
      const el = marca.getElement();
      el.setAttribute('role', 'button');
      el.setAttribute('aria-label', 'Sitio de interés: ' + s.nombre);
      el.removeAttribute('title');
      marca.bindPopup(() => op.popupSitio(s.id), { className: 'popup-sitio', maxWidth: 300, minWidth: 240, autoPanPadding: [24, 24] });
      marca.on('popupopen', e => {
        // Los botones de la viñeta (p. ej. «Ver el concejo») avisan a app.js
        e.popup.getElement().querySelectorAll('[data-concejo]').forEach(b => b.addEventListener('click', () => {
          marca.closePopup();
          op.alElegir('concejo', b.dataset.concejo, true);
        }));
      });
      sitios[s.id] = marca;
    });

    // Los puntos no tienen que estar en el sitio exacto, pero sí sin amontonarse: en píxeles de pantalla
    // se separan entre sí (SEP_PUNTOS) y se apartan de los carteles visibles. Si un punto no encuentra
    // hueco fuera de un cartel, se oculta hasta acercar más. Se recalcula tras cada zoom.
    function colocarSitios() {
      const ids = Object.keys(sitios);
      if (!ids.length || modo !== 'concejos') return;
      const caja = contenedor.getBoundingClientRect(), m = TAM_CLIC / 2 + 2;
      const carteles = Array.from(contenedor.querySelectorAll('.et-mapa:not(.oculta)')).map(el => el.getBoundingClientRect())
        .filter(r => r.width).map(r => ({ l: r.left - caja.left - m, t: r.top - caja.top - m, r: r.right - caja.left + m, b: r.bottom - caja.top + m }));
      const pts = ids.map((id, i) => { const p = map.latLngToContainerPoint(sitios[id].origen); return { id, i, x: p.x, y: p.y }; });
      const dentroDe = p => carteles.find(c => p.x > c.l && p.x < c.r && p.y > c.t && p.y < c.b);
      for (let vuelta = 0; vuelta < 40; vuelta++) {
        let movido = false;
        for (let a = 0; a < pts.length; a++) {
          for (let b = a + 1; b < pts.length; b++) {
            const A = pts[a], B = pts[b];
            let dx = B.x - A.x, dy = B.y - A.y, d = Math.hypot(dx, dy);
            if (d >= SEP_PUNTOS) continue;
            if (d < 0.01) { const ang = (A.i * 2.39996) % (2 * Math.PI); dx = Math.cos(ang); dy = Math.sin(ang); d = 1; }
            const empuje = (SEP_PUNTOS - d) / 2 + 0.2;
            A.x -= dx / d * empuje; A.y -= dy / d * empuje;
            B.x += dx / d * empuje; B.y += dy / d * empuje;
            movido = true;
          }
        }
        pts.forEach(p => {
          const c = dentroDe(p);
          if (!c) return;
          // Al borde más cercano del cartel
          const op4 = [[p.x - c.l, c.l - 0.5, null], [c.r - p.x, c.r + 0.5, null], [p.y - c.t, null, c.t - 0.5], [c.b - p.y, null, c.b + 0.5]];
          const mejor = op4.reduce((x, y) => (y[0] < x[0] ? y : x));
          if (mejor[1] != null) p.x = mejor[1]; else p.y = mejor[2];
          movido = true;
        });
        if (!movido) break;
      }
      pts.forEach(p => {
        const marca = sitios[p.id];
        marca.setLatLng(map.containerPointToLatLng([p.x, p.y]));
        const el = marca.getElement();
        if (el) el.classList.toggle('tapado', !!dentroDe(p));
      });
    }

    /* ---------- Modo según el zoom ---------- */
    let modo = null;
    const avisoModo = L.control({ position: 'topleft' });
    avisoModo.onAdd = () => {
      const d = L.DomUtil.create('div', 'mapa-ctrl');
      d.innerHTML = '<p class="mapa-modo" aria-live="polite"></p><button type="button" class="mapa-todo">Ver toda Asturias</button>';
      L.DomEvent.disableClickPropagation(d);
      L.DomEvent.disableScrollPropagation(d);
      d.querySelector('.mapa-todo').addEventListener('click', () => verTodo());
      return d;
    };
    avisoModo.addTo(map);
    function actualizarModo() {
      const z = map.getZoom();
      const nuevo = z >= ZOOM_CONCEJOS ? 'concejos' : 'zonas';
      if (nuevo !== modo) {
        modo = nuevo;
        contenedor.classList.toggle('modo-zonas', modo === 'zonas');
        contenedor.classList.toggle('modo-concejos', modo === 'concejos');
        contenedor.querySelector('.mapa-modo').textContent = modo === 'zonas'
          ? 'Viendo zonas. Acerca el mapa para ver cada concejo.'
          : 'Viendo concejos. Las líneas gruesas separan las zonas.';
      }
      colocarEtiquetas();
    }
    map.on('zoomend', actualizarModo);
    map.on('resize', colocarEtiquetas);

    function verTodo() {
      if (movimientoReducido()) map.setView(limites.getCenter(), zoomInicial());
      else map.flyTo(limites.getCenter(), zoomInicial(), { duration: 0.6 });
    }
    actualizarModo();

    /* ---------- API pública ---------- */
    return {
      // estado = { zonas: {id: {nivel, etiqueta, aria, atenuada}}, concejos: {...}, zonaSel, concejoSel }
      actualizar(estado) {
        ['zona', 'concejo'].forEach(tipo => {
          const datos = estado[tipo === 'zona' ? 'zonas' : 'concejos'] || {};
          Object.keys(capas[tipo]).forEach(id => {
            const d = datos[id] || { nivel: 'gris', etiqueta: '', aria: '', atenuada: false };
            const el = capas[tipo][id].getElement();
            el.setAttribute('class', `leaflet-interactive area area-${tipo} nivel-${d.nivel}${d.atenuada ? ' atenuada' : ''}`);
            el.setAttribute('aria-label', d.aria);
            el.setAttribute('aria-pressed', String(tipo === 'zona' ? estado.zonaSel === id && !estado.concejoSel : estado.concejoSel === id));
            const et = etiquetas[tipo][id].el;
            et.querySelector('.et-dato').innerHTML = d.etiqueta;
            et.classList.toggle('atenuada', !!d.atenuada);
            et.classList.toggle('sel', tipo === 'zona' ? estado.zonaSel === id : estado.concejoSel === id);
          });
        });
        prioridad = modo === 'zonas' ? estado.zonaSel : estado.concejoSel;
        if (estado.concejoSel) resaltar('sel', 'concejo', estado.concejoSel);
        else resaltar('sel', estado.zonaSel ? 'zona' : null, estado.zonaSel);
        colocarEtiquetas();
      },
      encuadrar(tipo, id) {
        const capa = capas[tipo][id];
        if (!capa) return;
        sinTocar = false;
        const opciones = { padding: [30, 30], maxZoom: tipo === 'zona' ? 11 : 12.5 };
        const b = capa.getBounds();
        // Una zona siempre se encuadra con zoom suficiente para ver sus concejos
        const z = Math.max(map.getBoundsZoom(b, false, L.point(60, 60)), ZOOM_CONCEJOS);
        const zoom = Math.min(z, opciones.maxZoom);
        if (movimientoReducido()) map.setView(b.getCenter(), zoom);
        else map.flyTo(b.getCenter(), zoom, { duration: 0.6 });
      },
      enfocar(tipo, id) {
        const capa = capas[tipo][id];
        const el = capa && capa.getElement();
        if (!el || !el.getClientRects().length) return false;
        el.focus();
        return true;
      },
      verTodo,
      // Acerca el mapa al sitio y abre su viñeta
      abrirSitio(id) {
        const marca = sitios[id];
        if (!marca) return;
        sinTocar = false;
        const zoom = Math.max(map.getZoom(), 11.5);
        const p = map.latLngToContainerPoint(marca.getLatLng());
        if (zoom === map.getZoom() && p.x > 40 && p.y > 40 && p.x < contenedor.clientWidth - 40 && p.y < contenedor.clientHeight - 40) {
          marca.openPopup(); // ya está a la vista: no hace falta moverse
          return;
        }
        if (movimientoReducido()) {
          map.setView(marca.getLatLng(), zoom, { animate: false });
          marca.openPopup();
          return;
        }
        // Se abre al terminar el vuelo; por si el mapa no llega a moverse (ya estaba ahí), hay un respaldo
        let abierto = false;
        const abrir = () => { if (!abierto) { abierto = true; marca.openPopup(); } };
        map.once('moveend', abrir);
        setTimeout(abrir, 900);
        map.flyTo(marca.getLatLng(), zoom, { duration: 0.6 });
      },
      redimensionar() { map.invalidateSize(); colocarEtiquetas(); },
    };
  }

  return { crear, ZOOM_CONCEJOS };
})();
