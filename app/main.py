from fastapi import FastAPI, HTTPException, Depends
from . import schemas, models, database, tasks
from sqlalchemy.orm import Session
from .database import get_db
import redis
from rq import Queue
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
import time
from .logger_config import logger

# --- MÉTRICA PERSONALIZADA ---
price_drop_counter = Counter('price_drops_total', 'Total de vezes que o preço baixou abaixo da meta')

# --- CONEXÕES ---
redis_conn = redis.Redis(host="redis", port=6379, decode_responses=True)
queue = Queue("scraping", connection=redis_conn)

# --- APP ---
app = FastAPI(title="Monitor Micro", version="1.0.0")

# --- INSTRUMENTAÇÃO PROMETHEUS (automática) ---
Instrumentator().instrument(app).expose(app)

# --- LOGS ---
logger.info("🚀 API do Monitor Micro iniciada!")

@app.get("/")
def root():
    logger.info("Endpoint / acessado")
    return {"message": "Monitor Micro - API com filas"}

@app.post("/scrape/")
def scrape_url(request: schemas.ScrapeRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    logger.info(f"Recebida URL para scraping: {request.url}")
    
    new_product = models.Product(url=str(request.url))
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
def list_products(db: Session = Depends(get_db)):
    logger.info("Listando produtos")
    return db.query(models.Product).all()

@app.get("/products/{product_id}/prices/")
def get_prices(product_id: int, db: Session = Depends(get_db)):
    logger.info(f"Buscando histórico do produto {product_id}")
    return db.query(models.PriceHistory).filter(models.PriceHistory.product_id == product_id).all()
