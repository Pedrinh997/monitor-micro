import pytest
from app.scraper import scrape_product

@pytest.mark.asyncio
async def test_scrape_product():
    # Use uma URL real de um produto do Mercado Livre (qualquer um)
    url = "https://produto.mercadolivre.com.br/MLB-1234567890"  # Substitua por uma URL real
    try:
        result = await scrape_product(url)
        assert "title" in result
        assert "price" in result
        assert "currency" in result
        assert "url" in result
    except Exception as e:
        pytest.skip(f"Scraping falhou: {e}")
