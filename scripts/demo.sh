#!/bin/bash
# Demo ao vivo do Monitor Micro — 1 comando
# Uso: ~/demo.sh

set -u

cd /mnt/d/monitor_micro

echo "═══════════════════════════════════════════════"
echo "  🎬 DEMO AO VIVO — MONITOR MICRO"
echo "═══════════════════════════════════════════════"

# 0. Garante que o dockerd está de pé
if ! sudo docker info > /dev/null 2>&1; then
  echo
  echo "[0/4] Docker daemon morto — subindo..."
  sudo nohup dockerd > /tmp/docker.log 2>&1 &
  sleep 12
  if ! sudo docker info > /dev/null 2>&1; then
    echo "❌ dockerd não subiu. Log: /tmp/docker.log"
    exit 1
  fi
  echo "     ✅ dockerd OK"
fi

# 1. Sobe stack
echo
echo "[1/4] Subindo containers..."
sudo docker compose up -d > /tmp/demo-up.log 2>&1 || true

# 2. Confirma API (com flag de falha real)
echo "[2/4] Verificando API..."
API_OK=0
for i in {1..20}; do
  R=$(curl -sS -m 2 http://127.0.0.1:8000/ 2>/dev/null)
  if [ -n "$R" ]; then
    echo "     ✅ API: $R"
    API_OK=1
    break
  fi
  sleep 2
done

if [ "$API_OK" -ne 1 ]; then
  echo
  echo "❌ API NÃO RESPONDEU após 40s. Abortando demo."
  echo
  echo "Diagnóstico:"
  echo "  sudo docker ps"
  echo "  sudo docker logs monitor_micro-api-1 --tail 50"
  exit 1
fi

# 3. Sobe túneis
echo "[3/4] Subindo túneis públicos..."
~/tunnel.sh start > /tmp/demo-tunnel.log 2>&1 || true
sleep 3

# 4. Mostra URLs
echo "[4/4] URLs públicas:"
echo
~/tunnel.sh url | sed 's/^/     /'
echo
echo "═══════════════════════════════════════════════"
echo "  ✅ PRONTO PARA DEMONSTRAR"
echo "═══════════════════════════════════════════════"
echo
echo "  Login: teste / 123456"
echo
