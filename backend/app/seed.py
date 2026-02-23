"""
CampusIQ — Database Seed Script
Populates the database with realistic demo data for hackathon demos.

Usage:
    cd backend
    python -m app.seed
"""

import asyncio
import random
from datetime import date, timedelta, datetime
from sqlalchemy import select
from app.core.database import engine, AsyncSessionLocal, Base
from app.core.security import hash_password
from app.models.models import (
    User, UserRole, Student, Faculty, Department, Course, Attendance, Prediction,
)

# ─── Configuration ────────────────────────────────────────────────

DEPARTMENTS = [
    {"name": "Computer Science & Engineering", "code": "CSE"},
    {"name": "Electronics & Communication", "code": "ECE"},
    {"name": "Mechanical Engineering", "code": "MECH"},
]

COURSES_BY_DEPT = {
    "CSE": [
        {"code": "CS301", "name": "Data Structures & Algorithms", "semester": 3, "credits": 4},
        {"code": "CS302", "name": "Database Management Systems", "semester": 3, "credits": 4},
        {"code": "CS303", "name": "Computer Networks", "semester": 3, "credits": 3},
        {"code": "CS304", "name": "Operating Systems", "semester": 3, "credits": 4},
        {"code": "CS305", "name": "Software Engineering", "semester": 3, "credits": 3},
        {"code": "CS501", "name": "Machine Learning", "semester": 5, "credits": 4},
        {"code": "CS502", "name": "Cloud Computing", "semester": 5, "credits": 3},
    ],
    "ECE": [
        {"code": "EC301", "name": "Signals & Systems", "semester": 3, "credits": 4},
        {"code": "EC302", "name": "Digital Electronics", "semester": 3, "credits": 4},
        {"code": "EC303", "name": "Electromagnetic Theory", "semester": 3, "credits": 3},
    ],
    "MECH": [
        {"code": "ME301", "name": "Thermodynamics", "semester": 3, "credits": 4},
        {"code": "ME302", "name": "Fluid Mechanics", "semester": 3, "credits": 4},
        {"code": "ME303", "name": "Manufacturing Processes", "semester": 3, "credits": 3},
    ],
}

STUDENT_NAMES = [
    "Rahul Sharma", "Priya Patel", "Amit Kumar", "Sneha Gupta", "Vikram Singh",
    "Ananya Reddy", "Arjun Nair", "Divya Joshi", "Karthik Rajan", "Meera Iyer",
    "Rohit Verma", "Neha Kapoor", "Suresh Pillai", "Pooja Mehta", "Aditya Bhat",
    "Kavya Menon", "Sanjay Rao", "Ritika Sinha", "Manish Tiwari", "Deepa Nair",
    "Akash Mishra", "Swati Desai", "Rajesh Kulkarni", "Tarini Chandra", "Varun Hegde",
    "Ishaan Malhotra", "Riya Aggarwal", "Nikhil Saxena", "Bhavna Chauhan", "Gaurav Pandey",
    "Simran Kaur", "Pranav Jain", "Anjali Dubey", "Tushar Goel", "Sakshi Bansal",
    "Harish Venkat", "Pallavi Sharma", "Mayank Arora", "Tanvi Bhatt", "Vivek Choudhary",
]

FACULTY_NAMES = [
    "Dr. Sunita Krishnan", "Prof. Ramesh Iyer", "Dr. Lakshmi Narayanan",
    "Prof. Vikram Deshmukh", "Dr. Anand Murthy", "Prof. Geeta Radhakrishnan",
    "Dr. Suresh Babu", "Prof. Meena Sundaram", "Dr. Rajiv Menon",
]


GRADE_MAP = {"A+": 10, "A": 9, "B+": 8, "B": 7, "C": 6, "D": 5, "F": 2}


