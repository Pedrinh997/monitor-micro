#!/usr/bin/env bash
# Sobe docker + compose, garante servicos nativos desligados,
# espera API e Prometheus, roda healthcheck.
# Uso: ./scripts/fixup.sh

set -e
cd "$(dirname "$0")/.."

sudo -v

if ! docker info > /dev/null 2>&1; then
  echo "subindo dockerd..."
  sudo systemctl start docker 2>/dev/null || sudo service docker start 2>/dev/null
  sleep 8
fi

for svc in postgresql redis-server redis; do
  if systemctl is-active --quiet "$svc" 2>/dev/null; then
    echo "parando $svc"
    sudo systemctl stop "$svc"
    sudo systemctl disable "$svc" > /dev/null 2>&1
  fi
done

docker compose down > /dev/null 2>&1 || true
docker compose up -d

for i in $(seq 1 30); do
  curl -sS -m 3 http://127.0.0.1:8000/ 2>/dev/null | grep -q CryptoPulse && break
  sleep 2
done

for i in $(seq 1 30); do
  curl -sS -m 3 http://127.0.0.1:9090/api/v1/targets 2>/dev/null | grep -q '"health":"up"' && break
  sleep 2
done

./scripts/healthcheck.sh 2>&1 | sed -n '/RESUMO/,$p'
