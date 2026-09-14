from __future__ import annotations

import os


DEFAULT_CORS_ORIGINS = "http://localhost:3000"


def parse_cors_origins(raw: str | None = None) -> list[str]:
    value = raw if raw is not None else os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in value.split(",") if origin.strip()]
