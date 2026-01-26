# backend/app/ai_service.py

"""
AI service layer for the hotel assistant.
Refactored to use Vector Search (ChromaDB) and LLM (Gemini).
"""

from .llm import HotelAI
from .rag_loader import index_knowledge_base
from .knowledge import get_guest_faq_answer, get_staff_faq_answer

# Initialize AI and Knowledge Base
print("[AI Service] Initializing AI...")
hotel_ai = HotelAI()

# Index documents on startup
print("[AI Service] Indexing knowledge base...")
try:
    # TODO: Indexing is currently blocking startup. Move to background task.
    # index_knowledge_base(hotel_ai)
    print("[AI Service] Knowledge base indexing SKIPPED (Blocking). run manually if needed.")
except Exception as e:
    print(f"[AI Service] Warning: Could not index knowledge base: {e}")



async def get_guest_answer(question: str, tenant_id: str = None) -> str:
    try:
        q = question.strip()
        if not q:
            return "Please provide a question."
        
        # 1. Retrieve relevant docs from Vector DB (FAST - no API call)
        try:
            # Try with more results for better matching
            docs = hotel_ai.query_docs("guest", q, n_results=5, tenant_id=tenant_id)
            if not docs or len(docs) == 0:
                # Try a simpler query if no results
                simple_query = q.split()[0] if q.split() else q
                docs = hotel_ai.query_docs("guest", simple_query, n_results=5, tenant_id=tenant_id)
        except Exception as e:
            print(f"[AI Service] Error querying docs: {e}")
            docs = []
        
        # 2. Generate Answer with LLM (intelligent responses for general questions)
        # Use RAG if available, but LLM can answer general questions even without RAG
        # 3. Generate Answer with LLM (only if quota not exceeded)
        # CHANGED: We now attempt generation even if docs are empty to allow for general chat
        try:
            response = await hotel_ai.generate_answer_async("guest", q, docs)
            return response
        except Exception as e:
            print(f"[AI Service] Error generating answer: {e}")
            # If we have docs, try offline mode immediately
            if docs:
                try:
                    return hotel_ai._generate_offline("guest", q, docs)
                except:
                    pass
            else:
                # If no docs and LLM failed, return the error so we can debug
                return f"I'm having trouble connecting to my brain right now. (Error: {str(e)})"
            # Fall through to FAQ fallback to FAQ
            try:
                faq = get_guest_faq_answer(q)
                if faq:
                    return faq
            except Exception as e:
                print(f"[AI Service] Error in FAQ fallback: {e}")
            
            # Last resort - helpful message
            return "I'm sorry, I'm having trouble processing your question right now. Please try rephrasing it or contact the front desk for assistance."
    except Exception as e:
        print(f"[AI Service] Unexpected error in get_guest_answer: {e}")
        import traceback
        traceback.print_exc()
        return f"I encountered an unexpected error. Please try again. (Error: {str(e)})"


async def get_staff_answer(question: str, tenant_id: str = None) -> str:
    try:
        q = question.strip()
        if not q:
            return "Please provide a question."
        
        # 1. Retrieve relevant docs (FAST - no API call)
        try:
            # Try with more results for better matching
            docs = hotel_ai.query_docs("staff", q, n_results=5, tenant_id=tenant_id)
            if not docs or len(docs) == 0:
                # Try a simpler query if no results
                simple_query = q.split()[0] if q.split() else q
                docs = hotel_ai.query_docs("staff", simple_query, n_results=5, tenant_id=tenant_id)
        except Exception as e:
            print(f"[AI Service] Error querying docs: {e}")
            docs = []
        
        # 2. Generate Answer with LLM (intelligent responses for general questions)
        # Use RAG if available, but LLM can answer general questions even without RAG
        try:
            # Always try LLM - it can handle both RAG-enhanced and general questions
            response = await hotel_ai.generate_answer_async("staff", q, docs if docs else [])
            return response
        except Exception as e:
            print(f"[AI Service] Error generating answer: {e}")
            # If we have docs, try offline mode as fallback
            if docs:
                try:
                    return hotel_ai._generate_offline("staff", q, docs)
                except:
                    pass
            
            # Fallback to FAQ
            try:
                faq = get_staff_faq_answer(q)
                if faq:
                    return faq
            except Exception as e:
                print(f"[AI Service] Error in FAQ fallback: {e}")
            
            # Last resort - helpful message
            return "I'm sorry, I'm having trouble processing your question right now. Please try rephrasing it or consult the training materials."
    except Exception as e:
        print(f"[AI Service] Unexpected error in get_staff_answer: {e}")
        import traceback
        traceback.print_exc()
        return f"I encountered an unexpected error. Please try again. (Error: {str(e)})"

# Agent Instance
from .agent.orchestrator import AgentOrchestrator
agent_orchestrator = AgentOrchestrator(hotel_ai)

async def get_agent_answer(audience: str, question: str, session_id: str = None, confirm: bool = False, tenant_id: str = None):
    """
    Handle a question via the Intelligent Agent.
    """
    print(f"[Agent Service] Processing: {question} (Tenant: {tenant_id})")
    return await agent_orchestrator.process_request(audience, question, session_id, confirm, tenant_id=tenant_id)

async def confirm_agent_action(action_id: str, confirm: bool):
    """
    Execute a pending action by ID.
    """
    print(f"[Agent Service] Confirming Action: {action_id} -> {confirm}")
    return await agent_orchestrator.execute_confirmed_action(action_id, confirm)
