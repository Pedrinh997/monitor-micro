from .base import BaseScraper

class AmazonScraper(BaseScraper):
    def get_title(self, soup) -> str:
        title_tag = soup.find("span", id="productTitle")
        if title_tag:
            return title_tag.get_text(strip=True)
        return "Título não encontrado"
    
    def get_price(self, soup) -> float:
        # Tenta vários seletores comuns da Amazon
        price_selectors = [
            "span.a-price-whole",
            "span.priceToPay span.a-price-whole",
            "span.a-price span.a-offscreen"
        ]
        for selector in price_selectors:
            price_tag = soup.select_one(selector)
            if price_tag:
                price_str = price_tag.get_text(strip=True).replace("R$", "").replace(".", "").replace(",", ".").strip()
                try:
                    return float(price_str)
                except:
                    continue
        return 0.0
    
    def get_currency(self) -> str:
        return "BRL"
