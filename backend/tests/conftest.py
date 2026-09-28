"""Test configuration.

Adds the backend/ directory to sys.path so `from app.study_plan import ...`
works without requiring an installed package.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
