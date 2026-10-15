#!/usr/bin/env bash
set -e

if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker não está rodando. Suba primeiro:"
  echo "   sudo setsid nohup dockerd > /tmp/docker.log 2>&1 < /dev/null & disown; sleep 15"
  exit 1
fi

pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 2

nohup cloudflared tunnel --url http://localhost:8000 > /tmp/cloudflared-api.log 2>&1 &
disown
nohup cloudflared tunnel --url http://localhost:8501 > /tmp/cloudflared-frontend.log 2>&1 &
disown

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

cd /mnt/d/monitor_micro
if grep -q "^API_URL=" .env; then
  sed -i "s|^API_URL=.*|API_URL=$API_URL|" .env
else
  echo "API_URL=$API_URL" >> .env
fi

echo ""
echo "  API:      $API_URL"
echo "  Frontend: $FRONT_URL"
