
import os
import redis
from rq import Worker, Queue, Connection
from app.core.config import REDIS_URL, QUEUE_NAME
from app.db.session import init_db

listen = [QUEUE_NAME]

def run_worker():
    # Ensure DB keys are ready (in case worker starts before main app migrates)
    # Ideally main app handles migration, but for stability:
    try:
        init_db()
    except Exception as e:
        print(f"Worker Init DB warning: {e}")

    conn = redis.from_url(REDIS_URL)
    with Connection(conn):
        print(f"Worker listening on {listen}...")
        worker = Worker(list(map(Queue, listen)))
        worker.work()

if __name__ == '__main__':
    run_worker()
