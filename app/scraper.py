import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any

async def scrape_product(url: str) -> Dict[str, Any]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
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
