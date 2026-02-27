"""
CampusIQ SQLAlchemy ORM Models
Defines the core database schema for the ERP system.
"""

import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, Enum, Text, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = relationship("Student", back_populates="user", uselist=False)
    faculty_profile = relationship("Faculty", back_populates="user", uselist=False)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)

    courses = relationship("Course", back_populates="department")
    students = relationship("Student", back_populates="department")
    faculty = relationship("Faculty", back_populates="department")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    roll_number = Column(String(20), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String(5))
    cgpa = Column(Float, default=0.0)
    admission_year = Column(Integer)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    department = relationship("Department", back_populates="students")
    attendances = relationship("Attendance", back_populates="student")
    predictions = relationship("Prediction", back_populates="student")


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(20), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    designation = Column(String(100))

    # Relationships
    user = relationship("User", back_populates="faculty_profile")
    department = relationship("Department", back_populates="faculty")
    courses = relationship("Course", back_populates="instructor")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    credits = Column(Integer, default=3)
    instructor_id = Column(Integer, ForeignKey("faculty.id"))

    # Relationships
    department = relationship("Department", back_populates="courses")
    instructor = relationship("Faculty", back_populates="courses")
    attendances = relationship("Attendance", back_populates="course")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    date = Column(Date, nullable=False)
    is_present = Column(Boolean, default=False)
    marked_at = Column(DateTime, default=datetime.utcnow)
    method = Column(String(20), default="manual")  # manual, qr, biometric

    # Relationships
    student = relationship("Student", back_populates="attendances")
    course = relationship("Course", back_populates="attendances")


# =============================================================
# ML FEATURE TABLES — Planned for v2
# The following tables are needed for full ML feature coverage:
# - AssignmentSubmission: assignment_id, student_id, submitted_at, score
# - QuizScore: quiz_id, student_id, course_id, marks_obtained, max_marks
# - LabRecord: student_id, course_id, participation_score, max_score
# - ClassParticipationLog: student_id, course_id, date, score
# Currently, predictions use training means for these features.
# =============================================================


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"))
    predicted_grade = Column(String(5))
    risk_score = Column(Float)  # 0.0 to 1.0
    confidence = Column(Float)
    factors = Column(JSON)  # SHAP explanation as JSON
    is_estimated = Column(Boolean, default=False)  # True if using training means for missing data
    data_completeness = Column(Float, default=1.0)  # Fraction of features with real data (0.0-1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="predictions")


class ActionLog(Base):
    """Audit trail for AI Copilot actions."""
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(String(50), nullable=False, index=True)
    action_id = Column(String(80), nullable=True, index=True)  # e.g. plan_xxx_act_0
    action_type = Column(String(20), nullable=False)  # READ, CREATE, UPDATE, DELETE, ANALYZE, NAVIGATE
    entity = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    risk_level = Column(String(10), default="safe")  # safe, low, high
    status = Column(String(20), default="pending")  # pending, approved, executed, rejected, failed
    payload = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")


class Notification(Base):
    """User notifications and alerts."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(30), default="info")  # info, warning, critical, success
    category = Column(String(30), default="system")  # attendance, prediction, copilot, system
    is_read = Column(Boolean, default=False)
    link = Column(String(255), nullable=True)  # optional navigation link
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")


class Timetable(Base):
    """Weekly timetable schedule entries."""
    __tablename__ = "timetable"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 5=Saturday
    start_time = Column(String(5), nullable=False)  # "09:00"
    end_time = Column(String(5), nullable=False)    # "10:00"
    room = Column(String(50), nullable=False)
    class_type = Column(String(20), default="lecture")  # lecture, lab, tutorial

    # Relationships
    course = relationship("Course")


# ─────── FINANCIAL MANAGEMENT MODULE ─────────────────────────────


class FeeStructure(Base):
    """Fee structure definitions."""
    __tablename__ = "fee_structures"

    id = Column(Integer, primary_key=True, index=True)
    semester = Column(Integer, nullable=False)
    fee_type = Column(String(50), nullable=False)  # tuition, hostel, lab, etc
    amount = Column(Float, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StudentFees(Base):
    """Student-specific fee records."""
    __tablename__ = "student_fees"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    fee_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    semester = Column(Integer, nullable=False)
    academic_year = Column(String(10), nullable=False)
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student")


class Invoice(Base):
    """Student invoices."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    amount_due = Column(Float, nullable=False)
    issued_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(20), default="issued")  # draft, issued, paid, overdue, cancelled
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student")
    payments = relationship("Payment", back_populates="invoice")


