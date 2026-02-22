"""
CampusIQ — Synthetic Data Generator
Generates realistic campus data for ML model training.

Usage:
    cd backend
    python -m app.ml.seed_data
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import date, timedelta

# ── Configuration ─────────────────────────────────────────────

NUM_STUDENTS = 500
NUM_COURSES = 20
NUM_DEPARTMENTS = 3
SEMESTER_DAYS = 90
SEED = 42

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")

DEPARTMENTS = ["CSE", "ECE", "MECH"]

COURSE_POOL = {
    "CSE": [
        ("CS301", "Data Structures", 4), ("CS302", "DBMS", 4),
        ("CS303", "Networks", 3), ("CS304", "OS", 4),
        ("CS305", "Software Eng.", 3), ("CS501", "Machine Learning", 4),
        ("CS502", "Cloud Computing", 3),
    ],
    "ECE": [
        ("EC301", "Signals & Systems", 4), ("EC302", "Digital Electronics", 4),
        ("EC303", "EM Theory", 3), ("EC304", "VLSI Design", 4),
        ("EC305", "Comm. Systems", 3), ("EC501", "Embedded Systems", 4),
    ],
    "MECH": [
        ("ME301", "Thermodynamics", 4), ("ME302", "Fluid Mechanics", 4),
        ("ME303", "Manufacturing", 3), ("ME304", "Mech. of Materials", 4),
        ("ME305", "Machine Design", 3), ("ME501", "Robotics", 4),
    ],
}


def generate_students(rng: np.random.Generator) -> pd.DataFrame:
    """Generate a student dataset with realistic distributions."""
    students = []
    for i in range(NUM_STUDENTS):
        dept = DEPARTMENTS[i % NUM_DEPARTMENTS]
        semester = rng.choice([3, 5, 7], p=[0.4, 0.35, 0.25])

        # Baseline academic profile — correlated features
        ability = rng.beta(3, 2)  # 0 to 1, skewed toward higher ability
        cgpa = round(4.0 + ability * 6.0 + rng.normal(0, 0.3), 2)
        cgpa = max(3.0, min(10.0, cgpa))

        # Study hours per week
        study_hours = max(2, int(5 + ability * 20 + rng.normal(0, 3)))

        # Motivation factor (affects attendance and submissions)
        motivation = rng.beta(2.5 + ability * 3, 2)

        students.append({
            "student_id": i + 1,
            "department": dept,
            "semester": semester,
            "cgpa": cgpa,
            "ability": round(ability, 3),
            "motivation": round(motivation, 3),
            "study_hours_per_week": study_hours,
            "has_scholarship": rng.random() < (0.2 + ability * 0.3),
            "extracurricular_hours": max(0, int(rng.normal(5, 3))),
            "commute_time_mins": max(5, int(rng.normal(30, 15))),
        })

    return pd.DataFrame(students)


def generate_enrollments_and_records(
    students_df: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    """Generate per-student per-course records (attendance, assignments, quizzes, final grade)."""
    records = []

    for _, student in students_df.iterrows():
        dept = student["department"]
        courses = COURSE_POOL[dept]

        for course_code, course_name, credits in courses:
            ability = student["ability"]
            motivation = student["motivation"]

            # ── Attendance ──
            # Base probability: higher ability + motivation = higher attendance
            att_prob = 0.3 + 0.4 * motivation + 0.15 * ability + rng.normal(0, 0.05)
            att_prob = max(0.1, min(0.98, att_prob))

            total_classes = rng.integers(35, 50)
            classes_attended = int(total_classes * att_prob)
            attendance_pct = round(100.0 * classes_attended / total_classes, 1)

            # ── Assignments ──
            total_assignments = rng.integers(5, 10)
            submitted = int(total_assignments * (0.4 + 0.5 * motivation + rng.normal(0, 0.08)))
            submitted = max(0, min(total_assignments, submitted))
            assignment_avg = round(max(0, min(100, 40 + ability * 50 + rng.normal(0, 8))), 1)
            assignment_submission_rate = round(100.0 * submitted / total_assignments, 1)

            # ── Quizzes ──
            num_quizzes = rng.integers(3, 8)
            quiz_avg = round(max(0, min(100, 30 + ability * 55 + rng.normal(0, 10))), 1)

            # ── Lab ──
            lab_sessions = rng.integers(8, 15)
            lab_attended = int(lab_sessions * (0.5 + 0.4 * motivation + rng.normal(0, 0.06)))
            lab_attended = max(0, min(lab_sessions, lab_attended))
            lab_pct = round(100.0 * lab_attended / lab_sessions, 1)

            # ── Mid-term Score ──
            midterm = round(max(0, min(100, 25 + ability * 60 + rng.normal(0, 10))), 1)

            # ── Final Grade (target variable) ──
            # Weighted combination: realistic formula
            raw_score = (
                0.25 * attendance_pct +
                0.15 * assignment_avg * (assignment_submission_rate / 100) +
                0.15 * quiz_avg +
                0.10 * lab_pct +
                0.20 * midterm +
                0.15 * student["cgpa"] * 10  # Normalize CGPA (0-10 scale) to ~0-100
            )
            raw_score += rng.normal(0, 3)  # Noise
            raw_score = max(0, min(100, raw_score))

            # Letter grade
            if raw_score >= 90:
                grade = "A+"
            elif raw_score >= 80:
                grade = "A"
            elif raw_score >= 70:
                grade = "B+"
            elif raw_score >= 60:
                grade = "B"
            elif raw_score >= 50:
                grade = "C"
            elif raw_score >= 40:
                grade = "D"
            else:
                grade = "F"

            # Grade points
            gp_map = {"A+": 10, "A": 9, "B+": 8, "B": 7, "C": 6, "D": 5, "F": 2}

            records.append({
                "student_id": student["student_id"],
                "department": dept,
                "semester": student["semester"],
                "cgpa": student["cgpa"],
                "study_hours_per_week": student["study_hours_per_week"],
                "has_scholarship": student["has_scholarship"],
                "extracurricular_hours": student["extracurricular_hours"],
                "commute_time_mins": student["commute_time_mins"],
                "course_code": course_code,
                "course_name": course_name,
                "credits": credits,
                "total_classes": total_classes,
                "classes_attended": classes_attended,
                "attendance_pct": attendance_pct,
                "total_assignments": total_assignments,
                "assignments_submitted": submitted,
                "assignment_submission_rate": assignment_submission_rate,
                "assignment_avg_score": assignment_avg,
                "num_quizzes": num_quizzes,
                "quiz_avg": quiz_avg,
                "lab_sessions": lab_sessions,
                "lab_attended": lab_attended,
                "lab_pct": lab_pct,
                "midterm_score": midterm,
                "raw_score": round(raw_score, 2),
                "grade": grade,
                "grade_points": gp_map[grade],
            })

    return pd.DataFrame(records)


def main():
    """Generate and save synthetic data."""
    print("🔬 CampusIQ Synthetic Data Generator")
    print("=" * 50)

    rng = np.random.default_rng(SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate students
    students_df = generate_students(rng)
    students_path = os.path.join(OUTPUT_DIR, "students.csv")
    students_df.to_csv(students_path, index=False)
    print(f"✅ Generated {len(students_df)} students → {students_path}")

    # Generate enrollment records
    records_df = generate_enrollments_and_records(students_df, rng)
    records_path = os.path.join(OUTPUT_DIR, "training_data.csv")
    records_df.to_csv(records_path, index=False)
    print(f"✅ Generated {len(records_df)} course records → {records_path}")

    # Stats
    print(f"\n📊 Dataset Stats:")
    print(f"   Students:    {len(students_df)}")
    print(f"   Records:     {len(records_df)}")
    print(f"   Departments: {records_df['department'].nunique()}")
    print(f"   Courses:     {records_df['course_code'].nunique()}")
    print(f"\n   Grade Distribution:")
    print(records_df["grade"].value_counts().sort_index().to_string())
    print(f"\n   Avg Attendance: {records_df['attendance_pct'].mean():.1f}%")
    print(f"   Avg Quiz Score: {records_df['quiz_avg'].mean():.1f}")
    print("=" * 50)


if __name__ == "__main__":
    main()
