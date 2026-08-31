# 📊 Monitor Micro – Price Monitoring with Microservices

**Monitor Micro** is a complete price monitoring system built with a microservices architecture.  
It uses **FastAPI** for the API, **Redis + RQ** for task queues, **PostgreSQL** for persistence, and **Prometheus + Grafana** for observability.

[![Python Version](https://img.shields.io/badge/python-3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](#)

## 🚀 Tech Stack
- **API:** FastAPI (async)
- **Queue:** Redis + RQ (Redis Queue)
- **Database:** PostgreSQL + SQLAlchemy (async)
- **Worker:** Python background worker
- **Frontend:** Streamlit (optional)
- **Observability:** Prometheus + Grafana
- **Containerization:** Docker + Docker Compose
- **Testing:** Pytest + pytest-asyncio

## ✨ Features
- 🔐 User authentication (JWT) – coming soon
- 🛒 Add products via Mercado Livre URL
- 📉 Price history tracking
- ⏰ Scheduled price updates (every 30 minutes)
- 🔔 Alerts when price drops below target
- 📊 Real-time metrics with Prometheus
- 📈 Dashboards with Grafana
- 🧪 Unit and integration tests

## 📦 How to Run Locally

Prerequisites: Python 3.14+, Docker and Docker Compose (optional, for PostgreSQL and Redis), Redis (local or via Docker), PostgreSQL (local or via Docker).

1. Clone the repository: git clone https://github.com/Pedrinh997/monitor-micro.git cd monitor-micro
2. Create and activate virtual environment: python -m venv venv source venv/bin/activate (Windows: venv\Scripts\Activate)
3. Install dependencies: pip install -r requirements.txt
4. Start PostgreSQL and Redis (via Docker): docker compose up -d db redis. Or, if you have them installed locally: sudo service postgresql start sudo service redis-server start
5. (Optional) Set up environment variables: Create a .env file with DATABASE_URL=postgresql+asyncpg://postgres:123456@localhost:5432/postgres and REDIS_HOST=localhost.
6. Run the API and Worker: Terminal 1 (API): uvicorn app.main:app --host 0.0.0.0 --port 8000. Terminal 2 (Worker): python -m app.worker.
7. Access: API Swagger at http://localhost:8000/docs, Frontend (Streamlit) at http://localhost:8501 (if running).

## 🐳 Running with Docker Compose
To run all services (API, Worker, Redis, PostgreSQL, Frontend) with a single command: docker compose up --build. Access: API at http://localhost:8000, Swagger at http://localhost:8000/docs, Frontend at http://localhost:8501.

## 🌐 Live Demo (via ngrok)
If you want to test the API publicly without deploying permanently: Run the demo script: ./run_demo.sh. In another terminal, get the public URL: curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'. Access the Swagger at: https://<your-ngrok-url>.ngrok-free.app/docs. Note: The ngrok URL is temporary and changes each time you restart the tunnel.

## 📁 Project Structure
monitor_micro/ ├── app/ │ ├── __init__.py │ ├── main.py # FastAPI application │ ├── database.py # SQLAlchemy async setup │ ├── models.py # SQLAlchemy models │ ├── schemas.py # Pydantic schemas │ ├── scraper.py # Product scraping logic │ ├── tasks.py # RQ task functions │ ├── worker.py # Worker entrypoint │ ├── logger_config.py # Loguru configuration │ └── metrics.py # Prometheus metrics ├── tests/ # Pytest tests ├── docker-compose.yml # Docker Compose for all services ├── Dockerfile # Docker image for API/Worker/Frontend ├── requirements.txt # Python dependencies ├── run_demo.sh # Quick demo script with ngrok └── README.md

## 🛠️ Technologies Used
- FastAPI – modern async web framework
- SQLAlchemy – ORM with async support
- asyncpg – async PostgreSQL driver
- Redis – message broker
- RQ – simple task queues
- Prometheus – metrics collection
- Grafana – metrics visualization
- Streamlit – simple frontend for demos
- Pytest – testing framework
- Docker Compose – container orchestration

## 📝 License
This project is licensed under the MIT License – see the LICENSE file for details.

## 👤 Author
Pedrinh997 (GitHub: https://github.com/Pedrinh997, LinkedIn: https://linkedin.com/in/your-profile)

## ⭐ Acknowledgments
Inspired by real-world price monitoring needs. Built as a portfolio project to demonstrate microservices, async Python, and observability.
