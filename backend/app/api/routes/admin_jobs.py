
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_current_tenant
from app.db.session import get_db_connection
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter()

class ExecutionJob(BaseModel):
    id: str
    quote_id: str
    status: str
    stripe_event_id: str
    attempts: int
    last_error: Optional[str]
    created_at: str

@router.get("/admin/jobs", response_model=List[ExecutionJob])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant_id: str = Depends(get_current_tenant)
):
    conn = get_db_connection()
    conn.row_factory = get_db_connection().row_factory
    
    query = "SELECT * FROM execution_jobs WHERE tenant_id = ?"
    params = [tenant_id]
    
    if status:
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@router.get("/admin/jobs/{job_id}", response_model=ExecutionJob)
async def get_job(
    job_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    conn = get_db_connection()
    conn.row_factory = get_db_connection().row_factory
    
    row = conn.execute("SELECT * FROM execution_jobs WHERE id = ? AND tenant_id = ?", (job_id, tenant_id)).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return dict(row)
