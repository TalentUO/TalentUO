/* ==========================================================================
 * Comprueba la coherencia de lo que la web enseña, sin navegador.
 *
 *   node "Afluencia Asturias/herramientas/comprobar_datos_web.js"
 *
 * Carga los mismos scripts que index.html (datos/) en un contexto aislado y
 * recorre todos los días y zonas a través de window.Datos, como hace la
 * interfaz. Termina con código 1 si alguna comprobación falla:
 *
 *   1. La previsión está dentro de su «rango probable» (min <= visitantes <= max).
 *   2. El «mejor día alternativo» tiene menos visitantes y menos presión que el
 *      día elegido, y cae dentro de los días que se pueden elegir.
 *   3. «Acceso regulado a los Lagos» solo sale como causa en la zona principal, y
 *      «Partido», solo en las zonas de Gijón y Oviedo, donde se juega.
 *   4. En las salidas completas (Funciones avanzadas): predicciones y calendario
 *      de alertas dentro de su rango, y los recuentos «entre X e Y días» de
 *      regulación contienen su valor central.
 *   5. Fecha de los datos: «hoy» es la fecha real si hay previsión para ella, no
 *      se ofrecen días ya pasados y la previsión con meteorología solo se anuncia
 *      si la previsión del tiempo sigue vigente.
 * ========================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WEB = path.resolve(__dirname, '..');
const FACTOR_LAGOS = 'Acceso regulado a los Lagos';
const FACTOR_PARTIDO = 'Partido';
const CONCEJOS_CON_ESTADIO = ['33024', '33044']; // Gijón y Oviedo

function contexto(busqueda, scripts) {
  const w = { console, location: { search: busqueda || '' }, document: {}, setTimeout, clearTimeout, Promise };
  w.window = w;
  vm.createContext(w);
  scripts.forEach(s => vm.runInContext(fs.readFileSync(path.join(WEB, s), 'utf8'), w, { filename: s }));
  return w;
}
const INICIO = ['datos/sitios.js', 'datos/modelo/salidas-inicio.js', 'datos/datos.js', 'datos/catalogo.js',
  'datos/fuente-modelo.js', 'datos/api.js'];

const fallos = [];
function comprobar(nombre, malos, total) {
  const ok = malos.length === 0;
  console.log(`${ok ? 'OK   ' : 'FALLA'} ${nombre}: ${ok ? total + ' casos' : malos.length + ' de ' + total}`);
  if (!ok) { malos.slice(0, 5).forEach(m => console.log('        ' + m)); fallos.push(nombre); }
}
function sumar(f, n) {
  const p = f.split('-').map(Number), d = new Date(p[0], p[1] - 1, p[2], 12);
  d.setDate(d.getDate() + n);
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

/* ---------- 1 a 3: Inicio, día a día ---------- */
async function inicio(busqueda, etiqueta) {
  const D = contexto(busqueda, INICIO).Datos;
  const info = await D.getInfo();
  const zonas = await D.getZonas();
  const principal = zonas.filter(z => z.principal).map(z => z.id);
  const estadios = (await D.getConcejos()).filter(c => CONCEJOS_CON_ESTADIO.indexOf(c.id) !== -1).map(c => c.zonaId);
  const rango = [], mejor = [], lagos = [], partido = [];
  let nPartido = 0;
  let n = 0, nMejor = 0, nFactores = 0;
  for (let i = 0; i < info.horizonteDias; i++) {
    const f = sumar(info.hoy, i);
    const previsiones = await D.getPrevisionDia(f);
    const porZona = {};
    previsiones.forEach(p => { porZona[p.zonaId] = p; });
    for (const p of previsiones) {
      if (p.visitantes == null) continue;
      n++;
      if (!(p.min <= p.visitantes && p.visitantes <= p.max)) rango.push(`${p.zonaId} ${f}: ${p.visitantes} fuera de ${p.min}-${p.max}`);
      const fx = await D.getFactores(p.zonaId, f);
      nFactores++;
      if (principal.indexOf(p.zonaId) === -1 && fx.some(x => x.texto === FACTOR_LAGOS)) lagos.push(`${p.zonaId} ${f}`);
      if (fx.some(x => x.texto === FACTOR_PARTIDO)) { nPartido++; if (estadios.indexOf(p.zonaId) === -1) partido.push(`${p.zonaId} ${f}`); }
      const md = await D.getMejorDia(p.zonaId, f);
      if (!md || !md.fecha) continue;
      nMejor++;
      const fin = sumar(info.hoy, info.horizonteDias - 1);
      if (!(md.diferenciaPct < 0) || !(md.visitantes < p.visitantes) || !(md.ratio < p.ratio) || md.fecha < info.hoy || md.fecha > fin) {
        mejor.push(`${p.zonaId} ${f} -> ${md.fecha}: ${md.visitantes} frente a ${p.visitantes} visitantes (${Math.round(md.diferenciaPct)} %)`);
      }
    }
  }
  comprobar(`${etiqueta}: previsión dentro de su rango probable`, rango, n);
  comprobar(`${etiqueta}: mejor día alternativo con menos gente y menos presión`, mejor, nMejor);
  comprobar(`${etiqueta}: «${FACTOR_LAGOS}» solo en la zona principal`, lagos, nFactores);
  comprobar(`${etiqueta}: «${FACTOR_PARTIDO}» solo en las zonas de Gijón y Oviedo (sale ${nPartido} veces)`,
    estadios.length === CONCEJOS_CON_ESTADIO.length ? partido : ['no se han localizado las zonas de Gijón y Oviedo'], nFactores);
  return info;
}

