"""Comprueba los .px de SADEI en data/raw/: título, Cangas de Onís/Llanes y rango temporal."""
import re, sys
from pathlib import Path
from pyaxis import pyaxis  # la función parse vive en el submódulo

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
for f in sorted(RAW.glob("sadei_*.px")) if len(sys.argv) == 1 else map(Path, sys.argv[1:]):
    txt = f.read_bytes().decode("cp1252", errors="replace")
    m = re.search(r'^TITLE="(.*?)";', txt, re.M) or re.search(r'^DESCRIPTION="(.*?)";', txt, re.M)
    tit = m.group(1) if m else "(sin TITLE) " + txt[:80]
    for enc in ("ISO-8859-1", "utf-8", "cp1252"):
        try:
            px = pyaxis.parse(str(f), encoding=enc); break
        except Exception as e:
            px = None; err = e
    if px is None:
        print(f.name, "ERROR pyaxis", err); continue
    df = px["DATA"]; cols = [c for c in df.columns]
    texto = " ".join(map(str, df[[c for c in cols if c != df.columns[-1]]].stack().unique()))
    tiempo = [c for c in cols if re.search(r"(?i)fecha|a.o|per.odo|mes|trimestre", c)]
    rango = {c: (sorted(map(str, df[c].unique()))[0], sorted(map(str, df[c].unique()))[-1], df[c].nunique()) for c in tiempo}
    print(f"{f.name} | enc={enc} | filas={len(df)} | cols={cols[:-1]}\n   TITLE={tit}\n   Cangas de Onís={'Cangas de On' in texto} Llanes={'Llanes' in texto} | tiempo={rango}")
