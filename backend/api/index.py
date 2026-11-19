"""Vercel Python entrypoint: exposes the FastAPI ASGI app as a single serverless function.

`vercel.json` rewrites every request to this function; FastAPI then routes on the original path.
"""

import sys
from pathlib import Path

# Make the sibling `app` package importable regardless of the function's working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

__all__ = ["app"]
