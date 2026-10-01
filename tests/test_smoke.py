"""Smoke tests — rodam SEM API no ar.

Só verificam que os módulos importam e a estrutura básica funciona.
O CI roda estes; os testes de integração rodam localmente.
"""
import pytest


def test_import_main():
    """app.main importa sem erro (pega erro de sintaxe/import quebrado)."""
    from app import main
    assert main.app is not None


def test_import_tasks():
    """app.tasks importa (worker)."""
    from app import tasks
    assert hasattr(tasks, "process_scrape_task")
    assert hasattr(tasks, "scrape_coingecko_sync")


def test_import_models():
    """Modelos SQLAlchemy existem."""
    from app import models
    assert hasattr(models, "User")
    assert hasattr(models, "Product")
    assert hasattr(models, "PriceHistory")
    assert hasattr(models, "SchedulerState")


def test_import_forecast():
    """Função de previsão existe."""
    from app.ml.forecast import predict_prices
    assert callable(predict_prices)


def test_import_email():
    """Função de email existe."""
    from app.email_utils import send_price_alert
    assert callable(send_price_alert)


def test_import_auth():
    """Função de auth existe."""
    from app import auth
    assert hasattr(auth, "get_current_user")
    assert hasattr(auth, "SECRET_KEY")


def test_scheduler_has_jobs():
    """Scheduler define jobs esperados."""
    from app import scheduler
    assert hasattr(scheduler, "start_scheduler")
    assert hasattr(scheduler, "scheduled_scrape_all")
    assert hasattr(scheduler, "upload_to_minio")
