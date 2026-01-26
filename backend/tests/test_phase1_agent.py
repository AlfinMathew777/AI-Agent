
import asyncio
# We import the service functions directly to test the logic without spinning up the full HTTP server,
# mimicking what the API endpoint would do (but faster for testing).
from app.ai_service import get_guest_answer, get_staff_answer

async def test_agent_capabilities():
    print("--- Starting Phase 1 Verification ---")

    # Test 1: Guest checking availability (Allowed Tool)
    print("\n[Test 1] Guest: 'Check availability for Standard Room on 2025-01-01'")
    print("Expected: Tool Call -> 'No' (Booked)")
    response = await get_guest_answer("Check availability for Standard Room on 2025-01-01")
    print(f"Agent Response: {response}")
    
    # Test 2: Guest checking availability (Allowed Tool - Success)
    print("\n[Test 2] Guest: 'Check availability for Deluxe Room on 2025-02-01'")
    print("Expected: Tool Call -> 'Yes'")
    response = await get_guest_answer("Check availability for Deluxe Room on 2025-02-01")
    print(f"Agent Response: {response}")

    # Test 3: Guest trying to Book (Restricted Tool)
    # The Tool Filter in llm.py should hide 'book_room' from guests.
    # The LLM should say it can't do that or provide contact info.
    print("\n[Test 3] Guest: 'Book the Deluxe Room for John Doe on 2025-02-01'")
    print("Expected: Denial (No tool access)")
    response = await get_guest_answer("Book the Deluxe Room for John Doe on 2025-02-01")
    print(f"Agent Response: {response}")

    # Test 4: Staff trying to Book (Allowed Tool)
    print("\n[Test 4] Staff: 'Book the Deluxe Room for John Doe on 2025-02-01'")
    print("Expected: Tool Call -> Success")
    response = await get_staff_answer("Book the Deluxe Room for John Doe on 2025-02-01")
    print(f"Agent Response: {response}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_agent_capabilities())
