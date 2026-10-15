"""Paso 1: metadatos de las fotos (Commons) y geocodificación (Nominatim) de los sitios. Guarda bruto.json."""
import json, re, sys, time, urllib.parse, urllib.request

UA = {'User-Agent': 'NTTTurism-piloto/1.0 (prototipo de hackathon; uso puntual)'}
tsv, salida = sys.argv[1], sys.argv[2]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode('utf-8'))

sitios = []
for linea in open(tsv, encoding='utf-8'):
    if not linea.strip():
        continue
    n, nombre, concejos, archivo = linea.rstrip('\n').split('\t')
    sitios.append({'n': int(n), 'nombre': nombre, 'concejosTxt': concejos, 'archivo': archivo})

# --- Commons: miniatura, autor, licencia y coordenadas de la foto ---
info = {}
for i in range(0, len(sitios), 40):
    titulos = '|'.join('File:' + s['archivo'] for s in sitios[i:i + 40])
    url = ('https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&prop=imageinfo|coordinates'
           '&iiprop=url|extmetadata&iiurlwidth=520&titles=' + urllib.parse.quote(titulos))
    d = get(url)
    norm = {x['from']: x['to'] for x in d['query'].get('normalized', [])}
    por_titulo = {p['title']: p for p in d['query']['pages']}
    for s in sitios[i:i + 40]:
        t = 'File:' + s['archivo']
        p = por_titulo.get(norm.get(t, t))
        if not p or p.get('missing') or 'imageinfo' not in p:
            print('SIN FOTO EN COMMONS:', s['n'], s['archivo'])
            continue
        ii = p['imageinfo'][0]
        meta = ii.get('extmetadata', {})
        limpiar = lambda v: re.sub(r'<[^>]+>', '', (v or {}).get('value', '')).strip()
        info[s['n']] = {
            'thumb': ii.get('thumburl'), 'pagina': ii.get('descriptionurl'),
            'autor': limpiar(meta.get('Artist')), 'licencia': limpiar(meta.get('LicenseShortName')),
            'coords': [p['coordinates'][0]['lat'], p['coordinates'][0]['lon']] if p.get('coordinates') else None,
        }
    time.sleep(1)

# --- Nominatim: búsqueda por nombre dentro de Asturias ---
def candidatos(nombre):
    c = [nombre, re.sub(r'\s*\([^)]*\)', '', nombre)]
    m = re.search(r'\(([^)]*)\)', nombre)
    if m:
        c.append(m.group(1))
    c.append(re.split(r'\s+y\s+|,\s*', re.sub(r'\s*\([^)]*\)', '', nombre))[0])
    vistos, out = set(), []
    for x in c:
        x = x.strip()
        if x and x not in vistos:
            vistos.add(x); out.append(x)
    return out

for s in sitios:
    s['geo'] = []
    for q in candidatos(s['nombre']):
        url = ('https://nominatim.openstreetmap.org/search?format=jsonv2&limit=3&countrycodes=es&bounded=1'
               '&viewbox=-7.25,43.72,-4.45,42.85&q=' + urllib.parse.quote(q + ', Asturias'))
        try:
            res = get(url)
        except Exception as e:
            print('error nominatim', s['n'], e); res = []
        time.sleep(1.1)
        for r in res:
            s['geo'].append({'q': q, 'lat': float(r['lat']), 'lon': float(r['lon']), 'tipo': r.get('type'), 'nombre': r.get('display_name')})
        if res:
            break
    s['commons'] = info.get(s['n'])
    print(s['n'], s['nombre'], '| geo:', len(s['geo']), '| foto:', bool(s['commons']), '| coords foto:', bool(s['commons'] and s['commons']['coords']))

json.dump(sitios, open(salida, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
