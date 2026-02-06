"""
Integration Wrapper
Wraps the enhanced chatbot for easy integration with existing ai_service.py
"""

from .enhanced_ai_service import EnhancedAIChatbot
from typing import Optional

# Global instance
_enhanced_chatbot = None


def get_enhanced_chatbot() -> EnhancedAIChatbot:
    """Get or create the enhanced chatbot singleton"""
    global _enhanced_chatbot
    if _enhanced_chatbot is None:
        _enhanced_chatbot = EnhancedAIChatbot()
    return _enhanced_chatbot


async def enhanced_guest_answer(question: str, tenant_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """
    Enhanced guest answer function that integrates with ACP backend
    
    This is a drop-in replacement for the existing get_guest_answer() function,
    but with full ACP integration for real bookings, property context, etc.
    
    Args:
        question: Guest question
        tenant_id: Property/tenant ID
        session_id: Session ID for conversation continuity
    
    Returns:
        Answer string
    """
    chatbot = get_enhanced_chatbot()
    
    # Process the message through enhanced chatbot
    response = await chatbot.process_message(
        message=question,
        session_id=session_id,
        tenant_id=tenant_id
    )
    
    # Return the answer text
    # The response dict has more info, but we return just the answer for compatibility
    return response.get("answer", "I'm sorry, I couldn't process that.")


async def enhanced_guest_answer_full(question: str, tenant_id: Optional[str] = None, session_id: Optional[str] = None) -> dict:
    """
    Enhanced guest answer function that returns full response dict
    
    Use this version if you want access to intent, entities, session info, etc.
    
    Args:
        question: Guest question
        tenant_id: Property/tenant ID
        session_id: Session ID for conversation continuity
    
    Returns:
        Full response dict with answer, intent, session_id, etc.
    """
    chatbot = get_enhanced_chatbot()
    
    return await chatbot.process_message(
        message=question,
        session_id=session_id,
        tenant_id=tenant_id
    )
