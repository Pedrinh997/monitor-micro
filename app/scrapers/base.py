from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """Classe abstrata para scrapers de diferentes sites."""
    
    @abstractmethod
    def get_title(self, soup) -> str:
        pass
    
    @abstractmethod
    def get_price(self, soup) -> float:
        pass
    
    @abstractmethod
    def get_currency(self) -> str:
        pass
