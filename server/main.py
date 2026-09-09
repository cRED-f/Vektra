"""Entry point — run the Vektra API server.

uvicorn imports `app` from this module (e.g. `uvicorn server.main:app`),
so it must be a module-level object rather than created inside main().
"""

from __future__ import annotations

import uvicorn

from server.api.app import create_app
from server.core.config import get_settings

# Module-level app object — imported by uvicorn/gunicorn as `server.main:app`.
app = create_app()


def main():
    settings = get_settings()
    uvicorn.run(
        "server.main:app",
        host=settings.gateway_host,
        port=settings.gateway_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
