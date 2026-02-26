"""
CampusIQ — AI-First Intelligent College ERP
Main FastAPI Application Entry Point
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.services.gemini_pool_service import close_http_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events."""
    # Startup
    yield
    # Shutdown - cleanup resources
    await close_http_client()


app = FastAPI(
    title="CampusIQ API",
    description="AI-First Intelligent College ERP — Predict, Adapt, Automate",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "CampusIQ API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


# ----- Route Registration -----
from app.api.routes import (
    auth, students, faculty, attendance, predictions,
    chatbot, admin, nlp_crud, copilot,
    users, courses, departments, notifications, export,
    timetable, finance, hr, operational_ai,
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(faculty.router, prefix="/api/faculty", tags=["Faculty"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["Attendance"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(nlp_crud.router, prefix="/api/ai-data", tags=["AI Data Operations"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["AI Copilot"])
app.include_router(users.router, prefix="/api/users", tags=["User Management"])
app.include_router(courses.router, prefix="/api/courses", tags=["Course Management"])
app.include_router(departments.router, prefix="/api/departments", tags=["Department Management"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(timetable.router, prefix="/api/timetable", tags=["Timetable"])
app.include_router(finance.router, prefix="/api/finance", tags=["Finance"])
app.include_router(hr.router, prefix="/api/hr", tags=["HR & Payroll"])
app.include_router(operational_ai.router, prefix="/api/ops-ai", tags=["Operational AI"])


# ----- Serve Frontend Static Files (Production) -----
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    # Mount static assets (JS, CSS, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static-assets")
    
    # Serve index.html for all non-API routes (SPA support)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't intercept API routes or docs
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
            return {"error": "Not found"}
        
        file_path = frontend_dist / full_path
        # If file exists (like favicon.ico), serve it
        if file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for SPA routing
        return FileResponse(frontend_dist / "index.html")

