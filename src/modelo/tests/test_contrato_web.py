"""Los JSON de salidas/ cumplen notas/contrato_web.md (si ya se ha ejecutado el modelo)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from util import SALIDAS  # noqa: E402
from validar_salidas import validar  # noqa: E402


@pytest.mark.skipif(not (SALIDAS / "predicciones.json").exists(), reason="ejecuta antes src/modelo/ejecutar.py")
def test_contrato_web():
    assert validar(SALIDAS) == []
