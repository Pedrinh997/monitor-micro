import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import models
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@db:5432/postgres")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def scrape_product_sync(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

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

    return {"title": title, "price": price, "currency": "BRL", "url": url}

def process_scrape_task(product_id: int, url: str):
    db = SessionLocal()
    try:
        data = scrape_product_sync(url)
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if product:
            product.title = data["title"]
            db.commit()

        price_entry = models.PriceHistory(
            product_id=product_id,
            price=data["price"],
            currency=data["currency"]
        )
        db.add(price_entry)
        db.commit()
        print(f"✅ Produto {product_id} atualizado: R$ {data['price']}")
    except Exception as e:
        print(f"❌ Erro no worker para produto {product_id}: {e}")
    finally:
        db.close()
