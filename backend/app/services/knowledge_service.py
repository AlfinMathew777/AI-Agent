# backend/app/services/knowledge_service.py

"""
Simple FAQ lookups for guest and staff.
This is a backup layer if RAG-lite can't find a good chunk.
"""

from typing import Optional


def get_guest_faq_answer(question: str) -> Optional[str]:
    q = question.lower()

    # very small examples – RAG will usually do the heavy lifting
    if "check-in" in q or "check in" in q:
        return "Check-in time is 2:00 pm. If you arrive earlier we can usually store your luggage at reception."

    if "check-out" in q or "check out" in q:
        return "Check-out time is 10:00 am. Late check-out may be available; please contact reception to check availability and fees."

    return None


def get_staff_faq_answer(question: str) -> Optional[str]:
    q = question.lower()

    if "complaint" in q:
        return "For guest complaints, stay calm, listen carefully, apologise and follow our service recovery steps. Check the complaints SOP for details."

    return None
