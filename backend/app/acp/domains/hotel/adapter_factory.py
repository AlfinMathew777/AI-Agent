"""
PMS Adapter Factory
Routes to appropriate adapter based on property PMS type
"""

from typing import Optional
from app.properties.registry import PropertyRegistry
from app.acp.domains.hotel.cloudbeds_adapter import CloudbedsAdapter
from app.acp.domains.hotel.adapter import HotelDomainAdapter


class AdapterFactory:
    """Factory for creating PMS adapters based on property configuration"""
    
    def __init__(self):
        self.registry = PropertyRegistry()
        self._adapter_cache = {}

    async def get_adapter(self, property_id: str):
        """Get adapter for a property, creating if needed"""
        # Check cache first
        if property_id in self._adapter_cache:
            return self._adapter_cache[property_id]
        
        # Load property from registry
        property = self.registry.get_property(property_id)
        if not property:
            # Fallback to synthetic adapter
            adapter = HotelDomainAdapter(db_path="synthetic_hotel.db")
            await adapter.initialize()
            return adapter
        
        # Route based on PMS type
        pms_type = property.pms_type.lower()
        
        if pms_type == "cloudbeds":
            credentials = self.registry.get_property_credentials(property_id)
            use_sandbox = property.config_json.get("use_sandbox", True)
            adapter = CloudbedsAdapter(
                db_path=f"cloudbeds_cache_{property_id}.db",
                use_sandbox=use_sandbox
            )
            if credentials:
                import os
                os.environ["CLOUDBEDS_CLIENT_ID"] = credentials.get("client_id", "")
                os.environ["CLOUDBEDS_CLIENT_SECRET"] = credentials.get("client_secret", "")
            await adapter.initialize()
            self._adapter_cache[property_id] = adapter
            return adapter
        
        elif pms_type == "mews":
            # Stub for future Mews integration
            from app.acp.domains.hotel.adapter import HotelDomainAdapter
            adapter = HotelDomainAdapter(db_path=f"mews_cache_{property_id}.db")
            await adapter.initialize()
            return adapter
        
        elif pms_type == "opera":
            # Stub for future Opera integration
            from app.acp.domains.hotel.adapter import HotelDomainAdapter
            adapter = HotelDomainAdapter(db_path=f"opera_cache_{property_id}.db")
            await adapter.initialize()
            return adapter
        
        elif pms_type == "sandbox":
            # Use synthetic adapter
            adapter = HotelDomainAdapter(db_path=f"synthetic_{property_id}.db")
            await adapter.initialize()
            return adapter
        
        else:
            # Default fallback
            adapter = HotelDomainAdapter(db_path="synthetic_hotel.db")
            await adapter.initialize()
            return adapter


# Global factory instance
_factory = AdapterFactory()


async def get_adapter(property_id: str):
    """Get adapter for property"""
    return await _factory.get_adapter(property_id)
