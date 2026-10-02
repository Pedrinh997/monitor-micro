# 📊 CryptoPulse

Sistema de monitoramento de preços de criptomoedas com arquitetura de microserviços.
Coleta via API REST → persistência → data lake → analytics → previsão ML → dashboard.

## 🎯 O que faz

- Cadastro e autenticação de usuários (JWT)
- Cadastro de moedas por ID da CoinGecko (`bitcoin`, `ethereum`, ...)
- Worker assíncrono (RQ) que puxa 30 dias de histórico em série temporal
- Histórico completo de preços no PostgreSQL
- Exportação **incremental** para Parquet no MinIO (data lake)
- Scheduler persistente (APScheduler + jobstore no Postgres)
- Analytics com DuckDB lendo os Parquets direto do MinIO
- Previsão de preços: ARIMA (após agregação diária), com fallback baseline
- Dashboard Streamlit com histórico + previsão + export CSV
- Alertas de email quando o preço cai abaixo do alvo (Mailpit em dev, SMTP em prod)
- Observabilidade: Prometheus (métricas) + Grafana (dashboards)

## 🏗️ Arquitetura

    [Streamlit] ←→ [FastAPI] ←→ [PostgreSQL]
                       ↓
              [Redis + Worker RQ]
                       ↓
              [CoinGecko API REST]
                       ↓
              [MinIO (Parquet data lake)]
                       ↓
              [DuckDB (analytics/ML)]
                       ↓
              [Prometheus] → [Grafana]
                       ↓
              [Mailpit (dev) / SMTP (prod)]

## 🚀 Stack

- **API:** FastAPI (async) + Uvicorn
- **Fila:** Redis + RQ
- **DB:** PostgreSQL 15 + SQLAlchemy (async + sync via psycopg2)
- **Data lake:** MinIO (S3-compatible), imagem `coollabsio/minio`
- **Analytics:** DuckDB (lê Parquets do MinIO)
- **ML:** pandas + statsmodels (ARIMA) com fallback baseline
- **Scheduler:** APScheduler com jobstore no Postgres
- **Frontend:** Streamlit + Plotly
- **Email (dev):** Mailpit (SMTP local sem auth)
- **Observabilidade:** Prometheus + Grafana

## 🔌 Fonte de dados

**CoinGecko API pública** — sem auth, sem cartão:
- `/coins/{id}` → metadata (nome, símbolo)
- `/coins/{id}/market_chart?days=30&interval=daily` → 30 amostras de preço
- Retry exponencial em 429 (rate limit keyless ~30 req/min)

## 🚀 Como rodar

### Subir a stack

    sudo -v
    sudo setsid nohup dockerd > /tmp/docker.log 2>&1 < /dev/null &
    disown
    sleep 15
    sudo docker compose up -d

### Popular com moedas

    # Login
    TOKEN=$(curl -sS -X POST http://127.0.0.1:8000/auth/token \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=teste&password=123456" | jq -r .access_token)

    # Enviar 5 moedas por lote, esperar worker drenar (30s-3min cada)
    for coin in bitcoin ethereum solana cardano dogecoin; do
      curl -sS -X POST http://127.0.0.1:8000/scrape/ \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"url\":\"$coin\"}" | jq -c '{product_id, reused}'
      sleep 2
    done

### Interfaces

- **Streamlit:** http://localhost:8501 (login `teste` / `123456`)
- **API Swagger:** http://localhost:8000/docs
- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Mailpit UI:** http://localhost:8025
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)

## 🧪 Testes

    sudo docker exec monitor_micro-api-1 pytest -v tests/test_integration.py

Cobre: root, auth obrigatório, listagem, analytics, forecast, duplicata (409), metrics.
**7 testes**, batendo na API real.

## 📦 Estrutura

    app/
      main.py              FastAPI + scheduler startup + tabelas auto
      models.py            User, Product, PriceHistory, SchedulerState
      schemas.py           Pydantic
      database.py          async (asyncpg) + sync (psycopg2)
      tasks.py             worker RQ: CoinGecko com retry 429
      scheduler.py         APScheduler + upload incremental MinIO
      email_utils.py       Mailpit (dev) ou SMTP TLS (prod)
      ml/forecast.py       ARIMA com agregação diária + fallback baseline
      analytics/           DuckDB sobre Parquet
      routes/auth.py       JWT
    tests/
      conftest.py          fixtures (token, api_url)
      test_integration.py  7 testes batendo na API real
    app_ui.py              Streamlit
    docker-compose.yml     9 serviços (api, worker, db, redis, minio,
                           mailpit, frontend, prometheus, grafana)
    DEMO.md                Runbook de demonstração

## 🔧 Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste:

    DATABASE_URL=postgresql+asyncpg://postgres:123456@db:5432/postgres
    REDIS_HOST=redis
    REDIS_PORT=6379
    MINIO_ENDPOINT=minio:9000
    MINIO_ACCESS_KEY=minioadmin
    MINIO_SECRET_KEY=minioadmin

    # Email — dev: Mailpit sem auth; prod: SMTP com TLS
    SMTP_HOST=mailpit
    SMTP_PORT=1025
    SMTP_USER=
    SMTP_PASSWORD=
    EMAIL_FROM=alerts@monitor.micro

    # JWT
    SECRET_KEY=change-me-in-production

## ⚠️ Notas

- **Tabelas criadas automaticamente** no startup da API (idempotente).
- **Scheduler roda 24h/6h** (scrape/minio) — evita estourar rate limit do CoinGecko.
- **Upload incremental** ao MinIO via tabela `scheduler_state` (último id enviado).
- **Emails em dev** ficam no Mailpit (http://localhost:8025), não saem pra internet.
