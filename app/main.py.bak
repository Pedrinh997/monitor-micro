import os
import time
import redis
from rq import Queue
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator
from . import schemas, models, database, tasks, auth
from .database import get_db
from .logger_config import logger
from .metrics import price_drop_counter
from .routes import auth as auth_routes
from .scheduler import start_scheduler

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
async def scrape_url(request: schemas.ScrapeRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    start_time = time.time()
    logger.info(f"Recebida URL para scraping: {request.url}")

    new_product = models.Product(url=str(request.url), owner_id=current_user.id)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    job = queue.enqueue(tasks.process_scrape_task, new_product.id, str(request.url))

    duration = time.time() - start_time
    logger.info(f"Tarefa enfileirada para produto {new_product.id} | job_id: {job.id} | duracao: {duration:.2f}s")

    return {
        "message": "Produto criado. Scraping em andamento.",
        "product_id": new_product.id,
        "job_id": job.id
    }

@app.get("/products/")
async def list_products(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    logger.info("Listando produtos")
    return db.query(models.Product).filter(models.Product.owner_id == current_user.id).all()

@app.get("/products/{product_id}/prices/")
async def get_prices(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    logger.info(f"Buscando histórico do produto {product_id}")
    product = db.query(models.Product).filter(models.Product.id == product_id, models.Product.owner_id == current_user.id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    return db.query(models.PriceHistory).filter(models.PriceHistory.product_id == product_id).all()
