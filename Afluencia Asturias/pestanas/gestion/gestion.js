/* ==========================================================================
 * PESTAÑA «Gestión» — PROPIEDAD DE LA PERSONA 2 (rama web-gestion)
 * --------------------------------------------------------------------------
 * Componente vacío. interfaz/app.js llama a montar() la primera vez que se
 * abre la pestaña, y a mostrar() cada vez que se vuelve a ella.
 *
 *   contenedor  <section id="panel-gestion"> (vacío)
 *   datos       objeto de window.DatosModelo.cargar(): { predicciones,
 *               alternativas, regulacion, perfil, metricas, mapeo, sintetico, aviso }
 *               (forma completa en notas/coordinacion_web.md)
 *   util        utilidades compartidas: window.UtilWeb (pill, num, pct, esc, anunciar…)
 * ========================================================================== */
window.Pestanas = window.Pestanas || {};
window.Pestanas.gestion = {
  montar(contenedor, datos, util) {
    contenedor.innerHTML = '<h1 class="titulo-pagina">Gestión</h1><p class="g-lead">En construcción.</p>';
  },
  mostrar() {},
};
