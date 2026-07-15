"""Backend test bootstrap: put `backend/` on sys.path so tests import modules by their FULL
namespace path (`modules.ingest.src.services`) — module-local `src` aliases collide across
modules in one pytest session, full paths never do. Also what makes `app.*` importable."""

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
