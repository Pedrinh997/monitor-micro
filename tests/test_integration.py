"""Testes de integração — batem na API real (localhost:8000)."""
import pytest


def test_api_root(api_url):
    import requests
    r = requests.get(f"{api_url}/", timeout=5)
    assert r.status_code == 200
    assert "message" in r.json()


def test_products_requires_auth(api_url):
    import requests
    r = requests.get(f"{api_url}/products/", timeout=5)
    assert r.status_code == 401


def test_products_with_auth(api_url, auth_headers):
    import requests
    r = requests.get(f"{api_url}/products/", headers=auth_headers, timeout=5)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_analytics_stats(api_url, auth_headers):
    import requests
    r = requests.get(f"{api_url}/analytics/stats", headers=auth_headers, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "count" in data


def test_forecast_no_history(api_url, auth_headers):
    """Produto com ID improvável não tem histórico."""
    import requests
    r = requests.get(f"{api_url}/products/999999/forecast", headers=auth_headers, timeout=10)
    assert r.status_code == 200
    assert "error" in r.json() or "predictions" in r.json()


def test_scrape_duplicate_url(api_url, auth_headers):
    """Enviar URL repetida deve ser rejeitada (409) ou marcada como reused=true.

    Comportamento atual da API: 409 Conflict para URL já cadastrada.
    Contrato antigo (200 + reused=true) também é aceito por compatibilidade.
    """
    import requests
    url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

    # Primeira chamada — 200 (novo) ou 409 (já existia de sessões antigas)
    r1 = requests.post(f"{api_url}/scrape/", json={"url": url}, headers=auth_headers, timeout=10)
    assert r1.status_code in (200, 409), f"1ª chamada inesperada: {r1.status_code} {r1.text}"

    # Segunda chamada — deve ser 409 (duplicado) ou 200 com reused=true
    r2 = requests.post(f"{api_url}/scrape/", json={"url": url}, headers=auth_headers, timeout=10)
    assert r2.status_code in (200, 409), f"2ª chamada inesperada: {r2.status_code} {r2.text}"

    if r2.status_code == 409:
        # Comportamento novo — duplicado rejeitado explicitamente
        body = r2.json()
        assert "detail" in body or "already" in r2.text.lower()
    else:
        # Comportamento antigo — 200 com reused=true
        assert r2.json().get("reused") is True


def test_metrics_endpoint(api_url):
    """Prometheus /metrics é público."""
    import requests
    r = requests.get(f"{api_url}/metrics", timeout=5)
    assert r.status_code == 200
    assert "python_gc_objects" in r.text or "http_requests_total" in r.text
