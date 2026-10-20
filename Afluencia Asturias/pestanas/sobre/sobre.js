/* ==========================================================================
 * PESTAÑA «Sobre los datos»
 * --------------------------------------------------------------------------
 * Misma interfaz que pestanas/gestion/gestion.js:
 *   montar(contenedor, datos, util) la primera vez; mostrar() al volver.
 * Los textos están en pestanas/sobre/contenido.js; aquí solo se maquetan,
 * con el marcado y las clases de estilos/estilos.css (.prosa, .leyenda, .fuentes…).
 * ========================================================================== */
window.Pestanas = window.Pestanas || {};
window.Pestanas.sobre = {
  montar(contenedor, datos, util) {
    const cargar = new Promise((ok, ko) => {
      if (window.SobreContenido) return ok();
      const s = document.createElement('script');
      s.src = 'pestanas/sobre/contenido.js';
      s.onload = ok; s.onerror = () => ko(new Error('No se ha podido cargar pestanas/sobre/contenido.js'));
      document.head.appendChild(s);
    });
    return cargar.then(() => pintarSobre(contenedor, datos, util)).catch(err => {
      console.error(err);
      contenedor.innerHTML = '<div class="tarjeta"><p><strong>No se ha podido montar «Sobre los datos».</strong></p><p class="error-datos">' + util.esc(err.message) + '</p></div>';
    });
  },
  mostrar() {},
};

function pintarSobre(cont, datos, util) {
  const T = window.SobreContenido;
  const { esc, pct, ICONO, NIVEL, NBSP } = util;
  const u = datos.predicciones.umbrales;
  const algoritmo = { lightgbm: 'LightGBM', xgboost: 'XGBoost' }[datos.metricas.algoritmo] || datos.metricas.algoritmo;
  const textos = {
    verde: `Menos de ${pct(u.ambar)} sobre un día normal`,
    ambar: `Entre ${pct(u.ambar)} y ${pct(u.rojo)}`,
    rojo: `${pct(u.rojo)} o más`,
    gris: 'No hay muestra suficiente',
  };
  const leyenda = ['verde', 'ambar', 'rojo', 'gris'].map(n =>
    `<li><span class="sw-mapa nivel-${n}" aria-hidden="true"></span>${ICONO[n]}<span class="ley-txt"><strong>${NIVEL[n].nombre}</strong><span>${esc(textos[n])}</span></span></li>`).join('');

  cont.innerHTML = `
    <div class="prosa">
      <h1 class="titulo-pagina">Sobre los datos</h1>
      <p class="g-lead">${esc(T.intro)}</p>

      <h2>Cómo leer el semáforo</h2>
      <ul class="leyenda leyenda-grande">${leyenda}</ul>
      <p>Cada color va siempre acompañado de un icono, una trama en el mapa y su nombre, para que se entienda sin distinguir colores.</p>

      <h2>Qué es un «día normal»</h2>
      <p>${esc(T.diaNormal)}</p>

      <h2>Cómo funciona el modelo</h2>
      <p>${esc(T.modelo.join(' ').replace('{algoritmo}', algoritmo))}</p>
    </div>

    <h2 class="prosa-h">De dónde salen los datos</h2>
    <div class="fuentes">
      ${T.fuentes.map(f => `<article class="fuente">
        <p class="eyebrow">${esc(f.etiqueta)}</p>
        <h3>${esc(f.titulo)}</h3>
        <p>${esc(f.texto)}</p>
      </article>`).join('')}
    </div>

    <div class="prosa">
      <h2>Lo que no podemos ofrecer</h2>
      <ul class="no-lista">
        ${T.limitaciones.map(l => `<li><strong>${esc(l.titulo)}</strong> ${esc(l.texto)}</li>`).join('')}
      </ul>

      <h2>${esc(T.mapa.titulo)}</h2>
      <p>${esc(T.mapa.texto)}</p>
      ${datos.sintetico ? `<h2>Sobre estas cifras</h2><p>${esc(datos.aviso || 'DATOS SINTÉTICOS')}. Las cifras de esta versión se han generado para probar la web y no dicen nada de Asturias. Se sustituirán por las reales con el mismo formato.</p>` : ''}
    </div>`;
}
