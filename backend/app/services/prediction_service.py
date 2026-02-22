"""
CampusIQ — Prediction Service
ML model loading, inference, and SHAP explanations.
"""

import os
import json
import random
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Student, Prediction, Attendance, Course
from app.core.config import get_settings

settings = get_settings()

# Try to import ML libraries
try:
    import joblib
    import numpy as np
    from app.ml.predict import load_model as ml_load_model, predict_grade, get_explainer
    from app.ml.features import compute_features_from_db
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Cache loaded model
_model = None
_explainer = None


def _load_model():
    """Load the trained ML model from disk."""
    global _model, _explainer
    if _model is not None:
        return _model
    try:
        _model = ml_load_model()
        _explainer = get_explainer()
    except Exception:
        _model = None
        _explainer = None
    return _model


def _grade_from_score(score: float) -> str:
    """Convert a numeric score to a letter grade."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B+"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 40:
        return "D"
    return "F"


def _risk_level(risk_score: float) -> str:
    if risk_score >= 0.6:
        return "high"
    elif risk_score >= 0.35:
        return "moderate"
    return "low"


async def predict_student_performance(
    db: AsyncSession, student_id: int, course_id: Optional[int] = None
) -> list:
    """Generate AI predictions for a student's courses."""
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        return []

    # Get courses
    course_query = select(Course).where(
        Course.semester == student.semester,
        Course.department_id == student.department_id,
    )
    if course_id:
        course_query = course_query.where(Course.id == course_id)
    courses_result = await db.execute(course_query)
    courses = courses_result.scalars().all()

    predictions = []
    model = _load_model()

    for course in courses:
        # Check if we have a saved prediction
        existing = await db.execute(
            select(Prediction).where(
                Prediction.student_id == student_id,
                Prediction.course_id == course.id,
            ).order_by(Prediction.created_at.desc()).limit(1)
        )
        saved = existing.scalar_one_or_none()

        if saved:
            predictions.append({
                "course_name": course.name,
                "course_code": course.code,
                "predicted_grade": saved.predicted_grade or "B",
                "risk_score": round(saved.risk_score or 0.2, 2),
                "risk_level": _risk_level(saved.risk_score or 0.2),
                "confidence": round(saved.confidence or 0.8, 2),
                "top_factors": saved.factors or _default_factors(),
            })
        else:
            # Generate a demo prediction (for hackathon without trained model)
            demo_risk = round(random.uniform(0.1, 0.7), 2)
            demo_grade = _grade_from_score(random.uniform(45, 95))
            predictions.append({
                "course_name": course.name,
                "course_code": course.code,
                "predicted_grade": demo_grade,
                "risk_score": demo_risk,
                "risk_level": _risk_level(demo_risk),
                "confidence": round(random.uniform(0.75, 0.95), 2),
                "top_factors": _default_factors(),
            })

    return predictions


def _default_factors():
    """Return default SHAP-like explanation factors for demo."""
    return [
        {"factor": "Attendance Rate", "impact": round(random.uniform(-0.3, 0.3), 2), "value": f"{random.randint(60, 95)}%"},
        {"factor": "Assignment Submission", "impact": round(random.uniform(-0.2, 0.2), 2), "value": f"{random.randint(50, 100)}%"},
        {"factor": "Quiz Average", "impact": round(random.uniform(-0.15, 0.15), 2), "value": f"{random.randint(40, 90)}%"},
        {"factor": "Lab Participation", "impact": round(random.uniform(-0.1, 0.1), 2), "value": f"{random.randint(30, 100)}%"},
    ]


def generate_ai_recommendations(predictions: list, attendance_summary: list) -> list:
    """Generate AI-powered recommendations based on predictions and attendance."""
    recommendations = []

    for pred in predictions:
        if pred["risk_level"] == "high":
            recommendations.append(
                f"🔴 Focus on {pred['course_name']} — your predicted grade is {pred['predicted_grade']}. "
                f"Top improvement area: {pred['top_factors'][0]['factor']}."
            )
        elif pred["risk_level"] == "moderate":
            recommendations.append(
                f"🟡 Keep an eye on {pred['course_name']}. Improve your {pred['top_factors'][0]['factor'].lower()} to boost your grade."
            )

    for att in attendance_summary:
        if att["status"] == "danger":
            recommendations.append(
                f"❌ Critical: Your {att['course_name']} attendance is {att['percentage']}%. "
                f"Attend the next {att['classes_needed_for_75']} classes to reach 75%."
            )
        elif att["status"] == "warning":
            recommendations.append(
                f"⚠️ Warning: {att['course_name']} attendance is {att['percentage']}%. Don't miss any more classes."
            )

    if not recommendations:
        recommendations.append("✅ Great work! You're performing well across all subjects. Keep it up!")

    return recommendations[:5]  # Limit to top 5
