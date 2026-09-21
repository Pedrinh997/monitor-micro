# 📊 Monitor Micro

Sistema de monitoramento de preços com arquitetura de microserviços.
Scraping → persistência → data lake → analytics → previsão ML → dashboard.

## 🎯 O que faz

- Cadastro e autenticação de usuários (JWT)
- Cadastro de produtos por URL (scraping via `books.toscrape.com`)
- Worker assíncrono (RQ) que extrai título e preço
- Histórico completo de preços no PostgreSQL
- Exportação automática para Parquet no MinIO (data lake)
- Scheduler persistente (APScheduler + jobstore no Postgres)
- Analytics com DuckDB lendo os Parquets direto do MinIO
- Previsão de preços: baseline agora, ARIMA automático em >= 10 amostras
- Dashboard Streamlit com histórico + previsão
- Observabilidade: Prometheus (métricas) + Grafana (dashboards provisionados)

## 🏗️ Arquitetura

    [Frontend Streamlit] ←→ [API FastAPI] ←→ [PostgreSQL]
                                  ↓
                          [Redis + Worker RQ]
                                  ↓
                       [Scraper books.toscrape]
                                  ↓
                       [MinIO (Parquet data lake)]
                                  ↓
                       [DuckDB (analytics/ML)]
                                  ↓
                     [Prometheus] → [Grafana]

## 🚀 Stack

- **API:** FastAPI (async) + Uvicorn
- **Fila:** Redis + RQ
- **DB:** PostgreSQL 15 + SQLAlchemy (async + sync)
- **Data lake:** MinIO (S3-compatible)
- **Analytics:** DuckDB (lê Parquets)
- **ML:** pandas + statsmodels (ARIMA) com fallback baseline
- **Scheduler:** APScheduler + SQLAlchemyJobStore
- **Frontend:** Streamlit + Plotly
- **Observabilidade:** Prometheus + Grafana (provisionado via arquivos)
- **Container:** Docker + Docker Compose
- **Testes:** Pytest

## 📋 Pré-requisitos

- Docker + Docker Compose
- (Opcional) `jq` para inspecionar JSON no terminal

## 🏃 Como rodar

Todo o stack em um comando:

    docker compose up -d

Aguarde ~30s (Postgres + initdb). Depois rode uma vez:

    docker exec monitor_micro-api-1 python create_tables.py

Verifique:

    curl http://127.0.0.1:8000/

Resposta esperada: `{"message":"Monitor Micro - API com filas"}`

### Acessos

| Serviço | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Frontend | http://localhost:8501 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) |
| MinIO Console | http://localhost:9001 (minioadmin/minioadmin) |

## 🔌 Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/register` | Cadastrar usuário |
| POST | `/auth/token` | Obter JWT |
| POST | `/scrape/` | Enfileirar scraping de uma URL |
| GET | `/products/` | Listar produtos do usuário |
| GET | `/products/{id}/prices/` | Histórico de preços |
| GET | `/products/{id}/forecast?days=7` | Previsão (baseline / ARIMA) |
| GET | `/analytics/stats?product_id=` | Média/min/máx via DuckDB |
| GET | `/analytics/variation/{id}` | Variação % entre 2 últimas amostras |
| GET | `/metrics` | Métricas Prometheus |

Todas as rotas exceto `auth/*` e `/` exigem `Authorization: Bearer <token>`.

