import re
import datetime
import requests
import time
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import models
import os
from .logger_config import logger
from .metrics import price_drop_counter
from .email_utils import send_price_alert

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@db:5432/postgres")
DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def _get_with_retry(path, params=None, max_attempts=5):
    """GET com retry exponencial em 429 (rate limit do CoinGecko)."""
    url = f"{COINGECKO_BASE}{path}"
    for attempt in range(max_attempts):
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 429:
            wait = 30 * (attempt + 1)
            logger.warning(f"429 em {path}, aguardando {wait}s (tentativa {attempt+1}/{max_attempts})")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"CoinGecko 429 após {max_attempts} tentativas: {path}")


def scrape_product_sync(url: str) -> dict:
    from urllib.parse import urlparse
    logger.info(f"Iniciando scraping síncrono para: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    domain = urlparse(url).netloc.lower()
    if "books.toscrape.com" in domain:
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Titulo nao encontrado"
        price_tag = soup.find("p", class_="price_color")
        if price_tag:
            raw = price_tag.get_text(strip=True)
            m = re.search(r"([0-9]+(?:[.,][0-9]+)?)", raw)
            price = float(m.group(1).replace(",", ".")) if m else 0.0
        else:
            price = 0.0
        currency = "GBP"
    else:
        title_tag = soup.find("h1", class_="ui-pdp-title")
        title = title_tag.get_text(strip=True) if title_tag else "Titulo nao encontrado"
        price_tag = soup.find("meta", {"itemprop": "price"})
        price = float(price_tag.get("content", "0")) if price_tag else 0.0
        currency = "BRL"
    logger.info(f"Scraping concluido: {title} - {price} {currency}")
    return {"title": title, "price": price, "currency": currency, "url": url}


def scrape_coingecko_sync(coin_id: str, days: int = 30) -> list:
    """Busca metadata + histórico de preços com retry em 429."""
    logger.info(f"Iniciando CoinGecko para: {coin_id} ({days} dias)")

    # Metadata (opcional — se falhar, usa coin_id como nome)
    name = coin_id
    symbol = ""
    try:
        meta = _get_with_retry(f"/coins/{coin_id}")
        name = meta.get("name", coin_id)
        symbol = (meta.get("symbol") or "").upper()
    except Exception as e:
        logger.warning(f"Metadata de {coin_id} indisponível: {e}")

    title = f"{name} ({symbol})" if symbol else name
    time.sleep(3)  # respiro entre as duas chamadas

    # Histórico (obrigatório)
    data = _get_with_retry(
        f"/coins/{coin_id}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"},
    )

    prices = data.get("prices", [])
    out = []
    for ts_ms, price in prices:
        scraped_at = datetime.datetime.utcfromtimestamp(ts_ms / 1000)
        out.append({
            "title": title,
            "price": float(price),
            "currency": "USD",
            "scraped_at": scraped_at,
        })
    logger.info(f"CoinGecko: {len(out)} amostras para {coin_id}")
    return out


def process_scrape_task(product_id: int, url: str):
    logger.info(f"Worker iniciando processamento do produto {product_id}")
    db = SessionLocal()
    try:
        if url.startswith("http://") or url.startswith("https://"):
            d = scrape_product_sync(url)
            samples = [{"title": d["title"], "price": d["price"], "currency": d["currency"]}]
        else:
            samples = scrape_coingecko_sync(url, days=30)

        if not samples:
            logger.warning(f"Sem amostras para produto {product_id}")
            return

        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            logger.error(f"Produto {product_id} não encontrado")
            return

        if not product.title:
            product.title = samples[0]["title"]
            db.commit()
            logger.info(f"Produto {product_id} título atualizado para '{product.title}'")

        for s in samples:
            kwargs = {
                "product_id": product_id,
                "price": s["price"],
                "currency": s["currency"],
            }
            if "scraped_at" in s:
                kwargs["scraped_at"] = s["scraped_at"]
            db.add(models.PriceHistory(**kwargs))
        db.commit()
        logger.info(f"Produto {product_id}: {len(samples)} amostras salvas")

        last_price = samples[-1]["price"]
        if product.target_price and last_price < product.target_price:
            price_drop_counter.inc()
            logger.warning(f"🔔 ALERTA: {product.title} caiu para {last_price}")
            user = db.query(models.User).filter(models.User.id == product.owner_id).first()
            if user and user.email:
                send_price_alert(product.title, last_price, product.target_price, user.email)

    except Exception as e:
        logger.error(f"❌ Erro no worker para produto {product_id}: {e}")
    finally:
        db.close()
        logger.info(f"Worker finalizou processamento do produto {product_id}")
