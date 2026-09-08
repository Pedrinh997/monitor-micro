from .base import BaseScraper

class MercadoLivreScraper(BaseScraper):
    def get_title(self, soup) -> str:
        title_tag = soup.find("h1", class_="ui-pdp-title")
        return title_tag.get_text(strip=True) if title_tag else "Título não encontrado"
    
    def get_price(self, soup) -> float:
        price_tag = soup.find("meta", {"itemprop": "price"})
        if price_tag:
            price_str = price_tag.get("content", "0").replace(",", ".")
            return float(price_str)
        else:
            price_span = soup.find("span", class_="andes-money-amount__fraction")
            if price_span:
                price_str = price_span.get_text(strip=True).replace(".", "").replace(",", ".")
                return float(price_str)
        return 0.0
    
    def get_currency(self) -> str:
        return "BRL"
