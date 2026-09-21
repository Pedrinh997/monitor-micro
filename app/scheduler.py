from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger
from . import models, tasks
import os
import logging
import boto3
from io import BytesIO
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

from .database import SyncSessionLocal, SYNC_DATABASE_URL

def upload_to_minio():
    """Coleta preços do banco e salva em Parquet no MinIO."""
    logger.info("📤 Iniciando upload para MinIO")
    db = SyncSessionLocal()
    try:
        prices = db.query(models.PriceHistory).all()
        if not prices:
            print("ℹ️ Nenhum preço para salvar.")
            return
        data = [
            {
                "id": p.id,
                "product_id": p.product_id,
                "price": p.price,
                "currency": p.currency,
                "scraped_at": p.scraped_at.isoformat() if p.scraped_at else None,
            }
            for p in prices
        ]
        df = pd.DataFrame(data)
        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)

        s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}",
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            region_name="us-east-1",
        )
        try:
            s3.head_bucket(Bucket="price-history")
        except Exception:
            s3.create_bucket(Bucket="price-history")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3.put_object(
            Bucket="price-history",
            Key=f"scrapes/{timestamp}.parquet",
            Body=buffer.getvalue(),
        )
        print(f"✅ {len(data)} registros salvos no MinIO")
    except Exception as e:
        logger.error(f"❌ Erro no upload para MinIO: {e}")
    finally:
        db.close()

def scheduled_scrape_all():
    """Scraping agendado + upload para MinIO."""
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

    # Depois do scraping, envia para o MinIO
    upload_to_minio()

def start_scheduler():
    jobstores = {
        "default": SQLAlchemyJobStore(url=SYNC_DATABASE_URL)
    }
    job_defaults = {
        "coalesce": True,              # se perdeu vários ticks, roda só 1 vez
        "max_instances": 1,
        "misfire_grace_time": 86400,   # 24h: roda job atrasado ao subir a API
    }
    scheduler = BackgroundScheduler(jobstores=jobstores, job_defaults=job_defaults)
    scheduler.start()  # carrega jobs existentes do jobstore

    existing = {j.id for j in scheduler.get_jobs()}

    if "scrape_all_products" not in existing:
        scheduler.add_job(
            scheduled_scrape_all,
            trigger=IntervalTrigger(hours=6),
            id="scrape_all_products",
        )
        logger.info("  + job scrape_all_products adicionado")
    else:
        logger.info("  = job scrape_all_products já existia (preservado)")

    if "upload_to_minio" not in existing:
        scheduler.add_job(
            upload_to_minio,
            trigger=IntervalTrigger(hours=1),
            id="upload_to_minio",
        )
        logger.info("  + job upload_to_minio adicionado")
    else:
        logger.info("  = job upload_to_minio já existia (preservado)")

    logger.info("⏰ Agendador iniciado (jobstore Postgres persistente)")
    return scheduler
