"""
CampusIQ — Admin Routes
Campus-wide KPIs, department analytics, and alert center.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.dependencies import require_role
from app.models.models import User, UserRole, Student, Faculty, Department, Course, Attendance, Prediction

router = APIRouter()


@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get the full admin dashboard with campus-wide KPIs."""
    # Count totals
    students_count = (await db.execute(select(func.count(Student.id)))).scalar() or 0
    faculty_count = (await db.execute(select(func.count(Faculty.id)))).scalar() or 0
    dept_count = (await db.execute(select(func.count(Department.id)))).scalar() or 0

    # Get department KPIs
    departments = (await db.execute(select(Department))).scalars().all()
    dept_kpis = []

    for dept in departments:
        dept_students = (await db.execute(
            select(func.count(Student.id)).where(Student.department_id == dept.id)
        )).scalar() or 0

        dept_faculty = (await db.execute(
            select(func.count(Faculty.id)).where(Faculty.department_id == dept.id)
        )).scalar() or 0

        # Average CGPA
        avg_cgpa = (await db.execute(
            select(func.avg(Student.cgpa)).where(Student.department_id == dept.id)
        )).scalar() or 0

        dept_kpis.append({
            "department_id": dept.id,
            "department_name": dept.name,
            "department_code": dept.code,
            "total_students": dept_students,
            "total_faculty": dept_faculty,
            "avg_attendance": round(float(75 + (dept.id * 3) % 20), 1),  # Demo data
            "high_risk_pct": round(float(5 + (dept.id * 7) % 25), 1),  # Demo data
            "avg_cgpa": round(float(avg_cgpa), 2),
        })

    # Generate alerts
    alerts = _generate_demo_alerts(dept_kpis)

    campus_avg_att = (
        sum(d["avg_attendance"] for d in dept_kpis) / len(dept_kpis)
        if dept_kpis else 0
    )
    campus_risk = (
        sum(d["high_risk_pct"] for d in dept_kpis) / len(dept_kpis)
        if dept_kpis else 0
    )

    return {
        "total_students": students_count,
        "total_faculty": faculty_count,
        "total_departments": dept_count,
        "campus_avg_attendance": round(campus_avg_att, 1),
        "campus_high_risk_pct": round(campus_risk, 1),
        "department_kpis": dept_kpis,
        "recent_alerts": alerts,
    }


def _generate_demo_alerts(dept_kpis: list) -> list:
    """Generate AI-style alerts from department KPIs."""
    alerts = []
    alert_id = 1

    for dept in dept_kpis:
        if dept["high_risk_pct"] > 20:
            alerts.append({
                "id": alert_id,
                "alert_type": "high_risk",
                "severity": "critical",
                "message": f"{dept['department_name']} has {dept['high_risk_pct']}% high-risk students. Immediate intervention recommended.",
                "department": dept["department_name"],
                "student_name": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            alert_id += 1

        if dept["avg_attendance"] < 78:
            alerts.append({
                "id": alert_id,
                "alert_type": "low_attendance",
                "severity": "warning",
                "message": f"{dept['department_name']} average attendance is {dept['avg_attendance']}% — below campus target of 80%.",
                "department": dept["department_name"],
                "student_name": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            alert_id += 1

    if not alerts:
        alerts.append({
            "id": 1,
            "alert_type": "info",
            "severity": "info",
            "message": "All departments are performing within expected parameters. No critical alerts.",
            "department": None,
            "student_name": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    return alerts
