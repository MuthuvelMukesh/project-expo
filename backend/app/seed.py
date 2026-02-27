"""
CampusIQ — Database Seed Script
Populates the database with realistic demo data for all modules.

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
    Timetable, Employee, SalaryStructure, SalaryRecord, EmployeeAttendance,
    LeaveType, LeaveBalance, LeaveRequest,
    FeeStructure, StudentFees, Invoice, Payment, StudentLedger,
    Notification,
)

# ─── Configuration ────────────────────────────────────────────────

DEPARTMENTS = [
    {"name": "Computer Science & Engineering", "code": "CSE"},
    {"name": "Electronics & Communication", "code": "ECE"},
    {"name": "Mechanical Engineering", "code": "MECH"},
]

COURSES_BY_DEPT = {
    "CSE": [
        {"code": "CS101", "name": "Introduction to Programming", "semester": 1, "credits": 4},
        {"code": "CS102", "name": "Discrete Mathematics", "semester": 1, "credits": 3},
        {"code": "CS103", "name": "Digital Logic Design", "semester": 1, "credits": 3},
        {"code": "CS201", "name": "Object-Oriented Programming", "semester": 2, "credits": 4},
        {"code": "CS202", "name": "Linear Algebra", "semester": 2, "credits": 3},
        {"code": "CS301", "name": "Data Structures & Algorithms", "semester": 3, "credits": 4},
        {"code": "CS302", "name": "Database Management Systems", "semester": 3, "credits": 4},
        {"code": "CS303", "name": "Computer Networks", "semester": 3, "credits": 3},
        {"code": "CS304", "name": "Operating Systems", "semester": 3, "credits": 4},
        {"code": "CS305", "name": "Software Engineering", "semester": 3, "credits": 3},
        {"code": "CS401", "name": "Compiler Design", "semester": 4, "credits": 4},
        {"code": "CS402", "name": "Theory of Computation", "semester": 4, "credits": 3},
        {"code": "CS501", "name": "Machine Learning", "semester": 5, "credits": 4},
        {"code": "CS502", "name": "Cloud Computing", "semester": 5, "credits": 3},
        {"code": "CS601", "name": "Deep Learning", "semester": 6, "credits": 4},
        {"code": "CS701", "name": "Capstone Project", "semester": 7, "credits": 6},
    ],
    "ECE": [
        {"code": "EC101", "name": "Basic Electronics", "semester": 1, "credits": 4},
        {"code": "EC102", "name": "Engineering Physics", "semester": 1, "credits": 3},
        {"code": "EC201", "name": "Analog Circuits", "semester": 2, "credits": 4},
        {"code": "EC301", "name": "Signals & Systems", "semester": 3, "credits": 4},
        {"code": "EC302", "name": "Digital Electronics", "semester": 3, "credits": 4},
        {"code": "EC303", "name": "Electromagnetic Theory", "semester": 3, "credits": 3},
        {"code": "EC401", "name": "Microprocessors", "semester": 4, "credits": 4},
        {"code": "EC501", "name": "VLSI Design", "semester": 5, "credits": 4},
        {"code": "EC601", "name": "Embedded Systems", "semester": 6, "credits": 4},
        {"code": "EC701", "name": "Industry Project", "semester": 7, "credits": 6},
    ],
    "MECH": [
        {"code": "ME101", "name": "Engineering Mechanics", "semester": 1, "credits": 4},
        {"code": "ME102", "name": "Engineering Drawing", "semester": 1, "credits": 3},
        {"code": "ME201", "name": "Strength of Materials", "semester": 2, "credits": 4},
        {"code": "ME301", "name": "Thermodynamics", "semester": 3, "credits": 4},
        {"code": "ME302", "name": "Fluid Mechanics", "semester": 3, "credits": 4},
        {"code": "ME303", "name": "Manufacturing Processes", "semester": 3, "credits": 3},
        {"code": "ME401", "name": "Heat Transfer", "semester": 4, "credits": 4},
        {"code": "ME501", "name": "Machine Design", "semester": 5, "credits": 4},
        {"code": "ME601", "name": "Robotics & Automation", "semester": 6, "credits": 4},
        {"code": "ME701", "name": "Capstone Project", "semester": 7, "credits": 6},
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
            hashed_password=hash_password("admin123"),
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
                hashed_password=hash_password("faculty123"),
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

        # ── Students (varied semesters) ──
        students = []
        semesters = [1, 2, 3, 3, 3, 4, 5, 5, 6, 7]  # Weighted towards 3,5
        for i, sname in enumerate(STUDENT_NAMES):
            dept_code = list(departments.keys())[i % len(departments)]
            user = User(
                email=f"student{i+1}@campusiq.edu",
                hashed_password=hash_password("student123"),
                full_name=sname,
                role=UserRole.STUDENT,
            )
            db.add(user)
            await db.flush()

            sem = semesters[i % len(semesters)]
            cgpa = round(random.uniform(5.0, 9.8), 2)
            admission_year = 2025 - (sem // 2)
            student = Student(
                user_id=user.id,
                roll_number=f"{dept_code}{admission_year}{i+1:03d}",
                department_id=departments[dept_code].id,
                semester=sem,
                section=["A", "B"][i % 2],
                cgpa=cgpa,
                admission_year=admission_year,
            )
            db.add(student)
            await db.flush()
            students.append((student, dept_code))
        print(f"✅ Created {len(students)} students (semesters 1-7)")

        # ── Attendance Records (last 60 days) ──
        attendance_count = 0
        today = date.today()
        for student, dept_code in students:
            # Only courses matching the student's semester and department
            dept_courses = [c for code, c in courses.items() 
                          if code.startswith(dept_code[:2]) and c.semester == student.semester]
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
            dept_courses = [c for code, c in courses.items() 
                          if code.startswith(dept_code[:2]) and c.semester == student.semester]
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

        # ── Timetable ──
        time_slots = [
            ("09:00", "10:00"), ("10:15", "11:15"), ("11:30", "12:30"),
            ("14:00", "15:00"), ("15:15", "16:15"), ("16:30", "17:30"),
        ]
        rooms = ["LH-101", "LH-102", "LH-201", "LH-202", "LH-301", "LH-302",
                 "LAB-A", "LAB-B", "LAB-C", "TUT-1", "TUT-2"]
        class_types = ["lecture", "lecture", "lecture", "lab", "tutorial"]
        timetable_count = 0

        for code, course in courses.items():
            # Give each course 3 slots spread across the week
            used_days = random.sample(range(6), k=min(3, 6))  # 3 random days
            for day in used_days:
                slot_idx = random.randint(0, len(time_slots) - 1)
                start, end = time_slots[slot_idx]
                tt = Timetable(
                    course_id=course.id,
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    room=random.choice(rooms),
                    class_type=random.choice(class_types),
                )
                db.add(tt)
                timetable_count += 1

        await db.commit()
        print(f"✅ Created {timetable_count} timetable entries")

        # ═══════════════════════════════════════════════════
        # HR MODULE — Employees, Salary, Attendance, Leave
        # ═══════════════════════════════════════════════════

        # ── Employees (from existing faculty + admin + extra staff) ──
        employee_map = {}  # user_id -> Employee

        # Create Employee records for all faculty
        for fac, dept_code in faculty_list:
            emp = Employee(
                user_id=fac.user_id,
                employee_type="faculty",
                date_of_joining=date(2020, 6, 1) + timedelta(days=random.randint(0, 1500)),
                date_of_birth=date(1975, 1, 1) + timedelta(days=random.randint(0, 7300)),
                phone=f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}",
                address=random.choice([
                    "12, MG Road, Bengaluru", "45, Anna Salai, Chennai",
                    "78, FC Road, Pune", "23, Park Street, Kolkata",
                    "56, Banjara Hills, Hyderabad", "90, Civil Lines, Delhi",
                ]),
                city=random.choice(["Bengaluru", "Chennai", "Pune", "Hyderabad", "Delhi"]),
                state=random.choice(["Karnataka", "Tamil Nadu", "Maharashtra", "Telangana", "Delhi"]),
                bank_account=f"{random.randint(1000, 9999)}{random.randint(100000, 999999)}",
                bank_name=random.choice(["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "PNB"]),
                ifsc_code=f"{random.choice(['SBIN', 'HDFC', 'ICIC', 'UTIB', 'PUNB'])}0{random.randint(100000, 999999)}",
            )
            db.add(emp)
            await db.flush()
            employee_map[fac.user_id] = emp

        # Create Employee record for admin
        admin_emp = Employee(
            user_id=admin_user.id,
            employee_type="admin",
            date_of_joining=date(2019, 1, 15),
            date_of_birth=date(1980, 5, 20),
            phone="+91-98765-43210",
            address="1, University Campus, Bengaluru",
            city="Bengaluru",
            state="Karnataka",
            bank_account="3344556677",
            bank_name="SBI",
            ifsc_code="SBIN0001234",
        )
        db.add(admin_emp)
        await db.flush()
        employee_map[admin_user.id] = admin_emp

        # Create 4 extra non-teaching staff
        staff_names = [
            ("Rajesh Kumar", "staff"), ("Lakshmi Devi", "staff"),
            ("Mohammed Rafi", "staff"), ("Geetha Rani", "staff"),
        ]
        staff_roles = ["Office Assistant", "Lab Technician", "Library Staff", "Accounts Clerk"]
        for idx, (sname, stype) in enumerate(staff_names):
            staff_user = User(
                email=f"staff{idx+1}@campusiq.edu",
                hashed_password=hash_password("staff123"),
                full_name=sname,
                role=UserRole.FACULTY,  # Staff use faculty role for portal access
            )
            db.add(staff_user)
            await db.flush()
            staff_emp = Employee(
                user_id=staff_user.id,
                employee_type=stype,
                date_of_joining=date(2021, 1, 1) + timedelta(days=random.randint(0, 1000)),
                date_of_birth=date(1985, 1, 1) + timedelta(days=random.randint(0, 5475)),
                phone=f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}",
                address=f"{random.randint(1, 200)}, Staff Quarters, Campus",
                city="Bengaluru",
                state="Karnataka",
                bank_account=f"{random.randint(1000, 9999)}{random.randint(100000, 999999)}",
                bank_name=random.choice(["SBI", "HDFC Bank", "Canara Bank"]),
                ifsc_code=f"SBIN0{random.randint(100000, 999999)}",
            )
            db.add(staff_emp)
            await db.flush()
            employee_map[staff_user.id] = staff_emp
        await db.flush()
        print(f"✅ Created {len(employee_map)} employees (faculty + admin + staff)")

        # ── Salary Structures ──
        salary_tiers = {
            "admin": {"base": 95000, "da": 9500, "hra": 19000, "other": 5000, "pf": 11400, "ins": 1500, "tax": 0.15},
            "faculty": {"base": 75000, "da": 7500, "hra": 15000, "other": 3000, "pf": 9000, "ins": 1200, "tax": 0.10},
            "staff": {"base": 35000, "da": 3500, "hra": 7000, "other": 1500, "pf": 4200, "ins": 800, "tax": 0.05},
        }
        designations = {"admin": "Administrator", "faculty": "Professor", "staff": "Support Staff"}
        salary_structures = {}

        for uid, emp in employee_map.items():
            tier = salary_tiers.get(emp.employee_type, salary_tiers["staff"])
            # Add some variation to base salary
            variation = random.uniform(0.85, 1.20)
            ss = SalaryStructure(
                employee_id=emp.id,
                designation=designations.get(emp.employee_type, "Staff"),
                base_salary=round(tier["base"] * variation, 2),
                da=round(tier["da"] * variation, 2),
                hra=round(tier["hra"] * variation, 2),
                other_allowances=round(tier["other"] * variation, 2),
                pf_contribution=round(tier["pf"] * variation, 2),
                insurance=round(tier["ins"], 2),
                tax_rate=tier["tax"],
                effective_from=date(2025, 4, 1),
            )
            db.add(ss)
            await db.flush()
            salary_structures[emp.id] = ss

        print(f"✅ Created {len(salary_structures)} salary structures")

        # ── Salary Records (last 3 months) ──
        salary_record_count = 0
        today = date.today()
        for emp_id, ss in salary_structures.items():
            gross = ss.base_salary + ss.da + ss.hra + ss.other_allowances
            deductions = ss.pf_contribution + ss.insurance + (gross * ss.tax_rate)
            net = gross - deductions
            for months_ago in range(3):
                m = today.month - months_ago
                y = today.year
                if m <= 0:
                    m += 12
                    y -= 1
                sr = SalaryRecord(
                    employee_id=emp_id,
                    month=m,
                    year=y,
                    gross_salary=round(gross, 2),
                    deductions=round(deductions, 2),
                    net_salary=round(net, 2),
                    payment_date=date(y, m, 28) if months_ago > 0 else None,
                    status="paid" if months_ago > 0 else "processed",
                    notes=f"Salary for {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1]} {y}",
                )
                db.add(sr)
                salary_record_count += 1
        await db.flush()
        print(f"✅ Created {salary_record_count} salary records")

        # ── Employee Attendance (last 30 working days) ──
        emp_att_count = 0
        for uid, emp in employee_map.items():
            for day_offset in range(30):
                d = today - timedelta(days=day_offset)
                if d.weekday() >= 5:  # skip weekends
                    continue
                prob = random.random()
                if prob < 0.88:
                    status = "present"
                    cin = f"{random.randint(8,9):02d}:{random.randint(0,59):02d}"
                    cout = f"{random.randint(16,18)}:{random.randint(0,59):02d}"
                    hrs = random.uniform(7.5, 9.5)
                elif prob < 0.95:
                    status = "halfday"
                    cin = f"{random.randint(8,10):02d}:{random.randint(0,59):02d}"
                    cout = f"{random.randint(12,13)}:{random.randint(0,59):02d}"
                    hrs = random.uniform(3.5, 4.5)
                else:
                    status = "absent"
                    cin = None
                    cout = None
                    hrs = 0
                ea = EmployeeAttendance(
                    employee_id=emp.id,
                    date=d,
                    check_in=cin,
                    check_out=cout,
                    hours_worked=round(hrs, 1),
                    status=status,
                )
                db.add(ea)
                emp_att_count += 1
        await db.flush()
        print(f"✅ Created {emp_att_count} employee attendance records")

        # ── Leave Types ──
        leave_types_data = [
            {"name": "Casual Leave", "code": "CL", "max_days": 12, "carry": False, "desc": "For personal and casual purposes"},
            {"name": "Sick Leave", "code": "SL", "max_days": 10, "carry": True, "desc": "Medical leave with doctor certificate"},
            {"name": "Earned Leave", "code": "EL", "max_days": 15, "carry": True, "desc": "Earned/privilege leave accrued over service"},
            {"name": "Maternity Leave", "code": "ML", "max_days": 180, "carry": False, "desc": "Maternity leave as per policy"},
            {"name": "Paternity Leave", "code": "PL", "max_days": 15, "carry": False, "desc": "Paternity leave for childcare"},
            {"name": "Compensatory Off", "code": "CO", "max_days": 5, "carry": False, "desc": "Comp off for extra working days"},
        ]
        leave_type_objs = {}
        for lt in leave_types_data:
            lto = LeaveType(
                name=lt["name"], code=lt["code"],
                max_days_per_year=lt["max_days"],
                is_carry_forward=lt["carry"],
                description=lt["desc"],
                is_active=True,
            )
            db.add(lto)
            await db.flush()
            leave_type_objs[lt["code"]] = lto
        print(f"✅ Created {len(leave_type_objs)} leave types")

        # ── Leave Balances (for all employees, current year) ──
        lb_count = 0
        for uid, emp in employee_map.items():
            for code, lto in leave_type_objs.items():
                if code in ("ML", "PL"):
                    continue  # Skip maternity/paternity by default
                used = random.randint(0, min(4, lto.max_days_per_year))
                lb = LeaveBalance(
                    employee_id=emp.id,
                    leave_type_id=lto.id,
                    year=today.year,
                    total_days=lto.max_days_per_year,
                    used_days=used,
                    remaining_days=lto.max_days_per_year - used,
                )
                db.add(lb)
                lb_count += 1
        await db.flush()
        print(f"✅ Created {lb_count} leave balances")

        # ── Leave Requests (some sample requests) ──
        lr_count = 0
        emp_list = list(employee_map.values())
        leave_statuses = ["approved", "approved", "approved", "pending", "rejected"]
        for i in range(12):
            emp = random.choice(emp_list)
            lt_code = random.choice(["CL", "SL", "EL"])
            lto = leave_type_objs[lt_code]
            start = today - timedelta(days=random.randint(1, 60))
            num_days = random.randint(1, 3)
            end = start + timedelta(days=num_days - 1)
            status = random.choice(leave_statuses)
            lr = LeaveRequest(
                employee_id=emp.id,
                leave_type_id=lto.id,
                start_date=start,
                end_date=end,
                num_days=float(num_days),
                reason=random.choice([
                    "Family function", "Not feeling well", "Personal work",
                    "Medical appointment", "Out of station travel",
                    "Wedding ceremony", "Home renovation work",
                ]),
                status=status,
                reviewed_by=admin_user.id if status != "pending" else None,
                review_comment="Approved" if status == "approved" else ("Insufficient leave balance" if status == "rejected" else None),
                reviewed_at=datetime.now() if status != "pending" else None,
            )
            db.add(lr)
            lr_count += 1
        await db.flush()
        print(f"✅ Created {lr_count} leave requests")

        # ═══════════════════════════════════════════════════
        # FINANCE MODULE — Fees, Invoices, Payments
        # ═══════════════════════════════════════════════════

        # ── Fee Structures ──
        fee_types = [
            {"type": "tuition", "amount": 75000, "label": "Tuition Fee"},
            {"type": "hostel", "amount": 45000, "label": "Hostel Fee"},
            {"type": "lab", "amount": 15000, "label": "Laboratory Fee"},
            {"type": "library", "amount": 5000, "label": "Library Fee"},
            {"type": "exam", "amount": 8000, "label": "Examination Fee"},
            {"type": "sports", "amount": 3000, "label": "Sports & Activities Fee"},
        ]
        fee_structure_objs = []
        for sem in [1, 2, 3, 4, 5, 6, 7, 8]:
            for ft in fee_types:
                fs = FeeStructure(
                    semester=sem,
                    fee_type=ft["type"],
                    amount=ft["amount"],
                    valid_from=date(2025, 1, 1),
                    valid_to=date(2026, 12, 31),
                )
                db.add(fs)
                fee_structure_objs.append(fs)
        await db.flush()
        print(f"✅ Created {len(fee_structure_objs)} fee structures")

        # ── Student Fees ──
        student_fee_count = 0
        for student, dept_code in students:
            for ft in fee_types:
                is_paid = random.random() < 0.65  # 65% have paid
                due = today + timedelta(days=random.randint(-45, 30))
                sf = StudentFees(
                    student_id=student.id,
                    fee_type=ft["type"],
                    amount=ft["amount"],
                    due_date=due,
                    semester=student.semester,
                    academic_year="2025-26",
                    is_paid=is_paid,
                    paid_date=due - timedelta(days=random.randint(1, 15)) if is_paid else None,
                )
                db.add(sf)
                student_fee_count += 1
        await db.flush()
        print(f"✅ Created {student_fee_count} student fee records")

        # ── Invoices (for students with unpaid fees) ──
        invoice_count = 0
        inv_seq = 1
        invoices_created = []
        for student, dept_code in students:
            # Create 1-2 invoices per student
            num_inv = random.randint(1, 2)
            for inv_n in range(num_inv):
                status = random.choice(["issued", "issued", "paid", "overdue"])
                amt = random.choice([75000, 45000, 15000, 83000, 23000, 151000])
                issued = today - timedelta(days=random.randint(5, 60))
                due = issued + timedelta(days=30)
                inv = Invoice(
                    student_id=student.id,
                    invoice_number=f"INV-2026-{inv_seq:04d}",
                    amount_due=float(amt),
                    issued_date=issued,
                    due_date=due,
                    status=status,
                    description=f"Semester {student.semester} - {random.choice(['Tuition', 'Hostel', 'Lab + Exam', 'Full Semester'])} Fees",
                )
                db.add(inv)
                await db.flush()
                invoices_created.append((inv, student, status))
                inv_seq += 1
                invoice_count += 1
        print(f"✅ Created {invoice_count} invoices")

        # ── Payments (for paid invoices) ──
        payment_count = 0
        ledger_count = 0
        for inv, student, status in invoices_created:
            if status == "paid":
                pay = Payment(
                    invoice_id=inv.id,
                    student_id=student.id,
                    amount=inv.amount_due,
                    payment_date=inv.issued_date + timedelta(days=random.randint(1, 20)),
                    payment_method=random.choice(["bank_transfer", "card", "upi", "cash"]),
                    reference_number=f"TXN{random.randint(100000, 999999)}",
                    status="verified",
                    notes="Payment received and verified",
                )
                db.add(pay)
                payment_count += 1

                # Ledger entries
                ledger_debit = StudentLedger(
                    student_id=student.id,
                    transaction_type="debit",
                    amount=inv.amount_due,
                    balance=inv.amount_due,
                    description=f"Invoice {inv.invoice_number} - Fee Due",
                    reference_id=inv.id,
                )
                db.add(ledger_debit)
                ledger_credit = StudentLedger(
                    student_id=student.id,
                    transaction_type="credit",
                    amount=inv.amount_due,
                    balance=0.0,
                    description=f"Payment received for {inv.invoice_number}",
                    reference_id=inv.id,
                )
                db.add(ledger_credit)
                ledger_count += 2

        await db.flush()
        print(f"✅ Created {payment_count} payments, {ledger_count} ledger entries")

        # ═══════════════════════════════════════════════════
        # NOTIFICATIONS — Sample notifications for demo
        # ═══════════════════════════════════════════════════
        notif_templates = [
            {"title": "Welcome to CampusIQ!", "message": "Your account has been set up. Explore the dashboard to see your academic data.", "type": "info", "category": "system"},
            {"title": "Attendance Alert", "message": "Your attendance in CS301 has dropped below 75%. Please attend upcoming classes.", "type": "warning", "category": "attendance"},
            {"title": "Prediction Updated", "message": "Your risk assessment for Database Management Systems has been updated. Check your dashboard.", "type": "info", "category": "prediction"},
            {"title": "Fee Due Reminder", "message": "Your semester fees are due within 7 days. Please make the payment to avoid late charges.", "type": "warning", "category": "system"},
            {"title": "Great Performance!", "message": "You're in the top 20% of your class for attendance. Keep it up!", "type": "success", "category": "attendance"},
            {"title": "New Timetable Published", "message": "The updated timetable for this semester is now available.", "type": "info", "category": "system"},
        ]
        notif_count = 0
        # Notifications for admin
        for tmpl in notif_templates[:3]:
            n = Notification(
                user_id=admin_user.id,
                title=tmpl["title"],
                message=tmpl["message"],
                type=tmpl["type"],
                category=tmpl["category"],
                is_read=random.choice([True, False]),
            )
            db.add(n)
            notif_count += 1

        # Notifications for all students
        for student, _ in students:
            # Each student gets 2-4 random notifications
            for tmpl in random.sample(notif_templates, k=random.randint(2, 4)):
                n = Notification(
                    user_id=student.user_id,
                    title=tmpl["title"],
                    message=tmpl["message"],
                    type=tmpl["type"],
                    category=tmpl["category"],
                    is_read=random.choice([True, True, False]),
                )
                db.add(n)
                notif_count += 1

        # Notifications for faculty
        faculty_notifs = [
            {"title": "Class Reminder", "message": "You have a lecture at 10:15 AM in LH-201.", "type": "info", "category": "system"},
            {"title": "Student At Risk", "message": "3 students in your course are flagged as high-risk. Review their profiles.", "type": "warning", "category": "prediction"},
            {"title": "Leave Approved", "message": "Your casual leave request for Feb 20-21 has been approved.", "type": "success", "category": "system"},
        ]
        for fac, _ in faculty_list:
            for tmpl in random.sample(faculty_notifs, k=random.randint(1, 3)):
                n = Notification(
                    user_id=fac.user_id,
                    title=tmpl["title"],
                    message=tmpl["message"],
                    type=tmpl["type"],
                    category=tmpl["category"],
                    is_read=random.choice([True, False]),
                )
                db.add(n)
                notif_count += 1

        await db.commit()
        print(f"✅ Created {notif_count} notifications")

    print("\n" + "=" * 50)
    print("🎉 Seed complete! Demo credentials:")
    print("   Admin:   admin@campusiq.edu / admin123")
    print("   Faculty: faculty1@campusiq.edu / faculty123")
    print("   Student: student1@campusiq.edu / student123")
    print("   Staff:   staff1@campusiq.edu / staff123")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
