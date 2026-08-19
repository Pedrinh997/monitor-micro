# 📊 Monitor Micro – Scraping com Filas (Redis + RQ)

Sistema de monitoramento de preços usando arquitetura de microsserviços com filas.
A API publica tarefas no Redis, um Worker processa em background e os dados são salvos no PostgreSQL.

![Python Version](https://img.shields.io/badge/python-3.14-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🧠 Arquitetura

- **API (FastAPI):** Recebe requisições e publica tarefas na fila.
- **Worker (RQ):** Processa as tarefas de scraping em background.
- **Redis:** Gerencia a fila de tarefas.
- **PostgreSQL:** Armazena produtos e histórico de preços.

## 📋 Pré-requisitos

- Docker e Docker Compose instalados.
- WSL2 (para Windows) ou Linux/Mac.
- Git (para clonar).

## 🚀 Como rodar

```bash
# 1. Clone o repositório
git clone https://github.com/Pedrinh997/monitor-micro.git
cd monitor-micro

# 2. Configure as variáveis de ambiente (opcional, já há valores padrão)
cp .env.example .env

# 3. Suba os containers com Docker Compose
docker compose up --build
```

Acesse: `http://localhost:8000/docs` para ver a documentação interativa da API.

## 📌 Endpoints

- `POST /scrape/` – Envia uma URL para ser raspada (publica tarefa na fila).
- `GET /products/` – Lista todos os produtos salvos.
- `GET /products/{id}/prices/` – Histórico de preços de um produto.

## 🧪 Exemplo de uso

1. Acesse `http://localhost:8000/docs`.
2. Clique em `POST /scrape/` → `Try it out`.
3. Insira uma URL de produto do Mercado Livre (ex: `https://produto.mercadolivre.com.br/MLB-1234567890`).
4. Execute e veja o worker processar (logs no terminal).
5. Consulte `GET /products/` para listar os produtos raspados.

## 📁 Estrutura do projeto

```
monitor_micro/
├── app/
│   ├── database.py      # Conexão com PostgreSQL (async)
│   ├── models.py        # Tabelas Product e PriceHistory
│   ├── schemas.py       # Validação de entrada/saída
│   ├── scraper.py       # Lógica de scraping assíncrono
│   ├── tasks.py         # Funções que o worker executa
│   ├── worker.py        # Script do worker (consome a fila)
│   └── main.py          # API FastAPI
├── docker-compose.yml   # Orquestração dos serviços
├── Dockerfile           # Imagem da API e Worker
├── requirements.txt     # Dependências Python
├── .env                 # Variáveis de ambiente (não commitado)
├── .env.example         # Exemplo de variáveis
└── README.md
```

## 🛠️ Tecnologias utilizadas

- **FastAPI** – Framework web assíncrono.
- **SQLAlchemy** – ORM para PostgreSQL.
- **asyncpg** – Driver assíncrono para PostgreSQL.
- **Redis** – Broker de mensagens.
- **RQ (Redis Queue)** – Biblioteca de filas.
- **Docker Compose** – Orquestração de containers.

## 📝 Licença

MIT

## 👤 Autor

Pedrinh997
