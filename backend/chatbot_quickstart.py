#!/usr/bin/env python3
"""
Quick Start Script for Hotel Chatbot
Run this to test the chatbot interactively
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from chatbot.concierge_bot import HotelConciergeBot


async def interactive_demo():
    """Interactive chatbot demo"""
    print("\n" + "="*60)
    print("🏨 HOTEL CONCIERGE CHATBOT - INTERACTIVE DEMO")
    print("="*60)
    
    # Initialize bot
    print("\n[1/3] Initializing chatbot...")
    bot = HotelConciergeBot()
    
    # Create session
    session_id = "demo-session-001"
    property_id = "hotel_tas_luxury"
    
    try:
        welcome = await bot.initialize_session(session_id, property_id)
        print(f"\n✅ Bot initialized for property: {property_id}")
        print(f"\nBot: {welcome}")
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        print("\n💡 Make sure the database files exist in the backend directory:")
        print("   - backend/acp_properties.db")
        print("   - backend/acp_trust.db")
        return
    
    print("\n" + "="*60)
    print("CONVERSATION TEST SCENARIOS")
    print("="*60)
    
    # Test scenarios
    scenarios = [
        ("Property Info", "What hotel is this?"),
        ("Amenities", "Do you have WiFi?"),
        ("Check-in Time", "What time is check-in?"),
        ("Availability", "Do you have rooms available next weekend?"),
    ]
    
    for i, (title, message) in enumerate(scenarios, 1):
        print(f"\n--- Scenario {i}: {title} ---")
        print(f"User: {message}")
        
        try:
            result = await bot.process_message(session_id, message)
            print(f"\nBot: {result['response']}")
            print(f"Action: {result['action']}")
            
            if result.get('data'):
                print(f"Data: {result['data']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Interactive mode
    print("\n" + "="*60)
    print("INTERACTIVE MODE - Type 'quit' to exit")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            result = await bot.process_message(session_id, user_input)
            print(f"\nBot: {result['response']}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


async def automated_flow_test():
    """Test complete booking flow"""
    print("\n" + "="*60)
    print("🤖 AUTOMATED BOOKING FLOW TEST")
    print("="*60)
    
    bot = HotelConciergeBot()
    session_id = "auto-test-session"
    property_id = "hotel_tas_luxury"
    
    # Initialize
    print("\n[1/5] Initializing session...")
    try:
        welcome = await bot.initialize_session(session_id, property_id)
        print(f"✅ {welcome[:100]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return
    
    # Check availability
    print("\n[2/5] Checking availability...")
    result = await bot.process_message(session_id, "Do you have rooms available for March 15-17 for 2 guests?")
    print(f"✅ Action: {result['action']}")
    print(f"   Response preview: {result['response'][:150]}...")
    
    if result['action'] == 'show_availability':
        # Try to book
        print("\n[3/5] Attempting to book...")
        result = await bot.process_message(session_id, "Yes, book it")
        print(f"✅ Action: {result['action']}")
        
        if result['action'] == 'booking_confirmed':
            print(f"✅ BOOKING SUCCESSFUL!")
            print(f"   Confirmation: {result['data'].get('confirmation', 'N/A')}")
        else:
            print(f"⚠️  Booking status: {result['action']}")
    else:
        print(f"⚠️  No availability found or error occurred")
    
    # Test negotiation
    print("\n[4/5] Testing negotiation...")
    result = await bot.process_message(session_id, "Can I get a discount for next weekend?")
    print(f"✅ Action: {result['action']}")
    print(f"   Response preview: {result['response'][:150]}...")
    
    # Test amenities
    print("\n[5/5] Testing amenity queries...")
    result = await bot.process_message(session_id, "What's your pet policy?")
    print(f"✅ Action: {result['action']}")
    print(f"   Response preview: {result['response'][:150]}...")
    
    print("\n" + "="*60)
    print("AUTOMATED TEST COMPLETE ✅")
    print("="*60 + "\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hotel Chatbot Quick Start")
    parser.add_argument(
        '--mode',
        choices=['interactive', 'auto', 'both'],
        default='interactive',
        help='Demo mode (interactive, auto, or both)'
    )
    
    args = parser.parse_args()
    
    if args.mode in ['auto', 'both']:
        asyncio.run(automated_flow_test())
    
    if args.mode in ['interactive', 'both']:
        asyncio.run(interactive_demo())


if __name__ == "__main__":
    main()
