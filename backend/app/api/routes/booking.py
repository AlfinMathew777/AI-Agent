"""
Guided Booking Flow API

Provides step-by-step guided booking for guests with:
- Room availability check
- Service add-ons
- Booking summary
- Stripe checkout integration
"""

import os
import uuid
import sqlite3
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.db.session import get_db_connection
from app.api.deps import get_current_user_optional, get_tenant_header
from app.schemas.auth import TokenData

load_dotenv()

router = APIRouter()

# ============================================================
# Models
# ============================================================

class DateRangeRequest(BaseModel):
    check_in: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    guests: int = Field(default=2, ge=1, le=10)


class RoomOption(BaseModel):
    id: str
    room_number: str
    room_type: str
    price_per_night: float
    capacity: int
    amenities: List[str]
    description: str
    floor: int
    available: bool


class ServiceOption(BaseModel):
    id: str
    name: str
    description: str
    price: float
    per_night: bool = False


class BookingSummaryRequest(BaseModel):
    room_id: str
    check_in: str
    check_out: str
    guests: int
    services: List[str] = []
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None


class BookingSummary(BaseModel):
    room: RoomOption
    check_in: str
    check_out: str
    nights: int
    guests: int
    services: List[ServiceOption]
    room_total: float
    services_total: float
    taxes: float
    total: float
    breakdown: List[Dict[str, Any]]


class CheckoutRequest(BaseModel):
    booking_summary: Dict[str, Any]
    guest_name: str
    guest_email: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
    booking_id: str


# ============================================================
# Available Services
# ============================================================

HOTEL_SERVICES = [
    {
        "id": "breakfast",
        "name": "Daily Breakfast",
        "description": "Full breakfast buffet (7am-10am)",
        "price": 25.00,
        "per_night": True
    },
    {
        "id": "airport_pickup",
        "name": "Airport Pickup",
        "description": "Private car from airport",
        "price": 45.00,
        "per_night": False
    },
    {
        "id": "late_checkout",
        "name": "Late Checkout",
        "description": "Checkout extended to 4pm",
        "price": 35.00,
        "per_night": False
    },
    {
        "id": "extra_bed",
        "name": "Extra Bed",
        "description": "Rollaway bed in room",
        "price": 30.00,
        "per_night": True
    },
    {
        "id": "parking",
        "name": "Valet Parking",
        "description": "Secured underground parking",
        "price": 20.00,
        "per_night": True
    },
    {
        "id": "spa_access",
        "name": "Spa Access",
        "description": "Access to spa and pool",
        "price": 40.00,
        "per_night": True
    }
]

# Room type descriptions and base prices
ROOM_DESCRIPTIONS = {
    "Standard": {
        "description": "Comfortable room with essential amenities. Perfect for budget-conscious travelers.",
        "base_price": 180.00
    },
    "Deluxe": {
        "description": "Spacious room with premium bedding and city views. Great for business travelers.",
        "base_price": 260.00
    },
    "Suite": {
        "description": "Luxurious suite with separate living area. Ideal for families or extended stays.",
        "base_price": 420.00
    },
    "Ocean View": {
        "description": "Beautiful room with panoramic ocean views and balcony. Perfect for romantic getaways.",
        "base_price": 320.00
    },
    "Penthouse": {
        "description": "Ultimate luxury with private terrace and premium amenities. Our finest accommodation.",
        "base_price": 780.00
    }
}


# ============================================================
# Helper Functions
# ============================================================

def get_room_price(room_type: str) -> float:
    """Get base price for room type."""
    return ROOM_DESCRIPTIONS.get(room_type, {}).get("base_price", 200.00)


def get_room_description(room_type: str) -> str:
    """Get description for room type."""
    return ROOM_DESCRIPTIONS.get(room_type, {}).get("description", "Comfortable hotel room.")


def parse_amenities(amenities_str: str) -> List[str]:
    """Parse amenities string into list."""
    if not amenities_str:
        return ["WiFi", "TV", "AC"]
    return [a.strip() for a in amenities_str.split(",")]


