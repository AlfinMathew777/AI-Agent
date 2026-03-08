from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from datetime import datetime, timezone
from pathlib import Path
import os
import re
from app.core.security.admin import verify_admin
from app.api.deps import get_current_tenant
from app.services.rag_service import index_knowledge_base, index_file
from app.services.llm_service import HotelAI

# Initialize objects needed for routes
# Ideally dependency injection, but global instance for MVP is fine per original code
# But original code used `hotel_ai` imported from `ai_service` or `llm`?
# main.py imported: `from .ai_service import get_guest_answer, get_staff_answer, hotel_ai`
# So we import it from ai_service to share the singleton
from app.ai_service import hotel_ai

router = APIRouter()

# Global State (kept from main.py)
last_reindex_status = {
    "time": None,
    "error": None
}

from app.core.config import DATA_DIR


@router.post("/admin/reindex", dependencies=[Depends(verify_admin)])
async def reindex_knowledge_base_endpoint(
    audience: str = "all",
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Trigger a manual reindex of the knowledge base.
    audience: 'guest', 'staff', 'all'
    """
    global last_reindex_status
    
    try:
        stats = index_knowledge_base(hotel_ai, audience, tenant_id=tenant_id)
        
        # Add collection counts
        guest_stats = hotel_ai.get_collection_stats("guest", tenant_id)
        staff_stats = hotel_ai.get_collection_stats("staff", tenant_id)
        stats["guest_docs_count"] = guest_stats.get("count", 0)
        stats["staff_docs_count"] = staff_stats.get("count", 0)
        
        # Update Status
        last_reindex_status["time"] = datetime.now(timezone.utc).isoformat()
        last_reindex_status["error"] = None
        
        return {"status": "success", **stats}
    except Exception as e:
        last_reindex_status["time"] = datetime.now(timezone.utc).isoformat()
        last_reindex_status["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/index/status", dependencies=[Depends(verify_admin)])
async def get_index_status(tenant_id: str = Depends(get_current_tenant)):
    """Get current status of vector collections."""
    guest_stats = hotel_ai.get_collection_stats("guest", tenant_id)
    staff_stats = hotel_ai.get_collection_stats("staff", tenant_id)
    return {
        "guest_docs": guest_stats.get("count", 0),
        "staff_docs": staff_stats.get("count", 0),
        "last_reindex_time": last_reindex_status["time"],
        "last_reindex_error": last_reindex_status["error"]
    }

@router.post("/admin/upload", dependencies=[Depends(verify_admin)])
async def upload_file(
    file: UploadFile = File(...), 
    audience: str = Form(...), # "guest" or "staff"
    tenant_id: str = Depends(get_current_tenant)
):
    if audience not in ["guest", "staff"]:
        raise HTTPException(status_code=400, detail="Invalid audience")
    
    # 1. Validate Extension
    ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt"}
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {ALLOWED_EXTENSIONS}")

    # 2. Validate Size (10MB limit)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (Max 10MB)")

    # 3. Sanitize Filename
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
    
    # Tenant Isolated Path
    # data/{tenant_id}/{audience}/filename
    target_dir = DATA_DIR / tenant_id / audience
    target_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = target_dir / safe_filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
        
    # Index immediately
    try:
        chunks = index_file(hotel_ai, file_path, audience, tenant_id=tenant_id)
    except Exception as e:
        return {"status": "saved_but_indexing_failed", "error": str(e)}

    return {
        "status": "success", 
        "filename": safe_filename, 
        "audience": audience,
        "chunks_indexed": chunks if isinstance(chunks, int) else 0 
    }

@router.get("/admin/files", dependencies=[Depends(verify_admin)])
async def list_files(tenant_id: str = Depends(get_current_tenant)):
    """List all files in the knowledge base."""
    result = {"guest": [], "staff": []}
    
    for audience in ["guest", "staff"]:
        folder = DATA_DIR / tenant_id / audience
        if folder.exists():
            extensions = ["*.md", "*.txt", "*.pdf"]
            for ext in extensions:
                for f in folder.glob(ext):
                    result[audience].append(f.name)
                
    return result

@router.delete("/admin/files/{audience}/{filename}", dependencies=[Depends(verify_admin)])
async def delete_file(
    audience: str, 
    filename: str,
    tenant_id: str = Depends(get_current_tenant)
):
    if audience not in ["guest", "staff"]:
        raise HTTPException(status_code=400, detail="Invalid audience")
        
    file_path = DATA_DIR / tenant_id / audience / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        # 1. Delete file
        os.remove(file_path)
        
        # 2. Delete vectors
        deleted_count = hotel_ai.delete_vectors_by_filename(audience, filename, tenant_id=tenant_id)
        
        return {"status": "deleted", "file": filename, "vectors_deleted": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
