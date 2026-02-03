"""
Property Registry - Multi-tenant property management
Stores property configurations, PMS credentials, and tier settings
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Property(BaseModel):
    property_id: str
    name: str
    pms_type: str  # cloudbeds, mews, opera, sandbox
    pms_credentials_encrypted: Optional[str] = None
    config_json: Dict[str, Any] = {}
    is_active: bool = True
    created_at: Optional[str] = None


class PropertyRegistry:
    """Registry for managing multiple hotel properties"""
    
    def __init__(self, db_path: str = "acp_properties.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize property registry database"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                property_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                pms_type TEXT CHECK(pms_type IN ('cloudbeds','mews','opera','sandbox')),
                pms_credentials_encrypted TEXT,
                config_json TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_properties_active ON properties(is_active)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_properties_pms ON properties(pms_type)")
        
        conn.commit()
        conn.close()

    def register_property(self, data: Dict[str, Any]) -> bool:
        """Register a new property"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            property_id = data["property_id"]
            name = data["name"]
            pms_type = data.get("pms_type", "sandbox")
            credentials = data.get("pms_credentials", {})
            config = data.get("config", {})
            
            # Encrypt credentials (simple base64 for MVP, use proper encryption in production)
            import base64
            credentials_encrypted = base64.b64encode(
                json.dumps(credentials).encode()
            ).decode() if credentials else None
            
            config_json = json.dumps(config)
            
            cur.execute("""
                INSERT INTO properties 
                (property_id, name, pms_type, pms_credentials_encrypted, config_json, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (property_id, name, pms_type, credentials_encrypted, config_json))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"[PropertyRegistry] Error registering property: {e}")
            return False

    def get_property(self, property_id: str) -> Optional[Property]:
        """Get property by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute("""
                SELECT * FROM properties WHERE property_id = ?
            """, (property_id,))
            
            row = cur.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Decrypt credentials
            credentials_encrypted = row["pms_credentials_encrypted"]
            credentials = {}
            if credentials_encrypted:
                import base64
                try:
                    credentials = json.loads(
                        base64.b64decode(credentials_encrypted).decode()
                    )
                except:
                    pass
            
            config = json.loads(row["config_json"]) if row["config_json"] else {}
            
            return Property(
                property_id=row["property_id"],
                name=row["name"],
                pms_type=row["pms_type"],
                pms_credentials_encrypted=credentials_encrypted,
                config_json=config,
                is_active=bool(row["is_active"]),
                created_at=row["created_at"]
            )
        except Exception as e:
            print(f"[PropertyRegistry] Error getting property: {e}")
            return None

    def list_active_properties(self) -> List[Property]:
        """List all active properties"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute("""
                SELECT * FROM properties WHERE is_active = 1 ORDER BY name
            """)
            
            rows = cur.fetchall()
            conn.close()
            
            properties = []
            for row in rows:
                config = json.loads(row["config_json"]) if row["config_json"] else {}
                properties.append(Property(
                    property_id=row["property_id"],
                    name=row["name"],
                    pms_type=row["pms_type"],
                    pms_credentials_encrypted=row["pms_credentials_encrypted"],
                    config_json=config,
                    is_active=bool(row["is_active"]),
                    created_at=row["created_at"]
                ))
            
            return properties
        except Exception as e:
            print(f"[PropertyRegistry] Error listing properties: {e}")
            return []

    def update_property(self, property_id: str, patch: Dict[str, Any]) -> bool:
        """Update property configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            updates = []
            params = []
            
            if "name" in patch:
                updates.append("name = ?")
                params.append(patch["name"])
            
            if "pms_credentials" in patch:
                import base64
                credentials_encrypted = base64.b64encode(
                    json.dumps(patch["pms_credentials"]).encode()
                ).decode()
                updates.append("pms_credentials_encrypted = ?")
                params.append(credentials_encrypted)
            
            if "config" in patch:
                updates.append("config_json = ?")
                params.append(json.dumps(patch["config"]))
            
            if "is_active" in patch:
                updates.append("is_active = ?")
                params.append(1 if patch["is_active"] else 0)
            
            if not updates:
                return False
            
            params.append(property_id)
            query = f"UPDATE properties SET {', '.join(updates)} WHERE property_id = ?"
            
            cur.execute(query, params)
            conn.commit()
            conn.close()
            
            return cur.rowcount > 0
        except Exception as e:
            print(f"[PropertyRegistry] Error updating property: {e}")
            return False

    def get_property_credentials(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get decrypted PMS credentials for a property"""
        property = self.get_property(property_id)
        if not property or not property.pms_credentials_encrypted:
            return None
        
        try:
            import base64
            return json.loads(
                base64.b64decode(property.pms_credentials_encrypted).decode()
            )
        except:
            return None
