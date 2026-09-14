#!/usr/bin/env bash
# Print LAN demo env hints for S9 (phone + tablet on the same Compose stack).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -n "${LAN_IP:-}" ]]; then
  lan_ip="${LAN_IP}"
else
  lan_ip="$(ipconfig getifaddr en0 2>/dev/null || true)"
  if [[ -z "${lan_ip}" ]]; then
    lan_ip="$(ipconfig getifaddr en1 2>/dev/null || true)"
  fi
  if [[ -z "${lan_ip}" ]]; then
    lan_ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  fi
fi

if [[ -z "${lan_ip}" ]]; then
  echo "Could not detect LAN IP."
  echo "Example: LAN_IP=192.168.1.10 $0"
  echo "Or on macOS: ipconfig getifaddr en0"
  exit 1
fi

echo "# Detected LAN IP: ${lan_ip}"
echo "# Write these into .env (repo root), then: docker compose up --build -d"
echo
cat <<EOF
NEXT_PUBLIC_API_URL=http://${lan_ip}:8000
PUBLIC_WEB_BASE_URL=http://${lan_ip}:3000
CORS_ORIGINS=http://localhost:3000,http://${lan_ip}:3000
EOF
echo
echo "# Phone menu:  http://${lan_ip}:3000/t/<token>"
echo "# Cuisine:     http://${lan_ip}:3000/cuisine/login"
echo "# Admin:       http://${lan_ip}:3000/admin/login"
echo "# After boot:  cd apps/api && .venv/bin/alembic upgrade head && .venv/bin/python -m app.seed"