def calculate_nights(check_in: str, check_out: str) -> int:
    """Calculate number of nights between dates."""
    d1 = datetime.strptime(check_in, "%Y-%m-%d").date()
    d2 = datetime.strptime(check_out, "%Y-%m-%d").date()
    return (d2 - d1).days


# ============================================================
# API Endpoints
# ============================================================

@router.get("/booking/services")
async def get_available_services():
    """Get all available add-on services."""
    return {"services": HOTEL_SERVICES}


@router.post("/booking/rooms/available")
async def get_available_rooms(
    request: DateRangeRequest,
    tenant_id: str = Depends(get_tenant_header)
):
    """
    Get available rooms for the given date range.
    Returns rooms with pricing and descriptions.
    """
    # Validate dates
    try:
        check_in = datetime.strptime(request.check_in, "%Y-%m-%d").date()
        check_out = datetime.strptime(request.check_out, "%Y-%m-%d").date()
        
        if check_in >= check_out:
            raise HTTPException(status_code=400, detail="Check-out must be after check-in")
        if check_in < date.today():
            raise HTTPException(status_code=400, detail="Check-in cannot be in the past")
        if (check_out - check_in).days > 30:
            raise HTTPException(status_code=400, detail="Maximum stay is 30 nights")
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    nights = (check_out - check_in).days
    
    # Query available rooms
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        
        # Get rooms that are available (not booked for these dates)
        cursor.execute("""
            SELECT r.* FROM rooms r
            WHERE r.tenant_id = ?
            AND r.status = 'available'
            AND r.capacity >= ?
            AND r.id NOT IN (
                SELECT DISTINCT room_id FROM reservations 
                WHERE tenant_id = ?
                AND status != 'cancelled'
                AND (
                    (check_in_date <= ? AND check_out_date > ?)
                    OR (check_in_date < ? AND check_out_date >= ?)
                    OR (check_in_date >= ? AND check_out_date <= ?)
                )
            )
            ORDER BY r.room_type, r.room_number
        """, (
            tenant_id, 
            request.guests,
            tenant_id,
            request.check_in, request.check_in,
            request.check_out, request.check_out,
            request.check_in, request.check_out
        ))
        
        rooms = cursor.fetchall()
        
        # Build room options
        room_options = []
        seen_types = set()
        
        for row in rooms:
            room = dict(row)
            room_type = room["room_type"]
            price = get_room_price(room_type)
            
            room_option = RoomOption(
                id=room["id"],
                room_number=room["room_number"],
                room_type=room_type,
                price_per_night=price,
                capacity=room["capacity"],
                amenities=parse_amenities(room.get("amenities", "") or ""),
                description=get_room_description(room_type),
                floor=room.get("floor") or 1,
                available=True
            )
            room_options.append(room_option)
            seen_types.add(room_type)
        
        # Group by room type for display
        room_types_summary = []
        for room_type in sorted(seen_types):
            type_rooms = [r for r in room_options if r.room_type == room_type]
            if type_rooms:
                room_types_summary.append({
                    "room_type": room_type,
                    "price_per_night": type_rooms[0].price_per_night,
                    "total_price": type_rooms[0].price_per_night * nights,
                    "capacity": max(r.capacity for r in type_rooms),
                    "description": type_rooms[0].description,
                    "available_count": len(type_rooms),
                    "rooms": [r.dict() for r in type_rooms[:3]]  # First 3 rooms of each type
                })
        
        return {
            "check_in": request.check_in,
            "check_out": request.check_out,
            "nights": nights,
            "guests": request.guests,
            "room_types": room_types_summary,
            "total_available": len(room_options)
        }
        
    finally:
        conn.close()


