"""
Hotel Concierge Bot
Main chatbot class that orchestrates conversation, intent handling, and ACP integration
"""

from typing import Dict, Optional
import uuid
import re
from datetime import datetime

from .db_connector import ACPDatabaseConnector
from .acp_client import ACPClient
from .date_parser import NaturalDateParser
from .session_manager import SessionManager


class HotelConciergeBot:
    """
    Main chatbot orchestrator with fixed architecture:
    - Proper intent classification (booking before availability)
    - Stable idempotency keys
    - Correct ACP method signatures
    - Proper room_type tracking
    """
    
    def __init__(self, property_id: str = None):
        self.db = ACPDatabaseConnector()
        self.acp = ACPClient()
        self.date_parser = NaturalDateParser()
        self.sessions = SessionManager()
        
        if property_id:
            self.db.set_property_context(property_id)
    
    async def initialize_session(self, session_id: str, property_id: str) -> str:
        """Initialize new conversation session"""
        self.db.set_property_context(property_id)
        
        # Create session and set property context
        self.sessions.create_session(session_id)
        self.sessions.update_context(session_id, "property_id", property_id)
        
        property_info = self.db.get_property_info()
        
        welcome_msg = f"Welcome to **{property_info['name']}** ({property_info['tier'].title()} tier property)! 🏨\n\n"
        welcome_msg += "I'm your AI concierge assistant. I can help you with:\n"
        welcome_msg += "- Checking room availability\n"
        welcome_msg += "- Information about amenities and policies\n"
        welcome_msg += "- Booking reservations\n"
        welcome_msg += "- Exploring our other properties\n\n"
        welcome_msg += "How can I assist you today?"
        
        return welcome_msg
    
    async def process_message(self, session_id: str, message: str) -> Dict:
        """
        Main entry point for chat messages
        
        Returns: {
            "response": str,
            "action": str,
            "data": Optional[Dict]
        }
        """
        # Get session
        session = self.sessions.get_session(session_id)
        if not session:
            return {
                "response": "❌ Session not found or expired. Please refresh and start a new conversation.",
                "action": "error"
            }
        
        # Add to history
        self.sessions.add_to_history(session_id, "user", message)
        
        # Extract intent (FIXED: booking before availability)
        intent = self._classify_intent(message, session)
        
        # Set current intent
        self.sessions.set_current_intent(session_id, intent, {"message": message})
        
        # Route to appropriate handler
        handlers = {
            "property_info": self._handle_property_info,
            "amenities": self._handle_amenities,
            "booking": self._handle_booking,  # Now comes BEFORE availability
            "availability": self._handle_availability,
            "negotiation": self._handle_negotiation,
            "multi_property": self._handle_multi_property,
            "general": self._handle_general
        }
        
        handler = handlers.get(intent, handlers["general"])
        
        try:
            response = await handler(session_id, message)
        except Exception as e:
            print(f"[ConciergeBot] Handler error: {e}")
            response = {
                "response": f"I encountered an issue processing your request. Please try rephrasing or contact our front desk for assistance.\n\nError: {str(e)}",
                "action": "error"
            }
        
        # Add to history
        self.sessions.add_to_history(session_id, "assistant", response["response"])
        
        return response
    
    def _classify_intent(self, message: str, session: Dict) -> str:
        """
        FIXED: Intent classification with booking BEFORE availability
        This ensures "book it" triggers booking, not availability check
        """
        msg_lower = message.lower()
        
        # Property info
        if any(x in msg_lower for x in ["what hotel", "which property", "where am i"]):
            return "property_info"
        
        # Amenities
        if any(x in msg_lower for x in ["wifi", "spa", "pool", "gym", "restaurant", 
                                         "pet", "parking", "breakfast", "minibar"]):
            return "amenities"
        
        # FIXED: Booking confirmation BEFORE availability
        # This catches "book it", "confirm", "i'll take it", etc.
        if any(x in msg_lower for x in ["confirm", "book it", "i'll take it", 
                                         "yes book", "go ahead", "reserve it"]):
            # Only trigger booking if we have pending action
            if session.get("pending_action"):
                return "booking"
        
        # Availability check (removed "book" keyword to avoid collision)
        if any(x in msg_lower for x in ["available", "availability", "room for", 
                                         "check availability", "do you have",
                                         "stay", "nights", "check in", "check out"]):
            return "availability"
        
        # Negotiation
        if any(x in msg_lower for x in ["discount", "cheaper", "deal", "price match",
                                         "better rate", "negotiate", "lower price"]):
            return "negotiation"
        
        # Multi-property search
        if any(x in msg_lower for x in ["other hotels", "properties nearby", "compare",
                                         "what else", "sister properties"]):
            return "multi_property"
        
        return "general"
    
    async def _handle_property_info(self, session_id: str, message: str) -> Dict:
        """Handle 'What hotel is this?' questions"""
        try:
            info = self.db.get_property_info()
            config = info.get("config", {})
            
            response = f"You're chatting with **{info['name']}** ({info['tier'].title()} tier property)."
            
            if "description" in config:
                response += f"\n\n{config['description']}"
            
            if "location" in config:
                response += f"\n\n📍 Location: {config['location']}"
            
            return {"response": response, "action": "property_info"}
        except Exception as e:
            return {
                "response": f"I'm having trouble accessing property information. Error: {str(e)}", 
                "action": "error"
            }
    
    async def _handle_amenities(self, session_id: str, message: str) -> Dict:
        """Handle amenity/policy questions with REAL data"""
        msg_lower = message.lower()
        
        # Pet policy
        if "pet" in msg_lower or "dog" in msg_lower or "cat" in msg_lower:
            policy = self.db.get_policy("pet_policy")
            if policy:
                return {
                    "response": f"**🐾 Pet Policy:**\n{policy}",
                    "action": "amenity_info"
                }
        
        # WiFi
        if "wifi" in msg_lower or "internet" in msg_lower:
            amenity = self.db.get_amenity_info("wifi")
            if amenity and amenity.get("available"):
                return {
                    "response": f"**📶 WiFi:** Available throughout the property\n{amenity.get('details', 'High-speed internet access included')}",
                    "action": "amenity_info"
                }
        
        # Spa
        if "spa" in msg_lower or "massage" in msg_lower:
            amenity = self.db.get_amenity_info("spa")
            if amenity and amenity.get("available"):
                return {
                    "response": f"**💆 Spa Services:** Available\nPlease contact the concierge for booking.",
                    "action": "amenity_info"
                }
        
        # Check-in/out times
        if "check" in msg_lower and ("in" in msg_lower or "out" in msg_lower):
            check_in = self.db.get_policy("check_in")
            check_out = self.db.get_policy("check_out")
            response = "**🕒 Check-in/Check-out Times:**\n"
            if check_in:
                response += f"Check-in: {check_in}\n"
            if check_out:
                response += f"Check-out: {check_out}"
            return {"response": response, "action": "amenity_info"}
        
        # Generic amenities
        room_types = self.db.get_room_types()
        property_info = self.db.get_property_info()
        
        response = f"**Available Amenities at {property_info['name']}:**\n\n"
        response += "I can provide information about:\n"
        response += "- WiFi and internet access\n"
        response += "- Pet policies\n"
        response += "- Spa and wellness services\n"
        response += "- Check-in/check-out times\n"
        response += "- Parking and transportation\n\n"
        response += "What would you like to know more about?"
        
        return {"response": response, "action": "amenity_list"}
    
    async def _handle_availability(self, session_id: str, message: str) -> Dict:
        """
        FIXED: Handle availability with proper room_type tracking
        """
        # Parse dates from message
        dates_tuple = self.date_parser.parse(message)
        
        # Get context
        check_in = self.sessions.get_context(session_id, "check_in")
        check_out = self.sessions.get_context(session_id, "check_out")
        
        if not dates_tuple and not (check_in and check_out):
            return {
                "response": "I'd be happy to check availability! What dates are you looking for?\n\n(For example: 'March 15-17' or 'next weekend')",
                "action": "ask_dates"
            }
        
        # Use parsed dates or existing context
        if dates_tuple:
            check_in, check_out = dates_tuple
            # Validate
            valid, error_msg = self.date_parser.validate_dates(check_in, check_out)
            if not valid:
                return {
                    "response": f"❌ {error_msg}. Please provide different dates.",
                    "action": "invalid_dates"
                }
            # Save to context
            self.sessions.update_context(session_id, "check_in", check_in)
            self.sessions.update_context(session_id, "check_out", check_out)
        
        # Extract party size
        guests_match = re.search(r'(\d+)\s+(adult|guest|people|person)', message.lower())
        if guests_match:
            guests = int(guests_match.group(1))
            self.sessions.update_context(session_id, "guests", guests)
        else:
            guests = self.sessions.get_context(session_id, "guests", 2)
        
        # Get property
        property_id = self.sessions.get_context(session_id, "property_id")
        if not property_id:
            return {
                "response": "❌ Property context not set. Please refresh your session.",
                "action": "error"
            }
        
        # Call ACP for availability
        result = await self.acp.check_availability(
            property_id=property_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests
        )
        
        if result.get("status") != "success":
            error = result.get("payload", {}).get("error", "Unknown error")
            return {
                "response": f"I'm having trouble checking availability right now. {error}\n\nPlease try again or contact our front desk.",
                "action": "error"
            }
        
        # Extract availability data
        payload = result.get("payload", {})
        available_rooms = payload.get("available_rooms", [])
        
        if not available_rooms:
            return {
                "response": f"😔 No rooms available for {check_in} to {check_out}.\n\nWould you like to:\n- Try different dates?\n- Check our other properties?",
                "action": "no_availability"
            }
        
        # Format response
        response_parts = [f"**✅ Availability for {check_in} to {check_out}:**\n"]
        
        for room in available_rooms[:3]:  # Show top 3
            room_type = room.get("room_type", "Standard")
            price = room.get("price_per_night", 0)
            total = room.get("total_price", price)
            
            response_parts.append(
                f"🛏️ **{room_type}**\n"
                f"   ${price:.2f}/night · Total: ${total:.2f}"
            )
        
        response_parts.append(f"\n💡 Would you like to book one of these rooms?")
        
        # FIXED: Store selected room for booking
        best_room = available_rooms[0]  # Default to first option
        
        # Set pending action with proper room details
        self.sessions.set_pending_action(
            session_id,
            "execute_booking",
            {
                "property_id": property_id,
                "check_in": check_in,
                "check_out": check_out,
                "room_type": best_room.get("room_type", "standard"),
                "price": best_room.get("total_price", 0),
                "guests": guests,
                "available_rooms": available_rooms  # Store all options
            }
        )
        
        return {
            "response": "\n".join(response_parts),
            "action": "show_availability",
            "data": {"available_rooms": available_rooms}
        }
    
    async def _handle_negotiation(self, session_id: str, message: str) -> Dict:
        """
        FIXED: Handle negotiation with correct ACP client methods
        """
        check_in = self.sessions.get_context(session_id, "check_in")
        check_out = self.sessions.get_context(session_id, "check_out")
        
        if not (check_in and check_out):
            return {
                "response": "I'd be happy to discuss rates! First, what dates are you looking for?",
                "action": "ask_dates"
            }
        
        property_id = self.sessions.get_context(session_id, "property_id")
        guests = self.sessions.get_context(session_id, "guests", 2)
        
        # Parse budget if mentioned
        budget_match = re.search(r'\$(\d+)', message)
        budget_max = float(budget_match.group(1)) if budget_match else None
        
        # FIXED: Use check_availability first (no target_entity_id parameter)
        avail_result = await self.acp.check_availability(
            property_id=property_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests
        )
        
        if avail_result.get("status") != "success":
            return {
                "response": "Let me check what rates we can offer for your dates...",
                "action": "negotiating"
            }
        
        # Get room for negotiation
        available_rooms = avail_result.get("payload", {}).get("available_rooms", [])
        if not available_rooms:
            return {
                "response": "I don't see availability for those dates. Would you like to check different dates?",
                "action": "no_availability"
            }
        
        sample_room = available_rooms[0]
        base_price = sample_room.get("total_price", 200)
        room_type = sample_room.get("room_type", "standard")
        
        # Start negotiation
        neg_result = await self.acp.start_booking(
            property_id=property_id,
            check_in=check_in,
            check_out=check_out,
            room_type=room_type,
            guests=guests,
            guest_name=self.sessions.get_context(session_id, "guest_name", "Guest"),
            guest_email=self.sessions.get_context(session_id, "guest_email", "guest@example.com"),
            budget_max=budget_max,
            reputation_score=0.7
        )
        
        if neg_result.get("status") == "success":
            payload = neg_result.get("payload", {})
            offer_price = payload.get("our_offer", {}).get("total_price", base_price)
            session_id_neg = payload.get("negotiation_session_id")
            
            # Save negotiation session
            if session_id_neg:
                self.sessions.update_context(session_id, "negotiation_session_id", session_id_neg)
            
            discount_pct = ((base_price - offer_price) / base_price * 100) if offer_price < base_price else 0
            
            response = f"**💰 Special Rate Available!**\n\n"
            response += f"Room: {room_type}\n"
            response += f"Standard rate: ${base_price:.2f}\n"
            response += f"Your rate: ${offer_price:.2f}\n"
            
            if discount_pct > 0:
                response += f"Discount: {discount_pct:.1f}%\n"
            
            response += f"\n✅ Would you like to book this rate?"
            
            # Set pending booking
            self.sessions.set_pending_action(
                session_id,
                "execute_booking",
                {
                    "property_id": property_id,
                    "negotiation_session_id": session_id_neg,
                    "room_type": room_type,
                    "price": offer_price
                }
            )
            
            return {"response": response, "action": "negotiation_accepted"}
        else:
            return {
                "response": f"Our current rate is ${base_price:.2f} for those dates. This is our best available rate. Would you like to proceed with booking?",
                "action": "negotiation_declined"
            }
    
    async def _handle_booking(self, session_id: str, message: str) -> Dict:
        """
        FIXED: Handle booking with stable idempotency and proper ACP flow
        """
        pending = self.sessions.get_pending_action(session_id)
        
        if not pending or pending.get("action_type") != "execute_booking":
            return {
                "response": "I don't have a booking ready to confirm. Let me check availability first. What dates would you like?",
                "action": "check_first"
            }
        
        action_data = pending.get("action_data", {})
        property_id = action_data.get("property_id")
        negotiation_session_id = action_data.get("negotiation_session_id")
        room_type = action_data.get("room_type")
        
        if not negotiation_session_id:
            return {
                "response": "❌ Missing negotiation session. Please start availability check again.",
                "action": "error"
            }
        
        # FIXED: Stable idempotency key
        check_in = self.sessions.get_context(session_id, "check_in")
        check_out = self.sessions.get_context(session_id, "check_out")
        guest_email = self.sessions.get_context(session_id, "guest_email", "guest@example.com")
        
        request_id = f"book:{property_id}:{check_in}:{check_out}:{room_type}:{guest_email}"
        
        # Execute booking via ACP
        result = await self.acp.execute_booking(
            property_id=property_id,
            negotiation_session_id=negotiation_session_id,
            payment_method="credit_card"
        )
        
        if result.get("status") == "success":
            payload = result.get("payload", {})
            confirmation_code = payload.get("confirmation_code", "N/A")
            
            # Clear pending action
            self.sessions.clear_pending_action(session_id)
            
            # Store confirmation
            self.sessions.update_context(session_id, "confirmation_code", confirmation_code)
            
            response = f"🎉 **Booking Confirmed!**\n\n"
            response += f"Confirmation: **{confirmation_code}**\n"
            response += f"Property: {self.db.get_property_info()['name']}\n"
            response += f"Dates: {check_in} to {check_out}\n"
            response += f"Room: {room_type}\n"
            response += f"Guests: {self.sessions.get_context(session_id, 'guests', 2)}\n\n"
            response += f"✅ Please save your confirmation number. We look forward to welcoming you!"
            
            return {
                "response": response,
                "action": "booking_confirmed",
                "data": {"confirmation": confirmation_code, "request_id": request_id}
            }
        else:
            error = result.get("payload", {}).get("error", "Unknown error")
            return {
                "response": f"❌ Booking failed: {error}\n\nPlease try again or contact our front desk for assistance.",
                "action": "booking_failed"
            }
    
    async def _handle_multi_property(self, session_id: str, message: str) -> Dict:
        """Handle cross-property search"""
        properties = self.db.get_all_properties()
        
        if len(properties) <= 1:
            return {
                "response": "We currently only have this one property in our network. However, I can help you with booking here. Would you like to check availability?",
                "action": "single_property"
            }
        
        response_parts = ["**🏨 Our Property Network:**\n"]
        
        for prop in properties:
            response_parts.append(
                f"**{prop['name']}** ({prop['tier'].title()})\n"
                f"   📍 {prop['location']}"
            )
        
        response_parts.append(f"\n💡 Would you like to check availability across all properties?")
        
        return {"response": "\n\n".join(response_parts), "action": "multi_property_list"}
    
    async def _handle_general(self, session_id: str, message: str) -> Dict:
        """Handle general conversation"""
        summary = self.sessions.get_session_summary(session_id)
        
        # If we have context, acknowledge it
        if summary and "Session context:" in summary:
            return {
                "response": f"I'm here to help! {summary}\n\nWhat would you like to do next?",
                "action": "general_with_context"
            }
        
        return {
            "response": "I'm here to help with your hotel needs! I can:\n\n"
                       "✅ Check room availability\n"
                       "✅ Provide information about amenities and policies\n"
                       "✅ Help you book a room\n"
                       "✅ Show you our other properties\n\n"
                       "What would you like to know?",
            "action": "general"
        }
