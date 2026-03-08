"""Base Agent - Foundation for all A2A agents with LLM + broadcast capability."""

import os
import json
import asyncio
from datetime import datetime, UTC
from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Callable, Awaitable
from emergentintegrations.llm.chat import LlmChat, UserMessage


@dataclass
class AgentEvent:
    agent_id: str
    agent_name: str
    status: str          # idle | processing | completed | error
    action: str          # Short action label
    content: str         # Human-readable description
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    session_id: str = ""

    def to_dict(self):
        return asdict(self)


class BaseAgent:
    """Base class for all A2A hotel agents."""

    AGENT_COLORS = {
        "guest_agent":       "#38BDF8",
        "booking_agent":     "#22C55E",
        "pricing_agent":     "#F59E0B",
        "negotiation_agent": "#A78BFA",
        "payment_agent":     "#34D399",
        "inventory_agent":   "#60A5FA",
        "operations_agent":  "#FB923C",
        "orchestrator":      "#F472B6",
    }

    def __init__(
        self,
        agent_id: str,
        name: str,
        system_message: str,
        broadcast_fn: Optional[Callable] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.status = "idle"
        self.broadcast_fn = broadcast_fn
        self.color = self.AGENT_COLORS.get(agent_id, "#94A3B8")
        self._session_counter = 0

        llm_key = (
            os.environ.get("EMERGENT_LLM_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or ""
        )
        model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

        self._llm = LlmChat(
            api_key=llm_key,
            session_id=f"{agent_id}-base",
            system_message=system_message,
        ).with_model("gemini", model)

    async def broadcast(self, action: str, content: str, status: str = "processing", metadata: dict = None, session_id: str = "") -> None:
        self.status = status
        event = AgentEvent(
            agent_id=self.agent_id,
            agent_name=self.name,
            status=status,
            action=action,
            content=content,
            metadata=metadata or {},
            session_id=session_id,
        )
        if self.broadcast_fn:
            await self.broadcast_fn(event)

    async def think(self, prompt: str, session_id: str = "") -> str:
        """Call LLM and return response."""
        self._session_counter += 1
        # Use a per-session LLM instance to avoid cross-session contamination
        llm_key = (
            os.environ.get("EMERGENT_LLM_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or ""
        )
        model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"{self.agent_id}-{session_id}-{self._session_counter}",
            system_message=self._llm._system_message if hasattr(self._llm, '_system_message') else "You are a helpful AI hotel assistant.",
        ).with_model("gemini", model)

        try:
            response = await chat.send_message(UserMessage(text=prompt))
            return response
        except Exception as e:
            print(f"[{self.name}] LLM error: {e}")
            return f"[Fallback] Processing complete."

    def set_broadcast(self, fn: Callable):
        self.broadcast_fn = fn
