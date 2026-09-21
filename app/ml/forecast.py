"""Previsão de preços — baseline + ARIMA.

Regra:
- < MIN_SAMPLES_FOR_ARIMA amostras -> baseline (último preço)
- >= MIN_SAMPLES_FOR_ARIMA amostras -> ARIMA
"""
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .. import models
from ..database import SYNC_DATABASE_URL

MIN_SAMPLES_FOR_ARIMA = 10


def _predict_baseline(last_price: float, days: int) -> list:
    base = datetime.utcnow()
    return [
        {
            "date": (base + timedelta(days=i)).strftime("%Y-%m-%d"),
            "predicted_price": float(last_price),
        }
        for i in range(1, days + 1)
    ]


def _predict_arima(series: list, days: int) -> list:
    """series: lista de dicts ordenada por scraped_at ASC, com 'price' e 'scraped_at'."""
    import pandas as pd
    from statsmodels.tsa.arima.model import ARIMA

    df = pd.DataFrame(series)
    df["scraped_at"] = pd.to_datetime(df["scraped_at"])
    df = df.sort_values("scraped_at").set_index("scraped_at")

    # Se todos os preços são idênticos, ARIMA não tem sinal — usa baseline
    if df["price"].nunique() <= 1:
        raise ValueError("sem variação de preço")

    model = ARIMA(df["price"], order=(1, 0, 0))
    fit = model.fit()

    forecast = fit.forecast(steps=days)
    base = datetime.utcnow()
    return [
        {
            "date": (base + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
            "predicted_price": float(forecast.iloc[i]),
        }
        for i in range(days)
    ]


def predict_prices(product_id: int, days: int = 7) -> dict:
    engine = create_engine(SYNC_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        rows = (
            db.query(models.PriceHistory)
            .filter(models.PriceHistory.product_id == product_id)
            .order_by(models.PriceHistory.scraped_at.asc())
            .all()
        )
        if not rows:
            return {"product_id": product_id, "error": "sem histórico"}

        last = rows[-1]
        n = len(rows)

        method = "baseline_last_price"
        predictions = None

        if n >= MIN_SAMPLES_FOR_ARIMA:
            try:
                series = [
                    {"price": r.price, "scraped_at": r.scraped_at}
                    for r in rows
                    if r.scraped_at is not None
                ]
                predictions = _predict_arima(series, days)
                method = "arima(1,0,0)"
            except Exception as e:
                # Fallback silencioso para baseline
                predictions = None
                method = f"baseline_last_price (arima fallback: {type(e).__name__})"

        if predictions is None:
            predictions = _predict_baseline(last.price, days)

        return {
            "product_id": product_id,
            "model": method,
            "samples_used": n,
            "last_known_price": float(last.price),
            "last_known_at": last.scraped_at.isoformat() if last.scraped_at else None,
            "forecast_days": days,
            "predictions": predictions,
        }
    finally:
        db.close()
