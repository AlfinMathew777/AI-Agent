"""
Session Manager
Maintains conversation state and context across multiple turns
"""

import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class SessionManager:
    """Manages conversation sessions and context"""
    
    def __init__(self, ttl_minutes: int = 30):
        """
        Initialize session manager
        
        Args:
            ttl_minutes: Session time-to-live in minutes
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new session
        
        Args:
            session_id: Optional session ID (generates if not provided)
        
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "context": {},
            "history": [],
            "current_intent": None,
            "pending_action": None
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID
        
        Args:
            session_id: Session ID
        
        Returns:
            Session dict or None if not found/expired
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if expired
        if datetime.utcnow() - session["last_activity"] > self.ttl:
            del self.sessions[session_id]
            return None
        
        # Update activity
        session["last_activity"] = datetime.utcnow()
        return session
    
    def update_context(self, session_id: str, key: str, value: Any) -> bool:
        """
        Update session context
        
        Args:
            session_id: Session ID
            key: Context key
            value: Context value
        
        Returns:
            True if updated, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["context"][key] = value
        return True
    
    def get_context(self, session_id: str, key: str, default: Any = None) -> Any:
        """
        Get value from session context
        
        Args:
            session_id: Session ID
            key: Context key
            default: Default value if not found
        
        Returns:
            Context value or default
        """
        session = self.get_session(session_id)
        if not session:
            return default
        
        return session["context"].get(key, default)
    
    def add_to_history(self, session_id: str, role: str, message: str) -> bool:
        """
        Add message to conversation history
        
        Args:
            session_id: Session ID
            role: Message role (user/assistant)
            message: Message content
        
        Returns:
            True if added, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["history"].append({
            "role": role,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 20 messages to prevent memory bloat
        if len(session["history"]) > 20:
            session["history"] = session["history"][-20:]
        
        return True
    
    def get_history(self, session_id: str, limit: int = 10) -> list:
        """
        Get conversation history
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages to return
        
        Returns:
            List of message dicts
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session["history"][-limit:]
    
    def set_current_intent(self, session_id: str, intent: str, params: Dict[str, Any]) -> bool:
        """
        Set current intent being processed
        
        Args:
            session_id: Session ID
            intent: Intent type (e.g., 'book_room', 'check_availability')
            params: Intent parameters
        
        Returns:
            True if set, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["current_intent"] = {
            "intent": intent,
            "params": params,
            "started_at": datetime.utcnow().isoformat()
        }
        
        return True
    
    def get_current_intent(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current intent"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        return session.get("current_intent")
    
    def clear_current_intent(self, session_id: str) -> bool:
        """Clear current intent"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["current_intent"] = None
        return True
    
    def set_pending_action(self, session_id: str, action_type: str, action_data: Dict[str, Any]) -> bool:
        """
        Set a pending action that requires confirmation
        
        Args:
            session_id: Session ID
            action_type: Action type (e.g., 'execute_booking')
            action_data: Action data
        
        Returns:
            True if set, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        action_id = str(uuid.uuid4())
        session["pending_action"] = {
            "action_id": action_id,
            "action_type": action_type,
            "action_data": action_data,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return True
    
    def get_pending_action(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get pending action"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        return session.get("pending_action")
    
    def clear_pending_action(self, session_id: str) -> bool:
        """Clear pending action"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["pending_action"] = None
        return True
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["last_activity"] > self.ttl
        ]
        
        for sid in expired:
            del self.sessions[sid]
        
        return len(expired)
    
    def get_session_summary(self, session_id: str) -> str:
        """
        Get a text summary of the session for context
        
        Args:
            session_id: Session ID
        
        Returns:
            Summary text
        """
        session = self.get_session(session_id)
        if not session:
            return ""
        
        context = session["context"]
        summary_parts = []
        
        # Guest info
        if "guest_name" in context:
            summary_parts.append(f"Guest: {context['guest_name']}")
        
        # Dates
        if "check_in" in context and "check_out" in context:
            summary_parts.append(f"Dates: {context['check_in']} to {context['check_out']}")
        
        # Room
        if "room_type" in context:
            summary_parts.append(f"Room: {context['room_type']}")
        
        # Guests
        if "guests" in context:
            summary_parts.append(f"Guests: {context['guests']}")
        
        # Property
        if "property_id" in context:
            summary_parts.append(f"Property: {context['property_id']}")
        
        # Current intent
        if session["current_intent"]:
            intent = session["current_intent"]["intent"]
            summary_parts.append(f"Current intent: {intent}")
        
        # Negotiation
        if "negotiation_session_id" in context:
            summary_parts.append(f"Negotiation in progress")
        
        if summary_parts:
            return "Session context: " + ", ".join(summary_parts)
        
        return ""
