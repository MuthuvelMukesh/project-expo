"""
CampusIQ — Chatbot Service  (v2 – context-aware, robust routing)

Key improvements over v1:
  1. Errors are logged, not silently swallowed.
  2. LLM prompt injects live student/faculty context (attendance, CGPA, predictions).
  3. Routing uses an intent-confidence check instead of a flat keyword match—
     only routes to the NLP-CRUD engine when the message is clearly a data command.
  4. Fallback responses are richer with role-specific guidance and markdown tips.
  5. Ollama is always tried first for general chat; rule-based is true last resort.
"""

import logging
import httpx
import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import get_settings
from app.models.models import Student, Faculty, Course, Attendance, Prediction, User
from app.services.nlp_crud_service import process_nlp_crud

settings = get_settings()
log = logging.getLogger("campusiq.chatbot")


# ─── Intent detection ──────────────────────────────────────────

# Only route to CRUD engine when the message is clearly an *imperative data
# command*.  Phrases like "what is attendance" or "how does grading work" should
# NOT be routed as data queries.
_CRUD_VERB_PATTERNS = [
    # explicit data-fetch verbs followed by entity hints
    r"\b(show|list|display|fetch|get|find)\b.+\b(student|faculty|course|department|user|attendance|prediction|record)s?\b",
    # count / aggregate
    r"\b(how many|count|total)\b.+\b(student|faculty|course|department|user)s?\b",
    r"\b(average|avg|sum|minimum|maximum|highest|lowest|top)\b.+\b(cgpa|gpa|attendance|grade|score|mark)s?\b",
    # CUD
    r"\b(add|create|insert|register|new)\b.+\b(student|faculty|course|department|user)s?\b",
    r"\b(update|change|modify|set|edit)\b.+\b(student|faculty|course|department|user)s?\b",
    r"\b(delete|remove|drop)\b.+\b(student|faculty|course|department|user)s?\b",
    # "my" data requests that clearly want live data
    r"\bmy (attendance|cgpa|gpa|grades?|predictions?|profile|details|records?|schedule|courses?)\b",
    # explicit analysis
    r"\b(group by|distribution|analyze|stats|statistics)\b",
    # "all X" pattern
    r"\ball (students?|faculty|courses?|departments?|users?)\b",
]

_CRUD_RE = re.compile("|".join(_CRUD_VERB_PATTERNS), re.IGNORECASE)


def _is_data_query(message: str) -> bool:
    """Return True only when we're confident the message is a data/CRUD command."""
    return bool(_CRUD_RE.search(message))


# ─── User context builder ──────────────────────────────────────

async def _build_user_context(user_id: int, user_role: str, db: AsyncSession) -> str:
    """Fetch live stats about the current user so the LLM can give specific answers."""
    lines: list[str] = []
    try:
        if user_role == "student":
            stu_res = await db.execute(select(Student).where(Student.user_id == user_id))
            stu = stu_res.scalar_one_or_none()
            if stu:
                lines.append(f"Student roll number: {stu.roll_number}")
                lines.append(f"Semester: {stu.semester}, Section: {stu.section or 'N/A'}")
                lines.append(f"CGPA: {stu.cgpa}")

                # Per-course attendance stats
                courses_res = await db.execute(
                    select(Course).where(
                        Course.department_id == stu.department_id,
                        Course.semester == stu.semester,
                    )
                )
                courses = courses_res.scalars().all()
                att_summaries = []
                for c in courses[:6]:
                    total_res = await db.execute(
                        select(func.count(Attendance.id)).where(
                            Attendance.student_id == stu.id,
                            Attendance.course_id == c.id,
                        )
                    )
                    total = total_res.scalar() or 0
                    present_res = await db.execute(
                        select(func.count(Attendance.id)).where(
                            Attendance.student_id == stu.id,
                            Attendance.course_id == c.id,
                            Attendance.is_present == True,
                        )
                    )
                    present = present_res.scalar() or 0
                    pct = round(present / total * 100, 1) if total else 0
                    att_summaries.append(f"  {c.code} ({c.name}): {present}/{total} = {pct}%")

                if att_summaries:
                    lines.append("Attendance per course:")
                    lines.extend(att_summaries)

                # Latest predictions
                pred_res = await db.execute(
                    select(Prediction, Course.name, Course.code)
                    .join(Course, Prediction.course_id == Course.id, isouter=True)
                    .where(Prediction.student_id == stu.id)
                    .order_by(Prediction.created_at.desc())
                    .limit(6)
                )
                preds = pred_res.all()
                if preds:
                    lines.append("Latest grade predictions:")
                    for pred, cname, ccode in preds:
                        risk_label = "high" if pred.risk_score > 0.6 else "medium" if pred.risk_score > 0.3 else "low"
                        lines.append(f"  {ccode}: predicted {pred.predicted_grade}, risk {risk_label} ({pred.risk_score:.0%})")

        elif user_role == "faculty":
            fac_res = await db.execute(select(Faculty).where(Faculty.user_id == user_id))
            fac = fac_res.scalar_one_or_none()
            if fac:
                lines.append(f"Faculty employee ID: {fac.employee_id}")
                lines.append(f"Designation: {fac.designation or 'N/A'}")
                course_res = await db.execute(
                    select(Course).where(Course.instructor_id == fac.id)
                )
                courses = course_res.scalars().all()
                if courses:
                    lines.append(f"Teaching {len(courses)} courses: " + ", ".join(f"{c.code} ({c.name})" for c in courses))

    except Exception as e:
        log.warning("Failed to build user context: %s", e)

    return "\n".join(lines) if lines else "No additional user data available."


