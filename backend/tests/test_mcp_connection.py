import asyncio
from app.mcp_client import MCPClient

async def test_mcp():
    print("Testing MCP Connection...")
    client = MCPClient()
    
    try:
        # 1. Connect
        await client.connect()
        
        # 2. List Tools
        print("\n--- Available Tools ---")
        tools = await client.list_tools()
        for t in tools:
            print(f"- {t.name}: {t.description}")
            
        # 3. Call Tool (Check Availability)
        print("\n--- Calling Tool: check_room_availability ---")
        result = await client.call_tool("check_room_availability", {"room_type": "standard", "date": "2025-01-01"})
        print(f"Result: {result}")
        
        # 4. Call Tool (Book Room - Success)
        print("\n--- Calling Tool: book_room (Success) ---")
        result = await client.call_tool("book_room", {"guest_name": "Test Bot", "room_type": "deluxe", "date": "2025-02-01"})
        print(f"Result: {result}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_mcp())
