"""
Role-Based Access Control (RBAC) Configuration

Roles hierarchy (highest to lowest privilege):
- admin: Full platform access, can manage everything
- manager: Business intelligence, reports, limited configuration
- front_desk: Guest services, check-in/out, reservations
- housekeeping: Room cleaning tasks, room status updates
- restaurant: Food service, menu management
- guest: Booking flow, guest-facing features only
"""

from enum import Enum
from typing import List, Set


class UserRole(str, Enum):
    GUEST = "guest"
    FRONT_DESK = "front_desk"
    HOUSEKEEPING = "housekeeping"
    RESTAURANT = "restaurant"
    MANAGER = "manager"
    ADMIN = "admin"


# Define role hierarchy - who can access what
ROLE_HIERARCHY = {
    UserRole.ADMIN: 100,
    UserRole.MANAGER: 80,
    UserRole.FRONT_DESK: 60,
    UserRole.HOUSEKEEPING: 50,
    UserRole.RESTAURANT: 50,
    UserRole.GUEST: 10,
}


# Define what pages/features each role can access
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "pages": ["a2a", "chat", "admin", "operations", "analytics", "staff_chat", "management"],
        "features": ["manage_users", "manage_rooms", "view_analytics", "view_operations", 
                     "staff_ai", "management_ai", "booking", "file_upload", "system_config"],
        "api_access": ["admin", "manager", "staff", "guest"],
    },
    UserRole.MANAGER: {
        "pages": ["a2a", "chat", "operations", "analytics", "staff_chat", "management"],
        "features": ["view_analytics", "view_operations", "staff_ai", "management_ai", "booking"],
        "api_access": ["manager", "staff", "guest"],
    },
    UserRole.FRONT_DESK: {
        "pages": ["a2a", "chat", "operations", "staff_chat"],
        "features": ["view_operations", "staff_ai", "booking", "check_in_out", "reservations"],
        "api_access": ["staff", "guest"],
    },
    UserRole.HOUSEKEEPING: {
        "pages": ["operations", "staff_chat"],
        "features": ["view_operations", "staff_ai", "room_cleaning", "housekeeping_tasks"],
        "api_access": ["staff"],
    },
    UserRole.RESTAURANT: {
        "pages": ["operations", "staff_chat"],
        "features": ["view_operations", "staff_ai", "food_orders", "menu_management"],
        "api_access": ["staff"],
    },
    UserRole.GUEST: {
        "pages": ["chat"],
        "features": ["booking", "guest_services"],
        "api_access": ["guest"],
    },
}


def get_role_level(role: str) -> int:
    """Get the privilege level for a role."""
    try:
        return ROLE_HIERARCHY.get(UserRole(role), 0)
    except ValueError:
        return 0


def has_minimum_role(user_role: str, required_role: UserRole) -> bool:
    """Check if user has at least the required role level."""
    user_level = get_role_level(user_role)
    required_level = ROLE_HIERARCHY.get(required_role, 100)
    return user_level >= required_level


def can_access_page(user_role: str, page: str) -> bool:
    """Check if a user role can access a specific page."""
    try:
        role = UserRole(user_role)
        permissions = ROLE_PERMISSIONS.get(role, {})
        return page in permissions.get("pages", [])
    except ValueError:
        return False


def can_use_feature(user_role: str, feature: str) -> bool:
    """Check if a user role can use a specific feature."""
    try:
        role = UserRole(user_role)
        permissions = ROLE_PERMISSIONS.get(role, {})
        return feature in permissions.get("features", [])
    except ValueError:
        return False


def get_allowed_pages(user_role: str) -> List[str]:
    """Get list of pages a user role can access."""
    try:
        role = UserRole(user_role)
        permissions = ROLE_PERMISSIONS.get(role, {})
        return permissions.get("pages", [])
    except ValueError:
        return []


def get_allowed_features(user_role: str) -> List[str]:
    """Get list of features a user role can use."""
    try:
        role = UserRole(user_role)
        permissions = ROLE_PERMISSIONS.get(role, {})
        return permissions.get("features", [])
    except ValueError:
        return []


# Valid roles for registration/user creation
VALID_ROLES = [role.value for role in UserRole]

# Staff roles (all roles except guest)
STAFF_ROLES = [UserRole.FRONT_DESK.value, UserRole.HOUSEKEEPING.value, 
               UserRole.RESTAURANT.value, UserRole.MANAGER.value, UserRole.ADMIN.value]

# Management roles
MANAGEMENT_ROLES = [UserRole.MANAGER.value, UserRole.ADMIN.value]
