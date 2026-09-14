"""S9 — README must document the LAN two-device runbook."""

from pathlib import Path


README = Path(__file__).resolve().parents[3] / "README.md"


def test_readme_has_lan_two_device_runbook():
    text = README.read_text(encoding="utf-8")
    assert "## Deux appareils (même stack LAN)" in text
    assert "CORS_ORIGINS" in text
    assert "PUBLIC_WEB_BASE_URL" in text
    assert "NEXT_PUBLIC_API_URL" in text
    assert "docker compose up --build -d" in text
    assert "python -m app.seed" in text
    assert "/cuisine/login" in text
    assert "Feuille QR" in text or "feuille-qr" in text