class Payment(Base):
    """Payment records."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50), nullable=False)  # cash, card, bank_transfer
    reference_number = Column(String(100), unique=True, nullable=True)
    status = Column(String(20), default="pending")  # pending, verified, reconciled, failed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    student = relationship("Student")


class StudentLedger(Base):
    """Student financial ledger / account balance tracking."""
    __tablename__ = "student_ledger"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # debit, credit
    amount = Column(Float, nullable=False)
    balance = Column(Float, nullable=False)  # running balance
    description = Column(String(255), nullable=True)
    reference_id = Column(Integer, nullable=True)  # invoice or payment ID
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student")


class FeeWaiver(Base):
    """Fee waivers, scholarships, and discounts."""
    __tablename__ = "fee_waivers"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    waiver_type = Column(String(50), nullable=False)  # scholarship, discount, exemption
    amount = Column(Float, nullable=False)
    percentage = Column(Float, nullable=True)  # if percentage-based
    reason = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # admin
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=True)
    status = Column(String(20), default="active")  # active, expired, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student")
    approved_user = relationship("User")


# ─────── HR & PAYROLL MODULE ────────────────────────────────────


class Employee(Base):
    """Extended employee information for HR module."""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_type = Column(String(50), nullable=False)  # faculty, staff, admin
    date_of_joining = Column(Date, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    bank_account = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    salary_records = relationship("SalaryRecord", back_populates="employee")


class SalaryStructure(Base):
    """Salary structure definitions."""
    __tablename__ = "salary_structures"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    designation = Column(String(100), nullable=False)
    base_salary = Column(Float, nullable=False)
    da = Column(Float, default=0)  # Dearness Allowance
    hra = Column(Float, default=0)  # House Rent Allowance
    other_allowances = Column(Float, default=0)
    pf_contribution = Column(Float, default=0)  # Provident Fund
    insurance = Column(Float, default=0)
    tax_rate = Column(Float, default=0)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    employee = relationship("Employee")


class SalaryRecord(Base):
    """Salary payment records."""
    __tablename__ = "salary_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    gross_salary = Column(Float, nullable=False)
    deductions = Column(Float, nullable=False)
    net_salary = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    status = Column(String(20), default="pending")  # pending, processed, paid, failed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    employee = relationship("Employee", back_populates="salary_records")


class EmployeeAttendance(Base):
    """Extended employee attendance."""
    __tablename__ = "employee_attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(String(5), nullable=True)  # "09:30"
    check_out = Column(String(5), nullable=True)  # "17:30"
    hours_worked = Column(Float, nullable=True)
    status = Column(String(20), default="present")  # present, absent, halfday, leave
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    employee = relationship("Employee")


class LeaveType(Base):
    """Leave type definitions (Casual, Sick, Earned, etc.)."""
    __tablename__ = "leave_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)          # Casual Leave, Sick Leave, etc.
    code = Column(String(10), unique=True, nullable=False)          # CL, SL, EL, etc.
    max_days_per_year = Column(Integer, nullable=False, default=12)
    is_carry_forward = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LeaveBalance(Base):
    """Tracks per-employee, per-year leave balances."""
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    year = Column(Integer, nullable=False)
    total_days = Column(Integer, nullable=False)
    used_days = Column(Integer, default=0)
    remaining_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    employee = relationship("Employee")
    leave_type = relationship("LeaveType")


class LeaveRequest(Base):
    """Employee leave applications with approval workflow."""
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    num_days = Column(Float, nullable=False)                        # supports half-day (0.5)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="pending")                  # pending, approved, rejected, cancelled
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    employee = relationship("Employee")
    leave_type = relationship("LeaveType")
    reviewer = relationship("User")


# ─────── CONVERSATIONAL OPERATIONAL AI LAYER ───────────────────


class OperationalPlan(Base):
    """Stored operational plan generated from conversational intent."""
    __tablename__ = "operational_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(String(80), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    module = Column(String(30), nullable=False, default="nlp")
    message = Column(Text, nullable=False)

    intent_type = Column(String(20), nullable=False)  # READ, CREATE, UPDATE, DELETE, ANALYZE
    entity = Column(String(50), nullable=False)
    filters = Column(JSON, default=dict)
    scope = Column(JSON, default=dict)
    affected_fields = Column(JSON, default=list)
    values = Column(JSON, default=dict)

    confidence = Column(Float, default=0.0)
    ambiguity = Column(JSON, default=dict)
    risk_level = Column(String(10), default="LOW")  # LOW, MEDIUM, HIGH
    estimated_impact_count = Column(Integer, default=0)

    status = Column(String(30), default="draft")
    requires_confirmation = Column(Boolean, default=False)
    requires_senior_approval = Column(Boolean, default=False)
    requires_2fa = Column(Boolean, default=False)
    escalation_required = Column(Boolean, default=False)

    preview = Column(JSON, default=dict)
    rollback_plan = Column(JSON, default=dict)
    error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class OperationalApprovalDecision(Base):
    """Approval, rejection, or escalation decisions for a plan."""
    __tablename__ = "operational_approval_decisions"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(String(80), ForeignKey("operational_plans.plan_id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reviewer_role = Column(String(20), nullable=False)
    decision = Column(String(20), nullable=False)  # APPROVE, REJECT, ESCALATE
    approved_scope = Column(JSON, default=dict)
    rejected_scope = Column(JSON, default=dict)
    comment = Column(Text, nullable=True)
    two_factor_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    reviewer = relationship("User")


class OperationalExecution(Base):
    """Execution records with before/after snapshots for rollback."""
    __tablename__ = "operational_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(80), unique=True, nullable=False, index=True)
    plan_id = Column(String(80), ForeignKey("operational_plans.plan_id"), nullable=False, index=True)
    executed_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending, executed, failed, rolled_back

    before_state = Column(JSON, default=list)
    after_state = Column(JSON, default=list)
    failure_state = Column(JSON, default=dict)
    rollback_state = Column(JSON, default=dict)

    executed_at = Column(DateTime, nullable=True)
    rolled_back_at = Column(DateTime, nullable=True)

    executor = relationship("User")


class ImmutableAuditLog(Base):
    """Immutable audit event stream for conversational operations."""
    __tablename__ = "immutable_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(80), unique=True, nullable=False, index=True)
    plan_id = Column(String(80), nullable=True, index=True)
    execution_id = Column(String(80), nullable=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    module = Column(String(30), nullable=False)
    operation_type = Column(String(30), nullable=False)
    event_type = Column(String(30), nullable=False)  # intent_extracted, clarification_required, approved, executed, rollback, failed
    risk_level = Column(String(10), nullable=False)

    intent_payload = Column(JSON, default=dict)
    before_state = Column(JSON, default=list)
    after_state = Column(JSON, default=list)
    event_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")
