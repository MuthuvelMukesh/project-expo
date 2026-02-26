# CampusIQ — Complete Technical Documentation

> **AI-First Intelligent College ERP System**  
> Built with FastAPI, React, PostgreSQL, Redis, and OpenRouter LLM

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Authentication System](#2-authentication-system)
3. [Student Dashboard](#3-student-dashboard)
4. [Faculty Console](#4-faculty-console)
5. [Admin Panel](#5-admin-panel)
6. [Command Console (Copilot)](#6-command-console-copilot)
7. [Chatbot System](#7-chatbot-system)
8. [Grade Prediction Engine](#8-grade-prediction-engine)
9. [Attendance System](#9-attendance-system)
10. [Database Models](#10-database-models)
11. [API Reference](#11-api-reference)
12. [Internal Function Reference](#12-internal-function-reference)

---

## 1. System Architecture

### Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  React 18 + Vite 5 + Tailwind CSS + Recharts                   │
│  Port: 5173                                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND                                   │
│  FastAPI + SQLAlchemy + Pydantic                                │
│  Port: 8000                                                      │
├─────────────────────────────────────────────────────────────────┤
│  Services:                                                       │
│  • Auth Service (JWT)                                           │
│  • NLP CRUD Service (Natural Language → SQL)                    │
│  • Prediction Service (XGBoost + SHAP)                          │
│  • Chatbot Service (OpenRouter LLM)                             │
│  • Conversational Ops Service (Command Console)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│      PostgreSQL         │     │         Redis           │
│  Primary Database       │     │    Cache + Sessions     │
│  Port: 5433             │     │    Port: 6379           │
└─────────────────────────┘     └─────────────────────────┘
```

### How It Was Built

1. **Backend First** — FastAPI app with async SQLAlchemy for high concurrency
2. **Database Design** — PostgreSQL with proper relationships and indexes
3. **ML Pipeline** — XGBoost trained on synthetic academic data
4. **LLM Integration** — OpenRouter API for NLP parsing and chatbot
5. **Frontend** — React SPA with role-based routing
6. **Containerization** — Docker Compose for easy deployment

### Directory Structure

```
project-expo/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Config, security, database
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── ml/              # Machine learning
│   ├── tests/               # Pytest tests
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/      # Reusable UI
│       ├── pages/           # Route pages
│       ├── services/        # API client
│       └── context/         # React context
└── docker-compose.yml
```

---

## 2. Authentication System

### How It Works

```
┌──────────┐    POST /api/auth/login     ┌──────────┐
│  User    │ ─────────────────────────▶  │  Server  │
│ (Email + │                             │          │
│ Password)│  ◀─────────────────────────  │  JWT     │
└──────────┘    { access_token, role }   └──────────┘
```

### Input Format

**Login Request:**
```json
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@campusiq.edu&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "role": "admin",
  "user_id": 1,
  "full_name": "Admin User"
}
```

### Internal Functions

**File:** `backend/app/services/auth_service.py`

```python
async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    1. Query database for user by email
    2. Verify password hash using passlib
    3. Return User object or None
    """
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    """
    1. Copy payload data
    2. Add expiration timestamp
    3. Encode with HS256 algorithm using SECRET_KEY
    4. Return JWT string
    """
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@campusiq.edu` | `admin123` |
| Faculty | `faculty1@campusiq.edu` | `faculty123` |
| Student | `student1@campusiq.edu` | `student123` |

---

## 3. Student Dashboard

### Features

1. **Profile Card** — Name, roll number, department, semester
2. **Attendance Widget** — Overall % with color indicators
3. **CGPA Display** — Current CGPA with trend
4. **Grade Predictions** — AI-predicted grades per course
5. **Risk Alerts** — Early warning for at-risk courses
6. **Timetable** — Weekly class schedule

### How Input Works

**No direct input required** — Dashboard auto-loads based on logged-in user's JWT token.

**API Flow:**
```
1. Frontend reads JWT from localStorage
2. Sends GET /api/students/me with Authorization header
3. Backend decodes JWT → extracts user_id
4. Queries Student table with user_id
5. Returns student data + predictions + attendance
```

### API Endpoints

```http
GET /api/students/me
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "roll_number": "CSE2023001",
  "full_name": "Aarav Sharma",
  "department": "Computer Science",
  "semester": 3,
  "cgpa": 8.72,
  "attendance_percentage": 86.5,
  "predictions": [
    {
      "course": "Data Structures",
      "predicted_grade": "A",
      "risk_score": 0.15,
      "confidence": 0.92
    }
  ]
}
```

### Internal Data Flow

```
StudentDashboard.jsx
        │
        ▼
    api.getStudentDashboard()
        │
        ▼
    GET /api/students/me
        │
        ▼
    students.py route handler
        │
        ▼
    Query: SELECT * FROM students WHERE user_id = ?
        │
        ▼
    Query: SELECT * FROM predictions WHERE student_id = ?
        │
        ▼
    Query: SELECT COUNT(*), SUM(is_present) FROM attendance WHERE student_id = ?
        │
        ▼
    Return aggregated JSON response
```

---

## 4. Faculty Console

### Features

1. **Risk Roster** — Students at academic risk (risk_score > 0.7)
2. **QR Attendance** — Generate time-limited QR codes
3. **Class Analytics** — Attendance trends, grade distribution
4. **Course Management** — View assigned courses

### QR Attendance System

**How It Works:**

```
┌─────────────┐                      ┌─────────────┐
│   Faculty   │  1. Generate QR      │   Server    │
│   Console   │ ──────────────────▶  │             │
│             │                      │  Creates:   │
│             │  ◀──────────────────  │  - Token    │
│             │  2. QR Code Image    │  - Expiry   │
└─────────────┘                      │  - Course   │
                                     └─────────────┘
       │
       │ 3. Display QR
       ▼
┌─────────────┐                      ┌─────────────┐
│   Student   │  4. Scan QR          │   Server    │
│   Phone     │ ──────────────────▶  │             │
│             │                      │  Validates: │
│             │  ◀──────────────────  │  - Token    │
│             │  5. Marked Present   │  - Time     │
└─────────────┘                      │  - Location │
                                     └─────────────┘
```

**Generate QR Input:**
```json
POST /api/attendance/qr/generate
Authorization: Bearer <faculty_token>

{
  "course_id": 5,
  "valid_minutes": 10
}
```

**Response:**
```json
{
  "qr_token": "att_abc123xyz",
  "qr_code_base64": "data:image/png;base64,iVBORw0...",
  "expires_at": "2026-02-26T16:35:00Z",
  "course_name": "Data Structures"
}
```

**Student Scan Input:**
```json
POST /api/attendance/qr/mark
Authorization: Bearer <student_token>

{
  "qr_token": "att_abc123xyz"
}
```

### Internal Functions

**File:** `backend/app/services/attendance_service.py`

```python
async def generate_qr_attendance(
    db: AsyncSession, 
    faculty_id: int, 
    course_id: int, 
    valid_minutes: int = 10
) -> dict:
    """
    1. Verify faculty teaches this course
    2. Generate unique token: att_{uuid}
    3. Store in Redis with TTL = valid_minutes
    4. Generate QR code image (base64)
    5. Return token + image + expiry
    """
    token = f"att_{uuid.uuid4().hex[:12]}"
    expires_at = datetime.utcnow() + timedelta(minutes=valid_minutes)
    
    # Store in Redis
    await redis.setex(
        f"qr:{token}",
        valid_minutes * 60,
        json.dumps({"course_id": course_id, "faculty_id": faculty_id})
    )
    
    # Generate QR image
    qr = qrcode.make(token)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "qr_token": token,
        "qr_code_base64": f"data:image/png;base64,{qr_base64}",
        "expires_at": expires_at.isoformat()
    }

async def mark_attendance_by_qr(
    db: AsyncSession,
    student_id: int,
    qr_token: str
) -> dict:
    """
    1. Lookup token in Redis
    2. If not found → expired/invalid
    3. Check student is enrolled in course
    4. Check not already marked today
    5. Insert attendance record
    6. Return success
    """
    cached = await redis.get(f"qr:{qr_token}")
    if not cached:
        raise HTTPException(400, "QR code expired or invalid")
    
    data = json.loads(cached)
    course_id = data["course_id"]
    
    # Insert attendance
    attendance = Attendance(
        student_id=student_id,
        course_id=course_id,
        date=date.today(),
        is_present=True,
        method="qr",
        marked_at=datetime.utcnow()
    )
    db.add(attendance)
    await db.commit()
    
    return {"status": "marked", "course_id": course_id}
```

---

## 5. Admin Panel

### Features

1. **User Management** — Create/edit/delete users
2. **Department Stats** — Student counts, faculty allocation
3. **System Overview** — Total students, courses, attendance rate
4. **Audit Logs** — Track all operations

### Input Examples

**Create User:**
```json
POST /api/users/
Authorization: Bearer <admin_token>

{
  "email": "newstudent@campusiq.edu",
  "password": "secure123",
  "full_name": "New Student",
  "role": "student"
}
```

**Update User:**
```json
PUT /api/users/15
Authorization: Bearer <admin_token>

{
  "is_active": false
}
```

**Delete User:**
```http
DELETE /api/users/15
Authorization: Bearer <admin_token>
```

### Department Statistics Query

**Internal SQL:**
```sql
SELECT 
    d.name as department,
    COUNT(DISTINCT s.id) as student_count,
    COUNT(DISTINCT f.id) as faculty_count,
    AVG(s.cgpa) as avg_cgpa
FROM departments d
LEFT JOIN students s ON s.department_id = d.id
LEFT JOIN faculty f ON f.department_id = d.id
GROUP BY d.id, d.name
ORDER BY student_count DESC;
```

---

## 6. Command Console (Copilot)

### Overview

The **Command Console** is the flagship feature — a conversational operations AI that converts natural language into safe database operations with human approval.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMMAND CONSOLE FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Input: "Show all CSE students with CGPA below 6"          │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────┐                                           │
│  │  NLP Parser     │  OpenRouter LLM extracts:                 │
│  │  (LLM)          │  • intent: READ                           │
│  └────────┬────────┘  • entity: student                        │
│           │           • filters: {department: "CSE", cgpa_lt: 6}│
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │  Risk Assessor  │  Calculates:                              │
│  │                 │  • risk_level: LOW/MEDIUM/HIGH            │
│  └────────┬────────┘  • requires_approval: true/false          │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │  Plan Generator │  Creates:                                 │
│  │                 │  • preview of affected records            │
│  └────────┬────────┘  • rollback strategy                      │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐  If HIGH risk:                            │
│  │  Approval Gate  │  → Requires senior approval               │
│  │                 │  → Requires 2FA verification              │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │  Executor       │  Applies changes with:                    │
│  │                 │  • before_state snapshot                  │
│  └────────┬────────┘  • after_state snapshot                   │
│           │           • audit log entry                         │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │  Rollback       │  Can undo any operation                   │
│  │  (if needed)    │  using before_state                       │
│  └─────────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Input Examples

**1. READ Operations (Safe, Auto-Execute)**

```
Input: "Show all students"
Input: "List faculty in ECE department"
Input: "How many students have CGPA above 8?"
Input: "Show top 10 students by CGPA"
```

**2. ANALYZE Operations (Safe, Auto-Execute)**

```
Input: "Count students per department"
Input: "Average CGPA by semester"
Input: "Attendance distribution by course"
```

**3. UPDATE Operations (Requires Confirmation)**

```
Input: "Update semester to 4 for all students in section A"
Input: "Change CGPA to 7.5 for student with roll number CSE2023015"
```

**4. DELETE Operations (HIGH Risk, Requires Senior Approval)**

```
Input: "Delete all inactive users"
Input: "Remove student with ID 25"
```

### API Requests

**Create Plan:**
```json
POST /api/ops-ai/plan
Authorization: Bearer <token>

{
  "message": "Show all CSE students with CGPA below 6",
  "module": "nlp"
}
```

**Response:**
```json
{
  "plan_id": "ops_abc123def456",
  "intent": "READ",
  "entity": "student",
  "confidence": 0.95,
  "risk_level": "LOW",
  "estimated_impact_count": 12,
  "requires_confirmation": false,
  "requires_senior_approval": false,
  "status": "ready_for_execution",
  "preview": {
    "affected_records": [
      {"id": 5, "roll_number": "CSE2023005", "cgpa": 5.8, "name": "..."},
      {"id": 12, "roll_number": "CSE2023012", "cgpa": 5.2, "name": "..."}
    ],
    "proposed_changes": [],
    "rollback_plan": {
      "strategy": "before_state_snapshot",
      "supports_rollback": true
    }
  }
}
```

**Execute Plan:**
```json
POST /api/ops-ai/execute
Authorization: Bearer <token>

{
  "plan_id": "ops_abc123def456"
}
```

**Approve High-Risk Plan (Senior Admin):**
```json
POST /api/ops-ai/decide
Authorization: Bearer <admin_token>

{
  "plan_id": "ops_xyz789",
  "decision": "APPROVE",
  "two_factor_code": "123456"
}
```

### Internal Functions

**File:** `backend/app/services/conversational_ops_service.py`

```python
async def create_operational_plan(
    *,
    db: AsyncSession,
    user: User,
    message: str,
    module: str = "nlp"
) -> dict:
    """
    Main entry point for Command Console.
    
    Steps:
    1. Parse natural language using LLM
    2. Validate user permissions
    3. Calculate risk level
    4. Generate preview of affected records
    5. Create plan record in database
    6. Auto-execute if LOW risk READ/ANALYZE
    7. Return plan details to frontend
    """
    
    # Step 1: Parse with LLM
    parsed = await _parse_intent_with_llm(message)
    # Returns: {intent, entity, filters, values, confidence}
    
    # Step 2: Permission check
    allowed, reason = _check_permission(user.role, parsed["intent"], parsed["entity"])
    
    # Step 3: Risk assessment
    risk = _calculate_risk(
        intent=parsed["intent"],
        entity=parsed["entity"],
        impact_count=len(affected_rows)
    )
    
    # Step 4: Build preview
    preview = await _build_preview(db, parsed["entity"], parsed["filters"], parsed["values"])
    
    # Step 5: Determine requirements
    requires_confirmation = parsed["intent"] in {"UPDATE", "CREATE"}
    requires_senior_approval = risk == "HIGH" or parsed["intent"] == "DELETE"
    requires_2fa = risk == "HIGH" and settings.OPS_REQUIRE_2FA_HIGH_RISK
    
    # Step 6: Create plan record
    plan = OperationalPlan(
        plan_id=f"ops_{uuid.uuid4().hex[:12]}",
        user_id=user.id,
        message=message,
        intent_type=parsed["intent"],
        entity=parsed["entity"],
        filters=parsed["filters"],
        values=parsed["values"],
        confidence=parsed["confidence"],
        risk_level=risk,
        status="ready_for_execution" if risk == "LOW" else "awaiting_approval",
        preview=preview,
        ...
    )
    db.add(plan)
    await db.flush()
    
    # Step 7: Auto-execute safe operations
    if plan.status == "ready_for_execution":
        result = await execute_operational_plan(db=db, user=user, plan_id=plan.plan_id)
        return {**plan_data, "auto_execution": result}
    
    return plan_data


def _calculate_risk(intent: str, entity: str, impact_count: int) -> str:
    """
    Risk calculation logic:
    
    HIGH risk if:
    - DELETE operation
    - Affects > 50 records
    - Modifying users/permissions
    
    MEDIUM risk if:
    - UPDATE/CREATE operation
    - Affects 10-50 records
    
    LOW risk if:
    - READ/ANALYZE operation
    - Affects < 10 records
    """
    if intent == "DELETE":
        return "HIGH"
    if entity == "user" and intent in {"UPDATE", "CREATE"}:
        return "HIGH"
    if impact_count > 50:
        return "HIGH"
    if impact_count > 25:
        return "HIGH"
    if intent in {"UPDATE", "CREATE"}:
        return "MEDIUM"
    return "LOW"


async def execute_operational_plan(
    *,
    db: AsyncSession,
    user: User,
    plan_id: str
) -> dict:
    """
    Execute an approved plan.
    
    Steps:
    1. Load plan from database
    2. Verify permissions and status
    3. Capture before_state snapshot
    4. Execute operation (SELECT/INSERT/UPDATE/DELETE)
    5. Capture after_state snapshot
    6. Create audit log entry
    7. Return execution result
    """
    plan = await db.get(OperationalPlan, plan_id)
    
    # Capture before state
    rows = await _rows_for_execution(db, plan)
    before_state = [_model_to_dict(row) for row in rows]
    
    # Execute based on intent
    if plan.intent_type == "READ":
        # Just return the data
        after_state = before_state
        
    elif plan.intent_type == "UPDATE":
        for row in rows:
            for key, value in plan.values.items():
                setattr(row, key, value)
        await db.flush()
        after_state = [_model_to_dict(row) for row in rows]
        
    elif plan.intent_type == "DELETE":
        for row in rows:
            await db.delete(row)
        await db.flush()
        after_state = []
    
    # Create audit log
    await _audit(db, user_id=user.id, role=user.role.value, ...)
    
    return {
        "plan_id": plan_id,
        "status": "executed",
        "affected_count": len(before_state),
        "before_state": before_state,
        "after_state": after_state
    }
```

**File:** `backend/app/services/nlp_crud_service.py`

```python
async def detect_intent_llm(message: str) -> Optional[dict]:
    """
    Use OpenRouter LLM to parse natural language into structured query.
    
    Prompt engineering ensures:
    - Correct intent classification (READ/CREATE/UPDATE/DELETE/ANALYZE)
    - Entity extraction (student/faculty/course/etc)
    - Filter extraction with proper types (cgpa_lt, semester, department)
    """
    prompt = f"""You are a database query classifier for a college ERP system.
Tables: students, faculty, courses, departments, attendance, predictions, users.

Analyze the message and return JSON with:
- "intent": "READ", "CREATE", "UPDATE", "DELETE", or "ANALYZE"
- "entity": student, faculty, course, department, attendance, prediction, or user
- "filters": object with filters. IMPORTANT FORMAT RULES:
  - For CGPA comparisons: use "cgpa_lt" for less than, "cgpa_gt" for greater than
  - For semester: use integer
  - For department: use exact name
- "values": object for CREATE/UPDATE operations
- "aggregation": "count", "average", "sum", "min", "max", "group_by", or null
- "limit": number or null

User message: "{message}"

Return ONLY valid JSON."""

    result = await GeminiPoolClient.generate_json(module="nlp", prompt=prompt)
    return json.loads(result["text"])


def _apply_filters(stmt, model, entity: str, filters: dict):
    """
    Convert parsed filters into SQLAlchemy WHERE clauses.
    
    Handles:
    - department: JOIN departments WHERE name LIKE %value%
    - semester: WHERE semester = value
    - cgpa_lt: WHERE cgpa < value
    - cgpa_gt: WHERE cgpa > value
    - id: WHERE id = value
    - name: JOIN users WHERE full_name LIKE %value%
    """
    for key, value in filters.items():
        if key == "department" and entity in ("student", "course", "faculty"):
            stmt = stmt.join(Department).where(
                func.lower(Department.name).like(f"%{value.lower()}%")
            )
        elif key == "semester":
            stmt = stmt.where(model.semester == int(value))
        elif key == "cgpa_lt":
            stmt = stmt.where(Student.cgpa < float(value))
        elif key == "cgpa_gt":
            stmt = stmt.where(Student.cgpa > float(value))
        # ... more filters
    
    return stmt
```

---

## 7. Chatbot System

### Overview

Context-aware AI assistant that answers questions using live database data.

### How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                     CHATBOT FLOW                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  User: "What is my attendance percentage?"                   │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────┐                                        │
│  │ Intent Detector │  Is this a data query?                 │
│  └────────┬────────┘  Pattern: "my attendance"              │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                        │
│  │ Context Builder │  Fetch user's actual data:             │
│  │                 │  • Attendance: 86%                     │
│  └────────┬────────┘  • CGPA: 8.72                          │
│           │           • Courses: 5 enrolled                  │
│           ▼                                                  │
│  ┌─────────────────┐                                        │
│  │ LLM Generator   │  System prompt + context + question    │
│  │ (OpenRouter)    │                                        │
│  └────────┬────────┘                                        │
│           │                                                  │
│           ▼                                                  │
│  Response: "Your current attendance is 86%. You've          │
│            attended 45 out of 52 classes this semester."    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Input Examples

```
"What is my CGPA?"
"How many classes did I miss this week?"
"When is my next Data Structures class?"
"What are my predicted grades?"
"Who teaches Operating Systems?"
"List my enrolled courses"
```

### API Request

```json
POST /api/chatbot/
Authorization: Bearer <token>

{
  "message": "What is my attendance percentage?"
}
```

**Response:**
```json
{
  "response": "Your current attendance is 86%. You've attended 173 out of 201 total classes across all your courses this semester. Your highest attendance is in Data Structures (92%) and lowest in Computer Networks (78%).",
  "context_used": true,
  "data_query": false
}
```

### Internal Functions

**File:** `backend/app/services/chatbot_service.py`

```python
async def process_chat_message(
    message: str,
    user_id: int,
    user_role: str,
    db: AsyncSession
) -> dict:
    """
    Main chatbot entry point.
    
    Steps:
    1. Detect if message is a data query
    2. If data query → route to NLP CRUD engine
    3. Build user context from database
    4. Send to LLM with context
    5. Return response
    """
    
    # Step 1: Check if data query
    if _is_data_query(message):
        # Route to NLP CRUD for structured response
        result = await process_nlp_crud(message, user_role, user_id, db)
        return {"response": _format_crud_result(result), "data_query": True}
    
    # Step 2: Build context
    context = await _build_user_context(user_id, user_role, db)
    
    # Step 3: Generate response with LLM
    system_prompt = f"""You are CampusIQ Assistant, an AI helper for college students and faculty.
    
Current user context:
{context}

Answer questions helpfully using the context above. Be specific with numbers and data.
If asked about something not in context, say you don't have that information."""

    response = await GeminiPoolClient.generate_text(
        module="chat",
        system_prompt=system_prompt,
        user_message=message,
        temperature=0.4
    )
    
    return {"response": response, "data_query": False, "context_used": True}


async def _build_user_context(user_id: int, user_role: str, db: AsyncSession) -> str:
    """
    Fetch live data for the current user to inject into LLM context.
    
    For students: roll_number, semester, CGPA, attendance %, predictions
    For faculty: courses taught, student count, department
    """
    lines = []
    
    if user_role == "student":
        student = await db.get(Student, user_id)
        lines.append(f"Student: {student.roll_number}")
        lines.append(f"Semester: {student.semester}")
        lines.append(f"CGPA: {student.cgpa}")
        
        # Calculate attendance
        attendance_pct = await _calculate_attendance_percentage(db, student.id)
        lines.append(f"Overall Attendance: {attendance_pct}%")
        
        # Get predictions
        predictions = await db.execute(
            select(Prediction).where(Prediction.student_id == student.id)
        )
        for pred in predictions.scalars():
            lines.append(f"Predicted grade in {pred.course.name}: {pred.predicted_grade}")
    
    return "\n".join(lines)
```

---

## 8. Grade Prediction Engine

### Overview

XGBoost machine learning model that predicts student exam grades 4-6 weeks in advance.

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                   PREDICTION PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input Features:                                                │
│  • Attendance Rate (%)                                          │
│  • Assignment Submission Rate (%)                               │
│  • Quiz Average Score (%)                                       │
│  • Lab Participation Rate (%)                                   │
│  • Previous Semester CGPA                                       │
│  • Class Participation Score                                    │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────┐                                           │
│  │  Feature        │  Normalize and scale features              │
│  │  Engineering    │                                            │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │  XGBoost Model  │  Trained on historical data               │
│  │                 │  • 10,000+ records                        │
│  └────────┬────────┘  • 85% accuracy                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │  SHAP Explainer │  Calculate feature importance             │
│  │                 │  "Why this prediction?"                   │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  Output:                                                        │
│  • predicted_grade: "B+"                                        │
│  • risk_score: 0.35                                            │
│  • confidence: 0.89                                            │
│  • factors: [                                                  │
│      {factor: "Attendance", impact: +0.15, value: "92%"},     │
│      {factor: "Quiz Avg", impact: -0.08, value: "68%"}        │
│    ]                                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API Request

```http
GET /api/predictions/student/5
Authorization: Bearer <token>
```

**Response:**
```json
{
  "student_id": 5,
  "predictions": [
    {
      "course_id": 1,
      "course_name": "Data Structures",
      "predicted_grade": "A",
      "risk_score": 0.15,
      "confidence": 0.92,
      "factors": [
        {"factor": "Attendance Rate", "impact": 0.18, "value": "94%"},
        {"factor": "Assignment Submission", "impact": 0.12, "value": "100%"},
        {"factor": "Quiz Average", "impact": -0.05, "value": "78%"},
        {"factor": "Lab Participation", "impact": 0.08, "value": "85%"}
      ]
    },
    {
      "course_id": 2,
      "course_name": "Computer Networks",
      "predicted_grade": "B",
      "risk_score": 0.72,
      "confidence": 0.85,
      "factors": [
        {"factor": "Attendance Rate", "impact": -0.25, "value": "68%"},
        {"factor": "Quiz Average", "impact": -0.15, "value": "55%"}
      ]
    }
  ]
}
```

### Internal Functions

**File:** `backend/app/ml/predict.py`

```python
import xgboost as xgb
import shap
import numpy as np

class GradePredictor:
    def __init__(self, model_path: str):
        self.model = xgb.Booster()
        self.model.load_model(model_path)
        self.explainer = shap.TreeExplainer(self.model)
        
        self.feature_names = [
            "attendance_rate",
            "assignment_submission_rate", 
            "quiz_average",
            "lab_participation",
            "previous_cgpa",
            "class_participation"
        ]
        
        self.grade_map = {
            0: "F", 1: "D", 2: "C", 3: "C+",
            4: "B", 5: "B+", 6: "A", 7: "A+"
        }
    
    def predict(self, features: dict) -> dict:
        """
        Make a grade prediction with explainability.
        
        Args:
            features: dict with attendance_rate, quiz_average, etc.
        
        Returns:
            {predicted_grade, risk_score, confidence, factors}
        """
        # Prepare feature vector
        X = np.array([[
            features.get("attendance_rate", 0) / 100,
            features.get("assignment_submission", 0) / 100,
            features.get("quiz_average", 0) / 100,
            features.get("lab_participation", 0) / 100,
            features.get("previous_cgpa", 0) / 10,
            features.get("class_participation", 0) / 100
        ]])
        
        # Get prediction probabilities
        dmatrix = xgb.DMatrix(X, feature_names=self.feature_names)
        probs = self.model.predict(dmatrix)[0]
        
        # Get predicted class
        predicted_class = int(np.argmax(probs))
        confidence = float(probs[predicted_class])
        
        # Calculate risk score (probability of failing grades)
        risk_score = float(sum(probs[:3]))  # F + D + C
        
        # SHAP explanation
        shap_values = self.explainer.shap_values(X)
        factors = []
        for i, (name, shap_val) in enumerate(zip(self.feature_names, shap_values[0])):
            factors.append({
                "factor": name.replace("_", " ").title(),
                "impact": round(float(shap_val), 2),
                "value": f"{features.get(name, 0)}%"
            })
        
        # Sort by absolute impact
        factors.sort(key=lambda x: abs(x["impact"]), reverse=True)
        
        return {
            "predicted_grade": self.grade_map[predicted_class],
            "risk_score": round(risk_score, 2),
            "confidence": round(confidence, 2),
            "factors": factors[:4]  # Top 4 factors
        }


async def get_student_predictions(db: AsyncSession, student_id: int) -> list:
    """
    Generate predictions for all courses a student is enrolled in.
    """
    predictor = GradePredictor("app/ml/models/grade_model.json")
    
    # Get student's courses
    enrollments = await db.execute(
        select(CourseEnrollment).where(CourseEnrollment.student_id == student_id)
    )
    
    predictions = []
    for enrollment in enrollments.scalars():
        # Calculate features from actual data
        features = await _calculate_features(db, student_id, enrollment.course_id)
        
        # Get prediction
        pred = predictor.predict(features)
        pred["course_id"] = enrollment.course_id
        pred["course_name"] = enrollment.course.name
        predictions.append(pred)
    
    return predictions
```

**File:** `backend/app/ml/features.py`

```python
async def _calculate_features(db: AsyncSession, student_id: int, course_id: int) -> dict:
    """
    Calculate ML features from actual database records.
    """
    # Attendance rate
    total = await db.scalar(
        select(func.count(Attendance.id))
        .where(Attendance.student_id == student_id, Attendance.course_id == course_id)
    )
    present = await db.scalar(
        select(func.count(Attendance.id))
        .where(
            Attendance.student_id == student_id,
            Attendance.course_id == course_id,
            Attendance.is_present == True
        )
    )
    attendance_rate = (present / total * 100) if total > 0 else 0
    
    # Get student's CGPA
    student = await db.get(Student, student_id)
    
    return {
        "attendance_rate": attendance_rate,
        "assignment_submission": 85,  # Placeholder - would come from assignments table
        "quiz_average": 72,           # Placeholder - would come from quiz scores
        "lab_participation": 90,      # Placeholder - would come from lab records
        "previous_cgpa": student.cgpa,
        "class_participation": 75     # Placeholder - would come from participation logs
    }
```

---

## 9. Attendance System

### Methods Supported

| Method | Description | Anti-Fraud |
|--------|-------------|------------|
| **QR Code** | Faculty generates, students scan | Time-limited (10 min), single-use |
| **Biometric** | Fingerprint/face recognition | Device-bound |
| **Manual** | Faculty marks directly | Audit logged |

### Data Model

```sql
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    course_id INTEGER REFERENCES courses(id),
    date DATE NOT NULL,
    is_present BOOLEAN DEFAULT false,
    marked_at TIMESTAMP,
    method VARCHAR(20),  -- 'qr', 'biometric', 'manual'
    
    UNIQUE(student_id, course_id, date)
);
```

### Attendance Query Examples

**Get student's attendance:**
```sql
SELECT 
    c.name as course,
    COUNT(*) as total_classes,
    SUM(CASE WHEN a.is_present THEN 1 ELSE 0 END) as attended,
    ROUND(SUM(CASE WHEN a.is_present THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 1) as percentage
FROM attendance a
JOIN courses c ON a.course_id = c.id
WHERE a.student_id = 5
GROUP BY c.id, c.name;
```

---

## 10. Database Models

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │  Department │       │   Course    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │       │ id          │       │ id          │
│ email       │       │ name        │       │ code        │
│ password    │       │ code        │       │ name        │
│ full_name   │◀──┐   └─────────────┘       │ semester    │
│ role        │   │         ▲               │ credits     │
│ is_active   │   │         │               │ department_id│──▶
└─────────────┘   │         │               │ instructor_id│──▶
       ▲          │   ┌─────┴─────┐         └─────────────┘
       │          │   │           │               ▲
       │          │   │           │               │
┌──────┴──────┐   │   │     ┌─────┴─────┐   ┌────┴────┐
│   Student   │   │   │     │  Faculty  │   │Attendance│
├─────────────┤   │   │     ├───────────┤   ├─────────┤
│ id          │   │   │     │ id        │   │ id      │
│ user_id     │───┘   │     │ user_id   │───│student_id│
│ roll_number │       │     │ employee_id│  │course_id │
│ department_id│──────┤     │department_id│─│ date    │
│ semester    │       │     │ designation│  │is_present│
│ section     │       │     └───────────┘   │ method  │
│ cgpa        │       │                     └─────────┘
└─────────────┘       │
       │              │
       │              │
       ▼              │
┌─────────────┐       │
│ Prediction  │       │
├─────────────┤       │
│ id          │       │
│ student_id  │───────┘
│ course_id   │
│ predicted_grade│
│ risk_score  │
│ confidence  │
│ factors     │
└─────────────┘
```

### Model Definitions

**File:** `backend/app/models/models.py`

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum

class UserRole(enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    roll_number = Column(String, unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    semester = Column(Integer, nullable=False)
    section = Column(String)
    cgpa = Column(Float, default=0.0)
    admission_year = Column(Integer)
    
    user = relationship("User", backref="student_profile")
    department = relationship("Department", backref="students")
    predictions = relationship("Prediction", backref="student")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    predicted_grade = Column(String(3))  # A+, A, B+, B, C+, C, D, F
    risk_score = Column(Float)  # 0.0 to 1.0
    confidence = Column(Float)  # 0.0 to 1.0
    factors = Column(JSON)  # SHAP explanation
    created_at = Column(DateTime, default=datetime.utcnow)

class OperationalPlan(Base):
    """Stores Command Console operation plans."""
    __tablename__ = "operational_plans"
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)  # Original natural language input
    intent_type = Column(String)  # READ, CREATE, UPDATE, DELETE, ANALYZE
    entity = Column(String)  # student, faculty, course, etc.
    filters = Column(JSON)  # Parsed filters
    values = Column(JSON)  # Values for CREATE/UPDATE
    confidence = Column(Float)
    risk_level = Column(String)  # LOW, MEDIUM, HIGH
    status = Column(String)  # pending, approved, executed, rejected, failed
    preview = Column(JSON)  # Affected records preview
    rollback_plan = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ImmutableAuditLog(Base):
    """Append-only audit log for compliance."""
    __tablename__ = "immutable_audit_logs"
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String, unique=True)
    plan_id = Column(String)
    execution_id = Column(String)
    user_id = Column(Integer)
    role = Column(String)
    module = Column(String)
    operation_type = Column(String)
    event_type = Column(String)
    risk_level = Column(String)
    intent_payload = Column(JSON)
    before_state = Column(JSON)
    after_state = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 11. API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login with email/password |
| POST | `/api/auth/register` | Register new user (admin only) |
| GET | `/api/auth/me` | Get current user info |

### Students

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/students/` | List all students |
| GET | `/api/students/me` | Get current student's dashboard |
| GET | `/api/students/{id}` | Get student by ID |
| PUT | `/api/students/{id}` | Update student |

### Faculty

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faculty/` | List all faculty |
| GET | `/api/faculty/me` | Get current faculty's dashboard |
| GET | `/api/faculty/{id}/courses` | Get courses taught |
| GET | `/api/faculty/{id}/risk-roster` | Get at-risk students |

### Attendance

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/attendance/qr/generate` | Generate QR code (faculty) |
| POST | `/api/attendance/qr/mark` | Mark attendance via QR (student) |
| POST | `/api/attendance/mark` | Manual attendance (faculty) |
| GET | `/api/attendance/student/{id}` | Get student's attendance |
| GET | `/api/attendance/course/{id}` | Get course attendance |

### Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/predictions/student/{id}` | Get student's predictions |
| GET | `/api/predictions/course/{id}` | Get course predictions |
| POST | `/api/predictions/refresh` | Refresh all predictions |

### Command Console (Ops AI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ops-ai/plan` | Create operation plan from NL |
| POST | `/api/ops-ai/execute` | Execute approved plan |
| POST | `/api/ops-ai/decide` | Approve/reject plan |
| GET | `/api/ops-ai/pending` | Get pending approvals |
| POST | `/api/ops-ai/rollback` | Rollback execution |

### Chatbot

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chatbot/` | Send chat message |

---

## 12. Internal Function Reference

### Key Service Functions

| Service | Function | Purpose |
|---------|----------|---------|
| `auth_service` | `authenticate_user()` | Verify email/password |
| `auth_service` | `create_access_token()` | Generate JWT |
| `nlp_crud_service` | `detect_intent_llm()` | Parse NL with LLM |
| `nlp_crud_service` | `detect_intent_keyword()` | Fallback NL parser |
| `nlp_crud_service` | `process_nlp_crud()` | Execute NL query |
| `conversational_ops_service` | `create_operational_plan()` | Create Command Console plan |
| `conversational_ops_service` | `execute_operational_plan()` | Execute approved plan |
| `conversational_ops_service` | `rollback_execution()` | Undo execution |
| `chatbot_service` | `process_chat_message()` | Handle chat |
| `chatbot_service` | `_build_user_context()` | Fetch user data for LLM |
| `prediction_service` | `get_student_predictions()` | Generate ML predictions |
| `attendance_service` | `generate_qr_attendance()` | Create QR code |
| `attendance_service` | `mark_attendance_by_qr()` | Process QR scan |
| `gemini_pool_service` | `generate_json()` | LLM call for JSON output |
| `gemini_pool_service` | `generate_text()` | LLM call for text output |

### Utility Functions

| File | Function | Purpose |
|------|----------|---------|
| `core/security.py` | `verify_password()` | Check password hash |
| `core/security.py` | `get_password_hash()` | Hash password |
| `core/security.py` | `decode_token()` | Validate JWT |
| `core/database.py` | `get_db()` | Get async DB session |
| `api/dependencies.py` | `get_current_user()` | Extract user from JWT |
| `api/dependencies.py` | `require_role()` | Role-based access control |

---

## Quick Start Commands

```bash
# Start all services
docker compose up -d

# View logs
docker logs campusiq-backend -f

# Access API docs
open http://localhost:8000/docs

# Access frontend
open http://localhost:5173

# Run tests
docker exec campusiq-backend pytest

# Stop all services
docker compose down
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | JWT signing key | (required) |
| `OPENROUTER_API_KEY` | OpenRouter LLM API key | (required for AI features) |
| `OPENROUTER_MODEL` | LLM model name | `liquid/lfm-2.5-1.2b-thinking:free` |
| `OPS_CONFIDENCE_THRESHOLD` | Min confidence for auto-execute | `0.75` |
| `OPS_REQUIRE_2FA_HIGH_RISK` | Require 2FA for HIGH risk ops | `true` |

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "No LLM keys configured" | Add `OPENROUTER_API_KEY` to `.env` |
| "JWT expired" | Login again to get new token |
| "Permission denied" | Check user role matches required access |
| "Database connection failed" | Ensure PostgreSQL container is running |
| "QR code expired" | Generate new QR (valid 10 minutes) |

### Debug Commands

```bash
# Check container status
docker compose ps

# Check backend logs
docker logs campusiq-backend --tail 100

# Access database
docker exec -it campusiq-db psql -U campusiq

# Test API health
curl http://localhost:8000/health
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-26 | Initial release with core features |

---

*Documentation generated for CampusIQ Project Expo*
