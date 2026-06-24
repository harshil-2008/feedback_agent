from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import router as api_router
from storage.database import init_db

app = FastAPI(title="Feedback Agent API")

# Auto-create database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Serve static assets (CSS, JS) under /static
app.mount("/static", StaticFiles(directory="frontend", html=False), name="static")

# Root endpoint to serve the main HTML page
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

# Allow CORS for all origins (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Simple health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# If running directly, start uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
