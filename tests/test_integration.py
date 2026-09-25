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
    """Enviar URL repetida retorna reused=true."""
    import requests
    url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

    r1 = requests.post(f"{api_url}/scrape/", json={"url": url}, headers=auth_headers, timeout=10)
    assert r1.status_code == 200

    r2 = requests.post(f"{api_url}/scrape/", json={"url": url}, headers=auth_headers, timeout=10)
    assert r2.status_code == 200
    assert r2.json().get("reused") is True


def test_metrics_endpoint(api_url):
    """Prometheus /metrics é público."""
    import requests
    r = requests.get(f"{api_url}/metrics", timeout=5)
    assert r.status_code == 200
    assert "python_gc_objects" in r.text or "http_requests_total" in r.text
