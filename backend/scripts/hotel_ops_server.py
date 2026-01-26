import asyncio
from mcp.server.fastmcp import FastMCP
from typing import Literal

# Initialize FastMCP server
mcp = FastMCP("Hotel Operations")

# --- Mock Data ---
ROOM_INVENTORY = {
    "standard": {"total": 10, "booked": ["2025-01-01"]},
    "deluxe": {"total": 5, "booked": []},
    "suite": {"total": 2, "booked": ["2025-12-25"]},
}

@mcp.tool()
def check_room_availability(room_type: str, date: str) -> str:
    """
    Check if a specific room type is available on a given date.
    
    Args:
        room_type: One of 'standard', 'deluxe', 'suite'.
        date: Date in YYYY-MM-DD format.
    """
    room_type = room_type.lower()
    if room_type not in ROOM_INVENTORY:
        return f"Error: Unknown room type '{room_type}'. Available: Standard, Deluxe, Suite."
    
    inventory = ROOM_INVENTORY[room_type]
    
    # Simple check: if date is in 'booked' list, assume fully booked (simplified)
    # In a real app, we'd count bookings vs total.
    if date in inventory["booked"]:
        return f"No, {room_type.capitalize()} rooms are fully booked on {date}."
    
    return f"Yes! We have {room_type.capitalize()} rooms available on {date}."

@mcp.tool()
def book_room(guest_name: str, room_type: str, date: str) -> str:
    """
    Book a room for a guest.
    
    Args:
        guest_name: Full name of the guest.
        room_type: One of 'standard', 'deluxe', 'suite'.
        date: Date in YYYY-MM-DD format.
    """
    room_type = room_type.lower()
    if room_type not in ROOM_INVENTORY:
        return f"Error: Unknown room type '{room_type}'."
    
    # Check availability first
    if date in ROOM_INVENTORY[room_type]["booked"]:
        return f"Failed: {room_type.capitalize()} is not available on {date}."
    
    # "Book" it (in memory only for this script session)
    ROOM_INVENTORY[room_type]["booked"].append(date)
    return f"Success! Room booked for {guest_name} ({room_type.capitalize()}) on {date}. Confirmation #12345."

@mcp.tool()
def report_maintenance_issue(room_number: str, issue_description: str) -> str:
    """
    Log a maintenance request for a room.
    """
    # Simply echo back for now
    return f"Maintenance request logged for Room {room_number}: '{issue_description}'. Ticket #999 created."

if __name__ == "__main__":
    # Ensure mcp is installed: pip install mcp
    print("Starting Hotel Operations MCP Server...")
    mcp.run()
