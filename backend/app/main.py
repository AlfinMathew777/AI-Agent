import os
from dotenv import load_dotenv
from app.app_factory import create_app
from app.db.session import init_db

load_dotenv()

app = create_app()

@app.on_event("startup")
async def startup_event():
    # Check Admin Key on startup
    if not os.getenv("ADMIN_API_KEY"):
        print("WARNING: ADMIN_API_KEY is not set. Admin endpoints will fail.")
        
    init_db()