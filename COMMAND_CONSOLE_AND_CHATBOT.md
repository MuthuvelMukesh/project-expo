# CampusIQ — Command Console & Chatbot Technical Documentation

> Deep technical dive into the AI-powered conversational interfaces

---

## Table of Contents

1. [Overview: Two AI Interfaces](#1-overview-two-ai-interfaces)
2. [LLM Client Architecture](#2-llm-client-architecture)
3. [Command Console (Copilot)](#3-command-console-copilot)
4. [Chatbot System](#4-chatbot-system)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Code Reference](#6-code-reference)

---

## 1. Overview: Two AI Interfaces

CampusIQ has **two distinct AI interfaces** that serve different purposes:

| Feature | Command Console (Copilot) | Chatbot |
|---------|--------------------------|---------|
| **Purpose** | Execute database operations | Answer questions conversationally |
| **Output** | Structured data + execute actions | Natural language responses |
| **Risk Handling** | Multi-level approval workflow | None (read-only) |
| **Audit Trail** | Full immutable audit log | None |
| **File** | `conversational_ops_service.py` | `chatbot_service.py` |

### Why Two Systems?

1. **Command Console** — For operational tasks like "Update all CSE students' semester to 4" which modify data and need approval workflows.

2. **Chatbot** — For conversational queries like "What is my attendance?" which only need quick responses with live data.

---

## 2. LLM Client Architecture

Both systems use a unified LLM client: `GeminiPoolClient`

### File: `backend/app/services/gemini_pool_service.py`

```
┌─────────────────────────────────────────────────────────────────┐
│                     LLM CLIENT ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                                           │
│  │  Application    │  Command Console or Chatbot               │
│  │  Layer          │  calls GeminiPoolClient methods           │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              GeminiPoolClient                        │       │
│  │                                                      │       │
│  │  • generate_json(module, prompt)  → for parsing     │       │
│  │  • generate_text(module, system, user) → for chat   │       │
│  └────────┬─────────────────────┬──────────────────────┘       │
│           │                     │                              │
│           ▼                     ▼                              │
│  ┌─────────────────┐   ┌─────────────────┐                    │
│  │  OpenRouter     │   │  Google Gemini  │                    │
│  │  (Primary)      │   │  (Fallback)     │                    │
│  │                 │   │                 │                    │
│  │  Model:         │   │  Model:         │                    │
│  │  liquid/lfm-2.5 │   │  gemini-2.0     │                    │
│  │  -1.2b-thinking │   │  -flash         │                    │
│  └─────────────────┘   └─────────────────┘                    │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Methods

**1. `generate_json(module, prompt)` — For NLP Parsing**

```python
async def generate_json(module: str, prompt: str, timeout: float = 25.0) -> dict:
    """
    Returns: {"ok": True, "text": "<raw JSON string>"} 
    
    Steps:
    1. Check if OpenRouter is configured (OPENROUTER_API_KEY exists)
    2. If yes → call OpenRouter with system prompt "Return only valid JSON"
    3. If OpenRouter fails or not configured → try Gemini keys
    4. If all fail → raise GeminiPoolError
    """
```

**2. `generate_text(module, system_prompt, user_message)` — For Chat**

```python
async def generate_text(
    module: str,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.4,
) -> str:
    """
    Returns: Plain text response string
    
    Steps:
    1. Check if OpenRouter is configured
    2. If yes → call with system prompt + user message
    3. If fails → try Gemini fallback
    4. Temperature 0.4 allows some creativity while staying factual
    """
```

### OpenRouter Request Format

```python
# OpenRouter uses OpenAI-compatible API format
payload = {
    "model": "liquid/lfm-2.5-1.2b-thinking:free",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ],
    "temperature": 0.1  # Low for JSON, 0.4 for chat
}

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://campusiq.edu",
    "X-Title": "CampusIQ"
}
```

---

## 3. Command Console (Copilot)

### Purpose

Convert natural language into **safe, auditable database operations** with approval workflows.

### Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                 COMMAND CONSOLE PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER INPUT: "Show all CSE students with CGPA below 6"          │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 1: INTENT EXTRACTION (_extract_intent)          │      │
│  │                                                       │      │
│  │ Uses LLM (OpenRouter/Gemini) with this prompt:       │      │
│  │                                                       │      │
│  │ "Extract a strict JSON object for ERP operations:    │      │
│  │  - intent: READ|CREATE|UPDATE|DELETE|ANALYZE         │      │
│  │  - entity: student|faculty|course|...                │      │
│  │  - filters: {department: "CSE", cgpa_lt: 6.0}        │      │
│  │  - values: {} (for CREATE/UPDATE)                    │      │
│  │  - confidence: 0.0-1.0                               │      │
│  │  - ambiguity: {is_ambiguous, fields, question}"      │      │
│  │                                                       │      │
│  │ FALLBACK: If LLM fails → _keyword_intent() uses      │      │
│  │           regex patterns for basic extraction        │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 2: CLARIFICATION CHECK (_clarification_needed)  │      │
│  │                                                       │      │
│  │ if confidence < 0.75 OR ambiguity.is_ambiguous:      │      │
│  │   return {                                            │      │
│  │     needs_clarification: true,                        │      │
│  │     question: "Please specify the department..."      │      │
│  │   }                                                   │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 3: PERMISSION GATE (_permission_gate)           │      │
│  │                                                       │      │
│  │ ROLE_MATRIX defines what each role can do:           │      │
│  │                                                       │      │
│  │ student:                                              │      │
│  │   READ: {student, course, department, attendance}    │      │
│  │   CREATE/UPDATE/DELETE: ❌ (restricted)              │      │
│  │                                                       │      │
│  │ faculty:                                              │      │
│  │   READ: all entities                                  │      │
│  │   CREATE: {attendance}                               │      │
│  │   UPDATE: {attendance, course}                       │      │
│  │   DELETE: ❌                                          │      │
│  │                                                       │      │
│  │ admin:                                                │      │
│  │   READ/CREATE/UPDATE/DELETE: all entities ✔          │      │
│  │                                                       │      │
│  │ Also checks department scope isolation               │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 4: IMPACT ESTIMATION (_estimate_impact)         │      │
│  │                                                       │      │
│  │ SELECT COUNT(*) FROM students                         │      │
│  │ WHERE department_id = X AND cgpa < 6.0               │      │
│  │                                                       │      │
│  │ Result: 12 records will be affected                  │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 5: RISK CLASSIFICATION (_classify_risk)         │      │
│  │                                                       │      │
│  │ LOW:  READ/ANALYZE operations                        │      │
│  │ MEDIUM: UPDATE/CREATE with <25 records               │      │
│  │ HIGH:                                                 │      │
│  │   - DELETE any records                                │      │
│  │   - Affects >25 records                               │      │
│  │   - Modifies salary/financial fields                  │      │
│  │   - User/permission modifications                     │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 6: PREVIEW GENERATION (_build_preview)          │      │
│  │                                                       │      │
│  │ {                                                     │      │
│  │   "affected_records": [                               │      │
│  │     {"id": 5, "roll": "CSE2023005", "cgpa": 5.8},    │      │
│  │     {"id": 12, "roll": "CSE2023012", "cgpa": 5.2}    │      │
│  │   ],                                                  │      │
│  │   "proposed_changes": [...],  // for UPDATE          │      │
│  │   "rollback_plan": {                                  │      │
│  │     "strategy": "before_state_snapshot",             │      │
│  │     "supports_rollback": true                        │      │
│  │   }                                                   │      │
│  │ }                                                     │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 7: PLAN STATUS DETERMINATION                     │      │
│  │                                                       │      │
│  │ LOW risk + READ + allowed → "ready_for_execution"    │      │
│  │ MEDIUM risk → "awaiting_confirmation"                │      │
│  │ HIGH risk → "awaiting_approval" (senior admin)       │      │
│  │ Needs clarification → "clarification_required"       │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 8: SAVE PLAN TO DATABASE                         │      │
│  │                                                       │      │
│  │ INSERT INTO operational_plans (                       │      │
│  │   plan_id, user_id, message, intent_type, entity,    │      │
│  │   filters, values, risk_level, status, preview...    │      │
│  │ )                                                     │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 9: CREATE AUDIT LOG (_audit)                     │      │
│  │                                                       │      │
│  │ INSERT INTO immutable_audit_logs (                    │      │
│  │   event_id, plan_id, user_id, role, operation_type,  │      │
│  │   event_type, risk_level, intent_payload             │      │
│  │ )                                                     │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 10: AUTO-EXECUTE IF READY                        │      │
│  │                                                       │      │
│  │ if status == "ready_for_execution":                  │      │
│  │   → execute_operational_plan()                       │      │
│  │   → Return results immediately                       │      │
│  │                                                       │      │
│  │ else:                                                 │      │
│  │   → Return plan for user confirmation/approval       │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Execution Pipeline (execute_operational_plan)

```
┌─────────────────────────────────────────────────────────────────┐
│              EXECUTION PIPELINE                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. LOAD PLAN from database                                     │
│       │                                                         │
│       ▼                                                         │
│  2. VALIDATE STATUS                                             │
│     - Not in clarification_required/rejected/escalated          │
│     - If requires_senior_approval → must be "approved"          │
│       │                                                         │
│       ▼                                                         │
│  3. CAPTURE BEFORE STATE                                        │
│     rows = SELECT * FROM entity WHERE filters                   │
│     before_state = [serialize each row to dict]                 │
│       │                                                         │
│       ▼                                                         │
│  4. EXECUTE BASED ON INTENT                                     │
│                                                                 │
│     READ/ANALYZE:                                               │
│       → No changes, just return before_state                    │
│                                                                 │
│     CREATE:                                                     │
│       → INSERT INTO entity (values)                             │
│       → after_state = [new row]                                 │
│                                                                 │
│     UPDATE:                                                     │
│       → for each row:                                           │
│           UPDATE entity SET key=value WHERE id=row.id           │
│       → after_state = [updated rows]                            │
│                                                                 │
│     DELETE:                                                     │
│       → for each row:                                           │
│           DELETE FROM entity WHERE id=row.id                    │
│       → after_state = []                                        │
│       │                                                         │
│       ▼                                                         │
│  5. UPDATE EXECUTION RECORD                                     │
│     execution.status = "executed"                               │
│     execution.before_state = [...]                              │
│     execution.after_state = [...]                               │
│       │                                                         │
│       ▼                                                         │
│  6. CREATE AUDIT LOG                                            │
│     Records complete before/after state for rollback            │
│       │                                                         │
│       ▼                                                         │
│  7. RETURN RESULT                                               │
│     {plan_id, execution_id, status, affected_count,             │
│      before_state, after_state}                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### LLM Prompt for Intent Extraction

```python
# File: conversational_ops_service.py → _extract_intent()

prompt = f"""
Extract a strict JSON object for ERP operations from this user message.
Return keys exactly:
intent: READ|CREATE|UPDATE|DELETE|ANALYZE|ESCALATE
entity: canonical lowercase singular entity
filters: object
scope: object
affected_fields: array of strings
values: object
confidence: float between 0 and 1
ambiguity: {{is_ambiguous: boolean, fields: array[string], question: string|null}}

Message: {message}
"""
```

### Entity Registry

```python
ENTITY_REGISTRY = {
    "student": {
        "model": Student,
        "fields": ["roll_number", "semester", "section", "cgpa", "admission_year"],
        "module": "nlp"
    },
    "faculty": {
        "model": Faculty,
        "fields": ["employee_id", "designation", "department_id"],
        "module": "hr"
    },
    "course": {
        "model": Course,
        "fields": ["code", "name", "semester", "credits", "department_id"],
        "module": "nlp"
    },
    # ... more entities
}
```

### Role Permission Matrix

```python
ROLE_MATRIX = {
    "student": {
        "READ": {"student", "course", "department", "attendance", "prediction"},
        "ANALYZE": {"attendance", "prediction"},
        "CREATE": set(),        # ❌ Cannot create
        "UPDATE": {"student"},  # Only self
        "DELETE": set(),        # ❌ Cannot delete
    },
    "faculty": {
        "READ": {"student", "course", "department", "attendance", "prediction"},
        "ANALYZE": {"student", "course", "attendance", "prediction"},
        "CREATE": {"attendance"},
        "UPDATE": {"attendance", "course"},
        "DELETE": set(),        # ❌ Cannot delete
    },
    "admin": {
        "READ": all_entities,
        "ANALYZE": all_entities,
        "CREATE": all_entities,
        "UPDATE": all_entities,
        "DELETE": all_entities,  # ✔ Full access
    },
}
```

---

## 4. Chatbot System

### Purpose

Provide **conversational responses** with live user context, without modifying data.

### Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHATBOT PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER INPUT: "What is my attendance percentage?"                │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ STEP 1: ROUTE DETECTION (_is_data_query)             │      │
│  │                                                       │      │
│  │ Check if message matches CRUD patterns:              │      │
│  │                                                       │      │
│  │ _CRUD_VERB_PATTERNS = [                              │      │
│  │   r"\b(show|list|display|fetch|get|find)\b.+"       │      │
│  │     r"\b(student|faculty|course)s?\b",              │      │
│  │   r"\b(how many|count|total)\b.+\b(student)s?\b",   │      │
│  │   r"\b(add|create|insert)\b.+\b(student)s?\b",      │      │
│  │   r"\bmy (attendance|cgpa|predictions?)\b",         │      │
│  │   ...                                                │      │
│  │ ]                                                    │      │
│  │                                                       │      │
│  │ "What is my attendance?" → matches "my attendance"  │      │
│  │ → is_data_query = True                               │      │
│  └───────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│           ┌──────────────┴──────────────┐                      │
│           │                             │                       │
│     [Data Query]               [Conversational Query]           │
│           │                             │                       │
│           ▼                             ▼                       │
│  ┌─────────────────┐          ┌─────────────────────────┐      │
│  │ ROUTE TO        │          │ STEP 2: BUILD USER      │      │
│  │ NLP CRUD ENGINE │          │ CONTEXT                 │      │
│  │                 │          │ (_build_user_context)   │      │
│  │ process_nlp_crud│          │                         │      │
│  │ (message, role, │          │ For student:            │      │
│  │  user_id, db)   │          │ - Roll number           │      │
│  │                 │          │ - Semester, CGPA        │      │
│  │ Returns:        │          │ - Attendance per course │      │
│  │ {summary, data} │          │ - Latest predictions    │      │
│  └────────┬────────┘          │                         │      │
│           │                   │ For faculty:            │      │
│           │                   │ - Employee ID           │      │
│           │                   │ - Courses teaching      │      │
│           │                   └────────────┬────────────┘      │
│           │                                │                    │
│           │                                ▼                    │
│           │                   ┌─────────────────────────┐      │
│           │                   │ STEP 3: BUILD SYSTEM    │      │
│           │                   │ PROMPT                  │      │
│           │                   │                         │      │
│           │                   │ "You are CampusIQ AI.   │      │
│           │                   │                         │      │
│           │                   │  Role: student          │      │
│           │                   │                         │      │
│           │                   │  Live data:             │      │
│           │                   │  - Roll: CSE2023001     │      │
│           │                   │  - CGPA: 8.72           │      │
│           │                   │  - Attendance:          │      │
│           │                   │    CS301: 45/52 = 86%   │      │
│           │                   │    CS302: 38/45 = 84%   │      │
│           │                   │                         │      │
│           │                   │  Guidelines:            │      │
│           │                   │  - Use exact numbers    │      │
│           │                   │  - Don't make up data"  │      │
│           │                   └────────────┬────────────┘      │
│           │                                │                    │
│           │                                ▼                    │
│           │                   ┌─────────────────────────┐      │
│           │                   │ STEP 4: QUERY LLM       │      │
│           │                   │ (_query_gemini)         │      │
│           │                   │                         │      │
│           │                   │ GeminiPoolClient        │      │
│           │                   │   .generate_text(       │      │
│           │                   │     module="chat",      │      │
│           │                   │     system_prompt=...,  │      │
│           │                   │     user_message=...,   │      │
│           │                   │     temperature=0.4     │      │
│           │                   │   )                     │      │
│           │                   └────────────┬────────────┘      │
│           │                                │                    │
│           │                                ▼                    │
│           │                   ┌─────────────────────────┐      │
│           │                   │ STEP 5: RULE-BASED      │      │
│           │                   │ FALLBACK (if LLM fails) │      │
│           │                   │                         │      │
│           │                   │ Check _KNOWLEDGE_BASE   │      │
│           │                   │ for keyword matches:    │      │
│           │                   │ "attendance" → tips     │      │
│           │                   │ "predict" → explanation │      │
│           │                   │ "risk" → score meaning  │      │
│           │                   └────────────┬────────────┘      │
│           │                                │                    │
│           └────────────────────────────────┤                    │
│                                            │                    │
│                                            ▼                    │
│                            ┌─────────────────────────────┐     │
│                            │ RETURN RESPONSE             │     │
│                            │                             │     │
│                            │ {                           │     │
│                            │   "response": "Your current│     │
│                            │     attendance is 86%...", │     │
│                            │   "sources": ["CampusIQ    │     │
│                            │     AI (Gemini)"],         │     │
│                            │   "suggested_actions": [   │     │
│                            │     "Show attendance       │     │
│                            │      details",             │     │
│                            │     "Which course has      │     │
│                            │      lowest attendance?"   │     │
│                            │   ]                        │     │
│                            │ }                          │     │
│                            └─────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Context Building

The chatbot fetches **live data** from the database to inject into the LLM prompt:

```python
async def _build_user_context(user_id: int, user_role: str, db: AsyncSession) -> str:
    """Fetch live stats about the current user so LLM can give specific answers."""
    lines = []
    
    if user_role == "student":
        # Get student record
        stu = await db.execute(select(Student).where(Student.user_id == user_id))
        student = stu.scalar_one_or_none()
        
        if student:
            lines.append(f"Student roll number: {student.roll_number}")
            lines.append(f"Semester: {student.semester}, Section: {student.section}")
            lines.append(f"CGPA: {student.cgpa}")
            
            # Get attendance per course
            for course in student_courses:
                total = COUNT(attendance WHERE student_id = stu.id)
                present = COUNT(attendance WHERE is_present = True)
                pct = round(present / total * 100, 1)
                lines.append(f"  {course.code}: {present}/{total} = {pct}%")
            
            # Get predictions
            for pred in student_predictions:
                risk_label = "high" if pred.risk_score > 0.6 else "medium"
                lines.append(f"  {course.code}: predicted {pred.predicted_grade}, risk {risk_label}")
    
    elif user_role == "faculty":
        # Get faculty courses
        lines.append(f"Teaching {len(courses)} courses: CS301, CS302, ...")
    
    return "\n".join(lines)
```

### System Prompt Construction

```python
def _build_system_prompt(user_role: str, user_context: str) -> str:
    return (
        f"You are CampusIQ, the AI assistant embedded in a college ERP system.\n\n"
        f"Role of the current user: {user_role}\n\n"
        f"Live data about this user:\n{user_context}\n\n"
        "Guidelines:\n"
        "- Answer concisely (3-6 sentences max) unless the question needs more detail.\n"
        "- When the user asks about their attendance, grades, or predictions, use the live data above.\n"
        "- If the answer is in the live data, reference the exact numbers.\n"
        "- If you don't know something, say so and suggest which dashboard section might help.\n"
        "- Use markdown formatting (bold, bullets) for readability.\n"
        "- Do NOT make up numbers that are not in the live data section above.\n"
        "- For operational tasks (creating/updating/deleting records), suggest using the Command Console."
    )
```

### Rule-Based Fallback (No LLM)

When LLM is unavailable, the chatbot uses a knowledge base:

```python
_KNOWLEDGE_BASE = {
    "attendance": (
        "**Attendance:** Check your attendance on the Student Dashboard. "
        "Each course shows your percentage and how many more classes you need for 75%."
    ),
    "predict": (
        "**Grade Predictions:** CampusIQ uses an XGBoost ML model trained on "
        "attendance, assignments, quizzes, and CGPA to predict your grade."
    ),
    "risk": (
        "**Risk Score:** Your risk score (0-1) indicates probability of academic difficulty. "
        "A score above 0.6 is flagged as high risk."
    ),
    "qr": (
        "**QR Attendance:** Your faculty generates a time-limited QR code in class. "
        "Scan it with CampusIQ and attendance is marked instantly."
    ),
    "copilot": (
        "**Command Console:** Use the Command Console to manage the ERP with natural language. "
        "Try: *Show all CSE students with CGPA above 8*"
    ),
}

def _rule_based_response(message: str, user_role: str) -> str:
    msg = message.lower()
    for keyword, response in _KNOWLEDGE_BASE.items():
        if keyword in msg:
            return response
    # Default help message based on role
    return role_specific_help_text
```

---

## 5. Data Flow Diagrams

### Command Console Flow

```
User → POST /api/ops-ai/plan → create_operational_plan()
                                    │
                                    ├── _extract_intent() → LLM
                                    ├── _permission_gate()
                                    ├── _estimate_impact()
                                    ├── _classify_risk()
                                    ├── _build_preview()
                                    └── Save OperationalPlan
                                    │
                                    ▼
                          [Status: ready_for_execution?]
                                    │
               YES ─────────────────┴───────────────── NO
                │                                       │
                ▼                                       ▼
     execute_operational_plan()              Return plan for
                │                            user confirmation
                ├── Load before_state
                ├── Execute SQL
                ├── Save after_state
                ├── Create audit log
                └── Return results
```

### Chatbot Flow

```
User → POST /api/chatbot/ → process_query()
                                │
                                ├── _is_data_query(message)
                                │         │
                    ┌───────────┴─────────┴───────────┐
                 [YES]                              [NO]
                    │                                 │
                    ▼                                 ▼
           process_nlp_crud()              _build_user_context()
           (NLP CRUD Engine)                        │
                    │                               ▼
                    │                      _query_gemini()
                    │                               │
                    │                    ┌──────────┴──────────┐
                    │                 [Success]            [Failure]
                    │                    │                     │
                    │                    ▼                     ▼
                    │              Return LLM         _rule_based_response()
                    │              response
                    │                    │                     │
                    └────────────────────┼─────────────────────┘
                                         │
                                         ▼
                               Return to user with
                               suggested_actions[]
```

---

## 6. Code Reference

### File Locations

| Component | File Path |
|-----------|-----------|
| Command Console Service | `backend/app/services/conversational_ops_service.py` |
| NLP CRUD Engine | `backend/app/services/nlp_crud_service.py` |
| Chatbot Service | `backend/app/services/chatbot_service.py` |
| LLM Client | `backend/app/services/gemini_pool_service.py` |
| API Routes - Ops | `backend/app/api/routes/operational_ai.py` |
| API Routes - Chat | `backend/app/api/routes/chatbot.py` |
| Models | `backend/app/models/models.py` |

### Key Functions Summary

**conversational_ops_service.py**
| Function | Purpose |
|----------|---------|
| `create_operational_plan()` | Main entry point - creates plan from NL |
| `execute_operational_plan()` | Execute approved/ready plan |
| `add_approval_decision()` | Handle senior approval for HIGH risk |
| `_extract_intent()` | Call LLM for intent parsing |
| `_keyword_intent()` | Fallback regex-based parser |
| `_permission_gate()` | Check role + department permissions |
| `_classify_risk()` | Determine LOW/MEDIUM/HIGH risk |
| `_build_preview()` | Generate affected records preview |
| `_audit()` | Create immutable audit log entry |

**chatbot_service.py**
| Function | Purpose |
|----------|---------|
| `process_query()` | Main entry point |
| `_is_data_query()` | Route to CRUD or chat |
| `_build_user_context()` | Fetch live data for prompt |
| `_query_gemini()` | Call LLM for response |
| `_rule_based_response()` | Fallback without LLM |

**gemini_pool_service.py**
| Function | Purpose |
|----------|---------|
| `generate_json()` | LLM call for JSON output |
| `generate_text()` | LLM call for prose output |
| `_openrouter_request()` | Make OpenRouter API call |
| `_use_openrouter()` | Check if OpenRouter configured |

### Database Tables

```sql
-- Command Console stores plans here
CREATE TABLE operational_plans (
    id SERIAL PRIMARY KEY,
    plan_id VARCHAR UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    message TEXT,                -- Original NL input
    intent_type VARCHAR,         -- READ/CREATE/UPDATE/DELETE/ANALYZE
    entity VARCHAR,              -- student/faculty/course/etc
    filters JSONB,               -- {department: "CSE", cgpa_lt: 6.0}
    values JSONB,                -- For CREATE/UPDATE
    confidence FLOAT,            -- LLM confidence 0-1
    risk_level VARCHAR,          -- LOW/MEDIUM/HIGH
    status VARCHAR,              -- ready_for_execution/awaiting_approval/etc
    preview JSONB,               -- Affected records preview
    rollback_plan JSONB,         -- How to undo
    created_at TIMESTAMP
);

-- Executions with before/after state
CREATE TABLE operational_executions (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR UNIQUE,
    plan_id VARCHAR REFERENCES operational_plans(plan_id),
    executed_by INTEGER,
    status VARCHAR,
    before_state JSONB,          -- Snapshot before changes
    after_state JSONB,           -- Snapshot after changes
    executed_at TIMESTAMP
);

-- Immutable audit log for compliance
CREATE TABLE immutable_audit_logs (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR UNIQUE,
    plan_id VARCHAR,
    execution_id VARCHAR,
    user_id INTEGER,
    role VARCHAR,
    operation_type VARCHAR,      -- READ/CREATE/UPDATE/DELETE
    event_type VARCHAR,          -- intent_extracted/executed/approved/rejected
    risk_level VARCHAR,
    intent_payload JSONB,
    before_state JSONB,
    after_state JSONB,
    created_at TIMESTAMP
);
```

---

## API Testing Examples

### Command Console

**Create a plan:**
```bash
curl -X POST http://localhost:8000/api/ops-ai/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Show all CSE students with CGPA below 6", "module": "nlp"}'
```

**Execute a plan:**
```bash
curl -X POST http://localhost:8000/api/ops-ai/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "ops_abc123def456"}'
```

### Chatbot

**Send message:**
```bash
curl -X POST http://localhost:8000/api/chatbot/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my attendance percentage?"}'
```

---

*Technical Documentation for CampusIQ Project Expo*
