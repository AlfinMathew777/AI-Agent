"""
Policy Agent - Role-aware Staff AI Assistant

This agent answers questions about hotel policies, SOPs, and procedures
based on the staff member's role. It uses ChromaDB RAG for knowledge retrieval
and Gemini for intelligent, role-contextual responses.
"""

import os
from typing import List, Dict, Optional
from app.services.llm_service import HotelAI

# Role-specific system prompts and context
ROLE_CONTEXTS = {
    "front_desk": {
        "title": "Front Desk Staff",
        "focus_areas": [
            "check-in and check-out procedures",
            "guest complaint handling",
            "room upgrades and changes",
            "reservation management",
            "payment processing",
            "VIP guest protocols",
            "emergency contacts"
        ],
        "system_prompt": """You are a knowledgeable Front Desk Assistant at a luxury hotel.
Your role is to help front desk staff with:
- Guest check-in/check-out procedures
- Handling complaints and service recovery
- Room upgrades and special requests
- Reservation changes and cancellations
- Payment and billing questions
- VIP and loyalty program protocols

Provide clear, actionable guidance. When relevant, mention:
1. The specific procedure or policy
2. Any exceptions or special cases
3. Escalation steps if needed
4. Time-sensitive considerations"""
    },
    
    "housekeeping": {
        "title": "Housekeeping Staff",
        "focus_areas": [
            "room cleaning standards",
            "turnover procedures",
            "maintenance reporting",
            "linen and supply management",
            "deep cleaning protocols",
            "lost and found procedures",
            "safety and hazard handling"
        ],
        "system_prompt": """You are a Housekeeping Operations Assistant.
Your role is to help housekeeping staff with:
- Room cleaning checklists and standards
- Turnover timing and prioritization
- Maintenance issue reporting
- Supply and linen management
- Deep cleaning and sanitization
- Lost and found protocols
- Safety procedures for hazards

Provide practical, step-by-step guidance. Include:
1. Specific procedures and checklists
2. Priority levels and timing
3. Who to notify for escalations
4. Safety reminders when relevant"""
    },
    
    "restaurant": {
        "title": "Restaurant Staff",
        "focus_areas": [
            "service standards",
            "menu knowledge",
            "dietary restrictions and allergies",
            "upselling techniques",
            "complaint handling",
            "reservation management",
            "food safety protocols"
        ],
        "system_prompt": """You are a Restaurant Operations Assistant.
Your role is to help F&B staff with:
- Service standards and sequences
- Menu items and dietary information
- Handling allergies and restrictions
- Upselling and recommendations
- Guest complaint resolution
- Table management and reservations
- Food safety and hygiene

Provide hospitality-focused guidance. Include:
1. Specific service procedures
2. Guest communication tips
3. Safety protocols when applicable
4. Escalation paths for issues"""
    },
    
    "manager": {
        "title": "Department Manager",
        "focus_areas": [
            "operational procedures",
            "staff management",
            "incident handling",
            "performance standards",
            "budget and resources",
            "inter-department coordination",
            "guest escalation protocols"
        ],
        "system_prompt": """You are a Management Operations Assistant.
Your role is to help managers with:
- Operational procedures across departments
- Staff scheduling and management
- Incident and crisis handling
- Performance monitoring and improvement
- Resource allocation and budgeting
- Cross-department coordination
- Complex guest issue resolution

Provide strategic and tactical guidance. Include:
1. Policy and procedure details
2. Decision-making frameworks
3. Escalation and approval paths
4. Documentation requirements"""
    },
    
    "admin": {
        "title": "Administrator",
        "focus_areas": [
            "all hotel operations",
            "policy management",
            "system configuration",
            "compliance requirements",
            "emergency procedures",
            "vendor management",
            "strategic planning"
        ],
        "system_prompt": """You are a comprehensive Hotel Operations Assistant with full access.
Your role is to help administrators with:
- All departmental procedures and policies
- System and process configuration
- Compliance and regulatory requirements
- Emergency and crisis management
- Vendor and partner management
- Strategic operational planning
- Staff training and development

Provide complete, authoritative guidance. Include:
1. Full policy and procedure details
2. Compliance and legal considerations
3. System-wide implications
4. Historical context when relevant"""
    }
}


