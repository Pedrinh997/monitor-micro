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
    """Cria usuário de teste e retorna JWT.

    Retry: a API pode estar em warm-up após restart do container
    (cache DuckDB sendo populado, scheduler iniciando). Sem retry,
    os 4 testes que usam este fixture falham com ConnectionError/timeout
    enquanto a API ainda não respondeu a primeira request.
    """
    import time
    username = "pytest_user"
    password = "pytest_pass_123"

    last_err = None
    for attempt in range(5):
        try:
            # Registra (ignora se já existe)
            requests.post(
                f"{api_url}/auth/register",
                json={"username": username, "email": f"{username}@test.com", "password": password},
                timeout=10,
            )
            # Login
            r = requests.post(
                f"{api_url}/auth/token",
                data={"username": username, "password": password},
                timeout=10,
            )
            if r.status_code == 200:
                return r.json()["access_token"]
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        time.sleep(2)

    raise RuntimeError(f"Login falhou após 5 tentativas: {last_err}")


@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
