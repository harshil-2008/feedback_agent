from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load .env from project root using absolute path, override any existing env vars
_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(_env_path, override=True)
print(f"[startup] Loaded .env from: {_env_path}")
print(f"[startup] SERPAPI_KEY present: {bool(os.getenv('SERPAPI_KEY'))}")
print(f"[startup] SERPAPI_KEY prefix: {os.getenv('SERPAPI_KEY','MISSING')[:10]}")

from storage.database import get_db, SessionLocal
from storage.models import Feedback
from data_ingestion_service.api.routes import router as api_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")

@app.get("/api/debug-env")
def debug_env():
    """Debug endpoint — shows which env vars are loaded at runtime."""
    return {
        "SERPAPI_KEY": os.getenv("SERPAPI_KEY", "MISSING")[:12] + "..." if os.getenv("SERPAPI_KEY") else "MISSING",
        "DISCORD_BOT_TOKEN": "SET" if os.getenv("DISCORD_BOT_TOKEN") else "MISSING",
        "env_file_path": _env_path,
        "env_file_exists": os.path.exists(_env_path),
    }

class FeedbackIn(BaseModel):
    source: str
    content: str
    user_id: str | None = None

@app.post("/feedback")
def receive_feedback(feedback: FeedbackIn):
    db = SessionLocal()
    try:
        db_feedback = Feedback(
            source=feedback.source,
            content=feedback.content,
            user_id=feedback.user_id,
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return {"id": db_feedback.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# Mount frontend static files LAST so it doesn't intercept API routes
from data_ingestion_service.api.search_routes import router as search_router
app.include_router(search_router, prefix="/api")
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
# Serve all frontend files (index.html, app.js, styles.css) from /
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
