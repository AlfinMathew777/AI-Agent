
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.llm import HotelAI
from app.rag_loader import _generate_id

# Load Env
load_dotenv()

BACKGROUND_YELLOW = "\033[43m"
RESET = "\033[0m"

def print_header(title):
    print(f"\n{BACKGROUND_YELLOW}=== {title} ==={RESET}\n")

async def run_audit():
    print_header("1. Configuration Truth")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Expected .env path: {os.path.abspath('.env')}")
    print(f"GOOGLE_API_KEY present: {'Yes' if os.getenv('GOOGLE_API_KEY') else 'No'}")
    
    hotel_ai = HotelAI()
    
    print(f"Chroma DB Path (Absolute): {os.path.abspath('./chroma_db')}")
    print(f"Provider: {hotel_ai.provider}")
    print(f"Model ID: {getattr(hotel_ai, '_gemini_model', 'N/A')}")
    if hasattr(hotel_ai, '_gemini_model') and hotel_ai._gemini_model:
        print(f"Model Name: {hotel_ai._gemini_model.model_name}")

    print_header("2. RAG Chunking 'Truth Check'")
    # Create a dummy file in memory (simulated)
    sample_text = (
        "This is paragraph one about the pool. It is open 8am to 8pm.\n\n"
        "This is paragraph two about breakfast. Served 6am to 10am.\n\n"
        "This is a huge paragraph three. " * 5
    )
    
    print(f"Original Text Length: {len(sample_text)} chars")
    chunks = [p.strip() for p in sample_text.split("\n\n") if p.strip()]
    print(f"Chunks generated: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"  Chunk {i+1} length: {len(c)} chars | ID: {_generate_id(c)[:8]}...")
        print(f"  Preview: {c[:50]}...")

    print_header("3. Retrieval 'Truth Check'")
    # Index these chunks to a temp collection or just query existing
    # Let's query existing for "pool" to see real DB state
    question = "When is the pool open?"
    print(f"Query: '{question}'")
    
    # Manually query to get distances (HotelAI.query_docs doesn't return distances by default, let's tap into collection)
    results = hotel_ai.guest_collection.query(
        query_texts=[question],
        n_results=3,
        include=['documents', 'metadatas', 'distances']
    )
    
    if results['documents']:
        print(f"Top-3 Retrieval Results:")
        for i in range(len(results['documents'][0])):
            doc_text = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            dist = results['distances'][0][i]
            print(f"  Result {i+1}:")
            print(f"    Source: {meta.get('source', 'unknown')}")
            print(f"    Distance: {dist:.4f} (Lower is better)")
            print(f"    Text: {doc_text[:100].replace('\n', ' ')}...")
    else:
        print("  No documents found in DB.")

    print_header("4. Prompt Construction 'Truth Check'")
    # Simulate prompt
    context_text = "\n".join(results['documents'][0]) if results['documents'] else "NO CONTEXT"
    role_desc = "You are a helpful Hotel Concierge."
    prompt = (
        f"{role_desc}\n\n"
        f"Context from knowledge base:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        f"Instructions: Use the provided context to answer..." # abbreviated
    )
    print(f"Prompt Length: {len(prompt)} characters")
    print(f"Context Length: {len(context_text)} characters")
    print("Prompt Head (First 5 lines):")
    print("\n".join(prompt.split("\n")[:5]))
    
if __name__ == "__main__":
    asyncio.run(run_audit())
