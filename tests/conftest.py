"""Fixtures compartilhadas para testes de integração."""
import os
import requests
import pytest

API_URL = os.getenv("API_URL_TEST", "http://localhost:8000")


@pytest.fixture(scope="session")
def api_url():
    return API_URL


@pytest.fixture(scope="session")
def token(api_url):
    """Cria usuário de teste e retorna JWT."""
    username = "pytest_user"
    password = "pytest_pass_123"

    # Registra (ignora se já existe)
    requests.post(
        f"{api_url}/auth/register",
        json={"username": username, "email": f"{username}@test.com", "password": password},
        timeout=5,
    )

    # Login
    r = requests.post(
        f"{api_url}/auth/token",
        data={"username": username, "password": password},
        timeout=5,
    )
    assert r.status_code == 200, f"Login falhou: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
