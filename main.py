"""
Smart Pharma AI Service - Main Entry Point

This is the main entry point for the Smart Pharma AI microservice.
It configures FastAPI application, CORS middleware, and includes API routes.

Usage:
    Development: uvicorn main:app --reload --port 8000
    Production:  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as ai_router
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    
    Startup:
        - Initialize database tables if they don't exist
        
    Shutdown:
        - Cleanup resources if needed
    """
    # Startup: Initialize database
    print("🚀 Starting Smart Pharma AI Service...")
    init_db()
    print("✅ Database initialized successfully")
    
    yield  # Application runs here
    
    # Shutdown: Cleanup
    print("👋 Shutting down Smart Pharma AI Service...")


# Create FastAPI application instance
app = FastAPI(
    title="Smart Pharma AI Service",
    description="""
    ## Smart Pharma AI Microservice
    
    A standalone AI-powered service for pharmaceutical inventory management.
    
    ### Features:
    - **FEFO Strategy**: First Expired, First Out inventory prioritization
    - **Expiry Alerts**: Real-time monitoring of expiring batches
    - **Priority Classification**: Automatic batch priority assignment
    
    ### Priority Levels:
    | Level | Days Until Expiry | Action |
    |-------|-------------------|--------|
    | CRITICAL | < 15 days | Sell immediately |
    | WARNING | 15-45 days | Prioritize for sale |
    | SAFE | > 45 days | Normal handling |
    
    ### Tech Stack:
    - FastAPI (Python)
    - SQLAlchemy ORM
    - PostgreSQL Database
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS middleware
# Allow requests from React frontend running on Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Vite dev server (React)
        "http://127.0.0.1:5173",      # Alternative localhost
        "http://localhost:3000",       # Create React App (if used)
        "http://127.0.0.1:3000",       # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include API routers
app.include_router(ai_router)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing service information.
    
    Returns service name, version, and links to documentation.
    """
    return {
        "service": "Smart Pharma AI Service",
        "version": "1.0.0",
        "status": "running",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "fefo_strategy": "/ai/fefo-strategy/{product_id}",
            "expiry_alerts": "/ai/expiry-alerts",
            "health": "/ai/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the application directly for development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
