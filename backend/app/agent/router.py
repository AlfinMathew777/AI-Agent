# Logic to route between CHAT and TOOL mode
import re

class AgentRouter:
    def decide_mode(self, question, context_chunks):
        """
        Decide whether to use CHAT (RAG) or TOOL mode.
        """
        q_lower = question.lower()
        
        # 1. Direct Intent Keywords for Tools
        tool_keywords = [
            "book", "reserve", "reservation", "schedule", 
            "check", "availability", "vacant", "free", 
            "complain", "issue", "fix", "repair", "broken",
            "housekeeping", "clean", "towel", "soap"
        ]
        
        for kw in tool_keywords:
            if kw in q_lower:
                # Naive check: ensure it's not just "check out" or "check in" times
                # For MVP, broad matching is safer to catch intent
                return "TOOL"
        
        # 2. Heuristic: If context is empty, maybe it's a tool request that RAG missed?
        # But for now, default to CHAT if no tool keywords found.
        
        return "CHAT"
