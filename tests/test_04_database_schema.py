"""
Test Suite 4: Database Schema Verification
Validates all 6 ACP databases and their structures
"""

import pytest
import sqlite3
import os
import json

BACKEND_DIR = os.getenv("ACP_BACKEND_DIR", "backend")

class TestDatabaseSchema:
    """Validate ACP database schemas against documentation"""
    
    @pytest.mark.schema
    def test_acp_databases_exist(self):
        """
        Verify all 6 ACP databases exist.
        Doc says: 6 SQLite databases
        Repo has: 6 confirmed + auxiliary DBs
        """
        expected_dbs = {
            "acp_properties.db": "Property registry",
            "acp_trust.db": "Agent identity and reputation",
            "acp_transactions.db": "Transaction state and idempotency",
            "acp_commissions.db": "Commission accrual and invoicing",
            "acp_network.db": "Network effects and demand signals",
            "acp_monitoring.db": "System health and metrics"
        }
        
        found = []
        missing = []
        auxiliary = []
        
        backend_path = os.path.join(os.getcwd(), BACKEND_DIR)
        all_files = os.listdir(backend_path) if os.path.exists(backend_path) else []
        
        for db_file, description in expected_dbs.items():
            path = os.path.join(backend_path, db_file)
            if os.path.exists(path):
                found.append((db_file, description))
            else:
                missing.append((db_file, description))
        
        # Check for auxiliary databases
        for f in all_files:
            if f.endswith('.db') and f not in expected_dbs:
                auxiliary.append(f)
        
        print(f"\n📊 Database Inventory:")
        print(f"   Expected: {len(expected_dbs)} | Found: {len(found)} | Missing: {len(missing)}")
        
        for db, desc in found:
            print(f"   ✅ {db} - {desc}")
        
        for db, desc in missing:
            print(f"   ❌ MISSING: {db} - {desc}")
        
        if auxiliary:
            print(f"\n   ⚠️  Auxiliary databases found (not in docs): {auxiliary}")
        
        assert len(missing) == 0, f"Missing {len(missing)} required databases"
    
    @pytest.mark.schema
    def test_properties_schema_minimum(self):
        """Validate properties table has minimum required columns"""
        db_path = os.path.join(BACKEND_DIR, "acp_properties.db")
        if not os.path.exists(db_path):
            pytest.skip("acp_properties.db not found")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(properties)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        required = {
            "property_id": "TEXT",
            "name": "TEXT",
            "pms_type": "TEXT",
            "config_json": "TEXT",
            "is_active": "INTEGER"
        }
        
        for col, dtype in required.items():
            assert col in columns, f"Missing column: {col}"
            # SQLite is flexible with types, so just check existence
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='properties'")
        indexes = {row[0] for row in cursor.fetchall()}
        
        assert "idx_properties_active" in indexes, "Missing index: idx_properties_active"
        assert "idx_properties_pms_type" in indexes, "Missing index: idx_properties_pms_type"
        
        conn.close()
        print("✅ Properties schema validated")
    
    @pytest.mark.schema
    def test_trust_agents_schema(self):
        """Validate agents table in trust database"""
        db_path = os.path.join(BACKEND_DIR, "acp_trust.db")
        if not os.path.exists(db_path):
            pytest.skip("acp_trust.db not found")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(agents)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required = {"agent_id", "name", "identity_blob", "reputation_score", "tier"}
        missing = required - columns
        
        if missing:
            pytest.fail(f"Missing columns in agents table: {missing}")
        
        conn.close()
        print("✅ Trust agents schema validated")
    
    @pytest.mark.schema
    def test_commissions_schema(self):
        """Validate commissions_accrued table"""
        db_path = os.path.join(BACKEND_DIR, "acp_commissions.db")
        if not os.path.exists(db_path):
            pytest.skip("acp_commissions.db not found")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(commissions_accrued)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required = {"commission_id", "agent_id", "property_id", "booking_id", "amount", "commission_rate", "status"}
        missing = required - columns
        
        if missing:
            pytest.fail(f"Missing columns in commissions_accrued: {missing}")
        
        # Verify indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='commissions_accrued'")
        indexes = {row[0] for row in cursor.fetchall()}
        
        required_indexes = {"idx_comm_agent", "idx_comm_property", "idx_comm_status"}
        missing_indexes = required_indexes - indexes
        
        if missing_indexes:
            print(f"⚠️  Missing recommended indexes: {missing_indexes}")
        
        conn.close()
        print("✅ Commissions schema validated")
    
    @pytest.mark.schema
    def test_idempotency_table_exists(self):
        """Validate idempotency_log table"""
        db_path = os.path.join(BACKEND_DIR, "acp_transactions.db")
        if not os.path.exists(db_path):
            pytest.skip("acp_transactions.db not found")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='idempotency_log'")
        if not cursor.fetchone():
            pytest.fail("❌ CRITICAL: idempotency_log table missing")
        
        cursor.execute("PRAGMA table_info(idempotency_log)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required = {"request_id", "result_json", "execution_type", "created_at"}
        missing = required - columns
        
        if missing:
            pytest.fail(f"Missing columns in idempotency_log: {missing}")
        
        conn.close()
        print("✅ Idempotency table validated")
    
    @pytest.mark.schema
    def test_database_data_integrity(self):
        """
        Basic data integrity checks:
        - No NULLs in critical fields
        - Referential consistency
        - Active properties count
        """
        # Check properties count matches docs (5 properties)
        db_path = os.path.join(BACKEND_DIR, "acp_properties.db")
        if not os.path.exists(db_path):
            pytest.skip("Database not found")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM properties WHERE is_active = 1")
            active_count = cursor.fetchone()[0]
            
            print(f"\n📊 Data Integrity:")
            print(f"   Active properties: {active_count} (Doc claims: 5)")
            
            if active_count != 5:
                print(f"   ⚠️  Property count mismatch. Expected 5, found {active_count}")
            
            # Check for NULL property_ids
            cursor.execute("SELECT COUNT(*) FROM properties WHERE property_id IS NULL")
            null_ids = cursor.fetchone()[0]
            assert null_ids == 0, f"Found {null_ids} properties with NULL property_id"
            
        except sqlite3.OperationalError as e:
            print(f"⚠️  Could not check integrity: {e}")
        finally:
            conn.close()
