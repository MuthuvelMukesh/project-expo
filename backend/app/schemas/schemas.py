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
    data_query: bool = False
    context_used: bool = False
    redirect_to_console: bool = False
    suggested_command: Optional[str] = None
    data: Optional[List[dict]] = None
    sources: Optional[List[str]] = None
    suggested_actions: Optional[List[str]] = None


# ─── NLP CRUD ────────────────────────────────────────────────────

class NLPCrudQuery(BaseModel):
    message: str = Field(..., example="Show all students in Computer Science department")
    context: Optional[dict] = Field(default=None, example=None)


class NLPCrudResponse(BaseModel):
    intent: str = Field(..., example="READ")
    entity: str = Field(..., example="Student")
    result: Optional[dict] = None
    summary: str = Field(..., example="Found 25 Student records:")
    row_count: Optional[int] = Field(default=None, example=25)
    sql_preview: Optional[str] = None
    error: Optional[str] = None


# ─── AI Copilot ──────────────────────────────────────────────────

class CopilotRequest(BaseModel):
    message: str = Field(..., example="Register 3 new students in Computer Science department")


class CopilotAction(BaseModel):
    action_id: str
    type: str  # READ, CREATE, UPDATE, DELETE, ANALYZE, NAVIGATE
    entity: str
    description: str
    risk_level: str = "safe"  # safe, low, high
    requires_confirmation: bool = False
    params: Optional[dict] = None


class CopilotPlan(BaseModel):
    plan_id: str
    message: str
    actions: List[CopilotAction]
    summary: str
    requires_confirmation: bool = False
    auto_executed: Optional[List[dict]] = None


class CopilotConfirm(BaseModel):
    plan_id: str
    approved_action_ids: List[str] = []
    rejected_action_ids: List[str] = []


class CopilotResult(BaseModel):
    plan_id: str
    actions_executed: int = 0
    actions_failed: int = 0
    actions_rejected: int = 0
    results: List[dict] = []
    summary: str = ""


class CopilotHistoryItem(BaseModel):
    id: int
    plan_id: str
    action_type: str
    entity: str
    description: str
    risk_level: str
    status: str
    created_at: datetime
    executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── User Management (Admin) ────────────────────────────────────

class UserManageCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    full_name: str
    role: UserRole
    # Optional profile fields
    department_id: Optional[int] = None
    roll_number: Optional[str] = None
    employee_id: Optional[str] = None
    semester: Optional[int] = 1
    section: Optional[str] = "A"
    designation: Optional[str] = "Assistant Professor"


class UserManageUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    department_id: Optional[int] = None
    semester: Optional[int] = None
    section: Optional[str] = None
    designation: Optional[str] = None


class UserDetail(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    department_name: Optional[str] = None
    roll_number: Optional[str] = None
    employee_id: Optional[str] = None
    semester: Optional[int] = None
    section: Optional[str] = None
    cgpa: Optional[float] = None
    designation: Optional[str] = None


# ─── Course Management ───────────────────────────────────────────

class CourseCreate(BaseModel):
    code: str
    name: str
    department_id: int
    semester: int
    credits: int = 3
    instructor_id: Optional[int] = None


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[int] = None
    semester: Optional[int] = None
    credits: Optional[int] = None
    instructor_id: Optional[int] = None


class CourseDetail(BaseModel):
    id: int
    code: str
    name: str
    department_id: int
    department_name: Optional[str] = None
    semester: int
    credits: int
    instructor_id: Optional[int] = None


# ─── Conversational Operational AI ─────────────────────────────

class OperationalPlanRequest(BaseModel):
    message: str
    module: str = "nlp"
    clarification: Optional[str] = None


class ClarificationPayload(BaseModel):
    code: str
    message: str
    unclear_parts: List[str]
    question: str
    confidence: float
    threshold: float


class OperationalPlanResponse(BaseModel):
    plan_id: str
    intent: str
    entity: str
    confidence: float
    risk_level: str
    estimated_impact_count: int
    requires_confirmation: bool
    requires_senior_approval: bool
    requires_2fa: bool
    status: str
    clarification: Optional[ClarificationPayload] = None
    preview: dict
    auto_execution: Optional[dict] = None
    ai_service: Optional[dict] = None
    permission: dict


class OperationalDecisionRequest(BaseModel):
    plan_id: str
    decision: str  # APPROVE, REJECT, ESCALATE
    approved_ids: Optional[List[int]] = None
    rejected_ids: Optional[List[int]] = None
    comment: Optional[str] = None
    two_factor_code: Optional[str] = None


class OperationalDecisionResponse(BaseModel):
    plan_id: str
    status: str
    decision: str
    two_factor_verified: bool
    approved_ids: List[int] = []
    rejected_ids: List[int] = []


class OperationalExecuteRequest(BaseModel):
    plan_id: str


class OperationalExecuteResponse(BaseModel):
    plan_id: str
    execution_id: str
    status: str
    affected_count: Optional[int] = None
    before_state: Optional[List[dict]] = None
    after_state: Optional[List[dict]] = None
    error: Optional[str] = None
    alert: Optional[str] = None


class OperationalRollbackRequest(BaseModel):
    execution_id: str


class OperationalRollbackResponse(BaseModel):
    execution_id: str
    plan_id: Optional[str] = None
    status: str
    error: Optional[str] = None


class AuditHistoryItem(BaseModel):
    event_id: str
    plan_id: Optional[str] = None
    execution_id: Optional[str] = None
    user_id: int
    role: str
    module: str
    operation_type: str
    event_type: str
    risk_level: str
    intent_payload: dict
    before_state: List[dict]
    after_state: List[dict]
    metadata: dict
    created_at: Optional[str] = None


class PendingApprovalItem(BaseModel):
    plan_id: str
    user_id: int
    requester_name: str
    module: str
    message: str
    intent_type: str
    entity: str
    risk_level: str
    estimated_impact_count: int
    requires_2fa: bool
    created_at: Optional[str] = None


class OpsModuleStat(BaseModel):
    module: str
    total: int
    executed: int
    failed: int
    rolled_back: int


class OpsRiskStat(BaseModel):
    risk_level: str
    count: int


class OpsStatsResponse(BaseModel):
    total_plans: int
    awaiting_approval: int
    executed_today: int
    failed_total: int
    by_risk: List[OpsRiskStat]
    by_module: List[OpsModuleStat]


# ─── Department Management ───────────────────────────────────────

class DepartmentCreate(BaseModel):
    name: str
    code: str = Field(..., max_length=10)


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None


class DepartmentDetail(BaseModel):
    id: int
    name: str
    code: str
    total_students: int = 0
    total_faculty: int = 0
    total_courses: int = 0


# ─── Notifications ───────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    type: str
    category: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Student Profile ─────────────────────────────────────────────

class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    section: Optional[str] = None
    semester: Optional[int] = None
    department_id: Optional[int] = None


# ─── Password Reset ──────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


# ─── Timetable ───────────────────────────────────────────────────

class TimetableSlotCreate(BaseModel):
    course_id: int
    day_of_week: int = Field(..., ge=0, le=5)  # 0=Mon ... 5=Sat
    start_time: str = Field(..., example="09:00")
    end_time: str = Field(..., example="10:00")
    room: str = Field(..., example="LH-301")
    class_type: str = Field(default="lecture")


class TimetableSlotOut(BaseModel):
    id: int
    course_id: int
    course_name: str = ""
    course_code: str = ""
    instructor_name: str = ""
    day_of_week: int
    start_time: str
    end_time: str
    room: str
    class_type: str

    class Config:
        from_attributes = True
