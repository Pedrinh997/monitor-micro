"""Previsão de preços — baseline (último preço).

Quando houver histórico suficiente, trocar _predict_baseline() por
ARIMA/Prophet mantendo a assinatura de predict_prices().
"""
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .. import models
from ..database import SYNC_DATABASE_URL


def _predict_baseline(last_price: float, days: int) -> list[dict]:
    """Baseline trivial: assume preço constante = último observado."""
    base = datetime.utcnow()
    return [
        {
            "date": (base + timedelta(days=i)).strftime("%Y-%m-%d"),
            "predicted_price": float(last_price),
        }
        for i in range(1, days + 1)
    ]


def predict_prices(product_id: int, days: int = 7) -> dict:
    """Prevê preços dos próximos N dias para um produto.

    Baseline atual: retorna o último preço conhecido repetido.
    Suficiente para validar o pipeline de ML de ponta a ponta.
    """
    engine = create_engine(SYNC_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        last = (
            db.query(models.PriceHistory)
            .filter(models.PriceHistory.product_id == product_id)
            .order_by(models.PriceHistory.scraped_at.desc())
            .first()
        )
        if last is None:
            return {
                "product_id": product_id,
                "error": "sem histórico de preço para este produto",
            }

        predictions = _predict_baseline(last.price, days)

        return {
            "product_id": product_id,
            "model": "baseline_last_price",
            "last_known_price": float(last.price),
            "last_known_at": last.scraped_at.isoformat() if last.scraped_at else None,
            "forecast_days": days,
            "predictions": predictions,
        }
    finally:
        db.close()
