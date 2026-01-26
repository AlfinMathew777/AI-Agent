
from typing import Dict
from collections import namedtuple

from app.integrations.base import RoomProvider, DiningProvider, EventProvider
from app.integrations.mock_room import MockRoomProvider
from app.integrations.mock_dining import MockDiningProvider
from app.integrations.mock_event import MockEventProvider
from app.core.config import INTEGRATION_MODE

ProviderSet = namedtuple('ProviderSet', ['room', 'dining', 'event'])

class ProviderRegistry:
    def __init__(self):
        self._providers = {} # Cache if needed

    def get_provider_set(self, tenant_id: str) -> ProviderSet:
        # In a real app, we might check DB for tenant specific config.
        # For now, default to env or "mock".
        
        # We can reuse instances since they are stateless (they accept tenant_id in methods)
        # OR they instantiate services internally.
        # Our mock implementations allow stateless usage (methods take tenant_id).
        
        return ProviderSet(
            room=MockRoomProvider(),
            dining=MockDiningProvider(),
            event=MockEventProvider()
        )

# Global singleton
registry = ProviderRegistry()

def get_provider_set(tenant_id: str) -> ProviderSet:
    return registry.get_provider_set(tenant_id)
