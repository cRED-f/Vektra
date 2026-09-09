"""Entry point — run the Vektra API server."""

from __future__ import annotations

import uvicorn

from server.api.app import create_app
from server.core.config import get_settings


def main():
    settings = get_settings()
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.gateway_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
