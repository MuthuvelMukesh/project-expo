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


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"))
    predicted_grade = Column(String(5))
    risk_score = Column(Float)  # 0.0 to 1.0
    confidence = Column(Float)
    factors = Column(JSON)  # SHAP explanation as JSON
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
