from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

# --- Restaurants ---
class RestaurantBase(BaseModel):
    name: str
    location: str
    phone: str
    hours_json: Dict[str, str]

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantResponse(RestaurantBase):
    id: str
    tenant_id: str
    created_at: datetime

# --- Menus ---
class MenuBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True

class MenuCreate(MenuBase):
    restaurant_id: str

class MenuResponse(MenuBase):
    id: str
    restaurant_id: str
    tenant_id: str

# --- Menu Items ---
class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tags: List[str] = []
    image_url: Optional[str] = None
    is_available: bool = True

class MenuItemCreate(MenuItemBase):
    menu_id: str

class MenuItemResponse(MenuItemBase):
    id: str
    menu_id: str
    tenant_id: str

# --- Events ---
class EventBase(BaseModel):
    title: str
    venue: str
    start_time: datetime
    end_time: datetime
    status: str = "scheduled"
    description: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: str
    tenant_id: str
    created_at: datetime
