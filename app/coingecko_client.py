"""Cliente mínimo para a API pública do CoinGecko (sem auth)."""
import time
import requests

BASE_URL = "https://api.coingecko.com/api/v3"

# Rate limit keyless: ~10-30 req/min. Usamos 2.5s entre chamadas = ~24/min.
_DELAY_BETWEEN_CALLS = 2.5


def _get(path, params=None):
    """GET com retry e backoff para 429."""
    url = f"{BASE_URL}{path}"
    for attempt in range(3):
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 429:
            wait = 60 * (attempt + 1)
            print(f"[coingecko] 429 rate-limited, aguardando {wait}s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"CoinGecko falhou após 3 tentativas: {path}")


def list_top_coins(limit=50, vs_currency="usd"):
    """Retorna top N moedas por market cap."""
    data = _get("/coins/markets", {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false",
    })
    return [
        {
            "id": c["id"],
            "symbol": c["symbol"],
            "name": c["name"],
            "image": c.get("image"),
            "current_price": c.get("current_price"),
        }
        for c in data
    ]


def get_historical_prices(coin_id, days=30, vs_currency="usd"):
    """Retorna lista de (timestamp_ms, price) para os últimos N dias."""
    time.sleep(_DELAY_BETWEEN_CALLS)
    data = _get(f"/coins/{coin_id}/market_chart", {
        "vs_currency": vs_currency,
        "days": days,
        "interval": "daily",
    })
    return data.get("prices", [])
