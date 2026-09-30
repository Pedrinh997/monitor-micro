"""Previsão de preços — baseline + ARIMA.

Regra:
- < MIN_SAMPLES_FOR_ARIMA amostras -> baseline (último preço)
- >= MIN_SAMPLES_FOR_ARIMA amostras -> ARIMA (após agrupar por dia)
"""
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .. import models
from ..database import SYNC_DATABASE_URL

MIN_SAMPLES_FOR_ARIMA = 10
MIN_DAYS_FOR_ARIMA = 5  # após agregar por dia


def _predict_baseline(last_price: float, days: int) -> list:
    base = datetime.utcnow()
    return [
        {
            "date": (base + timedelta(days=i)).strftime("%Y-%m-%d"),
            "predicted_price": float(last_price),
        }
        for i in range(1, days + 1)
    ]


def _aggregate_daily(series: list):
    """Agrupa amostras por dia (média) para eliminar datas duplicadas.

    Retorna DataFrame com índice DatetimeIndex diário sem duplicatas.
    """
    import pandas as pd

    df = pd.DataFrame(series)
    df["scraped_at"] = pd.to_datetime(df["scraped_at"])
    df["date"] = df["scraped_at"].dt.normalize()  # zera horas -> dia

    daily = df.groupby("date", as_index=False)["price"].mean()
    daily = daily.sort_values("date").set_index("date")
    return daily


def _predict_arima(series: list, days: int) -> list:
    """series: lista de dicts com 'price' e 'scraped_at'."""
    from statsmodels.tsa.arima.model import ARIMA

    daily = _aggregate_daily(series)

    if len(daily) < MIN_DAYS_FOR_ARIMA:
        raise ValueError(f"apenas {len(daily)} dias agregados")

    if daily["price"].nunique() <= 1:
        raise ValueError("sem variação de preço")

    model = ARIMA(daily["price"], order=(1, 0, 0))
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
        arima_error = None

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
                arima_error = f"{type(e).__name__}: {e}"
                predictions = None

        if predictions is None:
            predictions = _predict_baseline(last.price, days)
            if arima_error:
                method = f"baseline_last_price (arima fallback: {arima_error})"

        # Quantos dias únicos existem
        try:
            from pandas import to_datetime
            daily_count = len({to_datetime(r.scraped_at).date() for r in rows if r.scraped_at})
        except Exception:
            daily_count = None

        return {
            "product_id": product_id,
            "model": method,
            "samples_used": n,
            "days_used": daily_count,
            "last_known_price": float(last.price),
            "last_known_at": last.scraped_at.isoformat() if last.scraped_at else None,
            "forecast_days": days,
            "predictions": predictions,
        }
    finally:
        db.close()
