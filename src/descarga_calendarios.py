"""Descarga en bruto los calendarios (festivos, vacaciones escolares y acceso a los Lagos).

Reanudable: no vuelve a descargar un fichero que ya existe y es válido.
Respetuoso con los servidores: User-Agent identificable y pausa entre peticiones.
No modifica los PDF; el texto extraído (pdftotext) se guarda aparte como .txt.

Uso (desde la raíz del repositorio):
    python src/descarga_calendarios.py            # descarga lo que falte y verifica
    python src/descarga_calendarios.py --verifica # solo verifica lo ya descargado
"""
import argparse
import csv
import os
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "data" / "raw" / "calendario"
SALIDA_VERIFICACION = RAIZ / "data" / "raw" / "calendario" / "_verificacion.csv"
# Contacto del User-Agent: desde la variable de entorno TALENTUO_CONTACTO (no se
# versiona ningún dato personal).
UA = f"TalentUO-Hackathon-2026 (academic; contact {os.environ.get('TALENTUO_CONTACTO', 'equipo TalentUO')})"
PAUSA = 2.0
MIN_HTML = 1000  # bytes: una pagina real es mucho mayor; las de error miden decenas de bytes
MENSAJES_ERROR = ("host no configurado", "access denied", "forbidden", "page not found", "404 not found",
                  "service unavailable", "bad gateway", "error 404", "no encontrada")

BOPA = "https://miprincipado.asturias.es/bopa"
BOE = "https://www.boe.es/boe/dias"
EDUCASTUR = "https://www.educastur.es/documents/34868/39577"

