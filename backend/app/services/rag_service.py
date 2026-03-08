# backend/app/services/rag_service.py

import hashlib
from pathlib import Path
from app.services.llm_service import HotelAI

# Original: Path(__file__).parent / "data" -> app/data
# New: Path(__file__).parent / ".." / "data" -> app/services/../data -> app/data

from app.core.config import DATA_DIR
BASE_DIR = DATA_DIR

def _generate_id(content: str) -> str:
    """Generate a stable ID for a chunk based on its content."""
    return hashlib.md5(content.encode()).hexdigest()

def index_file(hotel_ai: HotelAI, file_path: Path, audience: str, tenant_id: str = None):
    """Index a single file given its path."""
    if not file_path.exists():
        print(f"[RAG] File not found: {file_path}")
        return
        
    if not tenant_id:
        print("[RAG] Error: tenant_id missing for indexing")
        return

    try:
        content = file_path.read_text(encoding="utf-8")
        # Split into paragraphs (chunks)
        file_chunks = [p.strip() for p in content.split("\n\n") if p.strip()]
        
        count = 0
        for i, chunk_text in enumerate(file_chunks):
            chunk_id = _generate_id(chunk_text)
            meta = {
                "filename": file_path.name,
                "audience": audience,
                "chunk_index": i,
                "tenant_id": tenant_id
            }
            try:
                hotel_ai.index_document(
                    audience=audience,
                    doc_id=chunk_id,
                    text=chunk_text,
                    metadata=meta,
                    tenant_id=tenant_id
                )
                count += 1
            except Exception as e:
                print(f"[RAG] Error indexing chunk {chunk_id}: {e}")
        print(f"[RAG] Indexed {count} chunks for {file_path.name}")
        return count
        
    except Exception as e:
        print(f"[RAG] Could not read {file_path}: {e}")
        return 0

def index_knowledge_base(hotel_ai: HotelAI, target_audience: str = "all", tenant_id: str = None):
    """
    Load all markdown docs from data/{tenant_id}/staff and data/{tenant_id}/guest 
    and index them into the Vector DB.
    Returns dict with stats.
    """
    if not tenant_id:
        return {"error": "tenant_id required"}
        
    print(f"[RAG] Indexing knowledge base for tenant {tenant_id}...")
    
    stats = {
        "files_processed": 0,
        "chunks_added": 0,
        "errors": []
    }
    
    audiences = ["staff", "guest"] if target_audience == "all" else [target_audience]
    
    # Base Dir is now tenant specific: DATA_DIR / tenant_id
    tenant_dir = BASE_DIR / tenant_id
    
    for audience in audiences:
        folder = tenant_dir / audience
        
        if not folder.exists():
            # Create empty to avoid error? Or just skip
            print(f"[RAG] Info: folder {folder} does not exist yet (skipping)")
            continue
            
        # Index md, txt, pdf
        extensions = ["*.md", "*.txt", "*.pdf"]
        for ext in extensions:
            for path in folder.glob(ext):
                try:
                    chunks = index_file(hotel_ai, path, audience, tenant_id=tenant_id)
                    stats["files_processed"] += 1
                    stats["chunks_added"] += chunks
                except Exception as e:
                    stats["errors"].append(f"{path.name}: {str(e)}")
            
    print(f"[RAG] Indexing complete: {stats}")
    return stats
