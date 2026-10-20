"""Auditoria calendarios: abre cada PDF, cuenta paginas, busca anio/comunidad/identificador en el texto."""
import glob, os, re, subprocess
import pypdf
D = "data/raw/calendario/"
reg = open("notas/fuentes/calendarios/registro_calendarios.md", encoding="utf-8").read()
filas = {}
for l in reg.splitlines():
    c = [x.strip() for x in l.strip().strip("|").split("|")]
    if len(c) >= 7 and c[0].endswith((".pdf", ".html")):
        filas[c[0]] = c
def txt(f):
    try: return subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", D+f, "-"], capture_output=True, text=True, encoding="utf-8").stdout
    except Exception: return ""
for f in sorted(glob.glob(D+"*.pdf")):
    n = os.path.basename(f)
    try: r = pypdf.PdfReader(f); pg = len(r.pages)
    except Exception as e: print(n, "NO ABRE", e); continue
    t = txt(n); letras = len(re.sub(r"\s", "", t))
    decl = filas.get(n, [None]*7)
    pdecl = decl[5] if len(decl) > 5 else None
    # identificador esperado en registro
    ident = None
    m = re.search(r"(BOE-A-\d{4}-\d+)", decl[1] if decl[1] else "") or re.search(r"/(\d{4}-\d{5})", decl[3] if decl[3] else "")
    flag = []
    if pdecl and pdecl.isdigit() and int(pdecl) != pg: flag.append(f"PAGS decl={pdecl} real={pg}")
    if not pdecl and n in filas: flag.append("sin pags declaradas")
    if n not in filas: flag.append("NO EN REGISTRO")
    if letras < 200: flag.append(f"IMAGEN/SIN TEXTO letras={letras}")
    # identificador en el texto
    idt = None
    if m:
        idt = m.group(1)
        if idt not in t.replace("\n", " ") and idt.replace("-", "") not in t: flag.append(f"id {idt} no aparece en texto")
    cab = re.sub(r"\s+", " ", t[:260])
    print(f"{n} pags={pg} letras={letras} {' | '.join(flag)}\n    {cab[:230]}")
print("\nHTML:")
for f in sorted(glob.glob(D+"*.html")):
    s = os.path.getsize(f); h = open(f, encoding="utf-8", errors="replace").read()
    tit = re.search(r"<title[^>]*>(.*?)</title>", h, re.S | re.I)
    print(os.path.basename(f), s, (tit.group(1).strip()[:100] if tit else h[:60].replace("\n"," ")))