# ─── LLM call ──────────────────────────────────────────────────

async def _query_ollama(
    message: str,
    user_role: str,
    user_context: str,
) -> Optional[str]:
    """Query Ollama with a rich, context-injected prompt."""
    system_prompt = f"""You are **CampusIQ**, the AI assistant embedded in a college ERP system.

Role of the current user: **{user_role}**

Live data about this user:
{user_context}

Guidelines:
- Answer concisely (3-6 sentences max) unless the question needs more detail.
- When the user asks about *their* attendance, grades, or predictions, use the live data above to give a specific, personalised answer.
- If the answer is definitively in the live data, reference the exact numbers.
- If you genuinely don't know something, say so and suggest which dashboard section might help.
- Use markdown formatting (bold, bullets) for readability.
- Do NOT make up numbers that are not in the live data section above."""

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.4},
                },
            )

            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "").strip()
                if content:
                    return content
                log.warning("Ollama returned empty content for: %s", message[:80])
            else:
                log.error("Ollama HTTP %s — %s", resp.status_code, resp.text[:200])

    except httpx.ConnectError:
        log.info("Ollama not reachable — falling back to rule-based.")
    except httpx.TimeoutException:
        log.warning("Ollama timed out for: %s", message[:80])
    except Exception as e:
        log.error("Unexpected Ollama error: %s", e, exc_info=True)

    return None


# ─── Main entry point ──────────────────────────────────────────

async def process_query(
    message: str,
    user_role: str,
    user_id: int,
    db: AsyncSession = None,
) -> dict:
    """Process a natural language query using NLP CRUD engine or LLM chat."""

    # ── 1.  Try NLP CRUD engine for clear data commands ──
    if db and _is_data_query(message):
        try:
            crud_result = await process_nlp_crud(
                message=message,
                user_role=user_role,
                user_id=user_id,
                db=db,
            )

            response_text = crud_result["summary"]

            # append a markdown table when we have data
            raw_data = (crud_result.get("result") or {}).get("data")
            if raw_data and len(raw_data) > 0:
                headers = list(raw_data[0].keys())
                table = [" | ".join(headers), " | ".join(["---"] * len(headers))]
                for row in raw_data[:20]:
                    table.append(" | ".join(str(row.get(h, "")) for h in headers))
                response_text += "\n\n" + "\n".join(table)
                if len(raw_data) > 20:
                    response_text += f"\n\n*...and {len(raw_data) - 20} more records*"

            return {
                "response": response_text,
                "sources": ["CampusIQ AI Data Engine"],
                "suggested_actions": _get_data_actions(crud_result),
            }

        except Exception as e:
            log.error("NLP CRUD engine failed: %s", e, exc_info=True)
            # We still fall through to the LLM – NOT silently lost anymore.

    # ── 2.  Build user-specific context for the LLM ──
    user_context = "No session context available."
    if db:
        user_context = await _build_user_context(user_id, user_role, db)

    # ── 3.  Ask the LLM with full context ──
    llm_response = await _query_ollama(message, user_role, user_context)
    if llm_response:
        return {
            "response": llm_response,
            "sources": ["CampusIQ AI (Local LLM)"],
            "suggested_actions": _get_suggested_actions(message, user_role),
        }

    # ── 4.  Rule-based fallback (last resort) ──
    response = _rule_based_response(message, user_role)
    return {
        "response": response,
        "sources": ["CampusIQ Knowledge Base (offline)"],
        "suggested_actions": _get_suggested_actions(message, user_role),
    }


# ─── Rule-based fallback ───────────────────────────────────────

