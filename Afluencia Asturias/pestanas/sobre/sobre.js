/* ==========================================================================
 * PESTAÑA «Sobre los datos» — PROPIEDAD DE LA PERSONA 2 (rama web-gestion)
 * --------------------------------------------------------------------------
 * Componente vacío. Misma interfaz que pestanas/gestion/gestion.js:
 *   montar(contenedor, datos, util) la primera vez; mostrar() al volver.
 * ========================================================================== */
window.Pestanas = window.Pestanas || {};
window.Pestanas.sobre = {
  montar(contenedor, datos, util) {
    contenedor.innerHTML = '<div class="prosa"><h1 class="titulo-pagina">Sobre los datos</h1><p class="g-lead">En construcción.</p></div>';
  },
  mostrar() {},
};
