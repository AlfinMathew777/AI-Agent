"""A2A API Routes - WebSocket, agent status, events, and chat integration."""

import json
import asyncio
from datetime import datetime, UTC
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.agents.orchestrator import get_orchestrator, connection_manager, agent_status_store

router = APIRouter(tags=["A2A"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    guest_name: Optional[str] = "Guest"
    guest_email: Optional[str] = "guest@hotel.com"


# ─── WebSocket ────────────────────────────────────────────────────────────────

@router.websocket("/ws/a2a")
async def websocket_a2a(websocket: WebSocket):
    """Live WebSocket for real-time agent activity feed."""
    await connection_manager.connect(websocket)
    try:
        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to A2A Agent Network",
            "agents": agent_status_store.get_all(),
            "timestamp": datetime.now(UTC).isoformat(),
        })

        # Send recent events replay
        orch = get_orchestrator()
        recent = orch.get_recent_events(20)
        if recent:
            await websocket.send_json({"type": "events_replay", "events": recent})

        # Keep connection alive - heartbeat
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data) if data else {}
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now(UTC).isoformat()})
                elif msg.get("type") == "get_status":
                    await websocket.send_json({
                        "type": "agent_statuses",
                        "agents": agent_status_store.get_all(),
                    })
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now(UTC).isoformat()})

    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as e:
        print(f"[WS] Error: {e}")
        await connection_manager.disconnect(websocket)


# ─── REST Endpoints ───────────────────────────────────────────────────────────

@router.get("/a2a/status")
async def get_agent_status():
    """Get current status of all agents."""
    return {
        "agents": agent_status_store.get_all(),
        "connected_clients": connection_manager.connected_count,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/a2a/events")
async def get_recent_events(limit: int = 50):
    """Get recent agent events for dashboard replay."""
    orch = get_orchestrator()
    return {
        "events": orch.get_recent_events(limit),
        "total": len(orch._events),
    }


@router.post("/a2a/chat")
async def a2a_chat(request: ChatRequest):
    """
    Main A2A chat endpoint.
    Runs through the full agent pipeline and returns the final response.
    """
    orch = get_orchestrator()

    # Inject guest context into entities (will be used by payment agent)
    result = await orch.run(
        message=request.message,
        session_id=request.session_id or "",
    )

    if result.get("response"):
        return {
            "role": "assistant",
            "answer": result["response"],
            "action": result.get("action"),
            "session_id": result.get("session_id"),
            "data": result.get("data", {}),
        }
    else:
        # Fall back to the standard RAG chatbot for general queries
        try:
            from app.chatbot.concierge_bot import ConciergeBot
            bot = ConciergeBot()
            session_id = request.session_id or "default"
            response = await bot.chat(session_id, request.message)
            return {
                "role": "assistant",
                "answer": response.get("response", "How can I assist you today?"),
                "action": response.get("action", "general"),
                "session_id": session_id,
            }
        except Exception as e:
            print(f"[A2A] Fallback chatbot error: {e}")
            return {
                "role": "assistant",
                "answer": "Our concierge desk is experiencing high volume. Please try again in a moment.",
                "action": "error",
                "session_id": request.session_id or "",
            }


@router.post("/a2a/simulate")
async def simulate_booking_flow(request: ChatRequest):
    """Simulate a full A2A booking flow for demo purposes."""
    orch = get_orchestrator()
    result = await orch.run(
        message=request.message or "I want to book 1 deluxe room for 3 nights starting tomorrow",
        session_id=request.session_id or "demo",
    )
    return result
