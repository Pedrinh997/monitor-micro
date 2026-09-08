from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .database import SyncSessionLocal
from . import models, tasks
import logging

logger = logging.getLogger(__name__)

def scheduled_scrape_all():
    logger.info("🔄 Executando scraping agendado para todos os produtos")
    db = SyncSessionLocal()
    try:
        products = db.query(models.Product).all()
        logger.info(f"🔎 {len(products)} produtos encontrados para scraping")
        for product in products:
            tasks.process_scrape_task(product.id, product.url)
    except Exception as e:
        logger.error(f"❌ Erro no scraping agendado: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        scheduled_scrape_all,
        trigger=IntervalTrigger(hours=6),
        id="scrape_all_products",
        replace_existing=True,
        next_run_time=None
    )
    scheduler.start()
    logger.info("⏰ Agendador iniciado: scraping automático a cada 6 horas")
    return scheduler
