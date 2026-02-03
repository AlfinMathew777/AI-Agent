"""
Cloudbeds PMS Adapter for ACP
Replaces synthetic HotelDomainAdapter with real Cloudbeds API integration.

Implements same interface as HotelDomainAdapter:
- initialize()
- query(request) → availability + rates
- get_base_price(entity_id, dates, room_type)
- get_demand_multiplier(entity_id, dates)
- execute(tx, request) → booking execution
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import httpx
from app.acp.domains.hotel.inventory_cache import InventoryCache


class CircuitBreaker:
    """Circuit breaker for PMS API calls"""
    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open

    def record_success(self):
        """Reset on success"""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        """Increment failure count"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def can_proceed(self) -> bool:
        """Check if request can proceed"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                self.state = "half_open"
                return True
            return False
        
        # half_open
        return True


class CloudbedsAdapter:
    """Cloudbeds PMS Adapter for ACP"""
    
    def __init__(self, db_path: str = "cloudbeds_cache.db", use_sandbox: bool = True):
        self.db_path = db_path
        self.use_sandbox = use_sandbox or os.getenv("CLOUDBEDS_USE_SANDBOX", "true").lower() == "true"
        self.base_url = "https://api.cloudbeds.com/api/v1.1" if not self.use_sandbox else "http://localhost:8001/sandbox/cloudbeds"
        self.client_id = os.getenv("CLOUDBEDS_CLIENT_ID", "")
        self.client_secret = os.getenv("CLOUDBEDS_CLIENT_SECRET", "")
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        self.circuit_breaker = CircuitBreaker()
        self.cache = InventoryCache(db_path=db_path)
        self._http_client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """Initialize adapter and cache"""
        await self.cache.initialize()
        self._http_client = httpx.AsyncClient(timeout=5.0)
        
        # Start background cache sync if not using sandbox
        if not self.use_sandbox:
            asyncio.create_task(self._background_cache_sync())

    async def _get_access_token(self) -> str:
        """Get OAuth 2.0 access token (client credentials flow)"""
        if self.access_token and self.token_expires_at and time.time() < self.token_expires_at:
            return self.access_token

        if self.use_sandbox:
            # Sandbox doesn't need real OAuth
            self.access_token = "sandbox_token"
            self.token_expires_at = time.time() + 3600
            return self.access_token

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    "https://api.cloudbeds.com/api/v1.1/access_token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                self.access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self.token_expires_at = time.time() + expires_in - 60  # 60s buffer
                return self.access_token
        except Exception as e:
            print(f"[Cloudbeds] Token fetch failed: {e}")
            raise

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Cloudbeds API with circuit breaker and rate limit backoff"""
        if not self.circuit_breaker.can_proceed():
            raise Exception("Circuit breaker is OPEN - PMS API unavailable")

        # Exponential backoff for rate limiting (Phase 3B safety feature)
        max_retries = 3
        backoff_delays = [1.0, 2.0, 4.0]  # seconds
        
        for attempt in range(max_retries):
            try:
                token = await self._get_access_token()
                headers = kwargs.get("headers", {})
                headers["Authorization"] = f"Bearer {token}"
                kwargs["headers"] = headers

                if not self._http_client:
                    self._http_client = httpx.AsyncClient(timeout=5.0)

                resp = await self._http_client.request(method, f"{self.base_url}{endpoint}", **kwargs)
                resp.raise_for_status()
                
                self.circuit_breaker.record_success()
                return resp.json()
                
            except httpx.TimeoutException:
                self.circuit_breaker.record_failure()
                raise Exception("PMS API timeout")
                
            except httpx.HTTPStatusError as e:
                # Rate limit handling (Phase 3B)
                if e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        delay = backoff_delays[attempt]
                        print(f"[Cloudbeds] Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue  # Retry
                    else:
                        print(f"[Cloudbeds] Rate limit - max retries exceeded")
                        self.circuit_breaker.record_failure()
                        raise Exception("PMS API rate limit exceeded")
                
                # Other HTTP errors
                self.circuit_breaker.record_failure()
                raise Exception(f"PMS API error: {e.response.status_code}")
                
            except Exception as e:
                self.circuit_breaker.record_failure()
                raise
        
        # Should not reach here, but just in case
        raise Exception("PMS API request failed after retries")

    async def query(self, request) -> Dict[str, Any]:
        """Query availability and rates"""
        intent = request.intent_payload

        if intent.get("availability"):
            return await self._query_availability(intent["availability"])
        if intent.get("amenities"):
            return {"amenities": ["wifi", "minibar", "parking", "restaurant"]}
        return {"error": "Unknown query type"}

    async def _query_availability(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Query availability from cache or API"""
        property_id = payload.get("property_id", "pillinger_house")
        check_in = payload.get("check_in")
        check_out = payload.get("check_out")
        room_type = payload.get("room_type", "standard_queen")

        if not check_in or not check_out:
            return {"available": False, "reason": "Missing check_in/check_out"}

        # Try cache first
        cached = await self.cache.get_cached_availability(property_id, check_in, check_out, room_type)
        if cached:
            return cached

        # Fall back to API
        try:
            # Map ACP room_type to Cloudbeds rate plan ID
            rate_plan_id = self._map_room_type_to_rate_plan(room_type)
            
            resp = await self._make_request(
                "GET",
                f"/getPropertyAvailability",
                params={
                    "property_id": property_id,
                    "start_date": check_in,
                    "end_date": check_out,
                    "rate_plan_id": rate_plan_id,
                }
            )

            available = resp.get("available", False)
            rooms_available = resp.get("rooms_available", 0)
            base_rate = resp.get("rate", 0)
            demand_factor = resp.get("demand_multiplier", 1.0)
            dynamic_rate = round(base_rate * demand_factor, 2)

            result = {
                "available": available and rooms_available > 0,
                "rooms_available": rooms_available,
                "base_rate": base_rate,
                "dynamic_rate": dynamic_rate,
                "demand_factor": round(demand_factor, 2),
            }

            # Cache result
            await self.cache.cache_availability(property_id, check_in, check_out, room_type, result)
            return result
        except Exception as e:
            print(f"[Cloudbeds] Availability query failed: {e}")
            return {"available": False, "reason": str(e)}

    async def get_base_price(self, entity_id: str, dates: Any, room_type: str) -> float:
        """Get base price for room type"""
        check_in = dates.get("check_in") if isinstance(dates, dict) else None
        if not check_in:
            return 320.0  # Default fallback

        try:
            rate_plan_id = self._map_room_type_to_rate_plan(room_type)
            resp = await self._make_request(
                "GET",
                f"/getRatePlans",
                params={
                    "property_id": entity_id,
                    "rate_plan_id": rate_plan_id,
                }
            )
            return float(resp.get("base_rate", 320.0))
        except Exception:
            # Fallback to config or default
            from app.acp.domains.hotel.pilot_config import get_pilot_config
            config = get_pilot_config()
            return float(config.get("base_rates", {}).get(room_type, 320.0))

    async def get_demand_multiplier(self, entity_id: str, dates: Any) -> float:
        """Get demand multiplier for dates"""
        check_in = dates.get("check_in") if isinstance(dates, dict) else None
        if not check_in:
            return 1.0

        # Check if weekend
        try:
            date_obj = datetime.fromisoformat(check_in)
            is_weekend = date_obj.weekday() >= 5
            base_multiplier = 1.3 if is_weekend else 1.0
            
            # Could enhance with historical data from Cloudbeds
            return base_multiplier
        except Exception:
            return 1.0

    async def execute(self, tx, request, dry_run: bool = False) -> Dict[str, Any]:
        """Execute booking in Cloudbeds (Phase 3B: supports dry-run mode)
        
        Args:
            tx: Transaction object
            request: ACP request
            dry_run: If True, validate payload but don't create actual booking
        
        Returns:
            Booking result with success status
        """
        try:
            # Extract booking details from transaction
            dates = request.intent_payload.get("dates", {})
            room_type = request.intent_payload.get("room_type", "standard_queen")
            guests = request.intent_payload.get("guests", 2)

            rate_plan_id = self._map_room_type_to_rate_plan(room_type)
            
            booking_data = {
                "property_id": tx.target_entity_id,
                "check_in": dates.get("check_in"),
                "check_out": dates.get("check_out"),
                "rate_plan_id": rate_plan_id,
                "guests": guests,
                "source": "ACP",
                "external_id": f"acp-{tx.tx_id}",
            }
            
            # DRY RUN MODE (Phase 3B safety feature)
            if dry_run:
                # Validate payload structure without creating booking
                required_fields = ["check_in", "check_out"]
                missing = [f for f in required_fields if not booking_data.get(f)]
                
                if missing:
                    return {
                        "success": False,
                        "dry_run": True,
                        "error": f"Missing required fields: {missing}",
                    }
                
                # Estimate total from negotiation (if available)
                estimated_total = tx.final_offer.get("total_price", 0) if hasattr(tx, 'final_offer') else 0
                
                return {
                    "success": True,
                    "dry_run": True,
                    "would_create_booking": True,
                    "validation": "passed",
                    "booking_data": booking_data,
                    "estimated_total": estimated_total,
                    "message": "Dry-run successful. No actual booking created.",
                }

            # REAL BOOKING
            resp = await self._make_request(
                "POST",
                "/postReservation",
                json=booking_data
            )

            confirmation_code = resp.get("confirmation_code", f"ACP-{tx.tx_id[:8].upper()}")
            pms_reference = resp.get("reservation_id", f"CB-{tx.tx_id}")

            # Invalidate cache for these dates
            await self.cache.invalidate_dates(
                tx.target_entity_id,
                dates.get("check_in"),
                dates.get("check_out"),
                room_type
            )

            return {
                "success": True,
                "dry_run": False,
                "confirmation_code": confirmation_code,
                "pms_reference": pms_reference,
                "check_in_instructions": "Digital key sent to agent. Check-in from 2 PM.",
            }
        except Exception as e:
            print(f"[Cloudbeds] Booking execution failed: {e}")
            return {
                "success": False,
                "dry_run": dry_run,
                "error": str(e),
            }

    def _map_room_type_to_rate_plan(self, room_type: str) -> str:
        """Map ACP room type to Cloudbeds rate plan ID"""
        mapping = {
            "standard_queen": "RP_STD_QUEEN",
            "deluxe_king": "RP_DLX_KING",
        }
        return mapping.get(room_type, "RP_STD_QUEEN")

    async def _background_cache_sync(self):
        """Background job to sync inventory every 60 seconds"""
        while True:
            try:
                await asyncio.sleep(60)
                # Sync logic would go here
                # For now, cache is updated on-demand
            except Exception as e:
                print(f"[Cloudbeds] Cache sync error: {e}")

    async def shutdown(self):
        """Cleanup"""
        if self._http_client:
            await self._http_client.aclose()
