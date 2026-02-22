"""
CampusIQ — Pydantic Schemas
Request/Response models for all API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ─── Auth ────────────────────────────────────────────────────────

class UserRole(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"


class UserCreate(BaseModel):
    email: str = Field(..., example="rahul@campus.edu")
    password: str = Field(..., min_length=6, example="secret123")
    full_name: str = Field(..., example="Rahul Sharma")
    role: UserRole = Field(..., example="student")


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


# ─── Student ─────────────────────────────────────────────────────

class StudentProfileCreate(BaseModel):
    roll_number: str
    department_id: int
    semester: int
    section: Optional[str] = None
    admission_year: Optional[int] = None


class StudentProfileOut(BaseModel):
    id: int
    roll_number: str
    semester: int
    section: Optional[str]
    cgpa: float
    department_name: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceSummary(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    total_classes: int
    attended: int
    percentage: float
    status: str  # "safe", "warning", "danger"
    classes_needed_for_75: int


class PredictionOut(BaseModel):
    course_name: str
    course_code: str
    predicted_grade: str
    risk_score: float
    risk_level: str  # "low", "moderate", "high"
    confidence: float
    top_factors: List[dict]


class StudentDashboard(BaseModel):
    student: StudentProfileOut
    attendance_summary: List[AttendanceSummary]
    predictions: List[PredictionOut]
    overall_risk: str
    overall_attendance: float
    ai_recommendations: List[str]


# ─── Attendance ──────────────────────────────────────────────────

class QRCodeGenerate(BaseModel):
    course_id: int
    valid_seconds: int = Field(default=90, ge=30, le=300)


class QRCodeResponse(BaseModel):
    qr_token: str
    qr_image_base64: str
    expires_at: datetime
    course_name: str


class AttendanceMark(BaseModel):
    qr_token: str


class AttendanceRecord(BaseModel):
    id: int
    student_name: str
    roll_number: str
    date: date
    is_present: bool
    method: str
    marked_at: datetime

    class Config:
        from_attributes = True


class CourseAttendanceAnalytics(BaseModel):
    course_id: int
    course_name: str
    total_students: int
    avg_attendance: float
    trend: List[dict]  # [{date, present_count, absent_count}]
    at_risk_students: int
    below_75_count: int


# ─── Faculty ─────────────────────────────────────────────────────

class FacultyProfileOut(BaseModel):
    id: int
    employee_id: str
    designation: Optional[str]
    department_name: Optional[str] = None

    class Config:
        from_attributes = True


class RiskStudent(BaseModel):
    student_id: int
    student_name: str
    roll_number: str
    attendance_pct: float
    predicted_grade: str
    risk_score: float
    risk_level: str
    top_factors: List[dict]


class ClassAnalytics(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    total_students: int
    avg_attendance: float
    avg_predicted_grade: str
    risk_distribution: dict  # {"low": 40, "moderate": 15, "high": 5}
    risk_students: List[RiskStudent]


# ─── Admin ───────────────────────────────────────────────────────

class DepartmentKPI(BaseModel):
    department_id: int
    department_name: str
    department_code: str
    total_students: int
    total_faculty: int
    avg_attendance: float
    high_risk_pct: float
    avg_cgpa: float


class AlertOut(BaseModel):
    id: int
    alert_type: str  # "high_risk", "low_attendance", "declining_trend"
    severity: str  # "info", "warning", "critical"
    message: str
    department: Optional[str]
    student_name: Optional[str]
    created_at: datetime


class AdminDashboard(BaseModel):
    total_students: int
    total_faculty: int
    total_departments: int
    campus_avg_attendance: float
    campus_high_risk_pct: float
    department_kpis: List[DepartmentKPI]
    recent_alerts: List[AlertOut]


# ─── Chatbot ─────────────────────────────────────────────────────

class ChatQuery(BaseModel):
    message: str = Field(..., example="What is my attendance in DBMS?")


class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None
    suggested_actions: Optional[List[str]] = None