# (fichero, url, oficial, nota)
MANIFEST = [
    # --- BOE: fiestas laborales (DG Trabajo) ---
    ("boe_fiestas_2022.pdf", f"{BOE}/2021/10/21/pdfs/BOE-A-2021-17113.pdf", True, "Res. 14-oct-2021, BOE-A-2021-17113"),
    ("boe_fiestas_2023.pdf", f"{BOE}/2022/10/14/pdfs/BOE-A-2022-16755.pdf", True, "Res. 7-oct-2022, BOE-A-2022-16755"),
    ("boe_fiestas_2024.pdf", f"{BOE}/2023/10/27/pdfs/BOE-A-2023-22014.pdf", True, "Res. 23-oct-2023, BOE-A-2023-22014"),
    ("boe_fiestas_2025.pdf", f"{BOE}/2024/10/18/pdfs/BOE-A-2024-21316.pdf", True, "Res. 15-oct-2024, BOE-A-2024-21316"),
    ("boe_fiestas_2026.pdf", f"{BOE}/2025/10/28/pdfs/BOE-A-2025-21667.pdf", True, "Res. 17-oct-2025, BOE-A-2025-21667"),
    ("boe_fiestas_2027.pdf", f"{BOE}/2026/10/13/pdfs/BOE-A-2026-21254.pdf", True, "Res. 8-oct-2026, BOE-A-2026-21254"),
    # --- BOPA: fiestas locales de Asturias ---
    ("bopa_fiestas_locales_2022.pdf", f"{BOPA}/2021/05/05/2021-03949.pdf", True, "Res. 14-abr-2021, BOPA 5-may-2021"),
    ("bopa_fiestas_locales_2023.pdf", f"{BOPA}/2022/05/23/2022-03495.pdf", True, "Res. 5-may-2022, BOPA 23-may-2022"),
    ("bopa_fiestas_locales_2024.pdf", f"{BOPA}/2023/04/27/2023-03229.pdf", True, "Res. 12-abr-2023, BOPA 27-abr-2023"),
    ("bopa_fiestas_locales_2025.pdf", f"{BOPA}/2024/05/30/2024-04382.pdf", True, "Res. 16-may-2024, BOPA 30-may-2024"),
    ("bopa_fiestas_locales_2026.pdf", "https://miprincipado.asturias.es/documents/d/guest/2025-04744", True, "Res. 3-jun-2025, BOPA 16-jun-2025"),
    ("bopa_fiestas_locales_2027.pdf", f"{BOPA}/2026/06/10/2026-04656.pdf", True, "Res. 22-may-2026, BOPA 10-jun-2026"),
    # --- Asturias: calendario escolar ---
    ("bopa_calendario_escolar_2022-23.pdf", f"{BOPA}/2022/04/25/2022-02717.pdf", True, "Res. 5-abr-2022"),
    ("bopa_calendario_escolar_2023-24.pdf", f"{BOPA}/2023/05/10/2023-03661.pdf", True, "Res. 27-abr-2023"),
    ("bopa_calendario_escolar_2024-25.pdf", f"{BOPA}/2024/05/30/2024-04412.pdf", True, "Res. 15-may-2024"),
    ("bopa_calendario_escolar_2025-26.pdf", f"{BOPA}/2025/05/21/2025-03852.pdf", True, "Res. 8-may-2025"),
    ("bopa_calendario_escolar_2026-27.pdf", f"{BOPA}/2026/06/01/2026-04361.pdf", True, "Res. 13-may-2026"),
    ("bopa_modif_calendario_escolar_2021-22_FP.pdf", "https://www.asturias.es/bopa/2021/09/06/2021-08142.pdf", True, "Res. 27-ago-2021 (organización FP); su disposición adicional única modifica el calendario escolar 2021-22 (FP presencial). Descargado desde www.asturias.es/bopa porque miprincipado.asturias.es dejó de responder"),
    ("educastur_calendario_escolar_2021-22_grafico.pdf", "https://www.educastur.es/documents/34868/262513/2021-06-calendario-21-22-vertical.pdf/42001202-fb54-1f40-5200-7530348cbbd5?t=1623323628050", True, "Calendario gráfico Educastur 2021-22; ALTERNATIVA al BOPA de 1-jun-2021 (no obtenido)"),
    ("juridicas_res_calendario_escolar_asturias_2021-22.html", "https://noticias.juridicas.com/base_datos/CCAA/699208-r-educacion-5-may-2021-ca-asturias-calendario-escolar-para-el-curso-2021-2022.html", False, "NO OFICIAL: copia del texto de la Res. 5-may-2021 (BOPA 1-jun-2021); el BOPA original no se obtuvo. NOTA 2026-10-15: la URL devuelve una pagina de error; la validacion HTML la rechaza"),
    ("educastur_festivos_locales_23-24.pdf", f"{EDUCASTUR}/2023-10-calendario-escolar-festivos-locales-23-24.pdf/899da8ad-dbb0-9ac8-5710-ed2583d25ea1?t=1696423648123", True, "Días sustitutivos de fiestas locales (no es el calendario escolar)"),
    ("educastur_festivos_locales_24-25.pdf", f"{EDUCASTUR}/2024-10-calendario-festivos-locales-24-25.pdf/3ed01499-b74e-406c-95fb-fb9a85a6fd02?t=1730207988146", True, "Días sustitutivos de fiestas locales (no es el calendario escolar)"),
    ("educastur_festivos_locales_25-26.pdf", f"{EDUCASTUR}/2025-09-calendario-festivos-locales-25-26.pdf", True, "Días sustitutivos de fiestas locales (no es el calendario escolar)"),
    ("educastur_festivos_locales_26-27.pdf", "https://www.educastur.es/documents/34868/39577/2026-09-calendario-festivos-locales-26-27.pdf/e869aa46-32e6-04ba-e030-e43d159891c5?t=1789720241394", True, "Días sustitutivos de fiestas locales (no es el calendario escolar)"),
    ("educastur_calendario_escolar_indice.html", "https://www.educastur.es/es/calendario-escolar", True, "Índice de calendarios en Educastur"),
    # --- Castilla y León: calendario escolar ---
    ("cyl_calendario_escolar_2021-22.pdf", "https://bocyl.jcyl.es/boletines/2021/05/05/pdf/BOCYL-D-05052021-21.pdf", True, "Orden EDU/501/2021, BOCYL 5-may-2021"),
    ("cyl_calendario_escolar_2022-23.pdf", "https://www.educa.jcyl.es/es/calendario-escolar.ficheros/1546291-BOCYL-D-10062022-26.pdf", True, "Orden EDU/624/2022, BOCYL 10-jun-2022"),
    ("cyl_calendario_escolar_2023-24.pdf", "https://www.educa.jcyl.es/es/calendario-escolar.ficheros/1619130-BOCYL-D-09052023-20.pdf", True, "Orden EDU/578/2023, BOCYL 9-may-2023"),
    ("cyl_calendario_escolar_2024-25.pdf", "https://educa.jcyl.es/en/calendario-escolar.files/1705097-BOCYL-D-24052024-16.pdf", True, "Orden EDU/463/2024, BOCYL 24-may-2024"),
    ("cyl_calendario_escolar_2025-26.pdf", "https://www.educa.jcyl.es/es/informacion/calendario-escolar-2025-2026.ficheros/1893070-BOCYL-D-29052025-27.pdf", True, "Orden EDU/527/2025, BOCYL 29-may-2025"),
    ("cyl_calendario_escolar_2026-27.pdf", "https://www.educa.jcyl.es/es/calendario-escolar-e1c54.ficheros/1893084-BOCYL-D-28052026-101-28.pdf", True, "Orden EDU/478/2026, BOCYL 28-may-2026"),
    # --- Madrid: calendario escolar ---
    ("madrid_calendario_escolar_2021-22.pdf", "https://www.bocm.es/boletin/CM_Orden_BOCM/2021/06/24/BOCM-20210624-24.PDF", True, "Orden 1734/2021, BOCM 24-jun-2021"),
    ("madrid_calendario_escolar_2022-23.pdf", "https://www.bocm.es/boletin/CM_Orden_BOCM/2022/05/23/BOCM-20220523-26.PDF", True, "Orden 1210/2022, BOCM 23-may-2022"),
    ("madrid_calendario_escolar_2023-24.pdf", "https://www.bocm.es/boletin/CM_Orden_BOCM/2023/06/12/BOCM-20230612-21.PDF", True, "Orden 1952/2023, BOCM 12-jun-2023"),
    ("madrid_calendario_escolar_2024-25.pdf", "https://www.bocm.es/boletin/CM_Orden_BOCM/2024/04/19/BOCM-20240419-18.PDF", True, "Orden 1177/2024, BOCM 19-abr-2024"),
    ("madrid_calendario_escolar_2025-26.pdf", "https://www.bocm.es/boletin/CM_Orden_BOCM/2025/05/13/BOCM-20250513-17.PDF", True, "Orden 1476/2025, BOCM 13-may-2025"),
    ("madrid_calendario_escolar_2026-27.pdf", "https://www.comunidad.madrid/docs/2026-06/bocm-131-04-06-2026_orden-2034-calendario-escolar-curso-2026-27.pdf", True, "Orden 2034/2026, BOCM 4-jun-2026 (copia en comunidad.madrid)"),
    # --- Lagos de Covadonga: DGT (BOE) ---
    ("boe_dgt_medidas_trafico_2022.pdf", f"{BOE}/2022/01/25/pdfs/BOE-A-2022-1125.pdf", True, "DGT, medidas especiales de tráfico 2022; tabla Asturias/Covadonga CO-04"),
    ("boe_dgt_medidas_trafico_2023.pdf", f"{BOE}/2023/01/27/pdfs/BOE-A-2023-2159.pdf", True, "DGT, medidas especiales de tráfico 2023"),
    ("boe_dgt_medidas_trafico_2024.pdf", f"{BOE}/2024/01/31/pdfs/BOE-A-2024-1773.pdf", True, "DGT, medidas especiales de tráfico 2024"),
    ("boe_dgt_medidas_trafico_2025.pdf", f"{BOE}/2025/01/25/pdfs/BOE-A-2025-1329.pdf", True, "DGT, medidas especiales de tráfico 2025"),
    ("boe_dgt_medidas_trafico_2026.pdf", f"{BOE}/2026/01/20/pdfs/BOE-A-2026-1255.pdf", True, "DGT, medidas especiales de tráfico 2026"),
    ("turismocangasdeonis_acceso_lagos_2026.html", "https://www.turismocangasdeonis.com/acceso-a-lagos.html", False, "Web del Ayuntamiento/turismo de Cangas de Onís (informativa)"),
    ("turismocangasdeonis_folleto_acceso_lagos.pdf", "https://www.turismocangasdeonis.com/folletos/acceso-a-lagos.pdf", False, "Folleto informativo; PDF de imagen (sin texto)"),
    ("pnpe_cortes_trafico_co4.html", "https://parquenacionalpicoseuropa.es/cortes-de-trafico-en-la-carretera-co-4-de-covadonga-a-los-lagos/", True, "Parque Nacional Picos de Europa: cortes CO-4 (oficial, obras/avisos)"),
    ("pnpe_regulacion_accesos_lagos.html", "https://parquenacionalpicoseuropa.es/regulacion-de-accesos-a-los-lagos-de-covadonga-en-transporte-publico/", True, "Parque Nacional Picos de Europa: regulación de accesos"),
    # --- Prensa (NO OFICIAL) ---
    ("prensa_elfielato_suspension_lagos_agosto2025.html", "https://www.elfielato.es/articulo/comarca-picos-europa/suspendidos-fuego-transporte-publico-lagos-funicular-bulnes/20250816204207083473.html", False, "Prensa; suspensión transporte por incendio 16-ago-2025"),
    ("prensa_vozpopuli_evacuacion_lagos_agosto2025.html", "https://www.vozpopuli.com/sucesos/evacuacion-en-los-lagos-de-covadonga-por-los-incendios-en-picos-de-europa-las-llamas-estan-mas-cerca.html", False, "Prensa; evacuación Lagos por incendio ago-2025"),
    ("prensa_telecinco_cierre_co4_agosto2023.html", "https://www.telecinco.es/noticias/sociedad/20230803/asturias-decreta-cierre-carretera-lagos-covadonga-coches-autocaravanas-particulares_18_010191467.html", False, "Prensa; cierre CO-4 a particulares 3-ago-2023"),
    ("prensa_elfielato_balance_plan_lagos_2025.html", "https://www.elfielato.es/articulo/cangas-de-onis/35000-usuarios-menos-plan-transporte-lagos-covadonga/20251213105442088961.html", False, "Prensa; balance plan transporte 2025 (182.683 viajeros)"),
    ("prensa_eldiariodeasturias_balance_plan_lagos_2025.html", "https://eldiariodeasturias.com/asturias/el-plan-especial-de-transporte-a-los-lagos-de-cuadonga-covadonga-movilizo-mas-de-182-000-viajeros-este-ano/", False, "Prensa; balance plan transporte 2025"),
]


