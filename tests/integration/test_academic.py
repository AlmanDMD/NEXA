"""Atalho na raiz do repositório para `pytest tests/integration/test_academic.py`."""

import importlib.util
from pathlib import Path
import sys

_ROOT_DIR = Path(__file__).resolve().parents[2]
_BACKEND_DIR = _ROOT_DIR / "backend"
_TARGET_FILE = _BACKEND_DIR / "tests" / "integration" / "test_academic.py"

if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

_spec = importlib.util.spec_from_file_location("nexa_academic_integration_suite", _TARGET_FILE)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Não foi possível carregar a suíte de integração em {_TARGET_FILE}.")

_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

for _attr_name, _attr_value in vars(_module).items():
    if not _attr_name.startswith("__"):
        globals()[_attr_name] = _attr_value
