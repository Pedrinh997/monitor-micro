import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import models
import os
from .logger_config import logger
from prometheus_client import Counter

price_drop_counter = Counter('price_drops_total', 'Total de vezes que o preço baixou abaixo da meta')

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@db:5432/postgres")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def scrape_product_sync(url: str) -> dict:
    logger.info(f"Iniciando scraping síncrono para: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        logger.debug(f"HTTP {response.status_code} para {url}")
    except Exception as e:
        logger.error(f"Falha ao requisitar {url}: {e}")
        raise

    soup = BeautifulSoup(response.text, "lxml")

    title_tag = soup.find("h1", class_="ui-pdp-title")
    title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"

    price_tag = soup.find("meta", {"itemprop": "price"})
    if price_tag:
        price_str = price_tag.get("content", "0").replace(",", ".")
        price = float(price_str)
    else:
        price_span = soup.find("span", class_="andes-money-amount__fraction")
        if price_span:
            price_str = price_span.get_text(strip=True).replace(".", "").replace(",", ".")
            price = float(price_str)
        else:
            price = 0.0
            logger.warning(f"Preço não encontrado para {url}")

    logger.info(f"Scraping concluído: {title} - R$ {price}")
    return {"title": title, "price": price, "currency": "BRL", "url": url}

def process_scrape_task(product_id: int, url: str):
    logger.info(f"Worker iniciando processamento do produto {product_id}")
    db = SessionLocal()
    try:
        data = scrape_product_sync(url)
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if product:
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
        
        # Verifica queda de preço
        if product and product.target_price and data["price"] < product.target_price:
            price_drop_counter.inc()
            logger.warning(f"🔔 ALERTA: {product.title} caiu para R$ {data['price']} (abaixo de {product.target_price})")
        else:
            logger.info(f"Produto {product_id} atualizado: R$ {data['price']}")
            
    except Exception as e:
        logger.error(f"❌ Erro no worker para produto {product_id}: {e}")
    finally:
        db.close()
        logger.info(f"Worker finalizou processamento do produto {product_id}")
