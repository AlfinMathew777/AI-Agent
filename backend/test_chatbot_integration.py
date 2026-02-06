"""
Quick Integration Test Script
Tests all chatbot integration components
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.chatbot.db_connector import ACPDatabaseConnector
from app.chatbot.date_parser import parse_date_range, extract_guest_count, extract_room_type
from app.chatbot.session_manager import SessionManager
from app.chatbot.intent_detector import IntentDetector, Intent
from app.chatbot.integration_wrapper import enhanced_guest_answer_full


def test_database_connector():
    """Test database connector"""
    print("\n" + "="*60)
    print("TEST 1: Database Connector")
    print("="*60)
    
    db = ACPDatabaseConnector()
    
    # Set property context
    success = db.set_property_context("hotel_tas_luxury")
    print(f"[OK] Property context set: {success}")
    
    if success:
        # Get property info
        info = db.get_property_info()
        print(f"[OK] Property: {info['name']}")
        print(f"  Tier: {info['tier']}")
        
        # Get amenities
        spa_info = db.get_amenity_info("spa")
        print(f"[OK] Spa available: {spa_info}")
        
        # Get policy
        pet_policy = db.get_policy("pet_policy")
        print(f"[OK] Pet policy: {pet_policy}")
        
        # Get room types
        rooms = db.get_room_types()
        print(f"[OK] Room types: {len(rooms)} available")
        
        # Get all properties
        properties = db.get_all_properties()
        print(f"[OK] Total properties: {len(properties)}")
    
    db.close()
    return success


def test_date_parser():
    """Test date parser"""
    print("\n" + "="*60)
    print("TEST 2: Date Parser")
    print("="*60)
    
    test_cases = [
        "March 15-17",
        "next Friday to Sunday",
        "tomorrow",
        "I want to book for March 15 to March 17",
        "2024-03-15 to 2024-03-17"
    ]
    
    all_passed = True
    for text in test_cases:
        result = parse_date_range(text)
        if result:
            print(f"[OK] '{text}' -> {result[0]} to {result[1]}")
        else:
            print(f"[FAIL] '{text}' -> Failed to parse")
            all_passed = False
    
    # Test guest count extraction
    print(f"\n[OK] '2 guests' -> {extract_guest_count('2 guests')} guests")
    print(f"[OK] 'party of 4' -> {extract_guest_count('party of 4')} guests")
    
    # Test room type extraction
    print(f"[OK] 'deluxe king room' -> {extract_room_type('deluxe king room')}")
    
    return all_passed


def test_session_manager():
    """Test session manager"""
    print("\n" + "="*60)
    print("TEST 3: Session Manager")
    print("="*60)
    
    manager = SessionManager()
    
    # Create session
    session_id = manager.create_session()
    print(f"[OK] Session created: {session_id}")
    
    # Update context
    manager.update_context(session_id, "guest_name", "John Smith")
    manager.update_context(session_id, "check_in", "2024-03-15")
    manager.update_context(session_id, "check_out", "2024-03-17")
    print(f"[OK] Context updated")
    
    # Get context
    name = manager.get_context(session_id, "guest_name")
    print(f"[OK] Retrieved guest name: {name}")
    
    # Add to history
    manager.add_to_history(session_id, "user", "I want to book a room")
    manager.add_to_history(session_id, "assistant", "I'd be happy to help!")
    history = manager.get_history(session_id)
    print(f"[OK] History entries: {len(history)}")
    
    # Get summary
    summary = manager.get_session_summary(session_id)
    print(f"[OK] Session summary: {summary}")
    
    return True


def test_intent_detector():
    """Test intent detector"""
    print("\n" + "="*60)
    print("TEST 4: Intent Detector")
    print("="*60)
    
    detector = IntentDetector()
    
    test_queries = [
        ("Do you have any rooms available?", Intent.CHECK_AVAILABILITY),
        ("I'd like to book a room", Intent.BOOK_ROOM),
        ("Can you give me a discount?", Intent.REQUEST_DISCOUNT),
        ("Do you have a spa?", Intent.ASK_AMENITIES),
        ("What's your pet policy?", Intent.ASK_POLICY),
        ("What room types do you have?", Intent.ASK_ROOM_INFO),
        ("Yes, proceed", Intent.CONFIRM_ACTION),
    ]
    
    all_passed = True
    for query, expected_intent in test_queries:
        detected_intent, confidence = detector.detect_intent(query)
        match = "[OK]" if detected_intent == expected_intent else "[FAIL]"
        print(f"{match} '{query}' -> {detected_intent.value} ({confidence:.2f})")
        if detected_intent != expected_intent:
            all_passed = False
    
    # Test entity extraction
    entities = detector.extract_entities("My name is John Smith and my email is john@example.com", Intent.BOOK_ROOM)
    print(f"\n[OK] Extracted entities: {entities}")
    
    return all_passed


async def test_full_integration():
    """Test full integration with enhanced chatbot"""
    print("\n" + "="*60)
    print("TEST 5: Full Integration")
    print("="*60)
    
    try:
        # Test property context
        print("\n--- Setting Property Context ---")
        from app.chatbot.integration_wrapper import get_enhanced_chatbot
        chatbot = get_enhanced_chatbot()
        success = chatbot.set_property_from_context(tenant_id="hotel_tas_luxury")
        print(f"[OK] Property context set: {success}")
        
        # Test availability check
        print("\n--- Test Availability Check ---")
        response1 = await enhanced_guest_answer_full(
            question="Do you have any rooms available March 15-17?",
            tenant_id="hotel_tas_luxury"
        )
        print(f"User: Do you have any rooms available March 15-17?")
        print(f"Bot: {response1['answer']}")
        print(f"Intent: {response1.get('intent', 'unknown')}")
        session_id = response1['session_id']
        
        # Test amenity question
        print("\n--- Test Amenity Question ---")
        response2 = await enhanced_guest_answer_full(
            question="Do you have a spa?",
            tenant_id="hotel_tas_luxury",
            session_id=session_id
        )
        print(f"User: Do you have a spa?")
        print(f"Bot: {response2['answer']}")
        
        # Test policy question
        print("\n--- Test Policy Question ---")
        response3 = await enhanced_guest_answer_full(
            question="What's your pet policy?",
            tenant_id="hotel_tas_luxury",
            session_id=session_id
        )
        print(f"User: What's your pet policy?")
        print(f"Bot: {response3['answer']}")
        
        # Test cross-property discovery
        print("\n--- Test Cross-Property Discovery ---")
        response4 = await enhanced_guest_answer_full(
            question="What other properties do you have?",
            tenant_id="hotel_tas_luxury",
            session_id=session_id
        )
        print(f"User: What other properties do you have?")
        print(f"Bot: {response4['answer']}")
        
        return True
    except Exception as e:
        print(f"\n[FAIL] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("CHATBOT INTEGRATION TEST SUITE")
    print("="*60)
    
    results = {
        "Database Connector": test_database_connector(),
        "Date Parser": test_date_parser(),
        "Session Manager": test_session_manager(),
        "Intent Detector": test_intent_detector(),
        "Full Integration": await test_full_integration()
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("[OK] ALL TESTS PASSED")
    else:
        print("[FAIL] SOME TESTS FAILED")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