## 📁 Estrutura do projeto

    monitor_micro/
    ├── app/
    │   ├── main.py               FastAPI app + endpoints
    │   ├── database.py           SQLAlchemy async + sync engines
    │   ├── models.py             ORM (User, Product, PriceHistory)
    │   ├── schemas.py            Pydantic schemas
    │   ├── auth.py               JWT + password hashing
    │   ├── routes/auth.py        Rotas de autenticação
    │   ├── tasks.py              RQ task: scrape + salvar
    │   ├── worker.py             Entrypoint do worker
    │   ├── scheduler.py          APScheduler (upload 1h / scrape 6h)
    │   ├── metrics.py            Contadores Prometheus
    │   ├── logger_config.py      Loguru
    │   ├── email_utils.py        Alertas por e-mail
    │   ├── telegram_utils.py     Alertas via Telegram
    │   ├── analytics/
    │   │   └── duckdb_analysis.py  Stats + variação via DuckDB
    │   └── ml/
    │       └── forecast.py       Baseline + ARIMA (auto-switch)
    ├── grafana/provisioning/     Datasource + dashboards
    ├── prometheus/               prometheus.yml
    ├── tests/                    Pytest
    ├── docker-compose.yml        8 serviços
    ├── Dockerfile
    ├── requirements.txt
    ├── create_tables.py          Cria schema no Postgres
    ├── app_ui.py                 Streamlit frontend
    ├── RUNBOOK.md                Comandos do dia-a-dia
    ├── BOOT.md                   Como subir após desligar o PC
    └── DEPLOY_VPS.md             Roteiro completo para VPS

## 🧪 Testando manualmente

### 1. Registrar usuário

    curl -X POST http://127.0.0.1:8000/auth/register \
      -H "Content-Type: application/json" \
      -d '{"username":"teste","email":"teste@teste.com","password":"123456"}'

### 2. Obter token

    TOKEN=$(curl -sS -X POST http://127.0.0.1:8000/auth/token \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=teste&password=123456" | jq -r .access_token)

### 3. Cadastrar produto

    curl -X POST http://127.0.0.1:8000/scrape/ \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"url":"https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"}'

### 4. Ver previsão

    curl -H "Authorization: Bearer $TOKEN" \
      http://127.0.0.1:8000/products/1/forecast

## ⏰ Automação

O scheduler roda **dentro da API** (APScheduler com jobstore persistente):

- **A cada 1 hora:** exporta `price_history` para Parquet no MinIO
- **A cada 6 horas:** re-scrape de todos os produtos → novos preços

Os jobs sobrevivem a `docker compose restart` e a desligar/ligar o PC
(ficam salvos no Postgres). Ao subir, jobs atrasados rodam na hora.

## 📊 Analytics + ML

**DuckDB** lê os Parquets direto do MinIO. Endpoints:

- `/analytics/stats` — preço médio, mínimo, máximo, contagem
- `/analytics/variation/{id}` — variação absoluta e percentual

**Previsão** (`app/ml/forecast.py`):

- < 10 amostras: baseline (último preço repetido)
- >= 10 amostras: ARIMA(1,0,0)
- Troca automática, sem mudar endpoint ou dashboard

## 🐳 Serviços no docker-compose

| Serviço | Porta | O quê |
|---|---|---|
| api | 8000 | FastAPI |
| worker | — | RQ worker |
| db | 5432 | PostgreSQL |
| redis | 6379 | Broker RQ |
| minio | 9000/9001 | S3 + console |
| frontend | 8501 | Streamlit |
| prometheus | 9090 | Métricas |
| grafana | 3000 | Dashboards |

## 📚 Documentação adicional

- [`RUNBOOK.md`](RUNBOOK.md) — comandos do dia-a-dia
- [`BOOT.md`](BOOT.md) — como subir após desligar o PC
- [`DEPLOY_VPS.md`](DEPLOY_VPS.md) — deploy em VPS com Nginx + HTTPS

## 🛣️ Roadmap

- [x] Fase 0 — Infra + Git + secrets
- [x] Fase 1 — Pipeline de dados (scrape → DB → MinIO)
- [x] Fase 2 — Analytics (DuckDB + endpoints + dashboard)
- [x] Fase 3 — ML (baseline + ARIMA preparado)
- [x] Fase 5 — Prometheus + Grafana provisionado
- [ ] Fase 4 — Deploy em VPS (roteiro em DEPLOY_VPS.md)
- [ ] ARIMA em produção (automático ao atingir 10 amostras/produto)

## 📝 Licença

MIT

## 👤 Autor

Pedrinh997 — https://github.com/Pedrinh997