def valida_html(contenido):
    """None si parece una pagina real; si no, el motivo. Misma idea que la cabecera %PDF de los PDF."""
    if len(contenido) < MIN_HTML:
        return "error_html_demasiado_corto"
    inicio = contenido[:1500].decode("utf-8", errors="ignore").lower()
    if any(m in inicio for m in MENSAJES_ERROR):
        return "error_html_mensaje_de_error"
    return None


def descarga(sesion, nombre, url):
    destino = DESTINO / nombre
    if destino.exists() and destino.stat().st_size > 0:
        return "ya_existia"
    r = None
    for intento in range(3):
        time.sleep(PAUSA * (intento + 1))
        try:
            r = sesion.get(url, timeout=90)
            break
        except requests.RequestException as e:
            err = type(e).__name__
    if r is None:
        return f"error_conexion_{err}"
    if r.status_code != 200:
        return f"error_http_{r.status_code}"
    es_pdf = nombre.endswith(".pdf")
    if es_pdf and not r.content.startswith(b"%PDF"):
        return "error_no_es_pdf"
    if nombre.endswith((".html", ".htm")):
        motivo = valida_html(r.content)
        if motivo:
            return motivo
    destino.write_bytes(r.content)
    return "descargado"


def paginas(pdf):
    if not shutil.which("pdfinfo"):
        return ""
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout or ""
    for linea in out.splitlines():
        if linea.startswith("Pages:"):
            return linea.split()[1]
    return ""


