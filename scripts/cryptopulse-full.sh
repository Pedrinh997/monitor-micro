#!/usr/bin/env bash
# Sobe API + Frontend, cada um em seu quick tunnel.

set -e

echo "=== Matando túneis antigos ==="
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 2

echo "=== Subindo túnel da API (8000) ==="
nohup cloudflared tunnel --url http://localhost:8000 > /tmp/cloudflared-api.log 2>&1 &
disown

echo "=== Subindo túnel do Frontend (8501) ==="
nohup cloudflared tunnel --url http://localhost:8501 > /tmp/cloudflared-frontend.log 2>&1 &
disown

echo "=== Aguardando URLs ==="
API_URL=""
FRONT_URL=""
for i in {1..30}; do
  [ -z "$API_URL" ]   && API_URL=$(grep -oE 'https://[a-z-]+\.trycloudflare\.com' /tmp/cloudflared-api.log 2>/dev/null | head -1)
  [ -z "$FRONT_URL" ] && FRONT_URL=$(grep -oE 'https://[a-z-]+\.trycloudflare\.com' /tmp/cloudflared-frontend.log 2>/dev/null | head -1)
  [ -n "$API_URL" ] && [ -n "$FRONT_URL" ] && break
  sleep 2
done

[ -z "$API_URL" ]   && { echo "❌ API falhou";      tail -20 /tmp/cloudflared-api.log;      exit 1; }
[ -z "$FRONT_URL" ] && { echo "❌ Frontend falhou"; tail -20 /tmp/cloudflared-frontend.log; exit 1; }

echo "=== Testando API ==="
for i in {1..15}; do
  R=$(curl -sS -m 5 "$API_URL/" 2>/dev/null)
  echo "$R" | grep -q "CryptoPulse" && break
  sleep 2
done

echo "=== Atualizando API_URL no .env ==="
cd /mnt/d/monitor_micro
if grep -q "^API_URL=" .env 2>/dev/null; then
  sed -i "s|^API_URL=.*|API_URL=$API_URL|" .env
else
  echo "API_URL=$API_URL" >> .env
fi

echo "=== Recriando frontend com nova URL ==="
sudo docker compose up -d --force-recreate frontend 2>&1 | tail -2

echo ""
echo "═══════════════════════════════════════════════════"
echo "  API:      $API_URL"
echo "  Frontend: $FRONT_URL"
echo "═══════════════════════════════════════════════════"
echo ""
echo "⚠️  Se o frontend travar no browser, é limitação"
echo "    do WebSocket em quick tunnel. Não tem fix."
