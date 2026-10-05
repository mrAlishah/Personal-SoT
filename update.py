#!/usr/bin/env python3
"""One-command local entry point for Personal-SoT Safe Update."""
import os
from pathlib import Path

from system.update.cli import main


if __name__ == "__main__":
    root = Path(os.path.abspath(__file__)).parent
    raise SystemExit(main(default_root=root))
