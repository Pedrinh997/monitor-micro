from .base import BaseScraper

class ShopeeScraper(BaseScraper):
    def get_title(self, soup) -> str:
        title_tag = soup.find("meta", {"property": "og:title"})
        if title_tag:
            return title_tag.get("content", "Título não encontrado")
        return "Título não encontrado"
    
    def get_price(self, soup) -> float:
        # Tenta diferentes estruturas da Shopee
        price_tag = soup.find("meta", {"property": "product:price:amount"})
        if price_tag:
            try:
                return float(price_tag.get("content", "0"))
            except:
                pass
        
        price_span = soup.find("div", class_="product-briefing")
        if price_span:
            price_text = price_span.get_text(strip=True)
            # Extrai o primeiro número com vírgula ou ponto
            import re
            match = re.search(r'[\d.,]+', price_text)
            if match:
                price_str = match.group().replace(".", "").replace(",", ".")
                try:
                    return float(price_str)
                except:
                    pass
        return 0.0
    
    def get_currency(self) -> str:
        return "BRL"
