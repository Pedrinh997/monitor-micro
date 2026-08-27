import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

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
