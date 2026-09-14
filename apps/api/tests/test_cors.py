from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.cors import parse_cors_origins
from app.main import app as fastapi_app


def test_health_allows_web_origin(client):
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_parse_cors_origins_splits_and_strips():
    assert parse_cors_origins("http://localhost:3000, http://192.168.1.10:3000") == [
        "http://localhost:3000",
        "http://192.168.1.10:3000",
    ]


def test_health_allows_lan_origin_from_env(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://192.168.1.10:3000",
    )
    # Re-import / rebuild app middleware with new env — call helper used by main.
    from app.cors import parse_cors_origins

    origins = parse_cors_origins()
    assert "http://192.168.1.10:3000" in origins

    # Mount a fresh app with those origins to assert header behaviour.
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    lan_app = FastAPI()
    lan_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @lan_app.get("/health")
    def health():
        return {"status": "ok"}

    client = TestClient(lan_app)
    response = client.get(
        "/health", headers={"Origin": "http://192.168.1.10:3000"}
    )
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://192.168.1.10:3000"
    )
