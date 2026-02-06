"""
ACP Database Connector
Provides direct access to ACP SQLite databases for property context, policies, amenities, etc.
"""

import sqlite3
import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class ACPDatabaseConnector:
    """Direct database access for chatbot to retrieve property information"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Auto-detect backend directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.join(current_dir, "..", "..")
            self.db_path = os.path.abspath(backend_dir)
        else:
            self.db_path = db_path
        
        self.property_context = None
        self._conn_cache = {}
    
    def _get_connection(self, db_name: str) -> sqlite3.Connection:
        """Get or create connection to a database"""
        if db_name not in self._conn_cache:
            db_file = os.path.join(self.db_path, db_name)
            if not os.path.exists(db_file):
                raise FileNotFoundError(f"Database not found: {db_file}")
            self._conn_cache[db_name] = sqlite3.connect(db_file)
            self._conn_cache[db_name].row_factory = sqlite3.Row
        return self._conn_cache[db_name]
    
    def set_property_context(self, property_id: str) -> bool:
        """
        Set current property from subdomain/URL param
        
        Args:
            property_id: Property identifier (e.g., 'hotel_tas_luxury', 'hotel_tas_standard')
        
        Returns:
            True if property found and set, False otherwise
        """
        try:
            conn = self._get_connection("acp_properties.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM properties WHERE property_id = ? AND is_active = 1",
                (property_id,)
            )
            row = cursor.fetchone()
            
            if row:
                config = json.loads(row["config_json"]) if row["config_json"] else {}
                self.property_context = {
                    "property_id": row["property_id"],
                    "name": row["name"],
                    "pms_type": row["pms_type"],
                    "config": config,
                    "tier": config.get("tier", "standard")
                }
                return True
            return False
        except Exception as e:
            print(f"[DB Connector] Error setting property context: {e}")
            return False
    
    def get_property_info(self) -> Dict:
        """Get current property details"""
        if not self.property_context:
            raise ValueError("No property context set. Call set_property_context() first.")
        return self.property_context
    
    def get_amenity_info(self, amenity_name: str) -> Optional[Dict]:
        """
        Query real amenities from properties.db config
        
        Args:
            amenity_name: Name of amenity (e.g., 'spa', 'pool', 'gym')
        
        Returns:
            Amenity info dict or None if not found
        """
        if not self.property_context:
            return None
        
        config = self.property_context.get("config", {})
        amenities = config.get("amenities", {})
        
        # Direct match
        if amenity_name in amenities:
            return {"name": amenity_name, "available": amenities[amenity_name]}
        
        # Fuzzy match
        for key, value in amenities.items():
            if amenity_name.lower() in key.lower():
                return {"name": key, "available": value}
        
        return None
    
    def get_room_types(self) -> List[Dict]:
        """Get actual room types from property config"""
        if not self.property_context:
            return []
        
        config = self.property_context.get("config", {})
        room_types = config.get("room_types", [])
        
        # If room_types not in config, return defaults based on tier
        if not room_types:
            tier = self.property_context.get("tier", "standard")
            if tier == "luxury":
                return [
                    {"type": "deluxe_king", "name": "Deluxe King Suite"},
                    {"type": "executive_suite", "name": "Executive Suite"},
                    {"type": "presidential", "name": "Presidential Suite"}
                ]
            elif tier == "budget":
                return [
                    {"type": "standard_double", "name": "Standard Double"},
                    {"type": "twin", "name": "Twin Room"}
                ]
            else:
                return [
                    {"type": "standard_queen", "name": "Standard Queen"},
                    {"type": "deluxe_king", "name": "Deluxe King"}
                ]
        
        return room_types
    
    def get_policy(self, policy_name: str) -> Optional[str]:
        """
        Get actual policies (pet, cancellation, etc.)
        
        Args:
            policy_name: Policy type (e.g., 'pet_policy', 'cancellation_policy')
        
        Returns:
            Policy text or None if not found
        """
        if not self.property_context:
            return None
        
        config = self.property_context.get("config", {})
        policies = config.get("policies", {})
        
        # Direct match
        if policy_name in policies:
            return policies[policy_name]
        
        # Fuzzy match
        for key, value in policies.items():
            if policy_name.lower() in key.lower():
                return value
        
        # Default policies based on tier
        tier = self.property_context.get("tier", "standard")
        defaults = {
            "luxury": {
                "pet_policy": "Pets welcome with $50/night fee. Spa and concierge services available.",
                "cancellation_policy": "Free cancellation up to 48 hours before check-in.",
                "check_in": "3:00 PM",
                "check_out": "12:00 PM (Late checkout available for premium guests)"
            },
            "standard": {
                "pet_policy": "Small pets allowed with $25/night fee.",
                "cancellation_policy": "Free cancellation up to 24 hours before check-in.",
                "check_in": "2:00 PM",
                "check_out": "11:00 AM"
            },
            "budget": {
                "pet_policy": "Pets not permitted.",
                "cancellation_policy": "Non-refundable. No changes allowed.",
                "check_in": "2:00 PM",
                "check_out": "10:00 AM"
            }
        }
        
        tier_defaults = defaults.get(tier, defaults["standard"])
        return tier_defaults.get(policy_name)
    
    def get_all_properties(self) -> List[Dict]:
        """For cross-property search"""
        try:
            conn = self._get_connection("acp_properties.db")
            cursor = conn.cursor()
            cursor.execute("SELECT property_id, name, config_json FROM properties WHERE is_active = 1")
            
            properties = []
            for row in cursor.fetchall():
                config = json.loads(row["config_json"]) if row["config_json"] else {}
                properties.append({
                    "property_id": row["property_id"],
                    "name": row["name"],
                    "tier": config.get("tier", "standard"),
                    "location": config.get("location", "Unknown")
                })
            
            return properties
        except Exception as e:
            print(f"[DB Connector] Error getting all properties: {e}")
            return []
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict]:
        """Get agent information from trust database"""
        try:
            conn = self._get_connection("acp_trust.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM agents WHERE agent_id = ?",
                (agent_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    "agent_id": row["agent_id"],
                    "agent_name": row["agent_name"],
                    "agent_type": row["agent_type"],
                    "reputation_score": row["reputation_score"],
                    "total_requests": row["total_requests"],
                    "successful_requests": row["successful_requests"]
                }
            return None
        except Exception as e:
            print(f"[DB Connector] Error getting agent info: {e}")
            return None
    

    def close(self):
        """Close all database connections"""
        for conn in self._conn_cache.values():
            conn.close()
        self._conn_cache.clear()