async def seed():
    """Main seed function."""
    print("🌱 CampusIQ Seed Script")
    print("=" * 50)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

    async with AsyncSessionLocal() as db:
        # ── Departments ──
        departments = {}
        for d in DEPARTMENTS:
            dept = Department(name=d["name"], code=d["code"])
            db.add(dept)
            await db.flush()
            departments[d["code"]] = dept
        print(f"✅ Created {len(departments)} departments")

        # ── Admin User ──
        admin_user = User(
            email="admin@campusiq.edu",
            hashed_password=hash_password("admin123"[:72]),
            full_name="Campus Administrator",
            role=UserRole.ADMIN,
        )
        db.add(admin_user)
        await db.flush()
        print("✅ Created admin user (admin@campusiq.edu / admin123)")

        # ── Faculty ──
        faculty_list = []
        for i, fname in enumerate(FACULTY_NAMES):
            dept_code = list(departments.keys())[i % len(departments)]
            user = User(
                email=f"faculty{i+1}@campusiq.edu",
                hashed_password=hash_password("faculty123"[:72]),
                full_name=fname,
                role=UserRole.FACULTY,
            )
            db.add(user)
            await db.flush()

            fac = Faculty(
                user_id=user.id,
                employee_id=f"FAC{1000+i}",
                department_id=departments[dept_code].id,
                designation=["Professor", "Associate Professor", "Assistant Professor"][i % 3],
            )
            db.add(fac)
            await db.flush()
            faculty_list.append((fac, dept_code))
        print(f"✅ Created {len(faculty_list)} faculty members")

        # ── Courses (assign faculty) ──
        courses = {}
        fac_idx = 0
        for dept_code, course_list in COURSES_BY_DEPT.items():
            for c in course_list:
                # Find a faculty from this department
                dept_faculty = [f for f, dc in faculty_list if dc == dept_code]
                instructor = dept_faculty[fac_idx % len(dept_faculty)] if dept_faculty else faculty_list[0][0]
                fac_idx += 1

                course = Course(
                    code=c["code"],
                    name=c["name"],
                    department_id=departments[dept_code].id,
                    semester=c["semester"],
                    credits=c["credits"],
                    instructor_id=instructor.id,
                )
                db.add(course)
                await db.flush()
                courses[c["code"]] = course
        print(f"✅ Created {len(courses)} courses")

        # ── Students ──
        students = []
        for i, sname in enumerate(STUDENT_NAMES):
            dept_code = list(departments.keys())[i % len(departments)]
            user = User(
                email=f"student{i+1}@campusiq.edu",
                hashed_password=hash_password("student123"[:72]),
                full_name=sname,
                role=UserRole.STUDENT,
            )
            db.add(user)
            await db.flush()

            cgpa = round(random.uniform(5.0, 9.8), 2)
            student = Student(
                user_id=user.id,
                roll_number=f"{dept_code}{2023}{i+1:03d}",
                department_id=departments[dept_code].id,
                semester=3,
                section=["A", "B"][i % 2],
                cgpa=cgpa,
                admission_year=2023,
            )
            db.add(student)
            await db.flush()
            students.append((student, dept_code))
        print(f"✅ Created {len(students)} students")

        # ── Attendance Records (last 60 days) ──
        attendance_count = 0
        today = date.today()
        for student, dept_code in students:
            dept_courses = [c for code, c in courses.items() if code.startswith(dept_code[:2])]
            for course in dept_courses:
                # Generate ~45 class days in last 60 days
                for day_offset in range(60):
                    class_date = today - timedelta(days=day_offset)
                    if class_date.weekday() >= 5:  # Skip weekends
                        continue
                    if random.random() > 0.75:  # ~75% of weekdays have this class
                        continue

                    # Student-specific attendance probability
                    base_prob = 0.5 + (student.cgpa / 20)  # Higher CGPA = higher attendance
                    is_present = random.random() < base_prob

                    att = Attendance(
                        student_id=student.id,
                        course_id=course.id,
                        date=class_date,
                        is_present=is_present,
                        method=random.choice(["qr", "manual", "biometric"]),
                    )
                    db.add(att)
                    attendance_count += 1

        await db.flush()
        print(f"✅ Created {attendance_count} attendance records")

        # ── Predictions ──
        prediction_count = 0
        for student, dept_code in students:
            dept_courses = [c for code, c in courses.items() if code.startswith(dept_code[:2])]
            for course in dept_courses:
                risk = round(random.uniform(0.05, 0.85), 2)
                grade_score = max(30, min(100, 100 - (risk * 60) + random.uniform(-10, 10)))
                grades = ["A+", "A", "B+", "B", "C", "D", "F"]
                grade_idx = max(0, min(6, int((100 - grade_score) / 15)))
                predicted_grade = grades[grade_idx]

                pred = Prediction(
                    student_id=student.id,
                    course_id=course.id,
                    predicted_grade=predicted_grade,
                    risk_score=risk,
                    confidence=round(random.uniform(0.72, 0.96), 2),
                    factors=[
                        {"factor": "Attendance Rate", "impact": round(random.uniform(-0.3, 0.3), 2), "value": f"{random.randint(55, 98)}%"},
                        {"factor": "Assignment Submission", "impact": round(random.uniform(-0.25, 0.25), 2), "value": f"{random.randint(40, 100)}%"},
                        {"factor": "Quiz Average", "impact": round(random.uniform(-0.2, 0.2), 2), "value": f"{random.randint(35, 95)}%"},
                        {"factor": "Lab Participation", "impact": round(random.uniform(-0.15, 0.15), 2), "value": f"{random.randint(30, 100)}%"},
                    ],
                )
                db.add(pred)
                prediction_count += 1

        await db.commit()
        print(f"✅ Created {prediction_count} predictions")

    print("\n" + "=" * 50)
    print("🎉 Seed complete! Demo credentials:")
    print("   Admin:   admin@campusiq.edu / admin123")
    print("   Faculty: faculty1@campusiq.edu / faculty123")
    print("   Student: student1@campusiq.edu / student123")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
