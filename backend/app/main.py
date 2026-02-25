"""
CampusIQ — AI-First Intelligent College ERP
Main FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CampusIQ API",
    description="AI-First Intelligent College ERP — Predict, Adapt, Automate",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    timetable, finance, hr,
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

