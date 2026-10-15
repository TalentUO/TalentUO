/* ==========================================================================
 * CONFIGURACIÓN EDITABLE de la pestaña Gestión (persona 2).
 * Aquí se cambian, sin tocar la lógica ni la interfaz:
 *   - la acción sugerida por color del semáforo,
 *   - el criterio orientativo «estudiar regulación / vigilar» (días al año),
 *   - cuántos días hacia delante se listan las alertas.
 * Son decisiones del equipo, NO datos oficiales de capacidad.
 * ========================================================================== */
window.GestionConfig = {
  // Acción sugerida por color. El texto sale tal cual en pantalla y en el CSV.
  acciones: {
    verde: { titulo: 'Sin medidas', texto: 'No hace falta actuar.' },
    ambar: { titulo: 'Aviso y transporte', texto: 'Aviso al público y refuerzo del transporte.' },
    rojo:  { titulo: 'Control y refuerzo máximo', texto: 'Control o reserva de acceso y refuerzo máximo del transporte.' },
    gris:  { titulo: 'Sin datos', texto: 'Sin previsión para este día.' },
  },
  // Días al año por encima del umbral a partir de los cuales se sugiere cada paso.
  criterio: { estudiar: 30, vigilar: 10 },
  // Días hacia delante del calendario de alertas (la previsión llega a 60 días).
  diasAlertas: 28,
};