def extrae_texto(pdf):
    """Guarda el texto como .txt junto al PDF; devuelve nº de caracteres con letras."""
    if not shutil.which("pdftotext"):
        return ""
    txt = pdf.with_suffix(".txt")
    subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), str(txt)], capture_output=True)
    return sum(c.isalpha() for c in txt.read_text(encoding="utf-8", errors="ignore")) if txt.exists() else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verifica", action="store_true", help="no descarga; solo verifica")
    args = ap.parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)
    sesion = requests.Session()
    sesion.headers["User-Agent"] = UA
    filas = []
    for nombre, url, oficial, nota in MANIFEST:
        estado = "no_descargado" if args.verifica else descarga(sesion, nombre, url)
        ruta = DESTINO / nombre
        if estado == "no_descargado" and ruta.exists():
            estado = "ya_existia"
        npag = letras = ""
        if ruta.suffix == ".pdf" and ruta.exists():
            npag, letras = paginas(ruta), extrae_texto(ruta)
        filas.append([nombre, estado, "oficial" if oficial else "NO OFICIAL", npag, letras, url, nota, date.today().isoformat()])
        print(f"{estado:18} {nombre}  pags={npag} letras={letras}")
    with open(SALIDA_VERIFICACION, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fichero", "estado", "fuente", "paginas", "letras_texto", "url", "nota", "fecha"])
        w.writerows(filas)


if __name__ == "__main__":
    sys.exit(main())
