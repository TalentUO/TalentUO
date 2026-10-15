# TalentUO

Repositorio compartido (privado) para datos y notas del proyecto.

## Estructura

- `data/raw/` – datos descargados tal cual de la fuente (no editar a mano).
- `data/manual/` – datos introducidos o corregidos manualmente.
- `notas/registro_descargas.md` – registro de cada descarga (fecha, fuente, archivo).
- `notas/registro_senales.md`, `notas/notas_senales.md`, `notas/decisiones_senales.md` – señales adelantadas (Wikipedia, Google Trends, OAPN): registro, hallazgos por fuente y decisiones pendientes. Script: `src/descarga_senales.py`.

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell/cmd)
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

`requirements-lock.txt` contiene las versiones exactas probadas (Python 3.11):
`pip install -r requirements-lock.txt`.

Dependencias principales: pandas, requests, openpyxl, pyaxis, pySpainMobility.
