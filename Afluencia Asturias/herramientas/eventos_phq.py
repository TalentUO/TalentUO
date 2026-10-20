"""Descarga los eventos de PredictHQ en Asturias para el próximo año y genera datos/eventos.js.

El token NO se guarda en el proyecto: se lee de la variable de entorno PHQ_TOKEN.
  PowerShell:  $env:PHQ_TOKEN = '...'; python herramientas/eventos_phq.py
  bash:        PHQ_TOKEN=... python herramientas/eventos_phq.py

Solo usa la librería estándar. Se queda con los eventos cuyo punto cae dentro de un concejo de
Asturias (límites de interfaz/geo-asturias.js) y con una asistencia estimada mínima (MIN_ASISTENCIA).
"""
import datetime, json, os, sys, urllib.parse, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_ASISTENCIA = 150  # los eventos más pequeños no mueven la afluencia de una zona
CATEGORIAS = {
    'sports': 'Deporte', 'concerts': 'Concierto', 'festivals': 'Festival', 'performing-arts': 'Artes escénicas',
    'community': 'Comunidad', 'expos': 'Feria', 'conferences': 'Conferencia',
}

token = os.environ.get('PHQ_TOKEN')
if not token:
    sys.exit('Falta la variable de entorno PHQ_TOKEN con el token de PredictHQ.')

# --- Concejos: decodifica el TopoJSON de interfaz/geo-asturias.js ---
texto = open(os.path.join(RAIZ, 'interfaz', 'geo-asturias.js'), encoding='utf-8').read()
clave = 'window.GeoAsturias = '
topo = json.loads(texto[texto.index(clave) + len(clave):].rstrip().rstrip(';'))
(sx, sy), (tx, ty) = topo['transform']['scale'], topo['transform']['translate']
arcos = []
for arco in topo['arcs']:
    x = y = 0
    puntos = []
    for dx, dy in arco:
        x += dx; y += dy
        puntos.append((x * sx + tx, y * sy + ty))
    arcos.append(puntos)

def anillo(indices):
    out = []
    for i in indices:
        a = arcos[i] if i >= 0 else arcos[~i][::-1]
        out += a if not out else a[1:]
    return out

concejos = []
for g in topo['objects']['concejos']['geometries']:
    polis = [g['arcs']] if g['type'] == 'Polygon' else g['arcs']
    concejos.append((g['id'], g['properties']['nombre'], [[anillo(r) for r in p] for p in polis]))

def dentro_anillo(x, y, a):
    d = False
    for i in range(len(a)):
        (x1, y1), (x2, y2) = a[i], a[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            d = not d
    return d

def concejo_de(lon, lat):
    for ine, _nombre, polis in concejos:
        for p in polis:
            if dentro_anillo(lon, lat, p[0]) and not any(dentro_anillo(lon, lat, h) for h in p[1:]):
                return ine
    return None

# --- PredictHQ ---
def get(url):
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

hoy = datetime.date.today()
params = {
    'within': '95km@43.33,-5.95', 'active.gte': hoy.isoformat(), 'active.lte': (hoy + datetime.timedelta(days=365)).isoformat(),
    'category': ','.join(CATEGORIAS), 'phq_attendance.gte': MIN_ASISTENCIA, 'sort': 'start', 'limit': 200,
}
url = 'https://api.predicthq.com/v1/events/?' + urllib.parse.urlencode(params)
brutos = []
while url:
    d = get(url)
    brutos += d['results']
    url = d.get('next')

eventos, fuera = [], 0
for r in brutos:
    lon, lat = r['location']
    ine = concejo_de(lon, lat)
    if not ine:
        fuera += 1
        continue
    lugar = next((e['name'] for e in r.get('entities', []) if e.get('type') == 'venue'), '')
    hora = r['start_local'][11:16]
    eventos.append({
        'id': r['id'], 'titulo': r['title'].strip(), 'categoria': CATEGORIAS.get(r['category'], r['category']),
        'inicio': r['start_local'][:10], 'fin': r['end_local'][:10], 'hora': None if hora == '00:00' else hora,
        'lugar': lugar, 'concejo': ine, 'lat': round(lat, 5), 'lon': round(lon, 5),
        'asistencia': r.get('phq_attendance'), 'rango': r.get('rank'),
    })

datos = {
    'fuente': 'PredictHQ', 'actualizado': hoy.isoformat(),
    'hastaDatos': max((e['fin'] for e in eventos), default=hoy.isoformat()), 'eventos': eventos,
}
with open(os.path.join(RAIZ, 'datos', 'eventos.js'), 'w', encoding='utf-8') as f:
    f.write('/* Eventos en Asturias (PredictHQ). Generado con herramientas/eventos_phq.py; no editar a mano.\n'
            ' * asistencia = estimación de PredictHQ (phq_attendance); concejo = código INE donde cae el evento. */\n')
    f.write('window.EventosAsturias = ' + json.dumps(datos, ensure_ascii=False, indent=1) + ';\n')
print(f'{len(eventos)} eventos en Asturias ({fuera} fuera, descartados); datos hasta {datos["hastaDatos"]}')
