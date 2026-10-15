"""Genera interfaz/geo-asturias.js: TopoJSON de los 78 concejos de Asturias.

Geometría: georef-spain-municipio (OpenDataSoft, a partir de IGN, año 2022).
Nombres oficiales en castellano: es-atlas (también a partir de IGN).
Uso: python generar_geo.py ods.geojson municipalities.json destino.js [tolerancia_grados]
"""
import json, sys
import topojson

ods_path, atlas_path, destino = sys.argv[1:4]
tol = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0002

atlas = json.load(open(atlas_path, encoding='utf-8'))
nombres = {g['id']: g['properties']['name'] for g in atlas['objects']['municipalities']['geometries']
           if str(g['id']).startswith('33')}

ods = json.load(open(ods_path, encoding='utf-8'))
vistos, feats = set(), []
for f in ods['features']:
    cod = f['properties']['mun_code']
    if cod in vistos:  # el conjunto repite algunos concejos con el nombre en asturiano
        continue
    vistos.add(cod)
    feats.append({'type': 'Feature', 'id': cod, 'properties': {'id': cod, 'nombre': nombres[cod]}, 'geometry': f['geometry']})
assert len(feats) == 78 and vistos == set(nombres), 'Faltan o sobran concejos'

topo = topojson.Topology({'type': 'FeatureCollection', 'features': feats}, object_name='concejos',
                         prequantize=1e6, toposimplify=tol, topology=True)
d = topo.to_dict()
for g in d['objects']['concejos']['geometries']:
    g['id'] = g['properties']['id']
    del g['properties']['id']
d.pop('bbox', None)

puntos = sum(len(a) for a in d['arcs'])
texto = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
with open(destino, 'w', encoding='utf-8') as f:
    f.write('/* Límites de los 78 concejos de Asturias (TopoJSON, objeto "concejos"; id = código INE).\n'
            ' * Geometría: Instituto Geográfico Nacional (CC BY 4.0), vía el conjunto georef-spain-municipio\n'
            ' * de OpenDataSoft (2022). Generado con un script y simplificado; no editar a mano. */\n')
    f.write('window.GeoAsturias = ' + texto + ';\n')
print(len(d['arcs']), 'arcos,', puntos, 'puntos,', len(texto) // 1024, 'KB')
