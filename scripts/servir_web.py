"""Arranca la web en local, sin internet, y la abre en el navegador.

    python scripts/servir_web.py            # http://127.0.0.1:8000/
    python scripts/servir_web.py --demo     # abre directamente el modo demo
    python scripts/servir_web.py --puerto 8080

Solo usa la biblioteca estándar de Python. Sirve «Afluencia Asturias/» sin caché,
para que tras ejecutar scripts/actualizar_datos_web.py baste con recargar.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import threading
import webbrowser
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "Afluencia Asturias"


class SinCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):  # sin ruido en la terminal
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--demo", action="store_true", help="abre la web en modo demo (?demo=1)")
    ap.add_argument("--sin-navegador", action="store_true")
    a = ap.parse_args()

    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", a.puerto), functools.partial(SinCache, directory=str(WEB)))
    url = f"http://127.0.0.1:{a.puerto}/" + ("?demo=1" if a.demo else "")
    print(f"Web en {url}  (Ctrl+C para parar)")
    if not a.sin_navegador:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
