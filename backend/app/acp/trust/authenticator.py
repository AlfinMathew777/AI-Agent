"""
ACP Trust Layer (SQLite prototype)
- Keeps your structure: authenticate() -> AuthResult
- Signature verification can be enforced later.
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


@dataclass
class AuthResult:
    valid: bool
    reason: Optional[str] = None
    agent_reputation: float = 0.0
    rate_limit_remaining: int = 0


class AgentIdentity(BaseModel):
    agent_id: str
    agent_name: str
    agent_type: str

    public_key: str = ""  # optional in prototype
    key_rotation_date: datetime = Field(default_factory=datetime.utcnow)

    reputation_score: float = Field(ge=0.0, le=1.0, default=0.5)
    total_transactions: int = 0
    successful_transactions: int = 0
    dispute_count: int = 0

    tier: str = "standard"
    requests_per_minute: int = 60

    allowed_domains: list = Field(default_factory=lambda: ["hotel"])
    blocked_entities: list = Field(default_factory=list)

    registration_date: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    verification_status: str = "verified"  # prototype default


class ACPAuthenticator:
    def __init__(self, db_path: str = "acp_trust.db"):
        self.db_path = db_path
        self._cache: Dict[str, AgentIdentity] = {}

    async def initialize(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_identities (
                agent_id TEXT PRIMARY KEY,
                identity_json TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                request_id TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now')),
                intent_type TEXT,
                success INTEGER,
                processing_time_ms INTEGER
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_request_logs_agent ON request_logs(agent_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_request_logs_time ON request_logs(timestamp)")
        conn.commit()
        conn.close()

    async def authenticate(self, request) -> AuthResult:
        identity = await self._get_identity(request.agent_id)
        if not identity:
            return AuthResult(valid=False, reason="Agent not registered")

        if identity.verification_status == "suspended":
            return AuthResult(valid=False, reason="Agent suspended")

        # Prototype: signature not enforced (you can enforce later)
        # If you want strict signature later:
        # - reconstruct payload without agent_signature
        # - verify using stored public_key

        ok, remaining = await self._check_rate_limit(identity.agent_id, identity.requests_per_minute)
        if not ok:
            return AuthResult(valid=False, reason="Rate limit exceeded")

        identity.last_active = datetime.utcnow()
        await self._save_identity(identity)

        return AuthResult(valid=True, agent_reputation=identity.reputation_score, rate_limit_remaining=remaining)

    async def authorize(self, request) -> bool:
        identity = await self._get_identity(request.agent_id)
        if not identity:
            return False

        if request.target_domain not in identity.allowed_domains and "*" not in identity.allowed_domains:
            return False

        if request.target_entity_id in identity.blocked_entities:
            return False

        # Low-rep agents can't execute in prototype
        if request.intent_type == "execute" and identity.reputation_score < 0.3:
            return False

        return True

    async def register_agent(self, identity: AgentIdentity) -> bool:
        if await self._get_identity(identity.agent_id):
            return False
        await self._save_identity(identity)
        return True

    # ---- helpers ----
    async def _get_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        if agent_id in self._cache:
            return self._cache[agent_id]

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT identity_json FROM agent_identities WHERE agent_id = ?", (agent_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        identity = AgentIdentity.model_validate_json(row[0])
        self._cache[agent_id] = identity
        return identity

    async def _save_identity(self, identity: AgentIdentity):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO agent_identities (agent_id, identity_json, updated_at)
            VALUES (?, ?, datetime('now'))
        """, (identity.agent_id, identity.model_dump_json()))
        conn.commit()
        conn.close()
        self._cache[identity.agent_id] = identity

    async def _check_rate_limit(self, agent_id: str, limit: int) -> tuple[bool, int]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # last 60 seconds
        cur.execute("""
            SELECT COUNT(*) FROM request_logs
            WHERE agent_id = ?
              AND timestamp >= datetime('now', '-60 seconds')
        """, (agent_id,))
        (count,) = cur.fetchone()
        conn.close()

        remaining = max(0, limit - count)
        return count < limit, remaining

    async def log_request(self, agent_id: str, request_id: str, intent_type: str, success: bool, processing_time_ms: int):
        """Log a request for tracking and analytics"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO request_logs (agent_id, request_id, intent_type, success, processing_time_ms)
            VALUES (?, ?, ?, ?, ?)
        """, (agent_id, request_id, intent_type, 1 if success else 0, processing_time_ms))
        conn.commit()
        conn.close()

    async def shutdown(self):
        self._cache.clear()
