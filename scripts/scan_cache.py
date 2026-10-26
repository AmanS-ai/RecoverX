#!/usr/bin/env python3
"""Convenience wrapper for the RecoverX scan command."""

import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))
    sys.argv = [str(project_root / "recoverx.py"), "scan", *sys.argv[1:]]
    runpy.run_path(str(project_root / "recoverx.py"), run_name="__main__")
