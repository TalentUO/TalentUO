/* ==========================================================================
 * CONFIGURACIÓN EDITABLE de la pestaña Funciones avanzadas.
 * Aquí se cambian, sin tocar la lógica ni la interfaz:
 *   - la acción sugerida por color del semáforo,
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
  // Días hacia delante del calendario de alertas (la previsión llega a un año vista).
  // Más allá de 7 días la previsión es la del modelo de largo plazo, sin el tiempo.
  diasAlertas: 28,
};
