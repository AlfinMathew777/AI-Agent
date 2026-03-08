"""
Enhanced AI Service
Integrates chatbot with ACP backend for real booking capabilities
"""

from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from .db_connector import ACPDatabaseConnector
from .acp_client import ACPClient
from .date_parser import parse_date_range, extract_guest_count, extract_room_type
from .session_manager import SessionManager
from .intent_detector import IntentDetector, Intent


class EnhancedAIChatbot:
    """
    Enhanced AI chatbot with full ACP integration
    Fixes all 8 critical failures:
    1. Property context detection ✓
    2. Real database integration ✓
    3. Real booking system via ACP ✓
    4. Date parsing ✓
    5. Conversation memory ✓
    6. Idempotency via gateway ✓
    7. Negotiation engine ✓
    8. Multi-property support ✓
    """
    
    def __init__(self, gateway_url: str = "http://localhost:8010"):
        self.db_connector = ACPDatabaseConnector()
        self.acp_client = ACPClient(base_url=gateway_url)
        self.session_manager = SessionManager()
        self.intent_detector = IntentDetector()
        self.default_property_id = None
    
    def set_property_from_context(self, tenant_id: Optional[str] = None, subdomain: Optional[str] = None) -> bool:
        """
        Set property context from tenant_id or subdomain
        
        Args:
            tenant_id: Tenant ID from request header
            subdomain: Subdomain from URL
        
        Returns:
            True if property context was set
        """
        # Try tenant_id first
        if tenant_id:
            if self.db_connector.set_property_context(tenant_id):
                self.default_property_id = tenant_id
                return True
        
        # Try subdomain
        if subdomain:
            # Map subdomain to property_id  
            # e.g., "luxury.southernhorizons.com" -> "hotel_tas_luxury"
            subdomain_map = {
                "luxury": "hotel_tas_luxury",
                "standard": "hotel_tas_standard",
                "budget": "hotel_tas_budget"
            }
            property_id = subdomain_map.get(subdomain)
            if property_id and self.db_connector.set_property_context(property_id):
                self.default_property_id = property_id
                return True
        
        # Fallback to first active property
        properties = self.db_connector.get_all_properties()
        if properties:
            property_id = properties[0]["property_id"]
            if self.db_connector.set_property_context(property_id):
                self.default_property_id = property_id
                return True
        
        return False
    
    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message with full context awareness
        
        Args:
            message: User message text
            session_id: Session ID for conversation continuity
            tenant_id: Tenant/property ID
        
        Returns:
            Response dict with answer, intent, actions, etc.
        """
        # Ensure property context is set
        if not self.db_connector.property_context:
            self.set_property_from_context(tenant_id=tenant_id)
        
        # Get or create session
        if not session_id:
            session_id = self.session_manager.create_session()
        else:
            if not self.session_manager.get_session(session_id):
                session_id = self.session_manager.create_session(session_id)
        
        # Add to history
        self.session_manager.add_to_history(session_id, "user", message)
        
        # Get session context
        session = self.session_manager.get_session(session_id)
        pending_action = self.session_manager.get_pending_action(session_id)
        has_pending = pending_action is not None
        
        # Detect intent
        intent, confidence = self.intent_detector.detect_intent(message, has_pending)
        
        print(f"[Enhanced Chatbot] Intent: {intent.value}, Confidence: {confidence:.2f}")
        
        # Route to appropriate handler
        try:
            if intent == Intent.CONFIRM_ACTION and pending_action:
                response = await self._handle_confirmation(session_id, pending_action)
            elif intent == Intent.DENY_ACTION and pending_action:
                response = await self._handle_denial(session_id, pending_action)
            elif intent == Intent.CHECK_AVAILABILITY:
                response = await self._handle_check_availability(session_id, message)
            elif intent == Intent.BOOK_ROOM:
                response = await self._handle_book_room(session_id, message)
            elif intent == Intent.REQUEST_DISCOUNT:
                response = await self._handle_request_discount(session_id, message)
            elif intent == Intent.ASK_AMENITIES:
                response = await self._handle_ask_amenities(session_id, message)
            elif intent == Intent.ASK_POLICY:
                response = await self._handle_ask_policy(session_id, message)
            elif intent == Intent.ASK_ROOM_INFO:
                response = await self._handle_ask_room_info(session_id, message)
            elif intent == Intent.DISCOVER_PROPERTIES:
                response = await self._handle_discover_properties(session_id, message)
            else:
                response = await self._handle_general_question(session_id, message)
            
            # Add response to history
            answer = response.get("answer", "I'm sorry, I couldn't process that.")
            self.session_manager.add_to_history(session_id, "assistant", answer)
            
            # Add session context to response
            response["session_id"] = session_id
            response["session_summary"] = self.session_manager.get_session_summary(session_id)
            
            return response
            
        except Exception as e:
            print(f"[Enhanced Chatbot] Error processing message: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"I encountered an error processing your request. Please try rephrasing or contact our front desk. (Error: {str(e)})",
                "intent": intent.value,
                "session_id": session_id,
                "error": str(e)
            }
    
    async def _handle_check_availability(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle availability check requests"""
        # Parse dates from message
        date_range = parse_date_range(message)
        
        # Extract other entities
        guest_count = extract_guest_count(message)
        room_type = extract_room_type(message)
        
        # Get context
        context = self.session_manager.get_session(session_id)["context"]
        
        # Update context if we got new info
        if date_range:
            self.session_manager.update_context(session_id, "check_in", date_range[0])
            self.session_manager.update_context(session_id, "check_out", date_range[1])
        if guest_count:
            self.session_manager.update_context(session_id, "guests", guest_count)
        if room_type:
            self.session_manager.update_context(session_id, "room_type", room_type)
        
        # Check if we have dates
        check_in = context.get("check_in") or (date_range[0] if date_range else None)
        check_out = context.get("check_out") or (date_range[1] if date_range else None)
        
        if not check_in or not check_out:
            return {
                "answer": "I'd be happy to check availability for you! What dates would you like to stay? For example, you can say 'March 15-17' or 'next Friday to Sunday'.",
                "intent": Intent.CHECK_AVAILABILITY.value,
                "needs_info": True
            }
        
        # Query ACP gateway for availability
        property_id = self.default_property_id or context.get("property_id")
        if not property_id:
            return {
                "answer": "I'm sorry, I couldn't determine which property you're inquiring about.",
                "intent": Intent.CHECK_AVAILABILITY.value,
                "error": "no_property_context"
            }
        
        property_info = self.db_connector.get_property_info()
        
        acp_response = await self.acp_client.check_availability(
            property_id=property_id,
            check_in=check_in,
            check_out=check_out,
            room_type=room_type,
            guests=guest_count
        )
        
        if acp_response.get("status") == "accepted":
            payload = acp_response.get("payload", {})
            available = payload.get("available", False)
            
            if available:
                rooms = payload.get("rooms", [])
                answer = f"Great news! {property_info['name']} has availability from {check_in} to {check_out}.\n\n"
                
                if rooms:
                    answer += "Available rooms:\n"
                    for room in rooms:
                        answer += f"- {room.get('room_type', 'Room')}: ${room.get('price', 'N/A')} per night\n"
                    answer += "\nWould you like to book one of these rooms?"
                else:
                    answer += f"We have rooms available. Would you like me to start a booking for you?"
                
                return {
                    "answer": answer,
                    "intent": Intent.CHECK_AVAILABILITY.value,
                    "available": True,
                    "rooms": rooms
                }
            else:
                answer = f"I'm sorry, {property_info['name']} doesn't have availability for {check_in} to {check_out}.\n\n"
                answer += "Would you like me to check our other properties?"
                
                return {
                    "answer": answer,
                    "intent": Intent.CHECK_AVAILABILITY.value,
                    "available": False
                }
        else:
            return {
                "answer": f"I encountered an issue checking availability: {acp_response.get('payload', {}).get('error', 'Unknown error')}",
                "intent": Intent.CHECK_AVAILABILITY.value,
                "error": acp_response.get("payload", {})
            }
    
    async def _handle_book_room(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle booking requests"""
        # Extract entities
        entities = self.intent_detector.extract_entities(message, Intent.BOOK_ROOM)
        context = self.session_manager.get_session(session_id)["context"]
        
        # Update context with extracted entities
        for key, value in entities.items():
            self.session_manager.update_context(session_id, key, value)
        
        # Parse dates if present in message
        date_range = parse_date_range(message)
        if date_range:
            self.session_manager.update_context(session_id, "check_in", date_range[0])
            self.session_manager.update_context(session_id, "check_out", date_range[1])
        
        # Check what information we need
        missing_info = self.intent_detector.needs_more_info(Intent.BOOK_ROOM, entities, context)
        if missing_info:
            return {
                "answer": missing_info,
                "intent": Intent.BOOK_ROOM.value,
                "needs_info": True
            }
        
        # We have all needed info - start negotiation
        property_id = self.default_property_id or context.get("property_id")
        check_in = context["check_in"]
        check_out = context["check_out"]
        room_type = context.get("room_type", "deluxe_king")
        guests = context.get("guests", 2)
        guest_name = context["guest_name"]
        guest_email = context["guest_email"]
        budget_max = context.get("budget_max")
        
        # Submit negotiation to ACP
        acp_response = await self.acp_client.start_booking(
            property_id=property_id,
            check_in=check_in,
            check_out=check_out,
            room_type=room_type,
            guests=guests,
            guest_name=guest_name,
            guest_email=guest_email,
            budget_max=budget_max,
            reputation_score=0.75  # Chatbot agents have good reputation
        )
        
        if acp_response.get("status") in ["negotiated", "counter"]:
            payload = acp_response.get("payload", {})
            offer = payload.get("our_offer", {})
            price = offer.get("price", 0)
            terms = offer.get("terms", {})
            
            # Store negotiation session
            negotiation_session_id = acp_response.get("negotiation_session_id")
            if negotiation_session_id:
                self.session_manager.update_context(session_id, "negotiation_session_id", negotiation_session_id)
                self.session_manager.update_context(session_id, "current_offer", offer)
            
            property_info = self.db_connector.get_property_info()
            
            answer = f"Perfect! I've prepared a booking quote for {property_info['name']}:\n\n"
            answer += f"📅 Dates: {check_in} to {check_out}\n"
            answer += f"🛏️ Room: {room_type.replace('_', ' ').title()}\n"
            answer += f"👥 Guests: {guests}\n"
            answer += f"💰 Price: ${price:.2f}\n"
            
            if terms:
                answer += f"\n✨ Included:\n"
                for key, value in terms.items():
                    if value is True:
                        answer += f"- {key.replace('_', ' ').title()}\n"
                    else:
                        answer += f"- {key.replace('_', ' ').title()}: {value}\n"
            
            if acp_response.get("status") == "negotiated":
                answer += f"\nShall I proceed with this booking for {guest_name}? (Reply 'yes' to confirm)"
                
                # Set pending action
                self.session_manager.set_pending_action(session_id, "execute_booking", {
                    "negotiation_session_id": negotiation_session_id,
                    "property_id": property_id,
                    "offer": offer
                })
            else:
                answer += f"\nWould you like to proceed with this rate, or would you prefer a different price?"
            
            return {
                "answer": answer,
                "intent": Intent.BOOK_ROOM.value,
                "offer": offer,
                "status": acp_response.get("status")
            }
        else:
            return {
                "answer": f"I encountered an issue preparing your booking: {acp_response.get('payload', {}).get('error', 'Unknown error')}",
                "intent": Intent.BOOK_ROOM.value,
                "error": acp_response.get("payload", {})
            }
    
    async def _handle_request_discount(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle discount/negotiation requests"""
        context = self.session_manager.get_session(session_id)["context"]
        
        # Check if we have an active negotiation
        negotiation_session_id = context.get("negotiation_session_id")
        if not negotiation_session_id:
            return {
                "answer": "I don't have an active booking quote to negotiate. Would you like me to check availability and create a quote first?",
                "intent": Intent.REQUEST_DISCOUNT.value,
                "needs_info": True
            }
        
        # Extract requested price from message
        entities = self.intent_detector.extract_entities(message, Intent.REQUEST_DISCOUNT)
        counter_price = entities.get("budget_max")
        
        current_offer = context.get("current_offer", {})
        current_price = current_offer.get("price", 0)
        
        if not counter_price:
            return {
                "answer": f"The current quote is ${current_price:.2f}. What price would you like to offer?",
                "intent": Intent.REQUEST_DISCOUNT.value,
                "needs_info": True
            }
        
        # Submit counter offer to ACP negotiation engine
        property_id = self.default_property_id or context.get("property_id")
        
        acp_response = await self.acp_client.continue_negotiation(
            property_id=property_id,
            negotiation_session_id=negotiation_session_id,
            counter_price=counter_price
        )
        
        if acp_response.get("status") in ["negotiated", "counter"]:
            payload = acp_response.get("payload", {})
            offer = payload.get("our_offer", {})
            new_price = offer.get("price", 0)
            
            # Update context
            self.session_manager.update_context(session_id, "current_offer", offer)
            
            if acp_response.get("status") == "negotiated":
                answer = f"Great! I can offer you ${new_price:.2f} - that's a deal! 🎉\n\n"
                answer += "Shall I proceed with the booking at this price? (Reply 'yes' to confirm)"
                
                # Set pending action
                self.session_manager.set_pending_action(session_id, "execute_booking", {
                    "negotiation_session_id": negotiation_session_id,
                    "property_id": property_id,
                    "offer": offer
                })
            else:
                round_num = payload.get("round", 1)
                answer = f"I can offer you ${new_price:.2f} (Round {round_num}).\n\n"
                answer += "Would you like to accept this price, or make another counter offer?"
            
            return {
                "answer": answer,
                "intent": Intent.REQUEST_DISCOUNT.value,
                "offer": offer,
                "status": acp_response.get("status")
            }
        elif acp_response.get("status") == "rejected":
            return {
                "answer": f"I'm sorry, but I can't go lower than ${current_price:.2f}. This is our best rate for your dates. Would you like to proceed with the current quote?",
                "intent": Intent.REQUEST_DISCOUNT.value,
                "rejected": True
            }
        else:
            return {
                "answer": f"I encountered an issue with the negotiation: {acp_response.get('payload', {}).get('error', 'Unknown error')}",
                "intent": Intent.REQUEST_DISCOUNT.value,
                "error": acp_response.get("payload", {})
            }
    
    async def _handle_ask_amenities(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle amenity questions using real database data"""
        property_info = self.db_connector.get_property_info()
        
        # Extract amenity name from message
        amenity_keywords = {
            "spa": ["spa", "massage", "treatment"],
            "pool": ["pool", "swimming"],
            "gym": ["gym", "fitness", "workout"],
            "restaurant": ["restaurant", "dining", "food"],
            "bar": ["bar", "drinks", "cocktail"],
            "parking": ["parking", "park"],
            "wifi": ["wifi", "internet", "wireless"],
            "concierge": ["concierge"],
            "room_service": ["room service"],
            "laundry": ["laundry", "dry cleaning"]
        }
        
        message_lower = message.lower()
        found_amenity = None
        
        for amenity, keywords in amenity_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                found_amenity = amenity
                break
        
        if found_amenity:
            amenity_info = self.db_connector.get_amenity_info(found_amenity)
            
            if amenity_info and amenity_info.get("available"):
                answer = f"Yes, {property_info['name']} has a {found_amenity.replace('_', ' ')}! "
                
                # Add tier-specific details
                tier = property_info.get("tier", "standard")
                if tier == "luxury":
                    if found_amenity == "spa":
                        answer += "Our luxury spa offers premium treatments. Spa access is complimentary for premium guests."
                    elif found_amenity == "pool":
                        answer += "Our heated infinity pool is open 6am-10pm daily."
                    elif found_amenity == "gym":
                        answer += "Our 24/7 fitness center features state-of-the-art equipment."
                elif tier == "standard":
                    if found_amenity == "spa":
                        answer += "Spa treatments are available for an additional fee."
                    elif found_amenity == "pool":
                        answer += "The pool is open 7am-9pm daily."
                
                return {
                    "answer": answer,
                    "intent": Intent.ASK_AMENITIES.value,
                    "amenity": found_amenity,
                    "available": True
                }
            else:
                return {
                    "answer": f"I'm sorry, {property_info['name']} doesn't have a {found_amenity.replace('_', ' ')}. However, we do have other great amenities. Would you like to know what's available?",
                    "intent": Intent.ASK_AMENITIES.value,
                    "amenity": found_amenity,
                    "available": False
                }
        
        # General amenities question
        config = property_info.get("config", {})
        amenities = config.get("amenities", {})
        
        available_amenities = [name.replace("_", " ").title() for name, available in amenities.items() if available]
        
        if available_amenities:
            answer = f"{property_info['name']} offers the following amenities:\n\n"
            for amenity in available_amenities:
                answer += f"✓ {amenity}\n"
            answer += "\nWould you like more details about any of these?"
        else:
            answer = f"{property_info['name']} is a comfortable {property_info.get('tier', 'standard')} property. What specific amenities are you interested in?"
        
        return {
            "answer": answer,
            "intent": Intent.ASK_AMENITIES.value,
            "amenities": available_amenities
        }
    
    async def _handle_ask_policy(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle policy questions using real database data"""
        property_info = self.db_connector.get_property_info()
        
        # Detect policy type
        policy_keywords = {
            "pet_policy": ["pet", "dog", "cat", "animal"],
            "cancellation_policy": ["cancel", "cancellation", "refund"],
            "check_in": ["check in", "check-in", "arrival"],
            "check_out": ["check out", "check-out", "departure", "late checkout"]
        }
        
        message_lower = message.lower()
        found_policy = None
        
        for policy, keywords in policy_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                found_policy = policy
                break
        
        if found_policy:
            policy_text = self.db_connector.get_policy(found_policy)
            
            if policy_text:
                answer = f"📋 {found_policy.replace('_', ' ').title()} at {property_info['name']}:\n\n{policy_text}"
                
                return {
                    "answer": answer,
                    "intent": Intent.ASK_POLICY.value,
                    "policy": found_policy
                }
        
        # General policy question
        answer = f"I can help you with {property_info['name']}'s policies. We have information on:\n\n"
        answer += "• Pet policy\n"
        answer += "• Cancellation policy\n"
        answer += "• Check-in/Check-out times\n\n"
        answer += "Which would you like to know about?"
        
        return {
            "answer": answer,
            "intent": Intent.ASK_POLICY.value
        }
    
    async def _handle_ask_room_info(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle room information questions"""
        property_info = self.db_connector.get_property_info()
        room_types = self.db_connector.get_room_types()
        
        answer = f"🛏️ {property_info['name']} offers the following room types:\n\n"
        
        for room in room_types:
            room_name = room.get("name", room.get("type", "Room").replace("_", " ").title())
            answer += f"• {room_name}\n"
        
        answer += "\nWould you like to check availability for any of these rooms?"
        
        return {
            "answer": answer,
            "intent": Intent.ASK_ROOM_INFO.value,
            "room_types": room_types
        }
    
    async def _handle_discover_properties(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle cross-property discovery"""
        # Parse dates if present
        date_range = parse_date_range(message)
        
        if date_range:
            # Use ACP gateway for cross-property search
            acp_response = await self.acp_client.discover_properties(
                check_in=date_range[0],
                check_out=date_range[1],
                guests=extract_guest_count(message)
            )
            
            if acp_response.get("status") == "accepted":
                payload = acp_response.get("payload", {})
                properties = payload.get("properties", [])
                
                if properties:
                    answer = f"I found {len(properties)} available properties for {date_range[0]} to {date_range[1]}:\n\n"
                    
                    for prop in properties:
                        answer += f"🏨 {prop.get('name', 'Property')}\n"
                        answer += f"   Location: {prop.get('location', 'N/A')}\n"
                        avail = prop.get('availability', {})
                        if avail.get('rooms'):
                            answer += f"   Starting at: ${avail['rooms'][0].get('price', 'N/A')}/night\n"
                        answer += "\n"
                    
                    answer += "Would you like to book at any of these properties?"
                else:
                    answer = f"I'm sorry, we don't have availability across our properties for {date_range[0]} to {date_range[1]}. Would you like to try different dates?"
                
                return {
                    "answer": answer,
                    "intent": Intent.DISCOVER_PROPERTIES.value,
                    "properties": properties
                }
        
        # No dates - just list properties
        properties = self.db_connector.get_all_properties()
        
        answer = "Southern Horizons Hospitality Group operates the following properties:\n\n"
        
        for prop in properties:
            answer += f"🏨 {prop['name']}\n"
            answer += f"   Location: {prop['location']}\n"
            answer += f"   Tier: {prop['tier'].title()}\n\n"
        
        answer += "Would you like to check availability at any of these properties?"
        
        return {
            "answer": answer,
            "intent": Intent.DISCOVER_PROPERTIES.value,
            "properties": properties
        }
    
    async def _handle_general_question(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle general questions - fallback to standard AI"""
        property_info = self.db_connector.get_property_info() if self.db_connector.property_context else None
        
        # Build context
        context_text = ""
        if property_info:
            context_text = f"You are the AI concierge for {property_info['name']}, a {property_info.get('tier', 'standard')} tier hotel. "
        
        context_text += self.session_manager.get_session_summary(session_id)
        
        # For now, return a helpful message
        # In production, this would integrate with the existing LLM
        answer = "I'm here to help! I can assist with:\n\n"
        answer += "• Checking room availability\n"
        answer += "• Making reservations\n"
        answer += "• Information about amenities\n"
        answer += "• Hotel policies\n"
        answer += "• Finding other properties\n\n"
        
        if property_info:
            answer += f"I'm currently assisting you with {property_info['name']}. "
        
        answer += "What would you like to know?"
        
        return {
            "answer": answer,
            "intent": Intent.GENERAL_QUESTION.value,
            "context": context_text
        }
    
    async def _handle_confirmation(self, session_id: str, pending_action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user confirmation of pending action"""
        action_type = pending_action["action_type"]
        action_data = pending_action["action_data"]
        
        if action_type == "execute_booking":
            # Execute the booking via ACP
            negotiation_session_id = action_data["negotiation_session_id"]
            property_id = action_data["property_id"]
            offer = action_data["offer"]
            
            acp_response = await self.acp_client.execute_booking(
                property_id=property_id,
                negotiation_session_id=negotiation_session_id
            )
            
            # Clear pending action
            self.session_manager.clear_pending_action(session_id)
            
            if acp_response.get("status") == "confirmed":
                payload = acp_response.get("payload", {})
                confirmation_code = payload.get("confirmation_code", "PENDING")
                
                context = self.session_manager.get_session(session_id)["context"]
                guest_name = context.get("guest_name", "Guest")
                guest_email = context.get("guest_email", "")
                
                property_info = self.db_connector.get_property_info()
                
                answer = f"🎉 Booking confirmed!\n\n"
                answer += f"Confirmation Code: {confirmation_code}\n"
                answer += f"Property: {property_info['name']}\n"
                answer += f"Dates: {context.get('check_in')} to {context.get('check_out')}\n"
                answer += f"Price: ${offer.get('price', 0):.2f}\n\n"
                answer += f"A confirmation email has been sent to {guest_email}.\n"
                answer += f"Thank you for choosing {property_info['name']}, {guest_name}! We look forward to welcoming you."
                
                return {
                    "answer": answer,
                    "intent": "booking_confirmed",
                    "confirmation_code": confirmation_code,
                    "success": True
                }
            else:
                return {
                    "answer": f"I'm sorry, there was an issue completing your booking: {acp_response.get('payload', {}).get('error', 'Unknown error')}. Please try again or contact our front desk.",
                    "intent": "booking_failed",
                    "error": acp_response.get("payload", {}),
                    "success": False
                }
        
        return {
            "answer": "Action confirmed.",
            "intent": "confirm_action"
        }
    
    async def _handle_denial(self, session_id: str, pending_action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user denial of pending action"""
        self.session_manager.clear_pending_action(session_id)
        
        return {
            "answer": "No problem! Is there anything else I can help you with?",
            "intent": "deny_action"
        }
