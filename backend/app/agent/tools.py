import asyncio
import json
from typing import Dict, Any, List
from .schemas import ActionPlan

class ToolRegistry:
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.tools = {
            "check_room_availability": {
                "name": "check_room_availability",
                "risk": "READ",
                "description": "Check if rooms are available (params: room_type, date)."
            },
            "book_room": {
                "name": "book_room",
                "risk": "WRITE",
                "description": "Book a room for a guest (params: guest_name, room_type, date)."
            },
            "list_restaurants": {
                "name": "list_restaurants",
                "risk": "READ",
                "description": "List all restaurants in the hotel."
            },
            "list_events": {
                "name": "list_events",
                "risk": "READ",
                "description": "List upcoming events (params: from_date, to_date)."
            },
            "check_table_availability": {
                "name": "check_table_availability",
                "risk": "READ",
                "description": "Check restaurant table availability (params: restaurant_id, date, time, party_size)."
            },
            "reserve_table": {
                "name": "reserve_table",
                "risk": "WRITE",
                "description": "Reserve a restaurant table (params: restaurant_id, customer_name, date, time, party_size)."
            },
            "check_event_availability": {
                "name": "check_event_availability",
                "risk": "READ",
                "description": "Check ticket availability (params: event_id, ticket_type, qty)."
            },
            "buy_event_tickets": {
                "name": "buy_event_tickets",
                "risk": "WRITE",
                "description": "Purchase event tickets (params: event_id, customer_name, ticket_type, qty)."
            }
        }

    def get_tool(self, name: str):
        return self.tools.get(name)

    async def execute(self, tool_name: str, params: Dict[str, Any], tenant_id: str = None):
        """
        Execute tool via MCP or Internal Service.
        """
        tool_def = self.tools.get(tool_name)
        if not tool_def:
            return f"Error: Tool '{tool_name}' not found."

        if not tenant_id:
            # Fallback for dev/testing if not passed
            print("[Agent Tools] Warning: tenant_id missing, using default.")
            tenant_id = "default-tenant-0000"

        print(f"[Agent Tools] Executing {tool_name} with params: {params} (Tenant: {tenant_id})")
        
        # Initialize Providers
        from app.integrations.registry import get_provider_set
        providers = get_provider_set(tenant_id)

        # --- COMMERCE TOOLS ---
        try:
            if tool_name == "list_restaurants":
                restaurants = providers.dining.list_restaurants(tenant_id)
                # Provider returns list of dicts. Tool returns JSON string.
                # Assuming provider logic matches old service return exactly.
                # MockDiningProvider.list_restaurants returns list.
                # Original tool returned json.dumps({"restaurants": ...}) ? 
                # Wait, original tool:
                # restaurants = commerce.list_restaurants(...) -> returns dict {"restaurants": [...]}
                # My MockDiningProvider.list_restaurants returns list [...].
                # So I need to wrap it to match original output format if client expects structure.
                # Checking schemas or original output: `return json.dumps(restaurants, indent=2)` where restaurants was {"restaurants": ...}
                # So I should wrap the list.
                return json.dumps({"restaurants": restaurants}, indent=2)
                
            elif tool_name == "list_events":
                events = providers.event.list_events(
                    tenant_id, 
                    start_date=params.get("date")
                )
                return json.dumps({"events": events}, indent=2)
                
            elif tool_name == "check_table_availability":
                # MockDiningProvider.check_table_availability returns dict with keys: available, count, first_table, message
                result = providers.dining.check_table_availability(
                    tenant_id,
                    params.get("restaurant_id"),
                    params.get("date"),
                    params.get("time"), 
                    int(params.get("party_size", 2))
                )
                # Original returned: json.dumps({available, count, first_available_table})
                # My mock returns "first_table". Mapping needed?
                # Mock: "first_table": tables[0]['table_number']
                # Original: "first_available_table": tables[0]['table_number']
                # I should probably map it to preserve strict contract if FE relies on it.
                response = {
                    "available": result["available"],
                    "count": result["count"],
                    "first_available_table": result.get("first_table"), # Mapping
                    "message": result.get("message")
                }
                return json.dumps(response)
                
            elif tool_name == "reserve_table":
                # Provider returns {status, booking_id, message}
                result = providers.dining.reserve_table(
                    tenant_id,
                    params.get("restaurant_id"),
                    params.get("date"),
                    params.get("time"),
                    int(params.get("party_size", 2)),
                    params.get("name") or params.get("customer_name")
                )
                # Original returned string message directly.
                return result["message"] # Mock provider puts the full message string there.
                
            elif tool_name == "check_event_availability":
                info = providers.event.check_event_availability(
                    tenant_id,
                    params.get("event_id"),
                    int(params.get("party_size", 2)) # Quantity
                )
                return json.dumps(info)
 
            elif tool_name == "buy_event_tickets":
                result = providers.event.buy_tickets(
                    tenant_id,
                    params.get("event_id"),
                    int(params.get("quantity", 2)),
                    params.get("name") or params.get("customer_name")
                )
                return result["message"]
 
            elif tool_name == "check_room_availability":
                room_type = params.get('room_type', 'Standard')
                date = params.get('date', 'Tomorrow')
                
                result = providers.room.check_room_availability(tenant_id, room_type, date)
                # result: {available, remaining, capacity, booked}
                
                if result["available"]:
                    return f"✅ Good news! {room_type} rooms are available on {date}. (Booked: {result['booked']}/{result['capacity']}, Remaining: {result['remaining']})"
                else:
                    return f"❌ I'm sorry, {room_type} rooms are sold out on {date}. (Booked: {result['booked']}/{result['capacity']})"
            
            elif tool_name == "book_room":
                guest_name = params.get('guest_name', 'Guest')
                room_type = params.get('room_type', 'Standard')
                date = params.get('date', 'Tomorrow')
                
                # Check avail first? Provider book_room might handle it, but tool logic laid it out.
                # Actually provider book_room calls create_booking which doesn't check avail in the mock?
                # Original tool checked avail explicitly.
                # Let's replicate original logic: check then book.
                
                avail_info = providers.room.check_room_availability(tenant_id, room_type, date)
                if not avail_info["available"]:
                     return f"❌ Failed to book: {room_type} rooms are no longer available on {date}."
                
                result = providers.room.book_room(tenant_id, guest_name, room_type, date)
                if result["booking_id"]:
                    return f"🎉 Success! Room booked for {guest_name} ({room_type}) on {date}. Booking ID: {result['booking_id']}"
                else:
                    return "❌ Error: Could not process booking due to a database error."
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Tool Execution Error: {str(e)}"
        
        return "Unknown tool execution path."
