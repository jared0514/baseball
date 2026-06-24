"""
MLB Baseball Analytics Platform — FastAPI Application
Main entry point for the backend API server.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database.models import init_db
from api.routers import (
    teams_router, players_router, games_router,
    standings_router, analysis_router, genai_router, ml_router
)

load_dotenv()

# ──────────────────────────────────────────────
# App Configuration
# ──────────────────────────────────────────────
app = FastAPI(
    title="⚾ MLB Analytics API",
    description="MLB Baseball Analytics Platform — 2024 Season Data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — Allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # Next.js dev
        "http://127.0.0.1:3000",
        "http://localhost:5173",     # Vite dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Register Routers
# ──────────────────────────────────────────────
app.include_router(teams_router)
app.include_router(players_router)
app.include_router(games_router)
app.include_router(standings_router)
app.include_router(analysis_router)
app.include_router(genai_router)
app.include_router(ml_router)


# ──────────────────────────────────────────────
# Root & Health Check
# ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "message": "⚾ MLB Analytics API is running!",
        "docs": "/docs",
        "version": "1.0.0",
        "season": 2024,
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}


# ──────────────────────────────────────────────
# Startup Event
# ──────────────────────────────────────────────
@app.on_event("startup")
def startup():
    """Initialize database on startup."""
    init_db()


# ──────────────────────────────────────────────
# Run (development)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
    )
