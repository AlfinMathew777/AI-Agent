"""Guest Agent - Analyzes user intent and routes to appropriate agents."""

import json
import re
from .base_agent import BaseAgent


SYSTEM = """You are the Guest Agent for Southern Horizons Hotel AI system.
Your role is to analyze guest requests and extract structured booking intent.

CRITICAL: When a guest mentions ANY of these words, the intent MUST be "booking" or "availability":
- "book", "reserve", "want to stay", "rooms for", "nights", "check in", "check-in"
- "suite", "deluxe", "standard", "ocean view" + any number
- "availability", "available rooms", "is there a room"

When given a guest message, respond ONLY with a valid JSON object:
{
  "intent": "booking" | "inquiry" | "complaint" | "general" | "availability" | "negotiation",
  "confidence": 0.0-1.0,
  "entities": {
    "check_in": "YYYY-MM-DD or null",
    "check_out": "YYYY-MM-DD or null",
    "nights": number or null,
    "rooms": number or null,
    "room_type": "standard|deluxe|suite|ocean view|null",
    "guests": number or null,
    "budget": number or null,
    "discount_requested": true/false,
    "discount_percent": number or null
  },
  "summary": "One-line summary of the guest request"
}

EXAMPLES:
- "Book 2 deluxe rooms for 3 nights" → intent: "booking", rooms: 2, room_type: "deluxe", nights: 3
- "I want a suite tomorrow" → intent: "booking", room_type: "suite", nights: 1
- "Can I get 10% off for 5 nights?" → intent: "negotiation", nights: 5, discount_requested: true, discount_percent: 10
- "What amenities do you have?" → intent: "inquiry"

Extract dates intelligently. TODAY is provided in the context."""


class GuestAgent(BaseAgent):
    def __init__(self, broadcast_fn=None):
        super().__init__(
            agent_id="guest_agent",
            name="Guest Agent",
            system_message=SYSTEM,
            broadcast_fn=broadcast_fn,
        )

    async def analyze(self, message: str, session_id: str = "") -> dict:
        await self.broadcast(
            action="Analyzing Intent",
            content=f'Processing: "{message[:80]}..."' if len(message) > 80 else f'Processing: "{message}"',
            status="processing",
            session_id=session_id,
        )

        from datetime import date
        today = date.today().isoformat()
        prompt = f"Today is {today}. Guest message: {message}"

        raw = await self.think(prompt, session_id)

        # Extract JSON from the response
        try:
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"intent": "general", "confidence": 0.5, "entities": {}, "summary": message[:100]}
        except Exception:
            result = {"intent": "general", "confidence": 0.5, "entities": {}, "summary": message[:100]}

        # Keyword-based intent correction (ensure LLM didn't misclassify obvious booking requests)
        msg_lower = message.lower()
        booking_keywords = ["book", "reserve", "reservation", "want a room", "want to stay", "check in", "check-in", "nights", " rooms", "suite", "deluxe", "ocean view", "available for"]
        discount_keywords = ["discount", "off", "deal", "negotiate", "% off", "percent off", "cheaper", "better price"]

        if result.get("intent") in ("general", "inquiry") and any(k in msg_lower for k in booking_keywords):
            result["intent"] = "booking"
            result["confidence"] = 0.85

        if any(k in msg_lower for k in discount_keywords):
            result["intent"] = "negotiation"
            result.setdefault("entities", {})["discount_requested"] = True

        # Extract room count from message if LLM missed it
        import re as _re
        if not result.get("entities", {}).get("rooms"):
            room_match = _re.search(r'(\d+)\s*room', msg_lower)
            if room_match:
                result.setdefault("entities", {})["rooms"] = int(room_match.group(1))

        # Extract nights from message if LLM missed it
        if not result.get("entities", {}).get("nights"):
            night_match = _re.search(r'(\d+)\s*night', msg_lower)
            if night_match:
                result.setdefault("entities", {})["nights"] = int(night_match.group(1))

        # Extract room type
        if not result.get("entities", {}).get("room_type"):
            for rtype in ["suite", "deluxe", "ocean view", "standard"]:
                if rtype in msg_lower:
                    result.setdefault("entities", {})["room_type"] = rtype
                    break

        await self.broadcast(
            action="Intent Classified",
            content=f"Intent: {result.get('intent', 'general').upper()} — {result.get('summary', '')}",
            status="completed",
            metadata=result,
            session_id=session_id,
        )

        return result
