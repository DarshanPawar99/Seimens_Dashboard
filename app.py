"""
app.py

Entry point for the LPG Stock Tracker Dashboard.

Responsibilities (only):
  1. Create the Dash app instance
  2. Attach the layout (from layout.py)
  3. Register callbacks (from callbacks.py)
  4. Expose `server` for Gunicorn

Architecture — clean dependency graph (no circular imports):

  config  ──────────────────────────────────────────────┐
  logger  ──────────────────────────────────────────┐   │
  stock_logic ── aggregations ──┐                   │   │
  data_loader ──────────────────┤── state ──┬── layout ─┤
  components ───────────────────┘           └── callbacks┘
                                                    │
                                                   app  ← gunicorn
"""

from __future__ import annotations

from dash import Dash

import callbacks  # noqa: F401  — registers all @callback decorators
from config import APP_TITLE
from layout import build_layout

app: Dash = Dash(
    __name__,
    title=APP_TITLE,
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

server = app.server  # exposed for Gunicorn
app.layout = build_layout()


if __name__ == "__main__":
    app.run(debug=True)
