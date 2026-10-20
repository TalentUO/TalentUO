/* ==========================================================================
 * CATÁLOGO: lo que no son cifras del modelo
 * --------------------------------------------------------------------------
 * Datos fijos que la web necesita además de las salidas del modelo:
 *   - los 78 concejos de Asturias (código INE y nombre oficial), agrupados en
 *     15 comarcas turísticas que solo sirven para dar a cada concejo su tipo
 *     de destino (costa, montaña, ciudad) y los lugares que encuentra el buscador;
 *   - el acceso a los sitios de interés (datos/sitios.js).
 * Las zonas de la previsión son las del modelo (mapeo de salidas-inicio.js),
 * no estas comarcas. Lo usa datos/fuente-modelo.js.
 * ========================================================================== */
window.Catalogo = (function () {
  'use strict';

  // Comarcas turísticas: tipo de destino y lugares conocidos (para el buscador)
  const ZONAS = [
    { id: 'costa-occidental', tipos: ['costa'],
      lugares: ['Luarca', 'Cudillero', 'Tapia de Casariego', 'Navia', 'Playa del Silencio', 'Cabo Busto', 'Puerto de Vega', 'Castropol'] },
    { id: 'oscos', tipos: ['montana'],
      lugares: ['Taramundi', 'Vegadeo', 'Santa Eulalia de Oscos', 'Villanueva de Oscos', 'San Martín de Oscos', 'Grandas de Salime', 'Boal', 'Ría del Eo'] },
    { id: 'suroccidente', tipos: ['montana'],
      lugares: ['Cangas del Narcea', 'Tineo', 'Muniellos', 'Pola de Allande', 'Ibias'] },
    { id: 'nalon', tipos: ['costa', 'montana'],
      lugares: ['Pravia', 'Muros de Nalón', 'San Esteban de Pravia', 'San Juan de la Arena', 'Grado', 'Salas', 'Cueva de la Peña de Candamo', 'Playa del Aguilar'] },
    { id: 'somiedo', tipos: ['montana'],
      lugares: ['Somiedo', 'Pola de Somiedo', 'Lagos de Saliencia', 'Valle del Lago', 'Teverga', 'Senda del Oso', 'Proaza', 'Quirós'] },
    { id: 'aviles', tipos: ['ciudad', 'costa'],
      lugares: ['Avilés', 'Salinas', 'Luanco', 'Cabo Peñas', 'Candás', 'Piedras Blancas', 'Playa de Xagó'] },
    { id: 'gijon', tipos: ['ciudad', 'costa'],
      lugares: ['Gijón', 'Xixón', 'Playa de San Lorenzo', 'Cimadevilla', 'Playa de Poniente', 'Jardín Botánico'] },
    { id: 'oviedo', tipos: ['ciudad'],
      lugares: ['Oviedo', 'Uviéu', 'Pola de Siero', 'Lugones', 'Noreña', 'Monte Naranco', 'Catedral de Oviedo'] },
    { id: 'cuencas', tipos: ['montana'],
      lugares: ['Mieres', 'Langreo', 'Pola de Laviana', 'Pola de Lena', 'Aller', 'Felechosa', 'Fuentes de Invierno', 'Pozo Sotón'] },
    { id: 'sidra', tipos: ['costa'],
      lugares: ['Villaviciosa', 'Colunga', 'Lastres', 'Tazones', 'Nava', 'Playa de Rodiles', 'Museo del Jurásico'] },
    { id: 'redes', tipos: ['montana'],
      lugares: ['Caso', 'Campo de Caso', 'Sobrescobio', 'Rioseco', 'Piloña', 'Infiesto', 'Parque Natural de Redes', 'Ponga', 'Beleño'] },
    { id: 'ribadesella', tipos: ['costa'],
      lugares: ['Ribadesella', 'Ribeseya', 'Cueva de Tito Bustillo', 'Playa de Santa Marina', 'Caravia', 'Descenso del Sella'] },
    { id: 'cangas', tipos: ['montana'],
      lugares: ['Cangas de Onís', 'Covadonga', 'Lagos de Covadonga', 'Lago Enol', 'Lago Ercina', 'Arriondas', 'Parres', 'Amieva', 'Onís', 'Benia de Onís', 'Puente Romano'] },
    { id: 'llanes', tipos: ['costa'],
      lugares: ['Llanes', 'Nueva', 'Posada', 'Poo', 'Barro', 'Playa de Torimbia', 'Playa de Gulpiyuri', 'Bufones de Pría', 'Cuevas del Mar'] },
    { id: 'cabrales', tipos: ['montana'],
      lugares: ['Cabrales', 'Arenas de Cabrales', 'Bulnes', 'Poncebos', 'Naranjo de Bulnes', 'Picu Urriellu', 'Ruta del Cares', 'Panes', 'Colombres'] },
  ];

  // [código INE, nombre oficial, zona del catálogo]
  const CONCEJOS = [
    ['33034', 'Valdés', 'costa-occidental'], ['33041', 'Navia', 'costa-occidental'],
    ['33070', 'Tapia de Casariego', 'costa-occidental'], ['33021', 'Cudillero', 'costa-occidental'],
    ['33017', 'Castropol', 'costa-occidental'], ['33018', 'Coaña', 'costa-occidental'],
    ['33023', 'El Franco', 'costa-occidental'], ['33074', 'Vegadeo', 'oscos'], ['33071', 'Taramundi', 'oscos'],
    ['33063', 'San Tirso de Abres', 'oscos'], ['33062', 'Santa Eulalia de Oscos', 'oscos'],
    ['33061', 'San Martín de Oscos', 'oscos'], ['33075', 'Villanueva de Oscos', 'oscos'],
    ['33027', 'Grandas de Salime', 'oscos'], ['33048', 'Pesoz', 'oscos'], ['33029', 'Illano', 'oscos'],
    ['33007', 'Boal', 'oscos'], ['33077', 'Villayón', 'oscos'], ['33011', 'Cangas del Narcea', 'suroccidente'],
    ['33073', 'Tineo', 'suroccidente'], ['33028', 'Ibias', 'suroccidente'], ['33001', 'Allande', 'suroccidente'],
    ['33022', 'Degaña', 'suroccidente'], ['33051', 'Pravia', 'nalon'], ['33039', 'Muros de Nalón', 'nalon'],
    ['33069', 'Soto del Barco', 'nalon'], ['33010', 'Candamo', 'nalon'], ['33026', 'Grado', 'nalon'],
    ['33059', 'Salas', 'nalon'], ['33078', 'Yernes y Tameza', 'nalon'], ['33068', 'Somiedo', 'somiedo'],
    ['33072', 'Teverga', 'somiedo'], ['33052', 'Proaza', 'somiedo'], ['33053', 'Quirós', 'somiedo'],
    ['33064', 'Santo Adriano', 'somiedo'], ['33005', 'Belmonte de Miranda', 'somiedo'], ['33004', 'Avilés', 'aviles'],
    ['33016', 'Castrillón', 'aviles'], ['33025', 'Gozón', 'aviles'], ['33020', 'Corvera de Asturias', 'aviles'],
    ['33030', 'Illas', 'aviles'], ['33014', 'Carreño', 'aviles'], ['33024', 'Gijón', 'gijon'],
    ['33044', 'Oviedo', 'oviedo'], ['33066', 'Siero', 'oviedo'], ['33035', 'Llanera', 'oviedo'],
    ['33042', 'Noreña', 'oviedo'], ['33054', 'Las Regueras', 'oviedo'], ['33057', 'Ribera de Arriba', 'oviedo'],
    ['33037', 'Mieres', 'cuencas'], ['33031', 'Langreo', 'cuencas'],
    ['33060', 'San Martín del Rey Aurelio', 'cuencas'], ['33032', 'Laviana', 'cuencas'], ['33033', 'Lena', 'cuencas'],
    ['33002', 'Aller', 'cuencas'], ['33038', 'Morcín', 'cuencas'], ['33058', 'Riosa', 'cuencas'],
    ['33076', 'Villaviciosa', 'sidra'], ['33019', 'Colunga', 'sidra'], ['33040', 'Nava', 'sidra'],
    ['33009', 'Cabranes', 'sidra'], ['33006', 'Bimenes', 'sidra'], ['33065', 'Sariego', 'sidra'],
    ['33015', 'Caso', 'redes'], ['33067', 'Sobrescobio', 'redes'], ['33049', 'Piloña', 'redes'],
    ['33050', 'Ponga', 'redes'], ['33056', 'Ribadesella', 'ribadesella'], ['33013', 'Caravia', 'ribadesella'],
    ['33012', 'Cangas de Onís', 'cangas'], ['33045', 'Parres', 'cangas'], ['33003', 'Amieva', 'cangas'],
    ['33043', 'Onís', 'cangas'], ['33036', 'Llanes', 'llanes'], ['33008', 'Cabrales', 'cabrales'],
    ['33046', 'Peñamellera Alta', 'cabrales'], ['33047', 'Peñamellera Baja', 'cabrales'],
    ['33055', 'Ribadedeva', 'cabrales']
  ];

  const copia = a => a.slice();
  return Object.freeze({
    // [{ id, tipos, lugares, concejos:[INE] }]
    zonas: () => ZONAS.map(z => ({ id: z.id, tipos: copia(z.tipos), lugares: copia(z.lugares),
      concejos: CONCEJOS.filter(c => c[2] === z.id).map(c => c[0]) })),
    // [{ id (INE), nombre, zonaId (comarca del catálogo) }]
    concejos: () => CONCEJOS.map(([id, nombre, zonaId]) => ({ id, nombre, zonaId })),
    // Sitios de interés (datos/sitios.js): sin previsión propia
    sitios: () => (window.SitiosTuristicos || []).map(s => Object.assign({}, s, { concejos: s.concejos.slice(), foto: s.foto && Object.assign({}, s.foto) })),
  });
})();
