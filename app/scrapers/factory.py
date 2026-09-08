from urllib.parse import urlparse
from .mercadolivre import MercadoLivreScraper
from .amazon import AmazonScraper
from .shopee import ShopeeScraper

def get_scraper(url: str):
    """Retorna o scraper apropriado para a URL."""
    domain = urlparse(url).netloc.lower()
    
    if "mercadolivre" in domain or "mercadolibre" in domain:
        return MercadoLivreScraper()
    elif "amazon" in domain:
        return AmazonScraper()
    elif "shopee" in domain:
        return ShopeeScraper()
    else:
        # Fallback: usa MercadoLivre como padrão (ou pode levantar erro)
        return MercadoLivreScraper()