/* ---------- 4: salidas completas (Funciones avanzadas, exportación) ---------- */
async function completas() {
  const w = contexto('', ['datos/modelo/salidas.js', 'datos/datos.js']);
  const d = await w.DatosModelo.cargar();
  const fuera = (lista, donde) => lista.filter(r => r.prediccion != null && r.p10 != null && r.p90 != null && !(r.p10 <= r.prediccion && r.prediccion <= r.p90))
    .map(r => `${donde} ${r.zona_mitma_id} ${r.fecha}: ${r.prediccion} fuera de ${r.p10}-${r.p90}`);
  comprobar('Salidas completas: predicciones dentro de su rango', fuera(d.predicciones.predicciones, 'predicciones'), d.predicciones.predicciones.length);
  comprobar('Salidas completas: calendario de alertas dentro de su rango', fuera(d.regulacion.calendario_alertas, 'calendario'), d.regulacion.calendario_alertas.length);
  const malos = [];
  let n = 0;
  const mira = (z, o, k, que) => {
    if (o[k + '_min'] == null || o[k + '_max'] == null) return;
    n++;
    if (o[k + '_min'] > o[k] || o[k + '_max'] < o[k]) malos.push(`${z.nombre_zona} ${o.anio} ${que}: ${o[k]} fuera de ${o[k + '_min']}-${o[k + '_max']}`);
  };
  d.regulacion.por_zona.forEach(z => {
    z.anios.filter(a => a.tipo === 'previsto').forEach(a => { mira(z, a, 'dias_rojos', 'días rojos'); mira(z, a, 'dias_alerta', 'días de alerta'); });
    (z.curva_umbral || []).filter(c => c.tipo === 'previsto').forEach(c => mira(z, c, 'dias', 'curva ' + c.umbral));
  });
  comprobar('Salidas completas: recuentos de regulación dentro de su rango', malos, n);
  return d;
}

/* ---------- 5: fecha de los datos (el reloj se fija con ?hoy=YYYY-MM-DD) ---------- */
async function fecha(d) {
  const fechaDatos = d.predicciones.fecha_hoy;
  const dias = d.predicciones.predicciones.filter(r => r.conjunto !== 'historico').map(r => r.fecha).sort();
  const primera = dias[0], ultima = dias[dias.length - 1];
  const casos = [
    // reloj, qué se espera
    { reloj: fechaDatos, hoy: primera, esHoy: primera === fechaDatos, vigente: true, fuera: false, que: 'el mismo día del cálculo' },
    { reloj: sumar(fechaDatos, 1), hoy: sumar(fechaDatos, 1), esHoy: true, vigente: true, fuera: false, que: 'al día siguiente' },
    { reloj: sumar(fechaDatos, 2), hoy: sumar(fechaDatos, 2), esHoy: true, vigente: false, fuera: false, que: 'dos días después' },
    { reloj: sumar(fechaDatos, 29), hoy: sumar(fechaDatos, 29), esHoy: true, vigente: false, fuera: false, que: 'un mes después' },
    { reloj: ultima, hoy: ultima, esHoy: true, vigente: false, fuera: false, que: 'el último día con previsión' },
    { reloj: sumar(ultima, 30), hoy: ultima, esHoy: false, vigente: false, fuera: true, que: 'pasado el último día' },
  ];
  const malos = [];
  for (const c of casos) {
    const D = contexto('?hoy=' + c.reloj, INICIO).Datos;
    const i = await D.getInfo();
    const mal = t => malos.push(`${c.que} (${c.reloj}): ${t}`);
    if (i.hoy !== c.hoy) mal(`abre en ${i.hoy} y debería abrir en ${c.hoy}`);
    if (i.esHoy !== c.esHoy) mal(`esHoy = ${i.esHoy}`);
    if (i.datosVigentes !== c.vigente) mal(`datosVigentes = ${i.datosVigentes}`);
    if (i.fueraDeRango !== c.fuera) mal(`fueraDeRango = ${i.fueraDeRango}`);
    if (i.fechaDatos !== fechaDatos) mal(`fechaDatos = ${i.fechaDatos}`);
    if (sumar(i.hoy, i.horizonteDias - 1) !== ultima) mal(`el último día elegible no es ${ultima}`);
    if (!c.vigente && i.diasConMeteo !== 0) mal(`anuncia ${i.diasConMeteo} días con meteorología con datos antiguos`);
    if (c.vigente && !(i.diasConMeteo > 0)) mal('no anuncia meteorología con datos del día');
    // Ningún día se anuncia «con meteorología» si la previsión del tiempo ya no vale, y sí los primeros si vale
    const n = Math.min(i.horizonteDias, 10);
    let conMeteo = 0;
    for (let k = 0; k < n; k++) conMeteo += (await D.getPrevisionDia(sumar(i.hoy, k))).filter(p => p.conMeteo).length;
    if (!c.vigente && conMeteo) mal(`${conMeteo} previsiones anunciadas con meteorología`);
    if (c.vigente && !conMeteo) mal('ninguna previsión con meteorología');
    // El próximo puente no puede haber pasado
    const p = await D.getProximoPuente(i.hoy);
    if (p && p.fin < i.hoy) mal(`próximo puente ya pasado (${p.inicio} a ${p.fin})`);
  }
  comprobar('Fecha de los datos: día de referencia, «hoy» y meteorología según el reloj', malos, casos.length);
  return sumar(fechaDatos, 1);
}

(async function () {
  await inicio('', 'Inicio (fecha real)');
  await inicio('?demo=1', 'Demo');
  const d = await completas();
  const diaSiguiente = await fecha(d);
  await inicio('?hoy=' + diaSiguiente, 'Inicio (día siguiente al cálculo, todos los días)');
  console.log(fallos.length ? `\nFALLAN ${fallos.length} comprobaciones` : '\nTODO OK');
  process.exit(fallos.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
