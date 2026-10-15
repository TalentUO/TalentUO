"""Descarga ficheros PC-Axis (.px) del SADEI a data/raw/ (Fase 1: solo bruto).

Los enlaces "Ver fichero .px" de la web (?f=...) devuelven HTML y el enlace directo
redirige a un host que no resuelve; el .px real se obtiene del PxWeb de SADEI:
seleccionar todos los valores -> Continuar -> botón "Archivo de PC-Axis". Si la tabla supera
100 000 celdas se baja en partes (_parteN.px) troceando la variable más larga (sin modificar).
Uso: python scripts/descarga_sadei.py [nombre_local.px ...]
"""
import sys
from html.parser import HTMLParser
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
PXWEB = "https://www.sadei.es/sadei/pxweb/es/01/"
UA = {"User-Agent": "Mozilla/5.0"}
MAX_CELDAS = 100_000  # límite del PxWeb de SADEI por consulta
BTN_CONTINUAR = "ctl00$ContentPlaceHolderMain$VariableSelector1$VariableSelector1$ButtonViewTable"
BTN_PX = "ctl00$ctl00$ContentPlaceHolderMain$CommandBar1$CommandBar1$ShortcutFileFileTypePX"
FICHEROS = {  # nombre local -> ruta PxWeb (carpeta/código)
    "sadei_receptor_nacional_concejos.px": "11__04__07/11040706.px",
    "sadei_receptor_extranjero_concejos.px": "11__04__07/11040704.px",
    "sadei_rentabilidad.px": "99__04__08__04/9904080406.px",
    "sadei_eoh_viajeros.px": "99__04__08__04/9904080402.px",
    "sadei_plazas_concejos.px": "11__02__02/11020202.px",
    "sadei_apartamentos_concejos.px": "11__02__04/11020418.px",
    "padron_concejos.px": "02__02__02/02020202.px",  # evolución de la población (censo/padrón/RRP), concejos
}


class _Form(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden, self.listas, self._sel = [], {}, None

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "input" and a.get("type") == "hidden":
            self.hidden.append((a["name"], a.get("value", "")))
        elif tag == "select":
            self._sel = a.get("name")
            if self._sel and self._sel.endswith("ValuesListBox"):
                self.listas[self._sel] = []
        elif tag == "option" and self._sel in self.listas:
            self.listas[self._sel].append(a.get("value"))

    def handle_endtag(self, tag):
        if tag == "select":
            self._sel = None


def _parse(html):
    p = _Form()
    p.feed(html)
    return p


def _lotes(listas):
    """Trozos de selección que caben en el límite de celdas; parte la variable más larga."""
    total = 1
    for v in listas.values():
        total *= len(v)
    if total <= MAX_CELDAS:
        return [listas]
    mayor = max(listas, key=lambda k: len(listas[k]))
    resto = total // len(listas[mayor])
    n = MAX_CELDAS // resto
    return [{**listas, mayor: listas[mayor][i:i + n]} for i in range(0, len(listas[mayor]), n)]


def descargar(ruta):
    """Devuelve una lista de (contenido, variables) — varias si la tabla excede el límite."""
    url = PXWEB + ruta
    return [_descargar_lote(url, lote) for lote in _lotes(_parse(requests.get(url, headers=UA, timeout=60).text).listas)]


def _descargar_lote(url, lote):
    s = requests.Session()
    s.headers.update(UA)
    p = _parse(s.get(url, timeout=60).text)
    datos = list(p.hidden)
    for nombre, valores in lote.items():
        datos += [(nombre, v) for v in valores]
    datos.append((BTN_CONTINUAR, "Continuar"))
    r = s.post(url, data=datos, timeout=120)
    p = _parse(r.text)
    datos = list(p.hidden) + [(BTN_PX + ".x", "5"), (BTN_PX + ".y", "5")]
    r2 = s.post(r.url, data=datos, timeout=120)
    if "attachment" not in r2.headers.get("content-disposition", ""):
        raise RuntimeError(f"no devolvió un fichero: {r2.status_code} {r2.headers.get('content-type')}")
    return r2.content, {k: len(v) for k, v in p.listas.items()}


if __name__ == "__main__":
    for nombre in sys.argv[1:] or FICHEROS:
        try:
            partes = descargar(FICHEROS[nombre])
        except Exception as e:  # se registra y se sigue con el resto
            print(nombre, "ERROR", e)
            continue
        for i, (contenido, _) in enumerate(partes, 1):
            destino = nombre if len(partes) == 1 else nombre.replace(".px", f"_parte{i}.px")
            (RAW / destino).write_bytes(contenido)
            print(destino, len(contenido), "bytes")
