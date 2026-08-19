import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rq import Worker, Queue
import redis

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = redis.from_url(redis_url)

if __name__ == "__main__":
    worker = Worker(Queue("scraping", connection=redis_conn))
    worker.work()