class PolicyAgent:
    """
    Role-aware Policy Assistant that answers questions about hotel operations.
    Uses RAG for knowledge retrieval and adapts responses based on staff role.
    """
    
    def __init__(self, hotel_ai: HotelAI):
        self.hotel_ai = hotel_ai
        self.provider = hotel_ai.provider
    
    def get_role_context(self, role: str) -> Dict:
        """Get the context configuration for a specific role."""
        return ROLE_CONTEXTS.get(role, ROLE_CONTEXTS["front_desk"])
    
    def _build_prompt(
        self, 
        role: str, 
        question: str, 
        context_chunks: List[str],
        include_sources: bool = True
    ) -> str:
        """Build a role-aware prompt for the LLM."""
        role_context = self.get_role_context(role)
        
        # Build context section
        if context_chunks:
            context_text = "\n\n---\n\n".join(context_chunks[:5])  # Top 5 chunks
            context_section = f"""
## Relevant Knowledge Base Content:
{context_text}
"""
        else:
            context_section = """
## Knowledge Base:
No specific documents found for this query. Provide general best-practice guidance.
"""
        
        # Build the full prompt
        prompt = f"""{role_context['system_prompt']}

You are currently assisting a {role_context['title']}.

{context_section}

## Staff Question:
{question}

## Response Guidelines:
1. Provide a direct, actionable answer
2. Include specific steps or procedures when applicable
3. Mention any escalation paths if the situation requires it
4. Keep the response professional but practical
5. If the information is not in the knowledge base, provide general best-practice guidance and recommend checking with a supervisor

Format your response clearly with:
- **Direct Answer**: The main point
- **Details**: Supporting information
- **Action Steps**: What to do (if applicable)
- **Escalation**: When/how to escalate (if applicable)
"""
        
        return prompt
    
    async def answer(
        self,
        role: str,
        question: str,
        tenant_id: str,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Answer a staff question with role-aware context.
        
        Returns:
            Dict with 'answer', 'sources', 'role_context'
        """
        # 1. Retrieve relevant documents from staff knowledge base
        context_chunks = self.hotel_ai.query_docs(
            audience="staff",
            query=question,
            n_results=5,
            tenant_id=tenant_id
        )
        
        # 2. Build role-aware prompt
        prompt = self._build_prompt(role, question, context_chunks)
        
        # 3. Generate response using the LLM
        try:
            if self.provider == "gemini" and self.hotel_ai._gemini_model:
                response = await self._generate_gemini_response(prompt, role)
            else:
                # Fallback to offline mode
                response = self._generate_offline_response(role, question, context_chunks)
        except Exception as e:
            print(f"[PolicyAgent] Error generating response: {e}")
            response = self._generate_offline_response(role, question, context_chunks)
        
        # 4. Extract source information
        sources = self._extract_sources(context_chunks) if context_chunks else []
        
        return {
            "answer": response,
            "sources": sources,
            "role_context": self.get_role_context(role)["title"],
            "chunks_used": len(context_chunks)
        }
    
    async def _generate_gemini_response(self, prompt: str, role: str) -> str:
        """Generate response using Gemini."""
        import asyncio
        import functools
        
        try:
            loop = asyncio.get_running_loop()
            func = functools.partial(
                self.hotel_ai._gemini_model.generate_content,
                prompt
            )
            
            response = await asyncio.wait_for(
                loop.run_in_executor(None, func),
                timeout=25.0
            )
            
            if hasattr(response, 'text') and response.text:
                return response.text
            elif hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    return part.text
            
            return "I was unable to generate a response. Please try rephrasing your question."
            
        except asyncio.TimeoutError:
            return "The request timed out. Please try again."
        except Exception as e:
            print(f"[PolicyAgent] Gemini error: {e}")
            raise
    
    def _generate_offline_response(
        self, 
        role: str, 
        question: str, 
        context_chunks: List[str]
    ) -> str:
        """Generate offline response using retrieved documents."""
        if not context_chunks:
            return f"""**Direct Answer**: I don't have specific information about "{question}" in the knowledge base.

**Recommendation**: 
- Check with your supervisor or department head
- Review the relevant SOP manual
- Contact HR or Training department for guidance

**Note**: This response is generated in offline mode. For more detailed answers, please ensure the knowledge base has relevant policy documents uploaded."""
        
        # Combine context into a helpful response
        combined = "\n\n".join(context_chunks[:3])
        
        return f"""**Direct Answer**: Based on our policy documents:

{combined}

**Note**: If you need more specific guidance, please check with your supervisor or refer to the complete policy documentation.

*This response was generated from the knowledge base. For additional context or clarification, consult your department head.*"""
    
    def _extract_sources(self, context_chunks: List[str]) -> List[Dict]:
        """Extract source information from context chunks."""
        # In a more advanced implementation, we would track metadata
        # For now, return a simple indicator
        sources = []
        for i, chunk in enumerate(context_chunks[:3]):
            preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
            sources.append({
                "index": i + 1,
                "preview": preview,
                "type": "policy_document"
            })
        return sources


# Singleton instance
_policy_agent: Optional[PolicyAgent] = None


def get_policy_agent() -> PolicyAgent:
    """Get or create the PolicyAgent singleton."""
    global _policy_agent
    if _policy_agent is None:
        from app.ai_service import hotel_ai
        _policy_agent = PolicyAgent(hotel_ai)
    return _policy_agent
