"""
Intent Detector
Detects user intent from natural language and routes to appropriate handlers
"""

import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum


class Intent(Enum):
    """Supported chatbot intents"""
    CHECK_AVAILABILITY = "check_availability"
    BOOK_ROOM = "book_room"
    CANCEL_BOOKING = "cancel_booking"
    MODIFY_BOOKING = "modify_booking"
    REQUEST_DISCOUNT = "request_discount"
    ASK_AMENITIES = "ask_amenities"
    ASK_POLICY = "ask_policy"
    ASK_ROOM_INFO = "ask_room_info"
    ASK_PRICING = "ask_pricing"
    DISCOVER_PROPERTIES = "discover_properties"
    GENERAL_QUESTION = "general_question"
    CONFIRM_ACTION = "confirm_action"
    DENY_ACTION = "deny_action"


class IntentDetector:
    """Detects user intent from natural language queries"""
    
    def __init__(self):
        # Intent patterns (regex patterns and keywords)
        self.intent_patterns = {
            Intent.CHECK_AVAILABILITY: [
                r'(?:check|see|find)\s+(?:availability|if\s+available)',
                r'do\s+you\s+have\s+(?:any\s+)?rooms?\s+(?:available|free)',
                r'(?:available|free)\s+rooms?',
                r'rooms?\s+(?:for|on)',
                r'what.*available'
            ],
            Intent.BOOK_ROOM: [
                r'book\s+(?:a\s+)?room',
                r'make\s+(?:a\s+)?(?:reservation|booking)',
                r'reserve\s+(?:a\s+)?room',
                r'i\s+(?:want|would\s+like|need)\s+to\s+book',
                r'can\s+i\s+book'
            ],
            Intent.CANCEL_BOOKING: [
                r'cancel\s+(?:my\s+)?(?:booking|reservation)',
                r'need\s+to\s+cancel',
                r'want\s+to\s+cancel'
            ],
            Intent.MODIFY_BOOKING: [
                r'change\s+(?:my\s+)?(?:booking|reservation)',
                r'modify\s+(?:my\s+)?(?:booking|reservation)',
                r'update\s+(?:my\s+)?(?:booking|reservation)'
            ],
            Intent.REQUEST_DISCOUNT: [
                r'discount',
                r'better\s+(?:price|rate)',
                r'cheaper',
                r'can\s+you\s+do\s+better',
                r'negotiate',
                r'deal'
            ],
            Intent.ASK_AMENITIES: [
                r'(?:do\s+you\s+have|is\s+there)\s+(?:a\s+)?(?:pool|spa|gym|restaurant|bar)',
                r'what\s+amenities',
                r'what\s+facilities',
                r'spa.*(?:price|cost|fee)',
                r'pool.*(?:hours|open)',
                r'gym.*(?:hours|open)'
            ],
            Intent.ASK_POLICY: [
                r'(?:pet|dog|cat)\s+(?:policy|allowed|friendly)',
                r'cancellation\s+policy',
                r'check[-\s]?in\s+(?:time|policy)',
                r'check[-\s]?out\s+(?:time|policy)',
                r'late\s+checkout',
                r'early\s+check[-\s]?in'
            ],
            Intent.ASK_ROOM_INFO: [
                r'(?:tell|what).*about.*(?:room|suite)',
                r'room\s+types?',
                r'what\s+rooms?\s+do\s+you\s+have',
                r'(?:deluxe|king|queen|suite).*(?:room|bed)'
            ],
            Intent.ASK_PRICING: [
                r'how\s+much.*(?:cost|price)',
                r'what.*(?:price|rate|cost)',
                r'pricing',
                r'rates?'
            ],
            Intent.DISCOVER_PROPERTIES: [
                r'what\s+(?:other\s+)?(?:properties|hotels)\s+do\s+you\s+have',
                r'list\s+all\s+(?:properties|hotels)',
                r'show\s+me\s+(?:all\s+)?(?:properties|hotels)',
                r'other\s+locations?'
            ],
            Intent.CONFIRM_ACTION: [
                r'^(?:yes|yeah|yep|sure|ok|okay|confirm|proceed|go\s+ahead)',
                r'yes,?\s+(?:please|do\s+it)',
                r'sounds?\s+good'
            ],
            Intent.DENY_ACTION: [
                r'^(?:no|nope|nah|cancel|nevermind|never\s+mind)',
                r'(?:don\'t|do\s+not)\s+(?:proceed|book|continue)',
                r'changed\s+my\s+mind'
            ]
        }
    
    def detect_intent(self, text: str, has_pending_action: bool = False) -> Tuple[Intent, float]:
        """
        Detect intent from user input
        
        Args:
            text: User input text
            has_pending_action: Whether there's a pending action awaiting confirmation
        
        Returns:
            Tuple of (Intent, confidence_score)
        """
        text_lower = text.lower().strip()
        
        # If there's a pending action, prioritize confirm/deny intents
        if has_pending_action:
            for intent in [Intent.CONFIRM_ACTION, Intent.DENY_ACTION]:
                score = self._match_intent(text_lower, intent)
                if score > 0.5:
                    return (intent, score)
        
        # Score all intents
        scores = {}
        for intent in Intent:
            scores[intent] = self._match_intent(text_lower, intent)
        
        # Get highest scoring intent
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        # If score is too low, default to general question
        if max_score < 0.3:
            return (Intent.GENERAL_QUESTION, 1.0)
        
        return (max_intent, max_score)
    
    def _match_intent(self, text: str, intent: Intent) -> float:
        """
        Calculate match score for an intent
        
        Args:
            text: User input text (lowercased)
            intent: Intent to match
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if intent not in self.intent_patterns:
            return 0.0
        
        patterns = self.intent_patterns[intent]
        matches = 0
        
        for pattern in patterns:
            if re.search(pattern, text):
                matches += 1
        
        if matches == 0:
            return 0.0
        
        # Normalize score based on number of patterns matched
        return min(1.0, matches / len(patterns) + 0.5)
    
    def extract_entities(self, text: str, intent: Intent) -> Dict[str, Any]:
        """
        Extract entities based on intent
        
        Args:
            text: User input text
            intent: Detected intent
        
        Returns:
            Dict of extracted entities
        """
        entities = {}
        text_lower = text.lower()
        
        # Extract guest name (look for "my name is X" or "I'm X")
        name_patterns = [
            r'my\s+name\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'i\'m\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'this\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text)  # Use original text for capitalization
            if match:
                entities['guest_name'] = match.group(1)
                break
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        if match:
            entities['guest_email'] = match.group(0)
        
        # Extract phone number
        phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        match = re.search(phone_pattern, text)
        if match:
            entities['guest_phone'] = match.group(0)
        
        # Extract price/budget
        price_pattern = r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(price_pattern, text)
        if match:
            price_str = match.group(1).replace(',', '')
            entities['budget_max'] = float(price_str)
        
        # Extract number of nights
        nights_pattern = r'(\d+)\s+nights?'
        match = re.search(nights_pattern, text_lower)
        if match:
            entities['num_nights'] = int(match.group(1))
        
        return entities
    
    def needs_more_info(self, intent: Intent, entities: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """
        Check if more information is needed to fulfill intent
        
        Args:
            intent: Detected intent
            entities: Extracted entities
            context: Session context
        
        Returns:
            Question to ask user, or None if no info needed
        """
        combined = {**context, **entities}
        
        if intent in [Intent.CHECK_AVAILABILITY, Intent.BOOK_ROOM]:
            # Need dates
            if "check_in" not in combined or "check_out" not in combined:
                return "What dates would you like to stay? For example, 'March 15-17' or 'next Friday to Sunday'."
            
            # Need guest count
            if "guests" not in combined:
                return "How many guests will be staying?"
            
            # For booking, need guest info
            if intent == Intent.BOOK_ROOM:
                if "guest_name" not in combined:
                    return "May I have your name for the reservation?"
                
                if "guest_email" not in combined:
                    return "What email address should I use for the booking confirmation?"
        
        elif intent == Intent.REQUEST_DISCOUNT:
            # Need current negotiation session
            if "negotiation_session_id" not in combined:
                return "I don't have an active booking quote. Would you like me to check availability first?"
        
        return None
