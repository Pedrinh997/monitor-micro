#!/usr/bin/env bash
# scripts/deploy_vps.sh
# Executa NA VPS. Idempotente.
# Uso: ./scripts/deploy_vps.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "❌ .env não existe. Copie .env.production.example e preencha."
  exit 1
fi

echo "==> git pull"
git pull --ff-only

echo "==> build"
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

echo "==> up"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "==> aguardando API"
for i in {1..30}; do
  if curl -sS -m 2 http://127.0.0.1:8000/ >/dev/null 2>&1; then
    echo "✅ API respondeu após ${i} tentativas"
    break
  fi
  sleep 2
done

echo "==> status"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