_KNOWLEDGE_BASE = {
    "attendance": (
        "📊 **Attendance:** Check your attendance on the **Student Dashboard**. "
        "Each course shows your percentage, status (safe/warning/danger), and "
        "how many more classes you need for 75%. You can also visit the "
        "**Attendance Details** page for a per-date heatmap calendar."
    ),
    "predict": (
        "🔮 **Grade Predictions:** CampusIQ uses an XGBoost ML model trained on "
        "attendance, assignments, quizzes, labs, and CGPA to predict your likely "
        "exam grade. Each prediction includes SHAP explanations of which factors "
        "matter most. See the **Predictions** section on your dashboard."
    ),
    "risk": (
        "⚠️ **Risk Score:** Your risk score (0–1) indicates the probability of "
        "academic difficulty. A score above 0.6 is flagged as **high risk** and "
        "triggers alerts to your mentor. The SHAP factors show exactly which "
        "areas need improvement."
    ),
    "qr": (
        "📱 **QR Attendance:** Your faculty generates a time-limited QR code in "
        "class (expires in ~90 seconds). Open CampusIQ → scan the QR → attendance "
        "is marked instantly. Each code is single-use and validated against the "
        "class schedule."
    ),
    "grade": (
        "📝 **Grading:** Grades are predicted using ML models trained on historical "
        "campus data. The prediction includes a confidence score and the top "
        "factors influencing your grade."
    ),
    "copilot": (
        "🤖 **AI Copilot:** Use the Copilot panel to manage the ERP with natural "
        "language. Try: *'Show all CSE students with CGPA above 8'* or *'Create "
        "a new course CS601'*. Destructive actions require confirmation."
    ),
    "timetable": (
        "📅 **Timetable:** View your weekly schedule on the **Timetable** page. "
        "It shows a colour-coded grid of lectures, labs, and tutorials with rooms "
        "and instructor names."
    ),
}


def _rule_based_response(message: str, user_role: str) -> str:
    """Keyword-match against the knowledge base, with role-aware defaults."""
    msg = message.lower()

    for keyword, response in _KNOWLEDGE_BASE.items():
        if keyword in msg:
            return response

    # Role-specific help menu
    if user_role == "student":
        return (
            "👋 Hi! I'm CampusIQ AI. Here's what I can help you with:\n\n"
            "• **My attendance** — ask about your attendance percentage\n"
            "• **My predictions** — see your predicted grades\n"
            "• **Risk score** — understand your academic risk\n"
            "• **Timetable** — view your class schedule\n"
            "• **QR attendance** — how to scan & mark attendance\n\n"
            "💡 Try asking: *'What is my attendance?'* or *'Am I at risk?'*"
        )
    elif user_role == "faculty":
        return (
            "👋 Hi! I'm CampusIQ AI. I can help you with:\n\n"
            "• **My courses** — your teaching load\n"
            "• **Risk roster** — students at academic risk\n"
            "• **Attendance analytics** — class attendance trends\n"
            "• **Data queries** — ask about students, grades, or departments\n\n"
            "💡 Try: *'Show students at risk in CS301'* or *'Average attendance for my courses'*"
        )
    else:
        return (
            "👋 Hi! I'm CampusIQ AI. As an admin, you can:\n\n"
            "• **Manage records** — users, courses, departments\n"
            "• **Campus analytics** — enrollment, risk, attendance trends\n"
            "• **AI Data queries** — natural language database queries\n"
            "• **Copilot** — multi-step operations via natural language\n\n"
            "💡 Try: *'How many students are there?'* or *'Show all departments'*"
        )


# ─── Suggested actions generator ───────────────────────────────

def _get_data_actions(crud_result: dict) -> list:
    """Follow-up actions based on CRUD result."""
    intent = crud_result.get("intent", "")
    entity = crud_result.get("entity", "").lower()

    actions = []
    if intent == "READ":
        actions = [f"Analyze {entity} statistics", f"Count total {entity}s", f"Filter {entity}s by department"]
    elif intent == "ANALYZE":
        actions = [f"Show all {entity}s", "Group by department", "Show top performers"]
    elif intent in ("CREATE", "UPDATE", "DELETE"):
        actions = [f"Show all {entity}s", f"Count {entity}s"]
    return actions[:3]


def _get_suggested_actions(message: str, user_role: str) -> list:
    """Contextual suggested follow-up actions."""
    msg = message.lower()
    actions = []

    if "attendance" in msg:
        actions.extend(["Show my attendance details", "Which course has lowest attendance?"])
    if "grade" in msg or "predict" in msg:
        actions.extend(["Show my predictions", "What can I do to improve?"])
    if "risk" in msg:
        actions.extend(["Show improvement suggestions", "View risk factors"])

    if not actions:
        if user_role == "student":
            actions = ["What is my attendance?", "Show my predictions", "Am I at risk?"]
        elif user_role == "faculty":
            actions = ["Show at-risk students", "My course analytics", "Attendance trend"]
        else:
            actions = ["Campus overview", "Show all departments", "Count students"]

    return actions[:3]
