# CampusIQ — Overall Technical Documentation

> **AI-First Intelligent College ERP System**  
> Complete technical reference for architecture, implementation, and deployment

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Schema](#4-database-schema)
5. [Backend Services](#5-backend-services)
6. [Frontend Structure](#6-frontend-structure)
7. [AI/ML Components](#7-aiml-components)
8. [API Reference](#8-api-reference)
9. [Authentication & Security](#9-authentication--security)
10. [Deployment](#10-deployment)
11. [Environment Configuration](#11-environment-configuration)

---

## 1. Project Overview

### What is CampusIQ?

CampusIQ is an **AI-First Intelligent College ERP** system that integrates:

- **Natural Language Operations** — Query and modify data using plain English
- **Predictive Analytics** — ML-powered grade predictions with explainability
- **Smart Automation** — Risk-based approval workflows for data operations
- **Real-time Insights** — Live dashboards with attendance, grades, and alerts

### Core Features

| Module | Description | Users |
|--------|-------------|-------|
| **Student Dashboard** | CGPA, attendance, predictions, timetable | Students |
| **Faculty Console** | Risk roster, QR attendance, course analytics | Faculty |
| **Admin Panel** | User management, department stats, system overview | Admin |
| **Command Console** | Natural language → database operations with audit | All roles |
| **Chatbot** | Context-aware AI assistant with live data | All roles |
| **Finance Management** | Fees, invoices, payments, ledgers | Students, Admin |
| **HR & Payroll** | Employee records, salary structures, payslips | Admin |
| **Governance Dashboard** | Audit logs, operation stats, rollback | Admin |

---

## 2. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     React 18 SPA (Vite 5)                         │  │
│  │  • Role-based routing (student/faculty/admin)                     │  │
│  │  • Tailwind CSS styling                                           │  │
│  │  • Recharts for analytics visualization                           │  │
│  │  • JWT stored in localStorage                                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                     │
│                                   │ HTTP/REST                           │
│                                   ▼                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                              API LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI (Python 3.11+)                         │  │
│  │  • Async request handling                                         │  │
│  │  • Pydantic validation                                            │  │
│  │  • OpenAPI documentation (/docs)                                  │  │
│  │  • JWT middleware                                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                     │
├───────────────────────────────────┼─────────────────────────────────────┤
│                           SERVICE LAYER                                  │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────┐    │
│  │  Auth Service  │  │  NLP CRUD       │  │  Conversational Ops  │    │
│  │  • JWT tokens  │  │  Engine         │  │  Service             │    │
│  │  • Password    │  │  • Intent parse │  │  • Risk assessment   │    │
│  │    hashing     │  │  • Query build  │  │  • Direct execution  │    │
│  └────────────────┘  │  • Keyword      │  │  • Audit logging     │    │
│                      │    fallback     │  │  • Rollback support  │    │
│  ┌────────────────┐  └─────────────────┘  └──────────────────────┘    │
│  │  Chatbot       │                                                    │
│  │  Service       │  ┌─────────────────┐  ┌──────────────────────┐    │
│  │  • Context     │  │  Prediction     │  │  Attendance          │    │
│  │    injection   │  │  Service        │  │  Service             │    │
│  │  • LLM calls   │  │  • XGBoost      │  │  • QR generation     │    │
│  │  • Rule        │  │  • SHAP explain │  │  • Token validation  │    │
│  │    fallback    │  │  • Risk scoring │  │  • Manual marking    │    │
│  └────────────────┘  └─────────────────┘  └──────────────────────┘    │
│                                   │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    LLM Client (GeminiClient)                      │  │
│  │  • Google Gemini — gemini-2.0-flash                               │  │
│  │  • Single API key with exponential backoff retry                  │  │
│  │  • Methods: ask_json() for structured output, ask() for text     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                     │
├───────────────────────────────────┼─────────────────────────────────────┤
│                            DATA LAYER                                    │
│  ┌─────────────────────────┐      │      ┌─────────────────────────┐  │
│  │     PostgreSQL 16       │◀─────┴─────▶│       Redis 7           │  │
│  │  • Primary database     │             │  • QR token cache       │  │
│  │  • Async SQLAlchemy     │             │  • Session store        │  │
│  │  • 20+ tables           │             │                         │  │
│  │  • JSON columns for     │             │                         │  │
│  │    flexible data        │             │                         │  │
│  └─────────────────────────┘             └─────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Request Flow Example

```
User: "Show all CSE students with CGPA below 6"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. React Frontend                                                │
│    POST /api/ops-ai/execute {message: "...", module: "nlp"}        │
│    Authorization: Bearer <JWT>                                   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FastAPI Router (operational_ai.py)                           │
│    → Validate JWT → Extract user from token                     │
│    → Call conversational_ops_service.create_and_execute()       │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Conversational Ops Service                                    │
│    → _extract_intent() → Call LLM                               │
│    → _permission_gate() → Check role matrix                     │
│    → _estimate_impact() → COUNT(*) query                        │
│    → _classify_risk() → LOW/MEDIUM/HIGH                         │
│    → Execute directly (no approval gates)                       │
│    → Save results to DB                                         │
│    → _audit() → Create audit log                                │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. LLM Client (GeminiClient)                                     │
│    → Configure google.generativeai with GEMINI_API_KEY          │
│    → Generate structured JSON: {intent, entity, filters, values} │
│    → Exponential backoff retry on failure                       │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Response to Frontend                                          │
│    {plan_id, intent, entity, risk_level, status,                │
│     affected_count, before_state, after_state, analysis}        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | FastAPI | 0.109+ | Async API server |
| ORM | SQLAlchemy | 2.0+ | Database abstraction |
| Database | PostgreSQL | 16 | Primary data store |
| Cache | Redis | 7 | Sessions, QR tokens |
| Validation | Pydantic | 2.0+ | Request/response schemas |
| Auth | python-jose | 3.3+ | JWT encoding/decoding |
| Password | passlib | 1.7+ | bcrypt hashing |
| HTTP Client | httpx | 0.27+ | Async LLM API calls |
| ML | XGBoost | 2.0+ | Grade prediction |
| Explainability | SHAP | 0.44+ | Feature importance |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | React | 18 | UI components |
| Build Tool | Vite | 5 | Dev server, bundling |
| Routing | React Router | 6 | SPA navigation |
| Styling | Tailwind CSS | 3.4+ | Utility-first CSS |
| Charts | Recharts | 2.12+ | Data visualization |
| HTTP | Fetch API | - | API communication |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Containerization | Docker | Service isolation |
| Orchestration | Docker Compose | Multi-container deployment |
| LLM | Google Gemini | NLP parsing, chatbot |

---

## 4. Database Schema

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │  Department │       │   Course    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)     │
│ email       │       │ name        │       │ code        │
│ password    │       │ code        │       │ name        │
│ full_name   │◀──┐   └──────┬──────┘       │ semester    │
│ role        │   │          │              │ credits     │
│ is_active   │   │          │              │ department_id│──▶
│ created_at  │   │          │              │ instructor_id│──▶
└─────────────┘   │          │              └─────────────┘
       ▲          │    ┌─────┴─────┐              ▲
       │          │    │           │              │
┌──────┴──────┐   │    │     ┌─────┴─────┐  ┌────┴─────┐
│   Student   │   │    │     │  Faculty  │  │Attendance│
├─────────────┤   │    │     ├───────────┤  ├──────────┤
│ id (PK)     │   │    │     │ id (PK)   │  │ id (PK)  │
│ user_id(FK) │───┘    │     │ user_id   │──│student_id│
│ roll_number │        │     │ employee_id│ │course_id │
│ department_id│───────┤     │department_id│ │ date     │
│ semester    │        │     │designation │ │is_present│
│ section     │        │     └───────────┘  │ method   │
│ cgpa        │        │                    └──────────┘
└─────────────┘        │
       │               │
       ▼               │
┌─────────────┐        │
│ Prediction  │        │
├─────────────┤        │
│ id (PK)     │        │
│ student_id  │────────┘
│ course_id   │
│predicted_grade│
│ risk_score  │
│ confidence  │
│ factors(JSON)│
└─────────────┘
```

### Core Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | Authentication & identity | email, hashed_password, role, is_active |
| `students` | Student profiles | user_id, roll_number, department_id, semester, cgpa |
| `faculty` | Faculty profiles | user_id, employee_id, department_id, designation |
| `departments` | Academic departments | name, code |
| `courses` | Course catalog | code, name, semester, credits, instructor_id |
| `attendance` | Attendance records | student_id, course_id, date, is_present, method |
| `predictions` | ML grade predictions | student_id, course_id, predicted_grade, risk_score, factors |
| `timetable` | Weekly schedule | course_id, day_of_week, start_time, room |

### Operational AI Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `operational_plans` | Command Console plans | plan_id, message, intent_type, entity, filters, risk_level, status |
| `operational_executions` | Execution records | execution_id, plan_id, before_state, after_state |
| `immutable_audit_logs` | Compliance audit trail | event_id, operation_type, intent_payload, before_state, after_state |

### Finance Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `fee_structures` | Fee definitions | semester, fee_type, amount |
| `student_fees` | Student-specific fees | student_id, fee_type, amount, due_date, is_paid |
| `invoices` | Student invoices | student_id, invoice_number, amount_due, status |
| `payments` | Payment records | invoice_id, amount, payment_method, status |
| `student_ledger` | Account balance | student_id, transaction_type, amount, balance |
| `fee_waivers` | Scholarships/discounts | student_id, waiver_type, amount |

### HR Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `employees` | Extended employee info | user_id, employee_type, date_of_joining, bank_account |
| `salary_structures` | Salary components | employee_id, base_salary, da, hra, pf_contribution |
| `salary_records` | Monthly payslips | employee_id, month, year, gross_salary, net_salary |

---

## 5. Backend Services

### Service Architecture

```
backend/app/services/
├── auth_service.py              # JWT authentication
├── attendance_service.py        # QR attendance system
├── chatbot_service.py           # Context-aware chatbot
├── conversational_ops_service.py # Command Console orchestration (primary AI ops)
├── gemini_pool_service.py       # LLM client abstraction
├── nlp_crud_service.py          # NL → SQL translation
└── prediction_service.py        # ML predictions
```

### Key Service Responsibilities

**1. GeminiClient (`gemini_pool_service.py`)**
```python
# Single Gemini API client for all AI features
class GeminiClient:
    @classmethod
    async def ask_json(cls, prompt, system_instruction) -> dict:
        # For structured output (NLP parsing)
        # Uses google.generativeai SDK with JSON mode
        
    @classmethod
    async def ask(cls, prompt, system_instruction, temperature=0.4) -> str:
        # For conversational output (chatbot)
        # Temperature 0.4 balances creativity vs accuracy
```

**2. Conversational Ops Service (`conversational_ops_service.py`)**
```python
# Command Console pipeline — direct execution, no approval gates
async def create_and_execute(db, user, message, module):
    # 1. _extract_intent() → LLM parsing
    # 2. Confidence check → clarification if too low
    # 3. _permission_gate() → Role + department check
    # 4. _estimate_impact() → COUNT affected rows
    # 5. _classify_risk() → LOW/MEDIUM/HIGH
    # 6. Execute directly → Capture before/after state
    # 7. _audit() → Immutable audit log

async def rollback_execution(db, user, execution_id):
    # Restore before_state → Update records → Audit
```

**3. NLP CRUD Service (`nlp_crud_service.py`)**
```python
# Natural language to database operations
async def process_nlp_crud(message, user_role, user_id, db):
    # 1. detect_intent_llm() → LLM parsing
    #    Falls back to detect_intent_keyword() if LLM fails
    # 2. _check_access() → Permission validation
    # 3. execute_read/analyze/create/update/delete()
    # 4. Format response with summary
```

**4. Chatbot Service (`chatbot_service.py`)**
```python
async def process_query(message, user_role, user_id, db):
    # 1. _is_data_query() → Route decision (CRUD vs chat)
    # 2. _build_user_context() → Fetch live data for LLM context
    # 3. _query_gemini() → Generate response
    # 4. _rule_based_response() → Fallback without LLM
```

---

## 6. Frontend Structure

### Page Routing

```jsx
// App.jsx - Role-based routing
<Routes>
    {/* Public */}
    <Route path="/login" element={<Login />} />
    
    {/* Student routes */}
    <Route path="/dashboard" element={<StudentDashboard />} />
    <Route path="/profile" element={<StudentProfile />} />
    <Route path="/attendance" element={<AttendanceDetails />} />
    
    {/* Faculty routes */}
    <Route path="/faculty" element={<FacultyConsole />} />
    
    {/* Admin routes */}
    <Route path="/admin" element={<AdminPanel />} />
    <Route path="/manage-users" element={<UserManagement />} />
    <Route path="/manage-courses" element={<CourseManagement />} />
    <Route path="/manage-departments" element={<DepartmentManagement />} />
    <Route path="/hr" element={<HRManagement />} />
    <Route path="/governance" element={<GovernanceDashboard />} />
    
    {/* Shared routes */}
    <Route path="/copilot" element={<CopilotPanel />} />
    <Route path="/finance" element={<FinanceManagement />} />
    <Route path="/timetable" element={<TimetablePage />} />
</Routes>
```

### Component Structure

```
frontend/src/
├── main.jsx                 # React entry point
├── App.jsx                  # Router + AuthProvider
├── index.css                # Global styles
│
├── context/
│   └── AuthContext.jsx      # JWT auth state management
│
├── pages/
│   ├── Login.jsx            # Authentication form
│   ├── StudentDashboard.jsx # Student home
│   ├── FacultyConsole.jsx   # Faculty home
│   ├── AdminPanel.jsx       # Admin home
│   ├── CopilotPanel.jsx     # Command Console UI
│   ├── GovernanceDashboard.jsx # Audit + approvals
│   └── ...
│
├── components/
│   ├── Sidebar.jsx          # Navigation
│   ├── ChatWidget.jsx       # Floating chatbot
│   ├── NotificationBell.jsx # Alert dropdown
│   └── ThemeToggle.jsx      # Dark/light mode
│
└── services/
    └── api.js               # HTTP client wrapper
```

### Authentication Flow

```jsx
// context/AuthContext.jsx
const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        // On mount: check localStorage for JWT
        const token = localStorage.getItem('token');
        if (token) {
            // Validate token with /api/auth/me
            fetchCurrentUser(token).then(setUser);
        }
        setLoading(false);
    }, []);
    
    const login = async (email, password) => {
        // POST /api/auth/login
        // Store token in localStorage
        // Set user state
    };
    
    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };
    
    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
```

---

## 7. AI/ML Components

### LLM Integration

**Provider:**
- **Google Gemini** — `GEMINI_API_KEY`

**Model Configuration:**
```python
# Google Gemini (single key)
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TEMPERATURE_JSON = 0.1    # For structured output
GEMINI_TEMPERATURE_CHAT = 0.4    # For conversational output
```

### Grade Prediction Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                   PREDICTION PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input Features:                                                │
│  • attendance_rate (0-100%)                                     │
│  • assignment_submission (0-100%)                               │
│  • quiz_average (0-100%)                                        │
│  • lab_participation (0-100%)                                   │
│  • previous_cgpa (0-10)                                         │
│  • class_participation (0-100%)                                 │
│                                                                 │
│                    ▼                                            │
│  ┌─────────────────────────────────────────────┐               │
│  │           XGBoost Classifier                 │               │
│  │  • Multi-class: F, D, C, C+, B, B+, A, A+   │               │
│  │  • Trained on historical academic data      │               │
│  └─────────────────────────────────────────────┘               │
│                    │                                            │
│                    ▼                                            │
│  ┌─────────────────────────────────────────────┐               │
│  │           SHAP Explainer                     │               │
│  │  • TreeExplainer for XGBoost                │               │
│  │  • Per-feature contribution scores          │               │
│  └─────────────────────────────────────────────┘               │
│                    │                                            │
│                    ▼                                            │
│  Output:                                                        │
│  {                                                              │
│    "predicted_grade": "B+",                                    │
│    "risk_score": 0.35,        // P(F) + P(D) + P(C)           │
│    "confidence": 0.89,        // Max class probability         │
│    "factors": [               // SHAP values                   │
│      {"factor": "Attendance", "impact": +0.15},               │
│      {"factor": "Quiz Avg", "impact": -0.08}                  │
│    ]                                                           │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### NLP Intent Extraction

**LLM Prompt Structure:**
```python
prompt = f"""
You are a database query classifier for a college ERP system.
Tables: students, faculty, courses, departments, attendance, predictions, users.

Analyze the message and return JSON with:
- "intent": "READ", "CREATE", "UPDATE", "DELETE", or "ANALYZE"
- "entity": student, faculty, course, department, attendance, prediction, or user
- "filters": object with filters (use cgpa_lt for "less than", cgpa_gt for "greater than")
- "values": object for CREATE/UPDATE operations
- "aggregation": "count", "average", "sum", "min", "max", "group_by", or null
- "limit": number or null

User message: "{message}"

Return ONLY valid JSON.
"""
```

**Keyword Fallback Patterns:**
```python
# Intent detection
if any(w in msg for w in ["add", "create", "insert"]): intent = "CREATE"
if any(w in msg for w in ["update", "modify", "change"]): intent = "UPDATE"
if any(w in msg for w in ["delete", "remove"]): intent = "DELETE"
if any(w in msg for w in ["count", "average", "total"]): intent = "ANALYZE"

# Filter extraction
cgpa_lt = re.search(r'cgpa\s*(?:below|under|<)\s*([\d.]+)', msg)
semester = re.search(r'semester\s+(\d+)', msg)
department = re.search(r'(?:in|from)\s+([A-Z][a-z]+)\s+department', msg)
```

---

## 8. API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login with email/password → JWT |
| `GET` | `/api/auth/me` | Get current user from JWT |

### Students

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/students/` | List all students |
| `GET` | `/api/students/me` | Get current student's dashboard |
| `GET` | `/api/students/{id}` | Get student by ID |

### Faculty

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/faculty/` | List all faculty |
| `GET` | `/api/faculty/me` | Get current faculty's dashboard |
| `GET` | `/api/faculty/{id}/risk-roster` | Get at-risk students |

### Attendance

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/attendance/qr/generate` | Generate QR code (faculty) |
| `POST` | `/api/attendance/qr/mark` | Mark via QR scan (student) |
| `GET` | `/api/attendance/student/{id}` | Get student attendance |

### Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/predictions/student/{id}` | Get student predictions |
| `GET` | `/api/predictions/course/{id}` | Get course-wide predictions |

### Command Console (Ops AI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ops-ai/execute` | Execute operation from natural language |
| `POST` | `/api/ops-ai/rollback` | Rollback execution |
| `GET` | `/api/ops-ai/history` | Get audit history |
| `GET` | `/api/ops-ai/stats` | Get operation stats |

### Chatbot

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chatbot/` | Send chat message |

### Finance

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/finance/fees/{student_id}` | Get student fees |
| `GET` | `/api/finance/invoices/{student_id}` | Get student invoices |
| `POST` | `/api/finance/payments` | Record payment |

### HR

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/hr/employees` | List employees |
| `GET` | `/api/hr/salary/{employee_id}` | Get salary structure |
| `POST` | `/api/hr/payroll/generate` | Generate monthly payroll |

---

## 9. Authentication & Security

### JWT Flow

```
┌──────────┐    POST /api/auth/login     ┌──────────┐
│  Client  │ ─────────────────────────▶  │  Server  │
│          │  {email, password}          │          │
│          │                             │          │
│          │  ◀─────────────────────────  │          │
│          │  {access_token, role}       │          │
└──────────┘                             └──────────┘
     │
     │ Store token in localStorage
     │
     ▼
┌──────────┐    GET /api/students/me     ┌──────────┐
│  Client  │ ─────────────────────────▶  │  Server  │
│          │  Authorization: Bearer JWT  │          │
│          │                             │ Decode   │
│          │  ◀─────────────────────────  │ Verify   │
│          │  {student data}             │ Return   │
└──────────┘                             └──────────┘
```

### Password Security

```python
# Password hashing with bcrypt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### Role-Based Access Control

```python
# Dependency for protected routes
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Decode JWT → Extract user_id → Query database
    
def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)):
        if user.role.value not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker

# Usage
@router.get("/admin/stats")
async def admin_stats(user: User = Depends(require_role("admin"))):
    ...
```

---

## 10. Deployment

### Docker Compose Services

```yaml
services:
  db:           # PostgreSQL 16
    ports: ["5433:5432"]
    
  redis:        # Redis 7
    ports: ["6379:6379"]
    
  backend:      # FastAPI
    ports: ["8000:8000"]
    depends_on: [db, redis]
    
  frontend:     # React + Vite
    ports: ["5173:5173"]
    depends_on: [backend]
```

### Quick Start

```bash
# 1. Clone and navigate
cd project-expo

# 2. Create environment file
cat > backend/.env << EOF
DATABASE_URL=postgresql+asyncpg://campusiq:campusiq_secret@db:5432/campusiq
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
EOF

# 3. Start all services
docker compose up -d

# 4. View logs
docker logs campusiq-backend -f

# 5. Access application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@campusiq.edu` | `admin123` |
| Faculty | `faculty1@campusiq.edu` | `faculty123` |
| Student | `student1@campusiq.edu` | `student123` |

---

## 11. Environment Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing key | (required) |
| `GEMINI_API_KEY` | Google Gemini API key | (required for AI) |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash` |
| `OPS_CONFIDENCE_THRESHOLD` | Min confidence for execution | `0.75` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration | `480` |

### Frontend Environment Variables

| Variable | Description |
|----------|-------------|
| `VITE_API_PROXY_TARGET` | Backend URL for API proxy |

---

## File Structure Reference

```
project-expo/
├── docker-compose.yml           # Service orchestration
├── README.md                    # Project overview
├── DOCUMENTATION.md             # Full documentation
├── COMMAND_CONSOLE_AND_CHATBOT.md # AI features documentation
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── .env                     # Environment config
│   │
│   └── app/
│       ├── main.py              # FastAPI entry point
│       ├── seed_db.py           # Database seeding
│       │
│       ├── api/
│       │   ├── dependencies.py  # Auth dependencies
│       │   └── routes/          # API endpoints (18 routers)
│       │
│       ├── core/
│       │   ├── config.py        # Settings management
│       │   ├── database.py      # SQLAlchemy setup
│       │   └── security.py      # JWT + password utils
│       │
│       ├── models/
│       │   └── models.py        # SQLAlchemy ORM models (20+ tables)
│       │
│       ├── schemas/
│       │   └── schemas.py       # Pydantic schemas
│       │
│       ├── services/            # Business logic (8 services)
│       │   ├── gemini_pool_service.py
│       │   ├── conversational_ops_service.py
│       │   ├── nlp_crud_service.py
│       │   ├── chatbot_service.py
│       │   └── ...
│       │
│       └── ml/                  # Machine learning
│           ├── predict.py
│           ├── train.py
│           └── features.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── index.html
    │
    └── src/
        ├── main.jsx             # React entry
        ├── App.jsx              # Router + Auth
        │
        ├── context/
        │   └── AuthContext.jsx  # Auth state
        │
        ├── pages/               # 15 page components
        │   ├── StudentDashboard.jsx
        │   ├── FacultyConsole.jsx
        │   ├── CopilotPanel.jsx
        │   └── ...
        │
        ├── components/          # Shared components
        │   ├── Sidebar.jsx
        │   ├── ChatWidget.jsx
        │   └── ...
        │
        └── services/
            └── api.js           # HTTP client
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No LLM keys configured" | Add `GEMINI_API_KEY` to `backend/.env` |
| "JWT expired" | Login again to get new token |
| "Permission denied" | Check user role matches required access |
| "Database connection failed" | Ensure PostgreSQL container is running |
| "QR code expired" | Generate new QR (valid 10 minutes) |
| Container won't start | Check `docker logs <container>` |
| 500 Internal Server Error | Check backend logs for stack trace |

### Debug Commands

```bash
# Container status
docker compose ps

# Backend logs (live)
docker logs campusiq-backend -f

# Database access
docker exec -it campusiq-db psql -U campusiq

# Redis CLI
docker exec -it campusiq-redis redis-cli

# API health check
curl http://localhost:8000/health

# Run tests
docker exec campusiq-backend pytest -v
```

---

*CampusIQ Technical Documentation — Project Expo*
