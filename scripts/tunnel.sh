#!/bin/bash
# Gerenciador de túneis: ngrok (Streamlit, URL fixa) + cloudflared (API, Grafana)
# Uso: tunnel.sh {start|stop|url|status|restart}

set -u

CLOUDFLARED="$HOME/.local/bin/cloudflared"
NGROK_LOG="/tmp/ngrok-streamlit.log"
LOG_DIR="/tmp/cloudflared"

# ⚠️ EDITAR AQUI se mudar o domínio:
NGROK_DOMAIN="directory-ungodly-tipoff.ngrok-free.dev"

CLOUDFLARED_TUNNELS=(
  "api:8000"
  "grafana:3000"
)

start() {
  mkdir -p "$LOG_DIR"

  echo "═══════ SUBINDO TÚNEIS ═══════"

  # --- Streamlit via ngrok (URL fixa) ---
  if pgrep -f "ngrok.*8501" > /dev/null 2>&1; then
    echo "  = streamlit (ngrok) já rodando"
  else
    nohup ngrok http http://localhost:8501 \
      --url="https://$NGROK_DOMAIN" \
      > "$NGROK_LOG" 2>&1 &
    echo "  + streamlit (ngrok) iniciado"
  fi

  # --- API + Grafana via cloudflared (URL efêmera) ---
  for entry in "${CLOUDFLARED_TUNNELS[@]}"; do
    name="${entry%%:*}"
    port="${entry##*:}"
    log="$LOG_DIR/$name.log"

    if pgrep -f "cloudflared.*localhost:$port" > /dev/null 2>&1; then
      echo "  = $name (cloudflared) já rodando"
    else
      nohup "$CLOUDFLARED" tunnel --url "http://localhost:$port" > "$log" 2>&1 &
      echo "  + $name (cloudflared) iniciado"
    fi
  done

  echo
  echo "  ⏳ Aguardando conexões (15s)..."
  sleep 15
  url
}

stop() {
  echo "═══════ PARANDO TÚNEIS ═══════"

  if pkill -f "ngrok.*8501" 2>/dev/null; then
    echo "  ✅ streamlit (ngrok) parado"
  else
    echo "  (streamlit já parado)"
  fi

  if pkill -f "cloudflared.*localhost" 2>/dev/null; then
    echo "  ✅ cloudflared (api+grafana) parado"
  else
    echo "  (cloudflared já parado)"
  fi
}

url() {
  echo "═══════ URLs PÚBLICAS ═══════"
  echo "  streamlit (FIXA): https://$NGROK_DOMAIN"

  for entry in "${CLOUDFLARED_TUNNELS[@]}"; do
    name="${entry%%:*}"
    log="$LOG_DIR/$name.log"
    if [ -f "$log" ]; then
      u=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$log" | head -1)
      if [ -n "$u" ]; then
        echo "  $name:            $u"
      else
        echo "  $name:            (subindo...)"
      fi
    else
      echo "  $name:            (não iniciado)"
    fi
  done
}

status() {
  echo "═══════ STATUS ═══════"
  pgrep -f "ngrok.*8501" > /dev/null 2>&1 \
    && echo "  ✅ streamlit (ngrok) rodando" \
    || echo "  ❌ streamlit (ngrok) parado"

  for entry in "${CLOUDFLARED_TUNNELS[@]}"; do
    name="${entry%%:*}"
    port="${entry##*:}"
    pgrep -f "cloudflared.*localhost:$port" > /dev/null 2>&1 \
      && echo "  ✅ $name (cloudflared) rodando" \
      || echo "  ❌ $name (cloudflared) parado"
  done
}

case "${1:-}" in
  start)   start ;;
  stop)    stop ;;
  url)     url ;;
  status)  status ;;
  restart) stop; sleep 2; start ;;
  *)       echo "Uso: tunnel.sh {start|stop|url|status|restart}" ;;
esac
