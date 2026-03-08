
import redis
from rq import Queue
from app.core.config import REDIS_URL, QUEUE_NAME, JOB_MAX_RETRIES, JOB_RETRY_BACKOFF_SECONDS
from app.queue.jobs import execute_quote_job
import uuid
from app.db.session import get_db_connection

# Global Redis Connection
redis_conn = redis.from_url(REDIS_URL)
q = Queue(QUEUE_NAME, connection=redis_conn)

def enqueue_execute_quote(tenant_id: str, quote_id: str, payment_id: str, stripe_event_id: str):
    """
    Enqueue the quote execution job.
    Idempotent: Stores job in DB 'execution_jobs' first.
    """
    job_id = str(uuid.uuid4())
    
    # 1. Create DB Job Record (Idempotency Key)
    conn = get_db_connection()
    conn.row_factory = get_db_connection().row_factory
    
    try:
        conn.execute('''
            INSERT INTO execution_jobs (id, tenant_id, quote_id, payment_id, stripe_event_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (job_id, tenant_id, quote_id, payment_id, stripe_event_id, "queued"))
        conn.commit()
    except Exception as e:
        # Constraint violation means job exists
        print(f"[Queue] Job for event {stripe_event_id} already exists (skipping enqueue). Error: {e}")
        # Look up existing job using the SAME connection (if valid) or New one?
        # If transaction failed, connection might be in failed state? 
        # SQLite: usually fine to select. But safer to rollback or close/reopen.
        try:
             conn.close()
        except: pass
        
        conn = get_db_connection()
        conn.row_factory = get_db_connection().row_factory
        existing_job = conn.execute(
            "SELECT id FROM execution_jobs WHERE tenant_id = ? AND stripe_event_id = ?",
            (tenant_id, stripe_event_id)
        ).fetchone()
        conn.close()
        
        if existing_job:
             return existing_job["id"]
        else:
             # Should not happen if constraint violation was real
             # Re-raise original error if we can't find it
             raise e

    # 2. Enqueue in Redis
    try:
        q.enqueue(
            execute_quote_job,
            args=(tenant_id, quote_id, payment_id, stripe_event_id, job_id),
            job_id=job_id,
            retry=None, # RQ Retry is tricky, we handle exceptions in job wrapper or use Retry scheduler
            # For MVP, rely on simple re-queue or manual retry if specific RQ retry not configured
            # If we want exponential backoff, we need rq-scheduler or custom exception handling
            # We implemented try/catch in execute_quote_job -> re-raise. Redis queue default retry is simplistic?
            # Let's rely on standard RQ behavior or a wrapper. For now, basic enqueue.
        )
        print(f"[Queue] Enqueued Job {job_id}")
    except Exception as e:
        # Update status to failed_enqueue
        print(f"[Queue] Failed to enqueue {job_id}: {e}")
        conn = get_db_connection()
        conn.execute("UPDATE execution_jobs SET status = 'failed_enqueue', last_error = ? WHERE id = ?", (str(e), job_id))
        conn.commit()
        conn.close()
        raise e
        
    return job_id
