"""
Simulated Cloudbeds API for Testing
Provides realistic PMS responses without real credentials
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Cloudbeds Sandbox Simulator")

# Simulated inventory
_inventory = {}
_rate_plans = {
    "RP_STD_QUEEN": {"base_rate": 320, "name": "Standard Queen"},
    "RP_DLX_KING": {"base_rate": 450, "name": "Deluxe King"},
}
_reservations = {}


def _simulate_latency():
    """Simulate realistic API latency"""
    delay = random.uniform(0.2, 0.8)
    time.sleep(delay)


def _simulate_error() -> bool:
    """5% chance of error"""
    return random.random() < 0.05


@app.get("/sandbox/cloudbeds/getPropertyAvailability")
async def get_availability(request: Request):
    """Simulate availability query"""
    _simulate_latency()
    
    if _simulate_error():
        if random.random() < 0.5:
            raise HTTPException(status_code=503, detail="Temporary timeout")
        else:
            raise HTTPException(status_code=400, detail="Rate change error")
    
    params = dict(request.query_params)
    property_id = params.get("property_id", "pillinger_house")
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    rate_plan_id = params.get("rate_plan_id", "RP_STD_QUEEN")
    
    # Generate realistic availability
    rate_plan = _rate_plans.get(rate_plan_id, _rate_plans["RP_STD_QUEEN"])
    base_rate = rate_plan["base_rate"]
    
    # Weekend multiplier
    try:
        date_obj = datetime.fromisoformat(start_date)
        is_weekend = date_obj.weekday() >= 5
        demand_multiplier = 1.3 if is_weekend else 1.0
    except:
        demand_multiplier = 1.0
    
    rooms_available = random.randint(2, 15)
    available = rooms_available > 0
    
    return {
        "available": available,
        "rooms_available": rooms_available,
        "rate": round(base_rate * demand_multiplier, 2),
        "demand_multiplier": round(demand_multiplier, 2),
        "rate_plan_id": rate_plan_id,
    }


@app.get("/sandbox/cloudbeds/getRatePlans")
async def get_rate_plans(request: Request):
    """Simulate rate plan query"""
    _simulate_latency()
    
    if _simulate_error():
        raise HTTPException(status_code=500, detail="Rate plan service error")
    
    params = dict(request.query_params)
    rate_plan_id = params.get("rate_plan_id", "RP_STD_QUEEN")
    
    rate_plan = _rate_plans.get(rate_plan_id, _rate_plans["RP_STD_QUEEN"])
    
    return {
        "rate_plan_id": rate_plan_id,
        "base_rate": rate_plan["base_rate"],
        "name": rate_plan["name"],
    }


@app.post("/sandbox/cloudbeds/postReservation")
async def create_reservation(request: Request):
    """Simulate reservation creation"""
    _simulate_latency()
    
    if _simulate_error():
        if random.random() < 0.5:
            raise HTTPException(status_code=409, detail="Overbooking error - no rooms available")
        else:
            raise HTTPException(status_code=500, detail="Reservation service error")
    
    body = await request.json()
    property_id = body.get("property_id")
    check_in = body.get("check_in")
    check_out = body.get("check_out")
    rate_plan_id = body.get("rate_plan_id")
    external_id = body.get("external_id", "")
    
    # Check availability
    if not _check_availability(property_id, check_in, check_out, rate_plan_id):
        raise HTTPException(status_code=409, detail="No availability for requested dates")
    
    # Create reservation
    reservation_id = f"CB-{int(time.time())}-{random.randint(1000, 9999)}"
    confirmation_code = f"ACP-{random.randint(100000, 999999)}"
    
    _reservations[reservation_id] = {
        "reservation_id": reservation_id,
        "confirmation_code": confirmation_code,
        "property_id": property_id,
        "check_in": check_in,
        "check_out": check_out,
        "rate_plan_id": rate_plan_id,
        "external_id": external_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    return {
        "reservation_id": reservation_id,
        "confirmation_code": confirmation_code,
        "status": "confirmed",
    }


def _check_availability(property_id: str, check_in: str, check_out: str, rate_plan_id: str) -> bool:
    """Check if dates are available (simplified)"""
    # In real implementation, would check against inventory
    return random.random() > 0.1  # 90% chance available


@app.get("/sandbox/cloudbeds/reservations/{reservation_id}")
async def get_reservation(reservation_id: str):
    """Get reservation details"""
    _simulate_latency()
    
    if reservation_id not in _reservations:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return _reservations[reservation_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
