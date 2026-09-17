import re
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import models
import os
from .logger_config import logger
from .metrics import price_drop_counter
from .email_utils import send_price_alert

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@db:5432/postgres")
DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def scrape_product_sync(url: str) -> dict:
    from urllib.parse import urlparse
    logger.info(f"Iniciando scraping síncrono para: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Falha ao requisitar {url}: {e}")
        raise

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
            logger.warning(f"Preco nao encontrado: {url}")
        currency = "GBP"
    else:
        title_tag = soup.find("h1", class_="ui-pdp-title")
        title = title_tag.get_text(strip=True) if title_tag else "Titulo nao encontrado"
        price_tag = soup.find("meta", {"itemprop": "price"})
        if price_tag:
            price = float(price_tag.get("content", "0").replace(",", "."))
        else:
            price_span = soup.find("span", class_="andes-money-amount__fraction")
            if price_span:
                price = float(price_span.get_text(strip=True).replace(".", "").replace(",", "."))
            else:
                price = 0.0
                logger.warning(f"Preco nao encontrado: {url}")
        currency = "BRL"

    logger.info(f"Scraping concluido: {title} - {price} {currency}")
    return {"title": title, "price": price, "currency": currency, "url": url}


def process_scrape_task(product_id: int, url: str):
    logger.info(f"Worker iniciando processamento do produto {product_id}")
    db = SessionLocal()
    try:
        data = scrape_product_sync(url)
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            logger.error(f"Produto {product_id} não encontrado")
            return
        
        if not product.title:
            product.title = data["title"]
            db.commit()
            logger.info(f"Produto {product_id} título atualizado para '{data['title']}'")

        price_entry = models.PriceHistory(
            product_id=product_id,
            price=data["price"],
            currency=data["currency"]
        )
        db.add(price_entry)
        db.commit()
        
        if product.target_price and data["price"] < product.target_price:
            price_drop_counter.inc()
            logger.warning(f"🔔 ALERTA: {product.title} caiu para R$ {data['price']} (abaixo de {product.target_price})")
            
            user = db.query(models.User).filter(models.User.id == product.owner_id).first()
            if user and user.email:
                send_price_alert(product.title, data["price"], product.target_price, user.email)
            
    except Exception as e:
        logger.error(f"❌ Erro no worker para produto {product_id}: {e}")
    finally:
        db.close()
        logger.info(f"Worker finalizou processamento do produto {product_id}")
