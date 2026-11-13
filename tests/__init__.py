"""Garhwali Language Lab test suite.

Tests import pipeline commands as plain modules, so this puts their folders on
the import path once for the whole suite. Run everything from the repository
root with ``python -m unittest``.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _folder in ("examples", "scripts/archive", "scripts/experiments", "scripts"):
    _path = str(_ROOT / _folder)
    if _path not in sys.path:
        sys.path.insert(0, _path)
