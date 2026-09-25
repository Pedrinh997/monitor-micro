# 🎬 DEMO AO VIVO — Monitor Micro

## Como ligar tudo em 1 comando

    ~/demo.sh

Esse script:
1. Sobe o dockerd + containers
2. Espera Postgres + API
3. Sobe os túneis (ngrok + cloudflared)
4. Imprime as URLs públicas

**Login:** `teste` / `123456`

---

## O que mostrar em 5 minutos

### 1. Dashboard público (30s)
Abre a URL do Streamlit. Faz login.
Mostra:
- Cards de analytics (amostras, média, min, max)
- Lista de produtos com preço atual

### 2. Histórico de um produto (1 min)
Clica em **📈 Ver** em qualquer produto.
Mostra:
- Gráfico de evolução do preço
- Botão de exportar CSV
- Card de previsão (baseline/ARIMA)

### 3. Swagger da API (1 min)
Abre `URL_API/docs`.
Mostra os endpoints documentados automaticamente pelo FastAPI.

### 4. Grafana (1 min)
Abre `URL_GRAFANA/login` (admin/admin).
Mostra o dashboard "Monitor Micro — API" com métricas em tempo real.

### 5. Scheduler (30s)
    docker exec monitor_micro-db-1 psql -U postgres -d postgres -c \
      "SELECT id, next_run_time FROM apscheduler_jobs;"

Mostra os 2 jobs (upload MinIO 1h, scrape 6h) com persistência no Postgres.

### 6. Logs em tempo real (30s)
    docker logs -f monitor_micro-worker-1

Mostra o worker processando jobs do RQ.

---

## Arquitetura (para explicar em 30s)

    Scraper → Postgres → Parquet/MinIO → DuckDB → API → Streamlit
                                                ↑
                                          ML forecast

8 containers Docker. Postgres, Redis, MinIO, Prometheus e Grafana.

---

## Comandos durante a demo

Ver URLs atuais:

    ~/tunnel.sh url

Parar tudo depois:

    ~/tunnel.sh stop
    docker compose down

Logs em tempo real:

    docker logs -f monitor_micro-api-1
    docker logs -f monitor_micro-worker-1

---

## Se algo der errado

**API não responde:**

    docker logs monitor_micro-api-1 --tail 50

**URL pública não abre:**

    ~/tunnel.sh restart

**Docker parado:**

    sudo nohup dockerd > /tmp/docker.log 2>&1 &
    sleep 8
    docker compose up -d
