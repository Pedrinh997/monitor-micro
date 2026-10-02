# 🎬 DEMO AO VIVO — Monitor Micro

Monitoramento de criptomoedas com ML. Pipeline completo: CoinGecko → Postgres → MinIO → ML.

## Ligar tudo em 1 comando

    scripts/demo.sh

Esse script:
1. Sobe o dockerd + containers
2. Espera Postgres + API
3. Sobe os túneis (ngrok + cloudflared)
4. Imprime as URLs públicas

**Login:** `teste` / `123456`

## O que mostrar em 5 minutos

### 1. Dashboard (30s)
Abre a URL do Streamlit. Faz login.
- Cards de analytics (amostras, média, min, max)
- 28 moedas com preço atual (💵) e data (📅)

### 2. Histórico + ML (1 min)
Clica em **📈 Ver** em qualquer moeda.
- Gráfico de evolução (30 dias)
- Botão **⬇️ Exportar CSV**
- Previsão ARIMA dos próximos 7 dias (`arima(1,0,0)`)

### 3. Swagger da API (1 min)
Abre `URL_API/docs`. Endpoints:
- `POST /scrape/` — cadastra moeda e enfileira
- `GET /products/{id}/forecast` — previsão ARIMA
- `GET /analytics/stats` — DuckDB sobre Parquet

### 4. Alertas de email (30s)
Mailpit captura emails em dev:
- UI: http://localhost:8025
- API: `curl http://localhost:8025/api/v1/messages`
- Setar `target_price` no Bitcoin → próximo scrape dispara alerta

### 5. Grafana (1 min)
`URL_GRAFANA/login` (admin/admin). Dashboard com métricas em tempo real.

### 6. Scheduler + logs (30s)

    docker exec monitor_micro-db-1 psql -U postgres -d postgres -c \
      "SELECT id, next_run_time FROM apscheduler_jobs;"

Mostra 2 jobs persistentes: scrape 24h, minio 6h.

## Arquitetura (30s)

    CoinGecko → Postgres → Parquet/MinIO → DuckDB → FastAPI → Streamlit
                                                     ↑
                                                 ARIMA forecast
                                                     ↓
                                            Mailpit / SMTP (alertas)

10 containers Docker. 28 moedas, ~2500 amostras de série temporal real.

## Comandos durante a demo

    scripts/tunnel.sh url              # URLs atuais
    docker logs -f monitor_micro-worker-1
    docker logs -f monitor_micro-api-1

## Parar depois

    scripts/tunnel.sh stop
    docker compose down

## Se algo der errado

**API não responde:**

    docker logs monitor_micro-api-1 --tail 50

**Docker parado:**

    sudo nohup dockerd > /tmp/docker.log 2>&1 &
    sleep 8
    docker compose up -d

**Email não envia:**

    docker logs monitor_micro-worker-1 | grep -iE "ALERTA|Email"
    curl http://localhost:8025/api/v1/messages