@router.post("/booking/summary")
async def create_booking_summary(
    request: BookingSummaryRequest,
    tenant_id: str = Depends(get_tenant_header)
):
    """
    Create a booking summary with full price breakdown.
    """
    # Validate dates
    nights = calculate_nights(request.check_in, request.check_out)
    if nights <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range")
    
    # Get room details
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE id = ? AND tenant_id = ?", 
                      (request.room_id, tenant_id))
        room_row = cursor.fetchone()
        
        if not room_row:
            raise HTTPException(status_code=404, detail="Room not found")
        
        room = dict(room_row)
        room_type = room["room_type"]
        price_per_night = get_room_price(room_type)
        
        room_option = RoomOption(
            id=room["id"],
            room_number=room["room_number"],
            room_type=room_type,
            price_per_night=price_per_night,
            capacity=room["capacity"],
            amenities=parse_amenities(room.get("amenities", "") or ""),
            description=get_room_description(room_type),
            floor=room.get("floor") or 1,
            available=True
        )
        
    finally:
        conn.close()
    
    # Calculate room cost
    room_total = price_per_night * nights
    
    # Calculate services cost
    selected_services = []
    services_total = 0.0
    
    for service_id in request.services:
        service = next((s for s in HOTEL_SERVICES if s["id"] == service_id), None)
        if service:
            service_option = ServiceOption(**service)
            selected_services.append(service_option)
            
            if service["per_night"]:
                services_total += service["price"] * nights
            else:
                services_total += service["price"]
    
    # Calculate taxes (10%)
    subtotal = room_total + services_total
    taxes = round(subtotal * 0.10, 2)
    total = round(subtotal + taxes, 2)
    
    # Build breakdown
    breakdown = [
        {
            "item": f"{room_type} Room ({nights} night{'s' if nights > 1 else ''})",
            "price": room_total
        }
    ]
    
    for service in selected_services:
        svc = next((s for s in HOTEL_SERVICES if s["id"] == service.id), None)
        if svc and svc["per_night"]:
            breakdown.append({
                "item": f"{service.name} ({nights} night{'s' if nights > 1 else ''})",
                "price": service.price * nights
            })
        else:
            breakdown.append({
                "item": service.name,
                "price": service.price
            })
    
    breakdown.append({"item": "Taxes & Fees (10%)", "price": taxes})
    
    return BookingSummary(
        room=room_option,
        check_in=request.check_in,
        check_out=request.check_out,
        nights=nights,
        guests=request.guests,
        services=selected_services,
        room_total=room_total,
        services_total=services_total,
        taxes=taxes,
        total=total,
        breakdown=breakdown
    )


