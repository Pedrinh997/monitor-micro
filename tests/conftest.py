"""Fixtures compartilhadas para testes.

- Fixtures de integração (api_url, token, auth_headers)
- Skip automático se API não estiver no ar (para CI)
"""
import os
import requests
import pytest

API_URL = os.getenv("API_URL_TEST", "http://localhost:8000")


def _api_is_up(url: str, timeout: float = 2.0) -> bool:
    try:
        r = requests.get(f"{url}/", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def api_url():
    """URL base da API. Skipa se API não estiver no ar."""
    if not _api_is_up(API_URL):
        pytest.skip(f"API não responde em {API_URL} — testes de integração skipados")
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
