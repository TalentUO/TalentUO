/* ==========================================================================
 * FUENTE DE DATOS FICTICIA (solo para el piloto de interfaz)
 * --------------------------------------------------------------------------
 * Genera cifras inventadas pero coherentes y deterministas: el mismo día y
 * la misma zona dan siempre el mismo resultado. Implementa el contrato
 * documentado en datos/api.js.
 *
 * Para usar el modelo real, sustituye este archivo por otro que defina
 * window.FuenteDatos con las mismas funciones (pueden devolver promesas).
 * Nada de la interfaz depende de lo que hay aquí dentro.
 * ========================================================================== */
(function () {
  'use strict';

  /* ---------- Configuración del piloto ---------- */
  const CONFIG = {
    fechaReferencia: null,      // 'YYYY-MM-DD' para fijar un "hoy" de demostración; null = fecha real
    horizonteDias: 366,         // días que se pueden elegir: de hoy a dentro de un año
    diasConMeteo: 7,            // a partir de aquí no hay meteorología fiable
    umbrales: { ambar: 1.2, rojo: 1.5 }, // visitantes / día normal
  };

  /* ---------- Zonas ---------- */
  // base = visitantes de un día normal (mediana anual inventada)
  // error = error típico del modelo en la zona (inventado)
  // Los concejos de cada zona están en LISTA_CONCEJOS, más abajo
  const ZONAS = [
    { id: 'costa-occidental', region: 'occ', kTemp: 1.0, kFinde: 0.9, nombre: 'Costa occidental', tipos: ['costa'], modelo: 'costa',
      lugares: ['Luarca', 'Cudillero', 'Tapia de Casariego', 'Navia', 'Playa del Silencio', 'Cabo Busto', 'Puerto de Vega', 'Castropol'],
      vecinos: 52000, base: 3400, error: 0.12, perfil: { pernocta: 0.48, asturianos: 0.5 },
      alternativas: [{ id: 'nalon', minutos: 30 }, { id: 'aviles', minutos: 40 }, { id: 'oscos', minutos: 40 }] },
    { id: 'oscos', region: 'occ', kTemp: 0.9, kFinde: 0.9, nombre: 'Oscos y Eo', tipos: ['montana'], modelo: 'montana',
      lugares: ['Taramundi', 'Vegadeo', 'Santa Eulalia de Oscos', 'Villanueva de Oscos', 'San Martín de Oscos', 'Grandas de Salime', 'Boal', 'Ría del Eo'],
      vecinos: 14000, base: 900, error: 0.16, perfil: { pernocta: 0.5, asturianos: 0.45 },
      alternativas: [{ id: 'costa-occidental', minutos: 40 }, { id: 'suroccidente', minutos: 60 }] },
    { id: 'suroccidente', region: 'occ', kTemp: 0.8, kFinde: 0.8, nombre: 'Suroccidente', tipos: ['montana'], modelo: 'montana',
      lugares: ['Cangas del Narcea', 'Tineo', 'Muniellos', 'Pola de Allande', 'Ibias'],
      vecinos: 28000, base: 1300, error: 0.2, perfil: { pernocta: 0.4, asturianos: 0.6 },
      sinDatos: 'La muestra de telefonía en esta zona es demasiado pequeña para dar una cifra fiable.',
      alternativas: [{ id: 'somiedo', minutos: 45 }, { id: 'costa-occidental', minutos: 50 }] },
    { id: 'nalon', region: 'cen', kTemp: 1.0, kFinde: 1.0, nombre: 'Bajo Nalón, Grado y Salas', tipos: ['costa', 'montana'], modelo: 'montana',
      lugares: ['Pravia', 'Muros de Nalón', 'San Esteban de Pravia', 'San Juan de la Arena', 'Grado', 'Salas', 'Cueva de la Peña de Candamo', 'Playa del Aguilar'],
      vecinos: 40000, base: 2400, error: 0.13, perfil: { pernocta: 0.35, asturianos: 0.65 },
      alternativas: [{ id: 'aviles', minutos: 25 }, { id: 'costa-occidental', minutos: 30 }, { id: 'somiedo', minutos: 45 }] },
    { id: 'somiedo', region: 'occ', kTemp: 1.1, kFinde: 0.85, nombre: 'Somiedo y Teverga', tipos: ['montana'], modelo: 'montana',
      lugares: ['Somiedo', 'Pola de Somiedo', 'Lagos de Saliencia', 'Valle del Lago', 'Teverga', 'Senda del Oso', 'Proaza', 'Quirós'],
      vecinos: 9500, base: 1400, error: 0.15, perfil: { pernocta: 0.42, asturianos: 0.6 },
      alternativas: [{ id: 'cuencas', minutos: 55 }, { id: 'nalon', minutos: 45 }, { id: 'oviedo', minutos: 50 }] },
    { id: 'aviles', region: 'cen', kTemp: 1.2, kFinde: 1.1, nombre: 'Avilés y cabo Peñas', tipos: ['ciudad', 'costa'], modelo: 'ciudad',
      lugares: ['Avilés', 'Salinas', 'Luanco', 'Cabo Peñas', 'Candás', 'Piedras Blancas', 'Playa de Xagó'],
      vecinos: 150000, base: 6800, error: 0.09, perfil: { pernocta: 0.3, asturianos: 0.62 },
      alternativas: [{ id: 'oviedo', minutos: 30 }, { id: 'nalon', minutos: 25 }, { id: 'gijon', minutos: 25 }] },
    { id: 'gijon', region: 'cen', kTemp: 1.4, kFinde: 1.0, nombre: 'Gijón', tipos: ['ciudad', 'costa'], modelo: 'ciudad',
      lugares: ['Gijón', 'Xixón', 'Playa de San Lorenzo', 'Cimadevilla', 'Playa de Poniente', 'Jardín Botánico'],
      vecinos: 268000, base: 15000, error: 0.08, perfil: { pernocta: 0.38, asturianos: 0.55 },
      alternativas: [{ id: 'sidra', minutos: 30 }, { id: 'aviles', minutos: 25 }, { id: 'oviedo', minutos: 30 }] },
    { id: 'oviedo', region: 'cen', kTemp: 0.9, kFinde: 0.9, nombre: 'Oviedo y Siero', tipos: ['ciudad'], modelo: 'ciudad',
      lugares: ['Oviedo', 'Uviéu', 'Pola de Siero', 'Lugones', 'Noreña', 'Monte Naranco', 'Catedral de Oviedo'],
      vecinos: 290000, base: 13500, error: 0.08, perfil: { pernocta: 0.34, asturianos: 0.58 },
      alternativas: [{ id: 'cuencas', minutos: 25 }, { id: 'aviles', minutos: 30 }, { id: 'gijon', minutos: 30 }] },
    { id: 'cuencas', region: 'cen', kTemp: 0.45, kFinde: 0.55, nombre: 'Cuencas mineras', tipos: ['montana'], modelo: 'montana',
      lugares: ['Mieres', 'Langreo', 'Pola de Laviana', 'Pola de Lena', 'Aller', 'Felechosa', 'Fuentes de Invierno', 'Pozo Sotón'],
      vecinos: 115000, base: 5200, error: 0.1, perfil: { pernocta: 0.2, asturianos: 0.72 },
      alternativas: [{ id: 'redes', minutos: 35 }, { id: 'oviedo', minutos: 25 }, { id: 'somiedo', minutos: 55 }] },
    { id: 'sidra', region: 'cen', kTemp: 0.95, kFinde: 1.05, nombre: 'Comarca de la Sidra', tipos: ['costa'], modelo: 'costa',
      lugares: ['Villaviciosa', 'Colunga', 'Lastres', 'Tazones', 'Nava', 'Playa de Rodiles', 'Museo del Jurásico'],
      vecinos: 28000, base: 3600, error: 0.12, perfil: { pernocta: 0.44, asturianos: 0.55 },
      alternativas: [{ id: 'gijon', minutos: 30 }, { id: 'ribadesella', minutos: 30 }, { id: 'redes', minutos: 40 }] },
    { id: 'redes', region: 'cen', kTemp: 0.9, kFinde: 0.8, nombre: 'Redes y Piloña', tipos: ['montana'], modelo: 'montana',
      lugares: ['Caso', 'Campo de Caso', 'Sobrescobio', 'Rioseco', 'Piloña', 'Infiesto', 'Parque Natural de Redes', 'Ponga', 'Beleño'],
      vecinos: 12000, base: 1300, error: 0.15, perfil: { pernocta: 0.36, asturianos: 0.62 },
      alternativas: [{ id: 'cuencas', minutos: 35 }, { id: 'sidra', minutos: 40 }, { id: 'cangas', minutos: 40 }] },
    { id: 'ribadesella', region: 'ori', kTemp: 1.1, kFinde: 1.0, nombre: 'Ribadesella', tipos: ['costa'], modelo: 'costa',
      lugares: ['Ribadesella', 'Ribeseya', 'Cueva de Tito Bustillo', 'Playa de Santa Marina', 'Caravia', 'Descenso del Sella'],
      vecinos: 6200, base: 2900, error: 0.13, perfil: { pernocta: 0.52, asturianos: 0.45 },
      alternativas: [{ id: 'sidra', minutos: 30 }, { id: 'llanes', minutos: 25 }, { id: 'redes', minutos: 45 }] },
    { id: 'cangas', region: 'ori', kTemp: 1.1, kFinde: 1.3, nombre: 'Cangas de Onís y Covadonga', tipos: ['montana'], modelo: 'montana',
      lugares: ['Cangas de Onís', 'Covadonga', 'Lagos de Covadonga', 'Lago Enol', 'Lago Ercina', 'Arriondas', 'Parres', 'Amieva', 'Onís', 'Benia de Onís', 'Puente Romano'],
      vecinos: 13500, base: 5000, error: 0.11, perfil: { pernocta: 0.4, asturianos: 0.42 },
      alternativas: [{ id: 'redes', minutos: 40 }, { id: 'ribadesella', minutos: 25 }, { id: 'cabrales', minutos: 30 }, { id: 'sidra', minutos: 45 }] },
    { id: 'llanes', region: 'ori', kTemp: 1.15, kFinde: 1.1, nombre: 'Llanes', tipos: ['costa'], modelo: 'costa',
      lugares: ['Llanes', 'Nueva', 'Posada', 'Poo', 'Barro', 'Playa de Torimbia', 'Playa de Gulpiyuri', 'Bufones de Pría', 'Cuevas del Mar'],
      vecinos: 13300, base: 5600, error: 0.11, perfil: { pernocta: 0.58, asturianos: 0.38 },
      alternativas: [{ id: 'ribadesella', minutos: 25 }, { id: 'cabrales', minutos: 30 }, { id: 'sidra', minutos: 50 }] },
    { id: 'cabrales', region: 'ori', kTemp: 1.05, kFinde: 1.15, nombre: 'Cabrales y Peñamellera', tipos: ['montana'], modelo: 'montana',
      lugares: ['Cabrales', 'Arenas de Cabrales', 'Bulnes', 'Poncebos', 'Naranjo de Bulnes', 'Picu Urriellu', 'Ruta del Cares', 'Panes', 'Colombres'],
      vecinos: 6400, base: 1900, error: 0.14, perfil: { pernocta: 0.45, asturianos: 0.35 },
      alternativas: [{ id: 'llanes', minutos: 30 }, { id: 'cangas', minutos: 30 }, { id: 'redes', minutos: 60 }] },
  ];
  const ZONA = {};
  ZONAS.forEach(z => { ZONA[z.id] = z; });

  /* ---------- Concejos (78) ---------- */
  // [código INE, nombre oficial, zona, peso, sensibilidad]
  // peso: parte de los visitantes de la zona que recibe el concejo (se normaliza dentro de la zona)
  // sensibilidad: cuánto amplía el concejo los altibajos de su zona (>1 = destino muy turístico)
  const LISTA_CONCEJOS = [
    ['33034', 'Valdés', 'costa-occidental', 3, 1.0], ['33041', 'Navia', 'costa-occidental', 2, 0.9],
    ['33070', 'Tapia de Casariego', 'costa-occidental', 1.5, 1.1], ['33021', 'Cudillero', 'costa-occidental', 2.5, 1.35],
    ['33017', 'Castropol', 'costa-occidental', 1, 1.0], ['33018', 'Coaña', 'costa-occidental', 0.6, 0.9],
    ['33023', 'El Franco', 'costa-occidental', 0.8, 1.0],
    ['33074', 'Vegadeo', 'oscos', 1.5, 0.9], ['33071', 'Taramundi', 'oscos', 1.2, 1.3], ['33063', 'San Tirso de Abres', 'oscos', 0.3, 0.8],
    ['33062', 'Santa Eulalia de Oscos', 'oscos', 0.5, 1.1], ['33061', 'San Martín de Oscos', 'oscos', 0.4, 1.0],
    ['33075', 'Villanueva de Oscos', 'oscos', 0.4, 1.1], ['33027', 'Grandas de Salime', 'oscos', 0.7, 1.0],
    ['33048', 'Pesoz', 'oscos', 0.2, 0.8], ['33029', 'Illano', 'oscos', 0.2, 0.8], ['33007', 'Boal', 'oscos', 0.5, 0.9],
    ['33077', 'Villayón', 'oscos', 0.4, 0.9],
    ['33011', 'Cangas del Narcea', 'suroccidente', 3, 1.0], ['33073', 'Tineo', 'suroccidente', 2.5, 1.0],
    ['33028', 'Ibias', 'suroccidente', 0.5, 1.0], ['33001', 'Allande', 'suroccidente', 0.6, 1.0], ['33022', 'Degaña', 'suroccidente', 0.4, 1.0],
    ['33051', 'Pravia', 'nalon', 1.5, 1.0], ['33039', 'Muros de Nalón', 'nalon', 1, 1.25], ['33069', 'Soto del Barco', 'nalon', 1, 1.15],
    ['33010', 'Candamo', 'nalon', 0.6, 0.9], ['33026', 'Grado', 'nalon', 1.5, 0.9], ['33059', 'Salas', 'nalon', 1.2, 1.0],
    ['33078', 'Yernes y Tameza', 'nalon', 0.15, 0.8],
    ['33068', 'Somiedo', 'somiedo', 3, 1.2], ['33072', 'Teverga', 'somiedo', 1.5, 1.05], ['33052', 'Proaza', 'somiedo', 1.2, 1.0],
    ['33053', 'Quirós', 'somiedo', 0.8, 0.95], ['33064', 'Santo Adriano', 'somiedo', 0.6, 1.0], ['33005', 'Belmonte de Miranda', 'somiedo', 0.5, 0.9],
    ['33004', 'Avilés', 'aviles', 4, 0.8], ['33016', 'Castrillón', 'aviles', 2, 1.15], ['33025', 'Gozón', 'aviles', 2, 1.2],
    ['33020', 'Corvera de Asturias', 'aviles', 1, 0.8], ['33030', 'Illas', 'aviles', 0.2, 0.8], ['33014', 'Carreño', 'aviles', 1.5, 1.1],
    ['33024', 'Gijón', 'gijon', 1, 1.0],
    ['33044', 'Oviedo', 'oviedo', 6, 0.9], ['33066', 'Siero', 'oviedo', 3, 0.9], ['33035', 'Llanera', 'oviedo', 1, 0.8],
    ['33042', 'Noreña', 'oviedo', 0.5, 0.85], ['33054', 'Las Regueras', 'oviedo', 0.3, 0.8], ['33057', 'Ribera de Arriba', 'oviedo', 0.4, 0.8],
    ['33037', 'Mieres', 'cuencas', 3, 0.8], ['33031', 'Langreo', 'cuencas', 2.5, 0.8], ['33060', 'San Martín del Rey Aurelio', 'cuencas', 1.2, 0.8],
    ['33032', 'Laviana', 'cuencas', 1, 0.95], ['33033', 'Lena', 'cuencas', 1.5, 1.0], ['33002', 'Aller', 'cuencas', 1.5, 1.2],
    ['33038', 'Morcín', 'cuencas', 0.6, 1.0], ['33058', 'Riosa', 'cuencas', 0.6, 1.1],
    ['33076', 'Villaviciosa', 'sidra', 3, 1.1], ['33019', 'Colunga', 'sidra', 2, 1.2], ['33040', 'Nava', 'sidra', 1.2, 0.9],
    ['33009', 'Cabranes', 'sidra', 0.4, 0.9], ['33006', 'Bimenes', 'sidra', 0.3, 0.8], ['33065', 'Sariego', 'sidra', 0.3, 0.8],
    ['33015', 'Caso', 'redes', 1, 1.1], ['33067', 'Sobrescobio', 'redes', 0.6, 1.1], ['33049', 'Piloña', 'redes', 1.6, 0.9],
    ['33050', 'Ponga', 'redes', 0.5, 1.0],
    ['33056', 'Ribadesella', 'ribadesella', 4, 1.0], ['33013', 'Caravia', 'ribadesella', 1, 1.1],
    ['33012', 'Cangas de Onís', 'cangas', 4, 1.1], ['33045', 'Parres', 'cangas', 2, 1.0], ['33003', 'Amieva', 'cangas', 0.6, 1.0],
    ['33043', 'Onís', 'cangas', 1, 1.2],
    ['33036', 'Llanes', 'llanes', 1, 1.0],
    ['33008', 'Cabrales', 'cabrales', 3, 1.1], ['33046', 'Peñamellera Alta', 'cabrales', 0.8, 1.0],
    ['33047', 'Peñamellera Baja', 'cabrales', 1, 0.95], ['33055', 'Ribadedeva', 'cabrales', 1.5, 1.05],
  ];
  const CONCEJOS = LISTA_CONCEJOS.map(([id, nombre, zona, peso, k]) => ({ id, nombre, zona, peso, k }));
  const CONCEJO = {};
  CONCEJOS.forEach(c => { CONCEJO[c.id] = c; });
  ZONAS.forEach(z => {
    z.concejos = CONCEJOS.filter(c => c.zona === z.id);
    const total = z.concejos.reduce((a, c) => a + c.peso, 0);
    z.concejos.forEach(c => { c.cuota = c.peso / total; c.unico = z.concejos.length === 1; });
  });

  /* ---------- Calendario (ficticio: verificar con el calendario oficial) ---------- */
  // [fecha, nombre, nombre del puente si lo genera]
  const LISTA_FESTIVOS = [
    ['2024-01-01', 'Año Nuevo', 'Puente de Año Nuevo'], ['2024-01-06', 'Reyes'],
    ['2024-03-28', 'Jueves Santo', 'Semana Santa'], ['2024-03-29', 'Viernes Santo', 'Semana Santa'],
    ['2024-05-01', 'Día del Trabajo'], ['2024-08-15', 'Asunción', 'Puente de agosto'],
    ['2024-09-09', 'Día de Asturias (trasladado)', 'Puente del Día de Asturias'], ['2024-10-12', 'Fiesta Nacional'],
    ['2024-11-01', 'Todos los Santos', 'Puente de Todos los Santos'],
    ['2024-12-06', 'Día de la Constitución', 'Puente de diciembre'], ['2024-12-09', 'Inmaculada (trasladado)', 'Puente de diciembre'],
    ['2024-12-25', 'Navidad'],
    ['2025-01-01', 'Año Nuevo'], ['2025-01-06', 'Reyes', 'Puente de Reyes'],
    ['2025-04-17', 'Jueves Santo', 'Semana Santa'], ['2025-04-18', 'Viernes Santo', 'Semana Santa'],
    ['2025-05-01', 'Día del Trabajo', 'Puente de mayo'], ['2025-08-15', 'Asunción', 'Puente de agosto'],
    ['2025-09-08', 'Día de Asturias', 'Puente del Día de Asturias'], ['2025-11-01', 'Todos los Santos'],
    ['2025-12-08', 'Inmaculada', 'Puente de diciembre'], ['2025-12-25', 'Navidad', 'Puente de Navidad'],
    ['2026-01-01', 'Año Nuevo', 'Puente de Año Nuevo'], ['2026-01-06', 'Reyes', 'Puente de Reyes'],
    ['2026-04-02', 'Jueves Santo', 'Semana Santa'], ['2026-04-03', 'Viernes Santo', 'Semana Santa'],
    ['2026-05-01', 'Día del Trabajo', 'Puente de mayo'], ['2026-08-15', 'Asunción'],
    ['2026-09-08', 'Día de Asturias', 'Puente del Día de Asturias'], ['2026-10-12', 'Fiesta Nacional', 'Puente del Pilar'],
    ['2026-11-02', 'Todos los Santos (trasladado)', 'Puente de Todos los Santos'],
    ['2026-12-07', 'Día de la Constitución (trasladado)', 'Puente de diciembre'], ['2026-12-08', 'Inmaculada', 'Puente de diciembre'],
    ['2026-12-25', 'Navidad', 'Puente de Navidad'],
    ['2027-01-01', 'Año Nuevo', 'Puente de Año Nuevo'], ['2027-01-06', 'Reyes'],
    ['2027-03-25', 'Jueves Santo', 'Semana Santa'], ['2027-03-26', 'Viernes Santo', 'Semana Santa'],
  ];
  const SEMANA_SANTA = [['2024-03-23', '2024-04-01'], ['2025-04-12', '2025-04-21'], ['2026-03-28', '2026-04-06'], ['2027-03-20', '2027-03-29']];

  /* ---------- Utilidades de fecha y azar determinista ---------- */
  function aISO(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function deISO(s) { const p = s.split('-').map(Number); return new Date(p[0], p[1] - 1, p[2], 12); }
  function sumar(s, n) { const d = deISO(s); d.setDate(d.getDate() + n); return aISO(d); }
  function diasEntre(a, b) { return Math.round((deISO(b) - deISO(a)) / 86400000); }
  function hoy() { return CONFIG.fechaReferencia || aISO(new Date()); }

  function hash(s) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function aleatorio() {
    let t = (hash(Array.prototype.join.call(arguments, '|')) + 0x6D2B79F5) >>> 0;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  const redondear = n => Math.round(n / 10) * 10;
  const limitar = (x, a, b) => Math.max(a, Math.min(b, x));

  const FESTIVOS = {};
  LISTA_FESTIVOS.forEach(f => { FESTIVOS[f[0]] = f[1]; });

  // Un festivo en lunes o viernes genera un fin de semana largo; en martes o jueves, un puente de 4 días.
  const PUENTES = {};
  LISTA_FESTIVOS.forEach(([f, , nombre]) => {
    if (!nombre) return;
    const dow = deISO(f).getDay();
    let ini = 0, fin = 0;
    if (dow === 1) ini = -2; else if (dow === 5) fin = 2;
    else if (dow === 2) ini = -3; else if (dow === 4) fin = 3;
    else return;
    for (let i = ini; i <= fin; i++) { const d = sumar(f, i); if (!PUENTES[d]) PUENTES[d] = nombre; }
  });

  function vacaciones(f) {
    const md = f.slice(5);
    if (md >= '12-23' || md <= '01-07') return 'Vacaciones de Navidad';
    for (const [a, b] of SEMANA_SANTA) if (f >= a && f <= b) return 'Vacaciones de Semana Santa';
    return null;
  }
  function lagosRegulado(f) {
    const m = +f.slice(5, 7), d = +f.slice(8);
    return m === 7 || m === 8 || (m === 9 && d <= 15) ||
      vacaciones(f) === 'Vacaciones de Semana Santa' || !!PUENTES[f];
  }

  /* ---------- Meteorología inventada ---------- */
  const PROB_LLUVIA = [0.55, 0.5, 0.5, 0.5, 0.45, 0.35, 0.3, 0.3, 0.35, 0.45, 0.55, 0.55];
  const TEMP_MEDIA = [12, 13, 15, 16, 19, 22, 24, 25, 23, 19, 15, 13];
  // El tiempo se parece en toda Asturias, con diferencias entre occidente, centro y oriente
  function meteo(f, region) {
    const m = deISO(f).getMonth();
    const r = 0.65 * aleatorio('lluvia', f) + 0.35 * aleatorio('lluvia', region || '', f);
    return {
      lluvia: r < PROB_LLUVIA[m],
      temp: TEMP_MEDIA[m] + Math.round((aleatorio('temp', f) - 0.5) * 8) + (region === 'occ' ? -1 : 0),
    };
  }

  /* ---------- "Modelo" ficticio ---------- */
  const TEMPORADA = {
    costa:   [0.5, 0.5, 0.6, 0.8, 0.85, 1.1, 1.7, 1.9, 1.15, 0.8, 0.55, 0.6],
    montana: [0.5, 0.55, 0.7, 0.95, 0.95, 1.1, 1.6, 1.8, 1.25, 1.0, 0.65, 0.7],
    ciudad:  [0.85, 0.85, 0.9, 1.0, 1.0, 1.05, 1.15, 1.2, 1.05, 1.0, 0.92, 1.02],
  };
  const DIA_NATURALEZA = [1.30, 0.85, 0.85, 0.85, 0.88, 1.08, 1.45];
  const DIA_CIUDAD = [1.05, 0.95, 0.95, 0.95, 0.97, 1.05, 1.18];
  const EFECTO_LLUVIA = { costa: 0.8, montana: 0.88, ciudad: 1.03 };
  const EFECTO_SOL = { costa: 1.12, montana: 1.08, ciudad: 1.0 };

  function textoTemporada(m) {
    if (m === 6 || m === 7) return 'Pleno verano';
    if (m === 5) return 'Comienzo del verano';
    if (m === 8) return 'Final del verano';
    if (m === 9) return 'Otoño';
    if (m === 10) return 'Otoño, temporada baja';
    if (m === 11 || m === 0 || m === 1) return 'Invierno, temporada baja';
    return 'Primavera';
  }
  function textoDia(dow) {
    return ['Es domingo', 'Día laborable', 'Día laborable', 'Día laborable', 'Día laborable', 'Es viernes', 'Es sábado'][dow];
  }

  function nivel(ratio) {
    if (ratio == null) return 'gris';
    if (ratio >= CONFIG.umbrales.rojo) return 'rojo';
    if (ratio >= CONFIG.umbrales.ambar) return 'ambar';
    return 'verde';
  }

  // esc (escenario): { lluvia: 'auto'|'si'|'no', puente: 'auto'|'si'|'no', lagos: 'auto'|'libre'|'regulado'|'cerrado' }
  function calcular(z, f, esc) {
    esc = esc || {};
    const d = deISO(f), m = d.getMonth(), dow = d.getDay();
    const off = diasEntre(hoy(), f);
    const nat = z.modelo !== 'ciudad';
    const factores = [];
    const add = (clave, texto, mult) => { if (Math.abs(mult - 1) >= 0.005) factores.push({ clave, texto, mult }); };

    add('temporada', textoTemporada(m), 1 + (TEMPORADA[z.modelo][m] - 1) * z.kTemp);
    add('dia', textoDia(dow), 1 + ((nat ? DIA_NATURALEZA : DIA_CIUDAD)[dow] - 1) * z.kFinde);

    let puente = PUENTES[f] || null;
    if (esc.puente === 'si' && !puente) puente = 'Puente (escenario)';
    if (esc.puente === 'no') puente = null;
    const festivo = FESTIVOS[f] || null;
    if (puente) add('puente', puente, nat ? 1.25 : 1.08);
    else if (festivo && dow !== 0 && dow !== 6 && esc.puente !== 'no') add('festivo', 'Festivo: ' + festivo, nat ? 1.3 : 1.1);

    const vac = vacaciones(f);
    if (vac) add('vacaciones', vac, nat ? 1.15 : 1.05);

    const conMeteo = off <= CONFIG.diasConMeteo;
    const mt = meteo(f, z.region);
    let lluvia = null;
    if (esc.lluvia === 'si') lluvia = true;
    else if (esc.lluvia === 'no') lluvia = false;
    else if (conMeteo) lluvia = mt.lluvia;
    if (lluvia === true) add('lluvia', esc.lluvia === 'si' ? 'Lluvia (escenario)' : 'Lluvia prevista', EFECTO_LLUVIA[z.modelo]);
    else if (lluvia === false && mt.temp >= 18) add('sol', esc.lluvia === 'no' ? 'Buen tiempo (escenario)' : 'Buen tiempo previsto', EFECTO_SOL[z.modelo]);

    if (z.id === 'cangas') {
      const acceso = esc.lagos && esc.lagos !== 'auto' ? esc.lagos : (lagosRegulado(f) ? 'regulado' : 'libre');
      if (acceso === 'regulado') add('lagos', 'Acceso regulado a los Lagos', 0.94);
      else if (acceso === 'cerrado') add('lagos', 'Acceso a los Lagos cerrado', 0.78);
    }

    // Variación propia de cada zona y día que el modelo no explica
    const azar = 1 + (aleatorio('dia', z.id, f) - 0.5) * 0.12;
    const ratio = factores.reduce((a, x) => a * x.mult, 1) * azar;
    const visitantes = redondear(z.base * ratio);
    const meteoConocida = conMeteo || (esc.lluvia && esc.lluvia !== 'auto');
    // La incertidumbre crece con la distancia, pero se estabiliza: más allá de unas semanas solo pesa el calendario
    const inc = 0.07 + 0.01 * limitar(off, 0, 14) + (meteoConocida ? 0 : 0.06);
    return {
      zona: z, fecha: f, ratio, visitantes, off, factores, conMeteo,
      min: redondear(visitantes * (1 - inc)), max: redondear(visitantes * (1 + inc)),
      esPrediccion: off >= 0,
    };
  }

  // Desviación "real" respecto a la predicción (para la validación y los datos históricos)
  function ruido(z, f) { return (aleatorio('real', z.id, f) - 0.5) * 2 * z.error * 1.6; }

  function publico(r) {
    const z = r.zona;
    if (z.sinDatos) {
      return { zonaId: z.id, fecha: r.fecha, nivel: 'gris', visitantes: null, min: null, max: null, normal: null,
        ratio: null, esPrediccion: r.esPrediccion, conMeteo: r.conMeteo, motivo: z.sinDatos };
    }
    return { zonaId: z.id, fecha: r.fecha, nivel: nivel(r.ratio), visitantes: r.visitantes, min: r.min, max: r.max,
      normal: z.base, ratio: r.ratio, esPrediccion: r.esPrediccion, conMeteo: r.conMeteo };
  }
  // Concejo: sigue a su zona, ampliando o suavizando sus altibajos, con una variación propia pequeña
  function calcularConcejo(c, f) {
    const z = ZONA[c.zona], rz = calcular(z, f);
    const azar = c.unico ? 1 : 1 + (aleatorio('concejo', c.id, f) - 0.5) * 0.1;
    const ratio = Math.max(0.2, 1 + (rz.ratio - 1) * c.k) * azar;
    const normal = Math.max(10, redondear(z.base * c.cuota));
    const visitantes = redondear(normal * ratio), inc = (rz.max - rz.visitantes) / rz.visitantes;
    return { concejo: c, zona: z, fecha: f, ratio, visitantes, normal, conMeteo: rz.conMeteo, esPrediccion: rz.esPrediccion,
      min: redondear(visitantes * (1 - inc)), max: redondear(visitantes * (1 + inc)) };
  }
  function publicoConcejo(r) {
    const c = r.concejo, z = r.zona;
    const ident = { concejoId: c.id, zonaId: z.id, fecha: r.fecha, esPrediccion: r.esPrediccion, conMeteo: r.conMeteo };
    if (z.sinDatos) {
      return Object.assign(ident, { nivel: 'gris', visitantes: null, min: null, max: null, normal: null, ratio: null, motivo: z.sinDatos });
    }
    return Object.assign(ident, { nivel: nivel(r.ratio), visitantes: r.visitantes, min: r.min, max: r.max, normal: r.normal, ratio: r.ratio });
  }

  // Resume una lista de días ya calculados (de una zona o de un concejo): medias diarias, día pico y días por nivel
  function resumir(dias, ident, sinDatos, publicar) {
    const n = dias.length;
    const comun = Object.assign(ident, { fecha: dias[0].fecha, desde: dias[0].fecha, hasta: dias[n - 1].fecha, dias: n,
      esPrediccion: dias.some(r => r.esPrediccion), conMeteo: dias.every(r => r.conMeteo) });
    if (sinDatos) {
      return Object.assign(comun, { nivel: 'gris', visitantes: null, min: null, max: null, normal: null, ratio: null,
        pico: null, diasPorNivel: null, motivo: sinDatos });
    }
    const media = k => dias.reduce((a, r) => a + r[k], 0) / n;
    const ratio = media('ratio');
    const pico = dias.reduce((a, r) => (r.ratio > a.ratio ? r : a));
    const diasPorNivel = { verde: 0, ambar: 0, rojo: 0 };
    dias.forEach(r => { diasPorNivel[nivel(r.ratio)]++; });
    return Object.assign(comun, {
      nivel: nivel(ratio), ratio, normal: dias[0].normal != null ? dias[0].normal : dias[0].zona.base,
      visitantes: redondear(media('visitantes')), min: redondear(media('min')), max: redondear(media('max')),
      pico: publicar(pico), diasPorNivel,
    });
  }
  function fechasEntre(desde, hasta) {
    const out = [];
    for (let f = desde; f <= hasta; f = sumar(f, 1)) out.push(f);
    return out;
  }

  function principales(r) {
    return r.factores.slice()
      .sort((a, b) => Math.abs(b.mult - 1) - Math.abs(a.mult - 1))
      .slice(0, 3)
      .map(x => ({ clave: x.clave, texto: x.texto, efecto: Math.round((x.mult - 1) * 100) }));
  }
  function zona(id) {
    const z = ZONA[id];
    if (!z) throw new Error('Zona desconocida: ' + id);
    return z;
  }

  const HORA = {
    montana: { texto: 'Antes de las 10:00', nota: 'La mayoría llega entre las 11:00 y las 13:00.' },
    costa: { texto: 'Después de las 18:00', nota: 'Hay más gente entre las 12:00 y las 17:00.' },
    ciudad: { texto: 'Por la mañana, antes de las 12:00', nota: 'Hay más gente por la tarde, entre las 17:00 y las 20:00.' },
  };

  const ACCIONES = {
    cangas: { rojo: 'Activar lanzaderas a los Lagos desde Cangas de Onís y avisar en los paneles de la N-625 y la AS-114.',
      ambar: 'Recomendar llegar antes de las 10:00 y usar los aparcamientos disuasorios.' },
    cabrales: { rojo: 'Avisar de aparcamiento completo en Poncebos y reforzar el funicular de Bulnes.',
      ambar: 'Difundir rutas alternativas a la del Cares en las oficinas de turismo.' },
    llanes: { rojo: 'Reforzar limpieza y socorrismo en playas e informar de playas alternativas.',
      ambar: 'Señalizar los aparcamientos de la entrada de Llanes.' },
  };
  const ACCIONES_TIPO = {
    costa: { rojo: 'Reforzar limpieza, socorrismo y aparcamientos alternativos en las playas.',
      ambar: 'Difundir playas y horarios con menos gente.' },
    montana: { rojo: 'Avisar de aparcamientos completos y reforzar el transporte público.',
      ambar: 'Recomendar llegar pronto y difundir rutas alternativas.' },
    ciudad: { rojo: 'Reforzar el transporte urbano y la limpieza en el centro.',
      ambar: 'Informar de horarios con menos gente en museos y monumentos.' },
  };
  function accion(z, n) { return (ACCIONES[z.id] && ACCIONES[z.id][n]) || ACCIONES_TIPO[z.modelo][n]; }

  /* ======================= Funciones del contrato ======================= */

  function getInfo() {
    return {
      hoy: hoy(), horizonteDias: CONFIG.horizonteDias, diasConMeteo: CONFIG.diasConMeteo,
      umbrales: Object.assign({}, CONFIG.umbrales), ficticio: true,
    };
  }

  function getZonas() {
    return ZONAS.map(z => ({ id: z.id, nombre: z.nombre, tipos: z.tipos.slice(), concejos: z.concejos.map(c => c.nombre),
      lugares: z.lugares.slice(), vecinos: z.vecinos, sinDatos: !!z.sinDatos }));
  }

  function getCalendario(desde, dias) {
    const out = [];
    for (let i = 0; i < dias; i++) {
      const f = sumar(desde, i), dow = deISO(f).getDay();
      out.push({ fecha: f, finde: dow === 0 || dow === 6, festivo: FESTIVOS[f] || null, puente: PUENTES[f] || null, vacaciones: vacaciones(f) });
    }
    return out;
  }

  function getProximoPuente(desde) {
    for (let i = 0; i < 240; i++) {
      const f = sumar(desde, i);
      if (PUENTES[f]) {
        let fin = f;
        while (PUENTES[sumar(fin, 1)] === PUENTES[f]) fin = sumar(fin, 1);
        return { nombre: PUENTES[f], inicio: f, fin };
      }
    }
    return null;
  }

  function getPrevisionDia(fecha) { return ZONAS.map(z => publico(calcular(z, fecha))); }

  // Resumen de una zona entre dos fechas (ambas incluidas)
  function resumenPeriodo(z, desde, hasta) {
    return resumir(fechasEntre(desde, hasta).map(f => calcular(z, f)), { zonaId: z.id }, z.sinDatos, publico);
  }

  function getPrevisionPeriodo(desde, hasta) { return ZONAS.map(z => resumenPeriodo(z, desde, hasta)); }

  // Sitios de interés: datos reales (datos/sitios.js), no previsiones. No se calcula su afluencia:
  // la interfaz usa la de su concejo principal (concejos[0]).
  function getSitios() {
    return (window.SitiosTuristicos || []).map(s => Object.assign({}, s, { concejos: s.concejos.slice(), foto: s.foto && Object.assign({}, s.foto) }));
  }

  // Eventos: datos reales de PredictHQ (datos/eventos.js), los que se solapan con [desde, hasta].
  // Solo se devuelven los que pueden mover la afluencia: impacto = asistencia / visitantes de un día
  // normal en su concejo. Grande si impacto ≥ IMPACTO.minimo y asistencia ≥ IMPACTO.asistenciaMin,
  // o si la asistencia es muy alta en términos absolutos (IMPACTO.asistenciaSiempre).
  const IMPACTO = { minimo: 0.5, asistenciaMin: 3500, asistenciaSiempre: 10000 };
  function impactoEvento(e) {
    const c = CONCEJO[e.concejo];
    if (!c || !e.asistencia) return null;
    const normal = Math.max(10, redondear(ZONA[c.zona].base * c.cuota));
    return { impacto: e.asistencia / normal, normalConcejo: normal };
  }
  const esGrande = e => !!e.impacto && ((e.impacto >= IMPACTO.minimo && e.asistencia >= IMPACTO.asistenciaMin) || e.asistencia >= IMPACTO.asistenciaSiempre);
  function getEventos(desde, hasta) {
    const d = window.EventosAsturias || { eventos: [], actualizado: null, hastaDatos: null, fuente: 'PredictHQ' };
    hasta = hasta || desde;
    const eventos = d.eventos.filter(e => e.inicio <= hasta && e.fin >= desde)
      .map(e => Object.assign({}, e, impactoEvento(e) || { impacto: null, normalConcejo: null })).filter(esGrande)
      .sort((a, b) => (a.inicio < b.inicio ? -1 : a.inicio > b.inicio ? 1 : (b.asistencia || 0) - (a.asistencia || 0)));
    return { fuente: d.fuente, actualizado: d.actualizado, hastaDatos: d.hastaDatos, criterio: Object.assign({}, IMPACTO), eventos };
  }

  function getConcejos() {
    return CONCEJOS.map(c => ({ id: c.id, nombre: c.nombre, zonaId: c.zona }));
  }

  function getPrevisionConcejos(desde, hasta) {
    if (!hasta || hasta === desde) return CONCEJOS.map(c => publicoConcejo(calcularConcejo(c, desde)));
    const fechas = fechasEntre(desde, hasta);
    return CONCEJOS.map(c => resumir(fechas.map(f => calcularConcejo(c, f)),
      { concejoId: c.id, zonaId: c.zona }, ZONA[c.zona].sinDatos, publicoConcejo));
  }

  function getSerieZona(zonaId, desde, dias) {
    const z = zona(zonaId), out = [];
    for (let i = 0; i < dias; i++) out.push(publico(calcular(z, sumar(desde, i))));
    return out;
  }

  function getFactores(zonaId, fecha) {
    const z = zona(zonaId);
    return z.sinDatos ? [] : principales(calcular(z, fecha));
  }

  function getMejorMomento(zonaId, desde, dias) {
    const z = zona(zonaId);
    if (z.sinDatos) return null;
    let mejor = null;
    for (let i = 0; i < dias; i++) {
      const r = calcular(z, sumar(desde, i));
      if (!mejor || r.ratio < mejor.ratio - 1e-9) mejor = r;
    }
    return { dia: publico(mejor), hora: Object.assign({}, HORA[z.modelo]) };
  }

  // Con hasta, compara la media del periodo
  function getAlternativas(zonaId, fecha, hasta) {
    const z = zona(zonaId);
    const prev = id => (hasta && hasta > fecha ? resumenPeriodo(zona(id), fecha, hasta) : publico(calcular(zona(id), fecha)));
    return z.alternativas
      .map(a => Object.assign(prev(a.id), { nombre: zona(a.id).nombre, minutos: a.minutos }))
      .filter(p => p.nivel === 'verde')
      .sort((a, b) => a.minutos - b.minutos)
      .slice(0, 3);
  }

  function perfilDia(z, fecha) {
    const d = deISO(fecha), dow = d.getDay(), m = d.getMonth();
    const finde = dow === 0 || dow === 6, verano = m === 6 || m === 7, puente = !!PUENTES[fecha];
    const pern = z.perfil.pernocta + (finde && !puente ? -0.07 : 0) + (puente ? 0.12 : 0) + (verano ? 0.1 : 0);
    const ast = z.perfil.asturianos + (finde && !puente ? 0.08 : 0) - (verano ? 0.18 : 0) - (puente ? 0.1 : 0);
    return { pern: limitar(pern, 0.1, 0.9), ast: limitar(ast, 0.1, 0.9) };
  }

  // Con hasta, devuelve la media del periodo
  function getPerfil(zonaId, fecha, hasta) {
    const z = zona(zonaId);
    if (z.sinDatos) return null;
    let sPern = 0, sAst = 0, n = 0;
    for (let f = fecha; f <= (hasta || fecha); f = sumar(f, 1)) {
      const p = perfilDia(z, f);
      sPern += p.pern; sAst += p.ast; n++;
    }
    const pern = Math.round(sPern / n * 100), ast = Math.round(sAst / n * 100);
    return { deUnDia: 100 - pern, conPernocta: pern, asturias: ast, restoEspana: 100 - ast };
  }

  const cacheFiabilidad = {};
  function getFiabilidad(zonaId) {
    if (cacheFiabilidad[zonaId]) return cacheFiabilidad[zonaId];
    const z = zona(zonaId);
    if (z.sinDatos) return null;
    const serie = [];
    let sumaError = 0, aciertos = 0, rojosReales = 0, rojosDetectados = 0;
    for (let f = '2025-01-01'; f <= '2025-06-30'; f = sumar(f, 1)) {
      const r = calcular(z, f);
      const real = redondear(r.visitantes * (1 + ruido(z, f)));
      const nP = nivel(r.ratio), nR = nivel(real / z.base);
      sumaError += Math.abs(real - r.visitantes) / real;
      if (nP === nR) aciertos++;
      if (nR === 'rojo') { rojosReales++; if (nP === 'rojo') rojosDetectados++; }
      serie.push({ fecha: f, real, prediccion: r.visitantes });
    }
    return (cacheFiabilidad[zonaId] = {
      desde: '2025-01-01', hasta: '2025-06-30', serie,
      errorMedio: Math.round(sumaError / serie.length * 100),
      nivelAcertado: Math.round(aciertos / serie.length * 100),
      rojosReales, rojosDetectados,
    });
  }

  function getDiasSobreUmbral(umbral, anio) {
    return ZONAS.map(z => {
      if (z.sinDatos) return { zonaId: z.id, anio, dias: null, picoVisitantes: null, picoPor100: null, sinDatos: true };
      let dias = 0, pico = 0;
      for (let f = anio + '-01-01'; f <= anio + '-12-31'; f = sumar(f, 1)) {
        const real = calcular(z, f).visitantes * (1 + ruido(z, f));
        if (real / z.base >= umbral) dias++;
        if (real > pico) pico = real;
      }
      return { zonaId: z.id, anio, dias, picoVisitantes: redondear(pico), picoPor100: Math.round(pico / z.vecinos * 100) };
    });
  }

  function getAlertas(desde, dias) {
    const out = [];
    for (let i = 0; i < dias; i++) {
      const f = sumar(desde, i);
      ZONAS.forEach(z => {
        if (z.sinDatos) return;
        const r = calcular(z, f), n = nivel(r.ratio);
        if (n === 'ambar' || n === 'rojo') {
          out.push({ fecha: f, zonaId: z.id, nivel: n, ratio: r.ratio, visitantes: r.visitantes, accion: accion(z, n) });
        }
      });
    }
    return out;
  }

  function simular(zonaId, fecha, escenario) {
    const z = zona(zonaId);
    const b = calcular(z, fecha), e = calcular(z, fecha, escenario || {});
    return {
      base: Object.assign(publico(b), { factores: principales(b) }),
      escenario: Object.assign(publico(e), { factores: principales(e) }),
    };
  }

  window.FuenteDatos = {
    getInfo, getZonas, getConcejos, getSitios, getEventos, getCalendario, getProximoPuente, getPrevisionDia, getPrevisionPeriodo,
    getPrevisionConcejos, getSerieZona, getFactores,
    getMejorMomento, getAlternativas, getPerfil, getFiabilidad, getDiasSobreUmbral, getAlertas, simular,
  };
})();
