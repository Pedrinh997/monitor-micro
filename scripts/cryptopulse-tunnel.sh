#!/usr/bin/env bash
pkill -f "cloudflared tunnel" 2>/dev/null; sleep 2
[ -f ~/.cloudflared/config.yml ] && mv ~/.cloudflared/config.yml ~/.cloudflared/config.yml.disable
nohup cloudflared tunnel --url http://localhost:8000 > /tmp/cloudflared.log 2>&1 &
disown
for i in {1..30}; do
  URL=$(grep -oE 'https://[a-z-]+\.trycloudflare\.com' /tmp/cloudflared.log 2>/dev/null | head -1)
  [ -n "$URL" ] && break
  sleep 2
done
[ -z "$URL" ] && { echo "❌ Túnel não subiu"; tail -20 /tmp/cloudflared.log; exit 1; }
for i in {1..15}; do
  R=$(curl -sS -m 5 "$URL/" 2>/dev/null)
  echo "$R" | grep -q "CryptoPulse" && { echo "✅ $URL"; exit 0; }
  sleep 2
done
echo "URL: $URL (ainda não respondeu)"
