# TalentUO

Repositorio compartido (privado) para datos y notas del proyecto.

## Estructura

- `data/raw/` – datos descargados tal cual de la fuente (no editar a mano).
- `data/manual/` – datos introducidos o corregidos manualmente.
- `notas/registro_descargas.md` – registro de cada descarga (fecha, fuente, archivo).
- `notas/decisiones_y_consideraciones.md` – decisiones importantes y límites de los datos.
- `scripts/` – `descarga_mitma.py` (descarga MITMA día a día, filtrada a Asturias, reanudable) y `verificar_mitma.py`.
- `logs/` – logs de las descargas (locales, no versionados).
- `data/raw/LEEME_datos_no_versionados.md` – qué ficheros pesados no se suben y cómo regenerarlos.

## Instalación

```bash
python -m venv .venv
.venv\Scriptsctivate        # Windows (PowerShell/cmd)
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

`requirements-lock.txt` contiene las versiones exactas probadas (Python 3.11):
`pip install -r requirements-lock.txt`.

Dependencias principales: pandas, requests, openpyxl, pyaxis, pySpainMobility.

## Estado (Fase 1: solo descarga en bruto)

Persona A (demanda y movilidad): MITMA viajes/pernoctaciones 2022–2025 (Asturias), estadísticos de día normal 2024, INE móviles, viviendas turísticas INE (semestral 2020–2026) y residuos COGERSA (**solo anual 2020–2021**, sin detalle mensual). Detalle, fechas reales y límites en `notas/registro_descargas.md`; lo no comprobado figura como **NO VERIFICADO**.
