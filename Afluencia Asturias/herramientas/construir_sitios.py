"""Paso 2: decide la posición de cada sitio (dentro de su concejo), descarga las fotos y escribe datos/sitios.js.

Prioridad de la posición:
  1. Resultado de Nominatim (nombre o búsqueda alternativa) que caiga dentro de uno de sus concejos.
  2. Coordenadas de la foto en Commons, si caen dentro de uno de sus concejos.
  3. Punto interior del concejo principal (marcado como aproximado).
"""
import io, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from PIL import Image
from shapely.geometry import shape, Point
from shapely.ops import polylabel

UA = {'User-Agent': 'NTTTurism-piloto/1.0 (prototipo de hackathon; uso puntual)'}
bruto, ods_path, geo_js, destino_js, dir_fotos = sys.argv[1:6]

# Nombre alternativo para buscar en Nominatim los sitios que no se encuentran por su nombre (clave = nº del sitio)
ALTERNATIVAS = {
    5: 'Sames', 6: 'Avilés', 8: 'Llodero', 9: 'Lapedo', 10: 'Martimporra', 15: 'Arenas de Cabrales',
    18: 'San Román de Candamo', 20: 'Covadonga', 22: 'Lago Enol', 23: 'Muniellos', 25: 'Cangas del Narcea',
    29: 'Salinas', 41: 'Artedo', 42: 'Degaña', 46: 'Universidad Laboral de Gijón', 51: 'Campa Torres',
    58: 'Chao Samartín', 59: 'San Antolín de Ibias', 60: 'Pastur', 65: 'Entralgo',
    90: 'Plaza del Fontán, Oviedo', 91: 'Monte Naranco', 92: 'Arriondas', 95: 'Panes', 96: 'Pesoz',
    102: 'Pimiango', 106: 'Soto de Ribera', 107: 'Angliru', 112: 'San Tirso de Abres', 133: 'Vegadeo',
    136: 'Valdediós',
}

def get(url, binario=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        datos = r.read()
    return datos if binario else json.loads(datos.decode('utf-8'))

# Concejos: nombre oficial -> INE y polígono detallado
t = open(geo_js, encoding='utf-8').read()
k = 'window.GeoAsturias = '
geo = json.loads(t[t.index(k) + len(k):].rstrip().rstrip(';'))
ine_por_nombre = {g['properties']['nombre']: g['id'] for g in geo['objects']['concejos']['geometries']}
poligono = {}
for f in json.load(open(ods_path, encoding='utf-8'))['features']:
    poligono.setdefault(f['properties']['mun_code'], shape(f['geometry']))

def concejos_de(txt):
    out = []
    for parte in re.split(r'\s*/\s*|,\s*', txt):
        if parte in ine_por_nombre:
            out.append(ine_por_nombre[parte])
        else:
            trozos = re.split(r'\s+y\s+', parte)
            assert all(x in ine_por_nombre for x in trozos), 'Concejo desconocido: ' + parte
            out += [ine_por_nombre[x] for x in trozos]
    return out

# Dentro del concejo, o a menos de ~400 m (playas y cabos quedan a veces justo fuera del límite costero)
def dentro(lat, lon, ines):
    p = Point(lon, lat)
    return (next((i for i in ines if poligono[i].contains(p)), None) or
            next((i for i in ines if poligono[i].distance(p) < 0.004), None))

sitios = json.load(open(bruto, encoding='utf-8'))
os.makedirs(dir_fotos, exist_ok=True)
salida, informe = [], {'nominatim': 0, 'alternativa': 0, 'foto': 0, 'aproximado': 0}
for s in sitios:
    ines = concejos_de(s['concejosTxt'])
    pos, fuente = None, None
    for g in s['geo']:
        if dentro(g['lat'], g['lon'], ines):
            pos, fuente = (g['lat'], g['lon']), 'nominatim'; break
    if not pos and s['n'] in ALTERNATIVAS:
        res = get('https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&countrycodes=es&bounded=1'
                  '&viewbox=-7.25,43.72,-4.45,42.85&q=' + urllib.parse.quote(ALTERNATIVAS[s['n']] + ', Asturias'))
        time.sleep(1.1)
        for r in res:
            if dentro(float(r['lat']), float(r['lon']), ines):
                pos, fuente = (float(r['lat']), float(r['lon'])), 'alternativa'; break
    c = s.get('commons') or {}
    if not pos and c.get('coords') and dentro(c['coords'][0], c['coords'][1], ines):
        pos, fuente = tuple(c['coords']), 'foto'
    if not pos:
        geom = poligono[ines[0]]
        if geom.geom_type == 'MultiPolygon':
            geom = max(geom.geoms, key=lambda x: x.area)
        p = polylabel(geom, 0.001)
        pos, fuente = (p.y, p.x), 'aproximado'
    informe[fuente] += 1
    # El concejo principal es aquel en el que cae el punto
    principal = dentro(pos[0], pos[1], ines) or ines[0]
    ines = [principal] + [i for i in ines if i != principal]

    sid = 's%03d' % s['n']
    ruta_foto = os.path.join(dir_fotos, sid + '.jpg')
    if c.get('thumb') and not os.path.exists(ruta_foto):
        url = re.sub(r'/\d+px-', '/500px-', c['thumb'])  # tamaño estándar de Wikimedia
        for intento in range(5):
            try:
                datos = get(url, binario=True)
                break
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    raise
                time.sleep(10 * (intento + 1))
        img = Image.open(io.BytesIO(datos)).convert('RGB')
        img.thumbnail((480, 360))
        img.save(ruta_foto, 'JPEG', quality=74, optimize=True, progressive=True)
        time.sleep(1.5)
    salida.append({
        'id': sid, 'nombre': s['nombre'], 'concejos': ines,
        'lat': round(pos[0], 5), 'lon': round(pos[1], 5), 'ubicacionAproximada': fuente == 'aproximado',
        'foto': {'src': 'assets/sitios/' + sid + '.jpg', 'autor': c.get('autor', ''), 'licencia': c.get('licencia', ''),
                 'pagina': c.get('pagina', '')} if c else None,
    })
    print(s['n'], fuente, pos, ' '.join(ines))

with open(destino_js, 'w', encoding='utf-8') as f:
    f.write('/* Sitios de interés turístico de Asturias (141), del documento del equipo del 15/10/2026.\n'
            ' * Posición: OpenStreetMap (Nominatim) o geolocalización de la foto, comprobada dentro del concejo;\n'
            ' * si no se encontró, punto interior del concejo (ubicacionAproximada = true).\n'
            ' * Fotos: Wikimedia Commons, licencias libres; autor y licencia en cada sitio (foto.autor, foto.licencia).\n'
            ' * concejos[0] es el concejo principal (donde está el punto). Generado con herramientas/construir_sitios.py. */\n')
    f.write('window.SitiosTuristicos = ' + json.dumps(salida, ensure_ascii=False, indent=1) + ';\n')
print(informe)
