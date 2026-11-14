"""Shared helpers for Garhwali Language Lab pipeline and research scripts.

Commands in ``scripts/`` import it directly (``python scripts/<name>.py`` puts
``scripts/`` on the import path), and ``pip install -e .`` makes it importable
from anywhere else, such as notebooks.
Keep it small and dependency-free: standard library only.
"""
