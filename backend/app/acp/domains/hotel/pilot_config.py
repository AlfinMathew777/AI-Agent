"""
Pilot Configuration Loader
Loads pilot.yaml and provides helper functions
"""

import os
import yaml
from typing import Any, Dict, Optional


_config_cache: Optional[Dict[str, Any]] = None


def get_pilot_config() -> Dict[str, Any]:
    """Load pilot configuration from YAML"""
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "config",
        "pilot.yaml"
    )
    
    if not os.path.exists(config_path):
        # Return default config
        return {
            "pilot": {
                "enabled": False,
                "property_id": "pillinger_house",
                "allowed_room_types": ["standard_queen", "deluxe_king"],
                "base_rates": {"standard_queen": 320, "deluxe_king": 450},
            }
        }
    
    with open(config_path, "r") as f:
        _config_cache = yaml.safe_load(f)
    
    return _config_cache


def is_pilot_enabled() -> bool:
    """Check if pilot mode is enabled"""
    config = get_pilot_config()
    return config.get("pilot", {}).get("enabled", False)


def get_allowed_property_id() -> Optional[str]:
    """Get the single allowed property ID in pilot mode"""
    config = get_pilot_config()
    if not is_pilot_enabled():
        return None
    return config.get("pilot", {}).get("property_id")
