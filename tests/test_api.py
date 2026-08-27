import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"  # <-- DRIVER ASSÍNCRONO

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app import models  # registro das tabelas
from app.main import app

# --- Configura o banco de teste (síncrono para os testes, mas a aplicação usa async) ---
# A aplicação usa create_async_engine, então precisamos substituir a engine global.
# Vamos recriar a engine com aioqlite para os testes e substituir a dependência.
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker

# Cria a engine assíncrona com SQLite
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
AsyncTestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Substitui a dependência get_db para usar a sessão assíncrona de teste
async def override_get_db():
    async with AsyncTestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Cria as tabelas (precisa ser executado dentro de um evento loop)
import asyncio
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init_db())

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Monitor Micro - API com filas"}

@patch("app.main.queue")
def test_scrape_endpoint(mock_queue):
    mock_queue.enqueue.return_value = MagicMock(id="fake_job_id")
    response = client.post("/scrape/", json={"url": "https://produto.mercadolivre.com.br/MLB-1234567890"})
    assert response.status_code == 200
    assert "product_id" in response.json()
    assert "job_id" in response.json()
