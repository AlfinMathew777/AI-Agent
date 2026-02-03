# tests/test_04_database_schema.py
"""
DATABASE SCHEMA TESTS
This verifies what's "real" vs "documented".
"""

import os
import sqlite3

BACKEND_DIR = "backend"

ACP_DBS = [
    "acp_properties.db",
    "acp_trust.db",
    "acp_transactions.db",
    "acp_commissions.db",
    "acp_network.db",
    "acp_monitoring.db"
]

def test_acp_databases_exist():
    """Test that all expected ACP databases exist."""
    missing = []
    for db in ACP_DBS:
        path = os.path.join(BACKEND_DIR, db)
        if not os.path.exists(path):
            missing.append(db)
    assert not missing, f"Missing ACP databases: {missing}"

def test_properties_schema_minimum():
    """Test properties database schema."""
    db_path = os.path.join(BACKEND_DIR, "acp_properties.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(properties)")
    cols = {r[1]: r[2] for r in cur.fetchall()}

    for required in ["property_id", "name", "pms_type", "config_json", "is_active"]:
        assert required in cols, f"Missing column: {required}"

    # indexes (don't hard fail if naming differs; but warn via assert message)
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='properties'")
    idx = [r[0] for r in cur.fetchall()]
    assert any("active" in i for i in idx), "Expected an index for is_active (name may differ)"
    assert any("pms" in i for i in idx), "Expected an index for pms_type (name may differ)"

    conn.close()

def test_idempotency_table_exists():
    """Test that idempotency_log table exists with correct schema."""
    db_path = os.path.join(BACKEND_DIR, "acp_transactions.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]

    assert "idempotency_log" in tables, "Missing idempotency_log table"

    cur.execute("PRAGMA table_info(idempotency_log)")
    cols = {r[1]: r[2] for r in cur.fetchall()}
    for required in ["request_id", "result_json", "execution_type", "created_at"]:
        assert required in cols, f"Missing column: {required}"

    conn.close()
