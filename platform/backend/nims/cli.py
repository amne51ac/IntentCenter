"""CLI entrypoint for running the ASGI app with Uvicorn (production or --reload)."""

from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8080"))
    reload = os.environ.get("NIMS_RELOAD", "true").lower() in ("1", "true", "yes")

    uvicorn.run(
        "nims.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
