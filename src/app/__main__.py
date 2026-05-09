# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Run the WSGI app via ``python -m app``.

Useful when the wheel is installed without the `app` console script (e.g.
in stripped-down container images) — `python -m app` still spins up the
Flask dev server bound to PORT.
"""

import os

from app.factory import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
    )
