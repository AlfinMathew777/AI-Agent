
import uuid
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.db.session import get_db_connection

class PricingService:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        # MVP Pricing Constants (Cents)
        self.ROOM_PRICING = {
            "standard": 18000, # $180
            "deluxe": 25000,   # $250
            "suite": 40000     # $400
        }
        self.DINNER_PER_PERSON = 4500 # $45
        self.EVENT_PRICE_DEFAULT = 7500 # $75
        self.BOOKING_FEE = 250 # $2.50
        self.TAX_RATE = 0.10 # 10% GST

    def calculate_quote(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quote based on context items.
        Context expected to contain:
        - room_type (str)
        - party_size (int)
        - selected_event (dict with price)
        - selected_restaurant (dict)
        """
        line_items = []
        subtotal = 0
        
        # 1. Room
        if "room_type" in context:
            rtype = context["room_type"].lower()
            price = self.ROOM_PRICING.get(rtype, self.ROOM_PRICING["standard"])
            line_items.append({
                "type": "room",
                "name": f"Room: {rtype.capitalize()}",
                "quantity": 1,
                "unit_price_cents": price,
                "total_cents": price
            })
            subtotal += price
            
        # 2. Dinner
        if "selected_restaurant" in context:
            party_size = int(context.get("party_size", 2))
            rest = context["selected_restaurant"]
            name = rest.get("name", "Dinner")
            price = self.DINNER_PER_PERSON
            total = price * party_size
            
            line_items.append({
                "type": "dinner",
                "name": f"Dinner at {name}",
                "quantity": party_size,
                "unit_price_cents": price,
                "total_cents": total
            })
            subtotal += total

        # 3. Event
        if "selected_event" in context:
            party_size = int(context.get("party_size", 2))
            evt = context["selected_event"]
            name = evt.get("name", "Event")
            # Use specific price if available, else default
            price = evt.get("ticket_price_cents") or evt.get("price") or self.EVENT_PRICE_DEFAULT
            total = price * party_size
            
            line_items.append({
                "type": "event",
                "name": f"Tickets: {name}",
                "quantity": party_size,
                "unit_price_cents": price,
                "total_cents": total
            })
            subtotal += total
            
        # 4. Fees
        # Booking fee (once per package or transaction)
        fees = self.BOOKING_FEE
        
        # 5. Tax
        tax = int(subtotal * self.TAX_RATE)
        
        total = subtotal + tax + fees
        
        return {
            "currency": "AUD",
            "line_items": line_items,
            "totals": {
                "subtotal_cents": subtotal,
                "tax_cents": tax,
                "fees_cents": fees,
                "total_cents": total
            }
        }

    def create_quote(self, session_id: str, context: Dict[str, Any], audience: str = "guest") -> Dict[str, Any]:
        """Generate and save a quote."""
        calculation = self.calculate_quote(context)
        quote_id = str(uuid.uuid4())
        
        conn = get_db_connection()
        conn.execute(
            '''INSERT INTO quotes (
                id, tenant_id, session_id, audience, status, currency, 
                subtotal_cents, tax_cents, fees_cents, total_cents, breakdown_json, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                quote_id, self.tenant_id, session_id, audience, "proposed",
                calculation["currency"],
                calculation["totals"]["subtotal_cents"],
                calculation["totals"]["tax_cents"],
                calculation["totals"]["fees_cents"],
                calculation["totals"]["total_cents"],
                json.dumps(calculation["line_items"]),
                "Automated Quote"
            )
        )
        conn.commit()
        conn.close()
        
        return {
            "quote_id": quote_id,
            **calculation
        }

    def create_receipt(self, quote_id: str, session_id: str, booking_refs: Dict[str, str]) -> Dict[str, Any]:
        """Convert a confirmed quote into a receipt."""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row # Use global import or consistent helper? Helper returns Row factory.
        
        # Fetch Quote
        quote = conn.execute("SELECT * FROM quotes WHERE id = ? AND tenant_id = ?", (quote_id, self.tenant_id)).fetchone()
        if not quote:
            conn.close()
            return None
            
        receipt_id = str(uuid.uuid4())
        
        conn.execute(
            '''INSERT INTO receipts (
                id, tenant_id, quote_id, session_id, status, currency,
                subtotal_cents, tax_cents, fees_cents, total_cents,
                breakdown_json, booking_refs_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                receipt_id, self.tenant_id, quote_id, session_id, "confirmed",
                quote["currency"],
                quote["subtotal_cents"],
                quote["tax_cents"],
                quote["fees_cents"],
                quote["total_cents"],
                quote["breakdown_json"],
                json.dumps(booking_refs)
            )
        )
        
        # Update Quote Status
        conn.execute("UPDATE quotes SET status = 'accepted' WHERE id = ?", (quote_id,))
        
        conn.commit()
        conn.close()
        
        return {
            "receipt_id": receipt_id,
            "total_cents": quote["total_cents"],
            "booking_refs": booking_refs
        }
