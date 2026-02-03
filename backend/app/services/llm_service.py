# backend/app/services/llm_service.py

import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Optional
import chromadb
from chromadb.utils import embedding_functions
from huggingface_hub import InferenceClient

# Load env vars
load_dotenv()


# Import MCP Client
try:
    from app.mcp_client import MCPClient
except Exception as e:
    print(f"[LLM] Warning: MCPClient Import FAILED: {e}")
    MCPClient = None

import google.ai.generativelanguage as glm # For tool formatting if needed

class HotelAI:
    def __init__(self):
        # Use PersistentClient to save data to disk
        from app.core.config import CHROMA_PATH
        print(f"[LLM] Using ChromaDB path: {CHROMA_PATH}")
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Collections
        self.guest_collection = self.chroma_client.get_or_create_collection(
            name="guest_docs", embedding_function=self.embed_fn
        )
        self.staff_collection = self.chroma_client.get_or_create_collection(
            name="staff_docs", embedding_function=self.embed_fn
        )
        
        # Provider setup
        self.provider = "offline"
        self._gemini_model = None
        self._hf_client = None
        
        # MCP Setup
        try:
            self.mcp_client = MCPClient()
        except Exception as e:
            print(f"[LLM] Warning: MCPClient Init Failed: {e}")
            self.mcp_client = None

        self.available_tools = []
        self._tools_cache = {}  # Cache tools by audience
        self._tools_cache_time = {}  # Track cache timestamp
        self._cache_ttl = 300  # Cache for 5 minutes
        
        # Quota tracking - Set to False to enable LLM for general questions
        # Set to True only if you want to completely bypass API
        self._quota_exceeded = False
        self._quota_reset_time = None
        
        self._setup_provider()

    def _setup_provider(self):
        """Determine which AI provider to use."""
        google_key = os.getenv("GOOGLE_API_KEY")
        hf_token = os.getenv("HF_TOKEN")
        
        if google_key:
            print("[LLM] Using Google Gemini (Free Tier/Pro)")
            genai.configure(api_key=google_key)
            
            # Use gemini-flash-latest for stable free tier usage
            self._gemini_model = genai.GenerativeModel(
                'gemini-flash-latest', 
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            self.provider = "gemini"
        
        elif hf_token:
            print("[LLM] Using HuggingFace Inference API")
            # Using Mistral 7B Instruct which is usually available on free tier
            self._hf_client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.2", token=hf_token)
            self.provider = "huggingface"
            
        else:
            print("[LLM] No API Keys found. Using OFFLINE SIMULATION mode.")
            self.provider = "offline"
    
    # Restoring missing methods
    
    def get_collection_name(self, audience: str, tenant_id: str) -> str:
        # Sanitize tenant_id just in case, though UUID is safe.
        safe_tenant = tenant_id.replace("-", "_")
        return f"{audience}_docs__{safe_tenant}"

    def get_collection(self, audience: str, tenant_id: str):
        col_name = self.get_collection_name(audience, tenant_id)
        return self.chroma_client.get_or_create_collection(
            name=col_name, embedding_function=self.embed_fn
        )

    def index_document(self, audience: str, doc_id: str, text: str, metadata: dict = None, tenant_id: str = None):
        """Add a document chunk to the vector DB."""
        if not tenant_id:
             print(f"[LLM] Error: tenant_id required for indexing")
             return
             
        collection = self.get_collection(audience, tenant_id)
        # Use upsert
        collection.upsert(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )

    def query_docs(self, audience: str, query: str, n_results: int = 5, tenant_id: str = None) -> List[str]:
        """Retrieve relevant document chunks."""
        # For backward compatibility, use default tenant if not provided
        if not tenant_id:
             tenant_id = "default-tenant-0000"
             print(f"[LLM] Warning: query_docs called without tenant_id. Using default tenant.")

        try:
            collection = self.get_collection(audience, tenant_id)
            
            # Check if collection has any documents
            count = collection.count()
            if count == 0:
                print(f"[LLM] Warning: Collection {collection.name} is empty.")
                return []
            
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, count)
            )
            docs = results['documents'][0] if results['documents'] else []
            print(f"[LLM] Found {len(docs)} documents for query: {query[:50]}... in {collection.name}")
            return docs
        except Exception as e:
            print(f"[LLM] Error querying documents: {e}")
            return []

    def delete_vectors_by_filename(self, audience: str, filename: str, tenant_id: str = None) -> int:
        """Delete all vectors associated with a specific file."""
        if not tenant_id: return 0
        
        collection = self.get_collection(audience, tenant_id)
        initial_count = collection.count()
        
        try:
            collection.delete(where={"filename": filename})
        except Exception as e:
            print(f"[LLM] Metadata delete failed, trying fallback: {e}")
            return 0
        
        final_count = collection.count()
        deleted = initial_count - final_count
        print(f"[LLM] Deleted {deleted} vectors for file: {filename} in {collection.name}")
        return deleted

    def get_collection_stats(self, audience: str, tenant_id: str = None) -> dict:
        """Get stats for a specific collection."""
        if not tenant_id: return {"count": 0, "error": "No tenant_id"}
        
        try:
            collection = self.get_collection(audience, tenant_id)
            return {
                "count": collection.count(),
                "audience": audience,
                "collection": collection.name
            }
        except Exception as e:
            print(f"[LLM] Error getting stats: {e}")
            return {"count": 0, "audience": audience, "error": str(e)}

    async def _get_gemini_tools(self, audience: str):
        """Get tools converted for Gemini, filtered by audience."""
        # Check cache first
        import time
        current_time = time.time()
        if audience in self._tools_cache:
            cache_age = current_time - self._tools_cache_time.get(audience, 0)
            if cache_age < self._cache_ttl:
                return self._tools_cache[audience]
        
        # 1. Fetch tools from MCP with timeout
        try:
            # Use asyncio.wait_for to add timeout
            import asyncio
            mcp_tools = await asyncio.wait_for(
                self.mcp_client.list_tools(),
                timeout=2.0  # 2 second timeout
            )
        except asyncio.TimeoutError:
            print(f"Warning: MCP tools fetch timed out. Using cached tools or empty list.")
            # Return cached tools if available, even if expired
            if audience in self._tools_cache:
                return self._tools_cache[audience]
            return []
        except Exception as e:
            print(f"Warning: Could not fetch MCP tools: {e}")
            # Return cached tools if available
            if audience in self._tools_cache:
                return self._tools_cache[audience]
            return []

        # 2. Filter based on Audience (Role-Based Access)
        allowed_tools = []
        for tool in mcp_tools:
            # Policy:
            # - Guest: Can only use 'check_room_availability'
            # - Staff: Can use everything
            if audience == "guest":
                if tool.name in ["check_room_availability"]:
                    allowed_tools.append(tool)
            else: # staff
                allowed_tools.append(tool)
        
        # 3. Convert to Gemini Tool format
        # Gemini expects a list of Tool objects, each containing function_declarations
        gemini_functions = []
        for tool in allowed_tools:
            # This is a simplified conversion. 
            # Real conversion needs to map JSON Schema types to Gemini types safely.
            # For this MVP, we declare them manually or use a helper if we had one.
            # We'll use a specific manual mapping for our known HotelOps tools to ensure stability.
            
            if tool.name == "check_room_availability":
                gemini_functions.append({
                    "name": "check_room_availability",
                    "description": tool.description,
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "room_type": {"type": "STRING", "description": "Type of room: standard, deluxe, suite"},
                            "date": {"type": "STRING", "description": "Date in YYYY-MM-DD format"}
                        },
                        "required": ["room_type", "date"]
                    }
                })
            elif tool.name == "book_room":
                gemini_functions.append({
                    "name": "book_room",
                    "description": tool.description,
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "guest_name": {"type": "STRING", "description": "Name of the guest"},
                            "room_type": {"type": "STRING", "description": "Type of room"},
                            "date": {"type": "STRING", "description": "Date YYYY-MM-DD"}
                        },
                        "required": ["guest_name", "room_type", "date"]
                    }
                })
        
        # Cache the result
        self._tools_cache[audience] = gemini_functions
        self._tools_cache_time[audience] = current_time
        
        return gemini_functions

    async def generate_answer_async(self, audience: str, question: str, context_chunks: List[str]) -> str:
        """Async version of generate_answer - handles both RAG and general questions intelligently."""
        try:
            # Check quota status - if exceeded, use offline mode for RAG, but try to be helpful
            if hasattr(self, '_quota_exceeded') and self._quota_exceeded:
                # Quota exceeded - use offline mode if we have context
                if context_chunks:
                    print(f"[LLM] Quota exceeded - using offline mode with context")
                    return self._generate_offline(audience, question, context_chunks)
                else:
                    # No context, but still try to be helpful
                    return (
                        f"I'm currently operating in offline mode. While I don't have specific information about '{question}' "
                        f"in my knowledge base, here are some general suggestions:\n\n"
                        f"• For hotel-specific questions, please contact the front desk\n"
                        f"• For general questions, I can provide basic guidance\n"
                        f"• Try asking about: facilities, dining, events, or local attractions\n\n"
                        f"Would you like to rephrase your question or contact the front desk for immediate assistance?"
                    )
            
            if self.provider == "gemini":
                if not self._gemini_model:
                    # No model, use offline mode
                    if context_chunks:
                        return self._generate_offline(audience, question, context_chunks)
                    raise Exception("Gemini model not initialized. Check GOOGLE_API_KEY environment variable.")
                return await self._generate_gemini(audience, question, context_chunks)
            elif self.provider == "huggingface":
                if not self._hf_client:
                    if context_chunks:
                        return self._generate_offline(audience, question, context_chunks)
                    raise Exception("HuggingFace client not initialized. Check HF_TOKEN environment variable.")
                return self._generate_huggingface(audience, question, context_chunks)
            else:
                return self._generate_offline(audience, question, context_chunks)
        except Exception as e:
            print(f"[LLM] Error in generate_answer_async: {e}")
            # Always fallback to offline mode if context available - don't raise
            if context_chunks:
                print(f"[LLM] Falling back to offline mode due to error")
                return self._generate_offline(audience, question, context_chunks)
            # Only raise if no context available
            return f"I encountered an error. Please try again. (Error: {str(e)[:100]})"

    # ... (Keep sync generate_answer as compatibility wrapper or strictly use async in main.py) ...
    
    async def _generate_gemini(self, audience, question, context_chunks):
        if not self._gemini_model:
            # No model available, use offline mode
            if context_chunks:
                return self._generate_offline(audience, question, context_chunks)
            return "Gemini model not initialized. Please check your GOOGLE_API_KEY environment variable."
        
        # Check if quota is exceeded - skip API call immediately (INSTANT bypass)
        if hasattr(self, '_quota_exceeded') and self._quota_exceeded:
            # Quota exceeded - use offline mode IMMEDIATELY (NO API CALL, NO WAITING)
            if context_chunks:
                print(f"[LLM] Quota exceeded - using offline mode INSTANTLY - SKIPPING API CALL")
                return self._generate_offline(audience, question, context_chunks)
            else:
                return "I'm currently unable to process requests due to API quota limits. Please try again later."
        
        role_desc = "You are a helpful Hotel Concierge." if audience == "guest" else "You are a Staff Assistant."
        
        # Ensure context_chunks is a list
        if not context_chunks:
            context_chunks = []
        if not isinstance(context_chunks, list):
            context_chunks = [str(context_chunks)]
        
        # Build intelligent prompt that handles both RAG and general questions
        if context_chunks:
            # RAG-enhanced: Use context when available
            context_text = "\n".join(context_chunks)
            prompt = (
                f"{role_desc}\n\n"
                f"Context from knowledge base:\n{context_text}\n\n"
                f"Question: {question}\n\n"
                f"Instructions: Use the provided context to answer hotel-specific questions accurately. "
                f"If the question is general conversation (e.g., greetings, 'how are you', 'tell me a joke'), "
                f"answer naturally and politely using your general knowledge. "
                f"However, if the question is about specific hotel details (amenities, hours, policies) and the information is NOT in the context, "
                f"admit that you don't have that specific information and suggest contacting the front desk."
            )
        else:
            # General question: Use LLM intelligence without RAG
            prompt = (
                f"{role_desc}\n\n"
                f"Question: {question}\n\n"
                f"Instructions:\n"
                f"- Answer this question using your general knowledge and intelligence.\n"
                f"- Be helpful, friendly, and professional.\n"
                f"- If this is a hotel-related question but you don't have specific information, provide general guidance.\n"
                f"- For hotel-specific details you don't know, suggest contacting the front desk.\n"
                f"- You can answer general questions about travel, hospitality, local areas, etc."
            )
        
        # Try API call ONCE - if it fails with quota error, immediately use offline mode
        import asyncio
        import random
        import re

        max_retries = 0  # NO RETRIES - try once, if quota error, use offline immediately
        
        for attempt in range(max_retries + 1):
            try:
                # Use simple generate_content - no tools for now to avoid errors
                print(f"[LLM] Attempting API call (attempt {attempt + 1})...")
                response = self._gemini_model.generate_content(prompt)

                # Extract Final Text
                try:
                    if hasattr(response, 'text') and response.text:
                        return response.text
                    elif hasattr(response, 'candidates') and response.candidates:
                        # Try to extract text from candidates
                        for candidate in response.candidates:
                            if hasattr(candidate, 'content') and candidate.content:
                                if hasattr(candidate.content, 'parts'):
                                    for part in candidate.content.parts:
                                        if hasattr(part, 'text') and part.text:
                                            return part.text
                    return "I received a response but couldn't extract the text. Please try again."
                except Exception as e:
                    print(f"[LLM] Error extracting response text: {e}")
                    return "I encountered an error processing the response. Please try again."

            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__
                print(f"[LLM] Error on attempt {attempt + 1}: {error_type}: {error_str[:200]}")
                
                # Check for quota/rate limit errors - IMMEDIATE detection, no retries
                is_quota_error = (
                    "429" in error_str or 
                    "quota" in error_str.lower() or 
                    "ResourceExhausted" in error_type or
                    "limit" in error_str.lower() or
                    "exceeded" in error_str.lower()
                )
                
                if is_quota_error:
                    # Mark quota as exceeded and set reset time (1 hour from now)
                    import time
                    self._quota_exceeded = True
                    self._quota_reset_time = time.time() + 3600  # 1 hour
                    
                    # For quota errors, IMMEDIATELY fall back to offline mode - NO RETRIES
                    if context_chunks:
                        print(f"[LLM] Quota exceeded detected - IMMEDIATELY using offline mode (NO RETRIES, NO WAITING)")
                        return self._generate_offline(audience, question, context_chunks)
                    else:
                        return "I'm currently unable to process requests due to API quota limits. Please try again later or contact support."
                
                # For ANY error (including 429), immediately fall back to offline mode - NO RETRIES
                if context_chunks:
                    print(f"[LLM] API error occurred - IMMEDIATELY using offline mode (NO RETRIES)")
                    return self._generate_offline(audience, question, context_chunks)
                
                # No context available, return error message
                if "API key" in error_str or "authentication" in error_str.lower():
                    return "I'm having trouble connecting to the AI service. Please check the API configuration."
                else:
                    return f"I encountered an error while processing your request. Please try again or rephrase your question."

    def _generate_huggingface(self, audience, question, context_chunks):
        role_desc = "You are a helpful Hotel Concierge." if audience == "guest" else "You are a Staff Assistant."
        prompt = (
            f"<s>[INST] {role_desc}\n"
            f"Context:\n" + "\n".join(context_chunks) + "\n\n"
            f"Question: {question}\n"
            f"Instructions: Answer based on context. if general question, answer naturally. [/INST]"
        )
        try:
            # Simple synchronous call
            return self._hf_client.text_generation(prompt, max_new_tokens=200)
        except Exception as e:
            return f"I'm sorry, my connection is unstable. (HuggingFace Error: {str(e)})"

    def _generate_offline(self, audience, question, context_chunks):
        """Offline mode that returns relevant document chunks in a helpful format."""
        if not context_chunks:
            return (
                f"I couldn't find specific information about '{question}' in the knowledge base. "
                f"Here are some things you might find helpful:\n\n"
                f"• Try rephrasing your question with different keywords\n"
                f"• Ask about specific topics like: dining, facilities, events, transport, or local attractions\n"
                f"• Contact the front desk for immediate assistance\n\n"
                f"If you're looking for general information, I can help with questions about:\n"
                f"- Hotel facilities and services\n"
                f"- Dining options and room service\n"
                f"- Local attractions and transport\n"
                f"- Events and entertainment"
            )
        
        # Combine all relevant chunks for a comprehensive answer
        combined_context = "\n\n".join(context_chunks[:3])  # Use top 3 chunks
        
        return (
            f"Based on your question about '{question}', here's what I found:\n\n"
            f"{combined_context}\n\n"
            f"If you need more specific information, please feel free to ask or contact the front desk."
        )
