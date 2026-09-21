import os
import time
import redis
from rq import Queue
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator
from . import schemas, models, database, tasks, auth
from .database import get_db_sync
from .logger_config import logger
from .metrics import price_drop_counter
from .routes import auth as auth_routes
from .scheduler import start_scheduler
from .analytics.duckdb_analysis import get_price_stats, get_price_variation
from .ml.forecast import predict_prices

# --- CONEXÕES ---
redis_conn = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", 6379)), decode_responses=True)
queue = Queue("scraping", connection=redis_conn)

# --- APP ---
app = FastAPI(title="Monitor Micro", version="1.0.0")

# Inclui rotas de autenticação
app.include_router(auth_routes.router)

# --- INSTRUMENTAÇÃO PROMETHEUS ---
Instrumentator().instrument(app).expose(app)

# --- LOGS ---
logger.info("🚀 API do Monitor Micro iniciada!")

# --- SCHEDULER ---
scheduler = None

@app.on_event("startup")
def startup_event():
    global scheduler
    scheduler = start_scheduler()
    logger.info("✅ Agendador iniciado com sucesso")

@app.on_event("shutdown")
def shutdown_event():
    if scheduler:
        scheduler.shutdown()
        logger.info("🛑 Agendador finalizado")

@app.get("/")
async def root():
    logger.info("Endpoint / acessado")
    return {"message": "Monitor Micro - API com filas"}

@app.post("/scrape/")
async def scrape_url(request: schemas.ScrapeRequest, db: Session = Depends(get_db_sync), current_user: models.User = Depends(auth.get_current_user)):
    start_time = time.time()
    url = str(request.url)
    logger.info(f"Recebida URL para scraping: {url}")

    existing = db.query(models.Product).filter(models.Product.url == url).first()

    if existing is not None:
        if existing.owner_id != current_user.id:
            raise HTTPException(
                status_code=409,
                detail="Esta URL já está sendo monitorada por outro usuário.",
            )
        product = existing
        logger.info(f"Reutilizando produto existente id={product.id}")
    else:
        product = models.Product(url=url, owner_id=current_user.id)
        db.add(product)
        db.commit()
        db.refresh(product)
        logger.info(f"Produto criado id={product.id}")

    job = queue.enqueue(tasks.process_scrape_task, product.id, url)

    duration = time.time() - start_time
    logger.info(f"Tarefa enfileirada para produto {product.id} | job_id: {job.id} | duracao: {duration:.2f}s")

    return {
        "message": "Scraping em andamento.",
        "product_id": product.id,
        "job_id": job.id,
        "reused": existing is not None,
    }


@app.get("/products/")
async def list_products(db: Session = Depends(get_db_sync), current_user: models.User = Depends(auth.get_current_user)):
    logger.info("Listando produtos")
    return db.query(models.Product).filter(models.Product.owner_id == current_user.id).all()

@app.get("/products/{product_id}/prices/")
async def get_prices(product_id: int, db: Session = Depends(get_db_sync), current_user: models.User = Depends(auth.get_current_user)):
    logger.info(f"Buscando histórico do produto {product_id}")
    product = db.query(models.Product).filter(models.Product.id == product_id, models.Product.owner_id == current_user.id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    return db.query(models.PriceHistory).filter(models.PriceHistory.product_id == product_id).all()


# ─── ANALYTICS (DuckDB + MinIO) ─────────────────────────────

@app.get("/analytics/stats")
async def analytics_stats(product_id: int | None = None, current_user: models.User = Depends(auth.get_current_user)):
    """Estatísticas de preço (média/min/máx/contagem) via DuckDB."""
    logger.info(f"Analytics stats | product_id={product_id}")
    return get_price_stats(product_id=product_id)


@app.get("/analytics/variation/{product_id}")
async def analytics_variation(product_id: int, current_user: models.User = Depends(auth.get_current_user)):
    """Variação absoluta e percentual entre os 2 últimos preços."""
    logger.info(f"Analytics variation | product_id={product_id}")
    return get_price_variation(product_id=product_id)


# ─── ML FORECAST ─────────────────────────────────────────────

@app.get("/products/{product_id}/forecast")
async def product_forecast(
    product_id: int,
    days: int = 7,
    current_user: models.User = Depends(auth.get_current_user),
):
    """Previsão de preços dos próximos N dias (default: 7)."""
    logger.info(f"Forecast | product_id={product_id} days={days}")
    return predict_prices(product_id=product_id, days=days)
