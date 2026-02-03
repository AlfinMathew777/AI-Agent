"""
ACP Transaction Manager (SQLite prototype)
- Minimal state machine storage.
- Adds update_transaction_from_result() used by gateway_server.py
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


@dataclass
class Transaction:
    tx_id: str
    request_id: str
    agent_id: str
    target_domain: str
    target_entity_id: str
    intent_type: str

    status: str  # "pending" | "negotiating" | "negotiated" | "confirmed" | "failed" | ...
    negotiation_round: int = 0
    negotiation_session_id: Optional[str] = None
    current_offer: Optional[Dict[str, Any]] = None
    agent_constraints: Optional[Dict[str, Any]] = None
    agent_context: Optional[Dict[str, Any]] = None

    created_at: str = ""
    expires_at: str = ""


class TransactionManager:
    def __init__(self, db_path: str = "acp_transactions.db"):
        self.db_path = db_path

    async def initialize(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                tx_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                tx_json TEXT NOT NULL,
                status TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_agent ON transactions(agent_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_request_id ON transactions(request_id)")
        
        # Phase 3B: Idempotency log to prevent duplicate bookings
        cur.execute("""
            CREATE TABLE IF NOT EXISTS idempotency_log (
                request_id TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                execution_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_created ON idempotency_log(created_at)")
        
        conn.commit()
        conn.close()


    async def create_transaction(self, request) -> Transaction:
        # Check if there's an existing transaction for this request_id
        existing = await self._get_transaction_by_request_id(request.request_id)
        if existing:
            return existing
        
        tx_id = str(uuid.uuid4())

        created_at = datetime.utcnow().isoformat()
        expires_at = (datetime.utcnow() + timedelta(minutes=30)).isoformat()

        tx = Transaction(
            tx_id=tx_id,
            request_id=request.request_id,
            agent_id=request.agent_id,
            target_domain=request.target_domain,
            target_entity_id=request.target_entity_id,
            intent_type=request.intent_type,
            status="pending",
            agent_constraints=request.constraints,
            agent_context=request.agent_context,
            created_at=created_at,
            expires_at=expires_at,
        )
        await self._persist(tx)
        return tx
    
    async def _get_transaction_by_request_id(self, request_id: str) -> Optional[Transaction]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT tx_json FROM transactions WHERE request_id = ? ORDER BY updated_at DESC LIMIT 1", (request_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return None
        
        tx_dict = json.loads(row[0])
        return Transaction(**tx_dict)
    
    async def get_transaction_by_session_id(self, session_id: str) -> Optional[Transaction]:
        """Look up transaction by negotiation_session_id"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # Search in JSON for session_id
        cur.execute("SELECT tx_json FROM transactions WHERE tx_json LIKE ? AND status = 'negotiating' ORDER BY updated_at DESC LIMIT 1", (f'%"negotiation_session_id": "{session_id}"%',))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return None
        
        tx_dict = json.loads(row[0])
        return Transaction(**tx_dict)

    async def set_status(self, tx: Transaction, new_status: str):
        tx.status = new_status
        await self._persist(tx)

    async def update_transaction_from_result(self, tx: Transaction, result: Dict[str, Any]):
        """
        Called by gateway after negotiation/execution.
        Updates tx status + current_offer if present.
        """
        status = result.get("status")
        
        # Store session_id if present
        session_id = result.get("session_id")
        if session_id:
            tx.negotiation_session_id = session_id

        if status in ("counter", "accepted"):
            await self.set_status(tx, "negotiating")
        elif status == "negotiated":
            tx.current_offer = result.get("payload", {}).get("our_offer") or result.get("payload", {})
            await self.set_status(tx, "negotiated")
        elif status == "confirmed":
            await self.set_status(tx, "confirmed")
        elif status in ("rejected", "error", "timeout"):
            await self.set_status(tx, "failed")

    async def _persist(self, tx: Transaction):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO transactions (tx_id, request_id, tx_json, status, agent_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            tx.tx_id,
            tx.request_id,
            json.dumps(asdict(tx)),
            tx.status,
            tx.agent_id,
            tx.created_at,
        ))
        conn.commit()
        conn.close()

    # Phase 3B: Idempotency Support
    async def get_idempotent_result(self, request_id: str, execution_type: str = "execute") -> Optional[Dict[str, Any]]:
        """Check if we've already executed this request_id
        
        Args:
            request_id: Unique request identifier from ACP request
            execution_type: Type of execution (execute, negotiate, discover)
        
        Returns:
            Cached result dict if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """SELECT result_json, execution_type, created_at 
               FROM idempotency_log 
               WHERE request_id = ?""",
            (request_id,),
        )
        row = cur.fetchone()
        conn.close()

        if row:
            result_json, stored_type, created_at = row
            # Log cache hit
            print(f"[IDEMPOTENCY] Cache HIT for request_id={request_id}, type={stored_type}, cached_at={created_at}")
            return json.loads(result_json)
        
        return None

    async def store_idempotent_result(
        self, 
        request_id: str, 
        result: Dict[str, Any], 
        execution_type: str = "execute"
    ):
        """Store execution result for future duplicate detection
        
        Args:
            request_id: Unique request identifier
            result: Execution result to cache
            execution_type: Type of execution (execute, negotiate, discover)
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Only store if result was successful or is a valid dry-run
        should_cache = (
            result.get("success") is True or  # Successful execution
            result.get("dry_run") is True  # Valid dry-run
        )
        
        if not should_cache:
            print(f"[IDEMPOTENCY] NOT caching failed result for request_id={request_id}")
            conn.close()
            return
        
        cur.execute(
            """INSERT OR REPLACE INTO idempotency_log 
               (request_id, result_json, execution_type, created_at)
               VALUES (?, ?, ?, datetime('now'))""",
            (request_id, json.dumps(result), execution_type),
        )
        conn.commit()
        conn.close()
        
        print(f"[IDEMPOTENCY] Cached result for request_id={request_id}, type={execution_type}")

    async def cleanup_old_idempotency_records(self, days: int = 30):
        """Clean up idempotency records older than N days
        
        Called periodically to prevent unbounded growth.
        Default: Keep 30 days of idempotency records.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """DELETE FROM idempotency_log 
               WHERE created_at < datetime('now', ? || ' days')""",
            (f"-{days}",)
        )
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"[IDEMPOTENCY] Cleaned up {deleted} old records (>{days} days)")
        
        return deleted

    async def shutdown(self):
        pass

