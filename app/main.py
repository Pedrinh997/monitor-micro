from fastapi import FastAPI, HTTPException, Depends
from . import schemas, models, database, tasks
from sqlalchemy.orm import Session
from .database import get_db
import redis
from rq import Queue

redis_conn = redis.Redis(host="redis", port=6379, decode_responses=True)
queue = Queue("scraping", connection=redis_conn)

app = FastAPI(title="Monitor Micro", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Monitor Micro - API com filas"}

@app.post("/scrape/")
def scrape_url(request: schemas.ScrapeRequest, db: Session = Depends(get_db)):
    new_product = models.Product(url=str(request.url))
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    job = queue.enqueue(tasks.process_scrape_task, new_product.id, str(request.url))

    return {
        "message": "Produto criado. Scraping em andamento.",
        "product_id": new_product.id,
        "job_id": job.id
    }

@app.get("/products/")
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@app.get("/products/{product_id}/prices/")
def get_prices(product_id: int, db: Session = Depends(get_db)):
    return db.query(models.PriceHistory).filter(models.PriceHistory.product_id == product_id).all()
