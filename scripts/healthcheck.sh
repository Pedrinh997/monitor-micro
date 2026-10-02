#!/usr/bin/env bash
# Healthcheck completo da stack CryptoPulse.
# Uso: ./scripts/healthcheck.sh
# Retorna 0 se tudo OK, 1 se algo falhou.

set -o pipefail
cd "$(dirname "$0")/.."

PASS=0
FAIL=0
WARN=0

ok()   { printf "  ✅ %s\n" "$1"; PASS=$((PASS+1)); }
bad()  { printf "  ❌ %s\n" "$1"; FAIL=$((FAIL+1)); }
warn() { printf "  ⚠️  %s\n" "$1"; WARN=$((WARN+1)); }
section() { printf "\n=== %s ===\n" "$1"; }

# --- 1. Containers ---
section "1. Containers"
EXPECTED="db redis api worker minio prometheus grafana mailpit"
RUNNING=$(sudo docker compose ps --status running --format '{{.Service}}' 2>/dev/null | sort)
for svc in $EXPECTED; do
  if echo "$RUNNING" | grep -qx "$svc"; then ok "$svc running"; else bad "$svc NÃO está running"; fi
done

# --- 2. API responde ---
section "2. API"
R=$(curl -sS -m 3 http://127.0.0.1:8000/ 2>/dev/null)
if echo "$R" | grep -q "CryptoPulse"; then ok "GET / → $R"; else bad "GET / falhou: $R"; fi

M=$(curl -sS -m 3 http://127.0.0.1:8000/metrics 2>/dev/null | head -1)
if echo "$M" | grep -q "^# HELP"; then ok "/metrics expondo"; else bad "/metrics vazio"; fi

# --- 3. Postgres ---
section "3. Postgres"
if sudo docker exec monitor_micro-db-1 pg_isready -U postgres >/dev/null 2>&1; then
  ok "pg_isready"
else
  bad "pg_isready falhou"
fi
TABLES=$(sudo docker exec monitor_micro-db-1 psql -U postgres -d crypto_pulse -tAc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null)
if [ "${TABLES:-0}" -gt 0 ]; then ok "$TABLES tabelas no schema public"; else bad "nenhuma tabela"; fi

# --- 4. Redis ---
section "4. Redis"
PONG=$(sudo docker exec monitor_micro-redis-1 redis-cli ping 2>/dev/null)
if [ "$PONG" = "PONG" ]; then ok "redis-cli ping → PONG"; else bad "redis não respondeu: $PONG"; fi

# --- 5. MinIO + bucket ---
section "5. MinIO / bucket price-history"
N_OBJ=$(sudo docker exec monitor_micro-minio-1 sh -c \
  "find /data/price-history -name '*.parquet' 2>/dev/null | wc -l")
if [ "${N_OBJ:-0}" -gt 0 ]; then ok "$N_OBJ parquets no bucket"; else warn "0 parquets no bucket"; fi

# --- 6. Worker / scheduler ---
section "6. Worker / scheduler"
WORKER_LOG=$(sudo docker logs monitor_micro-worker-1 --tail 50 2>&1 | grep -iE "scrape|task|job" | tail -1)
if [ -n "$WORKER_LOG" ]; then ok "worker logando: $WORKER_LOG"; else warn "worker sem log recente de task"; fi

# --- 7. Prometheus ---
section "7. Prometheus"
T=$(curl -sS -m 3 http://localhost:9090/api/v1/targets 2>/dev/null)
if echo "$T" | grep -q '"health":"up"'; then
  N_UP=$(echo "$T" | grep -o '"health":"up"' | wc -l)
  ok "$N_UP target(s) up"
else
  bad "nenhum target up"
fi

# --- 8. Grafana ---
section "8. Grafana"
H=$(curl -sS -o /dev/null -w "%{http_code}" http://localhost:3000/api/health 2>/dev/null)
if [ "$H" = "200" ]; then ok "Grafana health 200"; else bad "Grafana retornou $H"; fi
DS=$(curl -sS -u admin:admin http://localhost:3000/api/datasources 2>/dev/null | grep -c '"type"')
if [ "${DS:-0}" -ge 1 ]; then ok "$DS datasource(s) configurado(s)"; else warn "0 datasources"; fi

# --- 9. Mailpit ---
section "9. Mailpit"
MP=$(curl -sS -o /dev/null -w "%{http_code}" http://localhost:8025/ 2>/dev/null)
if [ "$MP" = "200" ]; then ok "Mailpit UI responde"; else warn "Mailpit retornou $MP"; fi

# --- 10. Analytics (cache + query real) ---
section "10. Analytics"
STATS=$(sudo docker exec monitor_micro-api-1 python3 -c "
from app.analytics.duckdb_analysis import get_price_stats
import json
print(json.dumps(get_price_stats()))
" 2>/dev/null)
if echo "$STATS" | grep -q '"count"'; then
  COUNT=$(echo "$STATS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null)
  ok "get_price_stats → count=$COUNT"
else
  bad "get_price_stats falhou: $STATS"
fi

CACHE_OK=$(sudo docker exec monitor_micro-api-1 sh -c \
  "test -f /tmp/duckdb_parquet_cache/.etags.json && echo yes || echo no")
if [ "$CACHE_OK" = "yes" ]; then ok "cache populado (.etags.json presente)"; else warn "cache vazio"; fi

# --- 11. Testes ---
section "11. Suíte de testes"
T_RESULT=$(sudo docker exec monitor_micro-api-1 \
  pytest tests/test_smoke.py tests/test_integration.py -q 2>&1 | tail -1)
if echo "$T_RESULT" | grep -qE "[0-9]+ passed"; then
  ok "$T_RESULT"
else
  bad "testes falharam: $T_RESULT"
fi

# --- Resumo ---
section "RESUMO"
printf "  PASS=%d  WARN=%d  FAIL=%d\n" "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
  printf "  ❌ stack com problemas\n"
  exit 1
elif [ "$WARN" -gt 0 ]; then
  printf "  ⚠️  stack OK com avisos\n"
  exit 0
else
  printf "  ✅ stack 100%% saudável\n"
  exit 0
fi
