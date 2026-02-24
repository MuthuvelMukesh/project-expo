"""
CampusIQ — Optimized Main Application
Add caching headers, compression, and security headers.

Apply these changes to: backend/app/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(
    title="CampusIQ API",
    description="AI-First Intelligent College ERP — Predict, Adapt, Automate",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── MIDDLEWARE: Security Headers ───────────────────────────────────────

# 1. Trust proxy headers (for production behind reverse proxy)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "0.0.0.0"])

# 2. GZIP Compression (reduce response size by 70-80%)
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# 3. CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── HEALTH CHECK ENDPOINTS ─────────────────────────────────────────────

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
    """Quick health check endpoint."""
    from app.core.database import verify_db_connection
    db_ok = await verify_db_connection()
    return {
        "status": "healthy",
        "database": "connected" if db_ok else "disconnected",
    }


# ─── SETUP STARTUP/SHUTDOWN EVENTS ──────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Called when server starts."""
    from app.core.database import verify_db_connection
    db_ok = await verify_db_connection()
    if not db_ok:
        print("⚠️  WARNING: Database not available at startup")
    else:
        print("✅ Database connection verified")
    
    # Warm up ML model
    try:
        from app.services.prediction_service import _load_model
        _load_model()
        print("✅ ML model pre-loaded")
    except Exception as e:
        print(f"⚠️  ML model could not be preloaded: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Called when server shuts down."""
    print("🛑 CampusIQ API shutting down...")


# ─── ROUTE REGISTRATION ────────────────────────────────────────────────

from app.api.routes import (
    auth, students, faculty, attendance, predictions,
    chatbot, admin, nlp_crud, copilot,
    users, courses, departments, notifications, export,
    timetable,
)

# Include all routers with prefixes
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


# ─── CUSTOM RESPONSE HEADERS FOR CACHING ──────────────────────────────

from fastapi.responses import JSONResponse
from functools import wraps

def add_cache_control(max_age: int = 3600):
    """Decorator to add cache-control headers to responses."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            response.headers["Cache-Control"] = f"public, max-age={max_age}"
            return response
        return wrapper
    return decorator


# Example: Cache department list for 1 hour
# @app.get("/api/departments")
# @add_cache_control(max_age=3600)
# async def list_departments(...):
#     ...


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