@router.post("/booking/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    http_request: Request,
    tenant_id: str = Depends(get_tenant_header)
):
    """
    Create Stripe checkout session for the booking.
    """
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse
    )
    
    summary = request.booking_summary
    total = float(summary.get("total", 0))
    
    if total <= 0:
        raise HTTPException(status_code=400, detail="Invalid booking total")
    
    # Generate booking ID
    booking_id = str(uuid.uuid4())
    
    # Get API key from environment
    api_key = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
    
    # Build URLs
    host_url = str(http_request.base_url).rstrip("/")
    # For frontend redirect after payment
    frontend_url = os.environ.get("FRONTEND_URL", host_url.replace("/api", "").replace(":8001", ":3000"))
    if "preview.emergentagent.com" in host_url:
        frontend_url = host_url.replace("/api", "")
    
    success_url = f"{frontend_url}?booking_status=success&session_id={{CHECKOUT_SESSION_ID}}&booking_id={booking_id}"
    cancel_url = f"{frontend_url}?booking_status=cancelled&booking_id={booking_id}"
    
    # Webhook URL
    webhook_url = f"{host_url}api/booking/webhook"
    
    # Initialize Stripe
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    # Create metadata
    metadata = {
        "booking_id": booking_id,
        "tenant_id": tenant_id,
        "guest_name": request.guest_name,
        "guest_email": request.guest_email,
        "room_id": summary.get("room", {}).get("id", ""),
        "room_type": summary.get("room", {}).get("room_type", ""),
        "check_in": summary.get("check_in", ""),
        "check_out": summary.get("check_out", ""),
        "nights": str(summary.get("nights", 0)),
        "total": str(total)
    }
    
    try:
        # Create checkout session
        checkout_request = CheckoutSessionRequest(
            amount=total,
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Store pending reservation
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Create reservation with pending_payment status
            cursor.execute("""
                INSERT INTO reservations 
                (id, tenant_id, room_id, room_number, guest_name, guest_email,
                 check_in_date, check_out_date, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking_id,
                tenant_id,
                summary.get("room", {}).get("id", ""),
                summary.get("room", {}).get("room_number", ""),
                request.guest_name,
                request.guest_email,
                summary.get("check_in", ""),
                summary.get("check_out", ""),
                total,
                "pending_payment",
                datetime.now(timezone.utc).isoformat()
            ))
            
            # Create payment transaction record
            cursor.execute("""
                INSERT INTO payment_transactions 
                (id, tenant_id, booking_id, session_id, amount, currency, 
                 payment_status, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                tenant_id,
                booking_id,
                session.session_id,
                total,
                "usd",
                "pending",
                str(metadata),
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
        finally:
            conn.close()
        
        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.session_id,
            booking_id=booking_id
        )
        
    except Exception as e:
        print(f"[Booking] Stripe error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create checkout: {str(e)}")


@router.get("/booking/status/{booking_id}")
async def get_booking_status(
    booking_id: str,
    session_id: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_header)
):
    """
    Get booking status. If session_id provided, also check with Stripe.
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM reservations 
            WHERE id = ? AND tenant_id = ?
        """, (booking_id, tenant_id))
        
        reservation = cursor.fetchone()
        if not reservation:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        result = {
            "booking_id": booking_id,
            "status": reservation["status"],
            "guest_name": reservation["guest_name"],
            "room_number": reservation["room_number"],
            "check_in": reservation["check_in_date"],
            "check_out": reservation["check_out_date"],
            "total": reservation["total_amount"]
        }
        
        # If session_id provided, check Stripe status
        if session_id and reservation["status"] == "pending_payment":
            try:
                from emergentintegrations.payments.stripe.checkout import StripeCheckout
                
                api_key = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
                stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
                
                checkout_status = await stripe_checkout.get_checkout_status(session_id)
                
                if checkout_status.payment_status == "paid":
                    # Update reservation to confirmed
                    cursor.execute("""
                        UPDATE reservations SET status = 'confirmed' 
                        WHERE id = ? AND status = 'pending_payment'
                    """, (booking_id,))
                    
                    # Update payment transaction
                    cursor.execute("""
                        UPDATE payment_transactions SET payment_status = 'paid'
                        WHERE booking_id = ? AND payment_status = 'pending'
                    """, (booking_id,))
                    
                    conn.commit()
                    result["status"] = "confirmed"
                    result["payment_status"] = "paid"
                    
            except Exception as e:
                print(f"[Booking] Error checking Stripe status: {e}")
        
        return result
        
    finally:
        conn.close()


@router.post("/booking/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    """
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    api_key = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            booking_id = webhook_response.metadata.get("booking_id")
            tenant_id = webhook_response.metadata.get("tenant_id", "default-tenant-0000")
            
            if booking_id:
                conn = get_db_connection()
                try:
                    cursor = conn.cursor()
                    
                    # Update reservation
                    cursor.execute("""
                        UPDATE reservations SET status = 'confirmed' 
                        WHERE id = ? AND tenant_id = ?
                    """, (booking_id, tenant_id))
                    
                    # Update payment transaction
                    cursor.execute("""
                        UPDATE payment_transactions SET payment_status = 'paid'
                        WHERE booking_id = ?
                    """, (booking_id,))
                    
                    conn.commit()
                    print(f"[Webhook] Booking {booking_id} confirmed via webhook")
                finally:
                    conn.close()
        
        return {"status": "received"}
        
    except Exception as e:
        print(f"[Webhook] Error: {e}")
        return {"status": "error", "message": str(e)}
