"""
CampusIQ — Chatbot Service  (v3 – Gemini-only, context-aware)

All LLM calls route exclusively through the Gemini key-pool client.
Ollama dependency removed. Rule-based fallback kept as last resort.
"""

import logging
import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import get_settings
from app.models.models import Student, Faculty, Course, Attendance, Prediction, User
from app.services.nlp_crud_service import process_nlp_crud
from app.services.gemini_pool_service import GeminiPoolClient, GeminiPoolError

settings = get_settings()
log = logging.getLogger("campusiq.chatbot")


# ─── Intent detection ──────────────────────────────────────────

# Only route to CRUD engine when message is clearly an imperative data command.
_CRUD_VERB_PATTERNS = [
    r"\b(show|list|display|fetch|get|find)\b.+\b(student|faculty|course|department|user|attendance|prediction|record)s?\b",
    r"\b(how many|count|total)\b.+\b(student|faculty|course|department|user)s?\b",
    r"\b(average|avg|sum|minimum|maximum|highest|lowest|top)\b.+\b(cgpa|gpa|attendance|grade|score|mark)s?\b",
    r"\b(add|create|insert|register|new)\b.+\b(student|faculty|course|department|user)s?\b",
    r"\b(update|change|modify|set|edit)\b.+\b(student|faculty|course|department|user)s?\b",
    r"\b(delete|remove|drop)\b.+\b(student|faculty|course|department|user)s?\b",
    r"\bmy (attendance|cgpa|gpa|grades?|predictions?|profile|details|records?|schedule|courses?)\b",
    r"\b(group by|distribution|analyze|stats|statistics)\b",
    r"\ball (students?|faculty|courses?|departments?|users?)\b",
]
_CRUD_RE = re.compile("|".join(_CRUD_VERB_PATTERNS), re.IGNORECASE)


def _is_data_query(message: str) -> bool:
    """Return True only when we're confident the message is a data/CRUD command."""
    return bool(_CRUD_RE.search(message))


# ─── User context builder ──────────────────────────────────────

async def _build_user_context(user_id: int, user_role: str, db: AsyncSession) -> str:
    """Fetch live stats about the current user so Gemini can give specific answers."""
    lines: list[str] = []
    try:
        if user_role == "student":
            stu_res = await db.execute(select(Student).where(Student.user_id == user_id))
            stu = stu_res.scalar_one_or_none()
            if stu:
                lines.append(f"Student roll number: {stu.roll_number}")
                lines.append(f"Semester: {stu.semester}, Section: {stu.section or 'N/A'}")
                lines.append(f"CGPA: {stu.cgpa}")

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


# ─── Gemini chat call ──────────────────────────────────────────

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


async def _query_gemini(message: str, user_role: str, user_context: str) -> Optional[str]:
    """Query Gemini via key pool for a conversational response."""
    try:
        return await GeminiPoolClient.generate_text(
            module="chat",
            system_prompt=_build_system_prompt(user_role, user_context),
            user_message=message,
            temperature=0.4,
        )
    except GeminiPoolError as e:
        log.warning("Gemini chat pool error: %s (code=%s)", e.message, e.code)
        return None
    except Exception as e:
        log.error("Unexpected Gemini error in chatbot: %s", e, exc_info=True)
        return None


# ─── Main entry point ──────────────────────────────────────────

async def process_query(
    message: str,
    user_role: str,
    user_id: int,
    db: AsyncSession = None,
) -> dict:
    """Process a natural language query using the NLP CRUD engine or Gemini chat."""

    # 1. Route clear data commands to the NLP CRUD engine
    if db and _is_data_query(message):
        try:
            crud_result = await process_nlp_crud(
                message=message,
                user_role=user_role,
                user_id=user_id,
                db=db,
            )

            response_text = crud_result["summary"]
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
                "sources": ["CampusIQ Data Engine"],
                "suggested_actions": _get_data_actions(crud_result),
            }
        except Exception as e:
            log.error("NLP CRUD engine failed: %s", e, exc_info=True)

    # 2. Build user-specific context for Gemini
    user_context = "No session context available."
    if db:
        user_context = await _build_user_context(user_id, user_role, db)

    # 3. Query Gemini
    llm_response = await _query_gemini(message, user_role, user_context)
    if llm_response:
        return {
            "response": llm_response,
            "sources": ["CampusIQ AI (Gemini)"],
            "suggested_actions": _get_suggested_actions(message, user_role),
        }

    # 4. Rule-based fallback — no LLM dependency
    return {
        "response": _rule_based_response(message, user_role),
        "sources": ["CampusIQ Knowledge Base"],
        "suggested_actions": _get_suggested_actions(message, user_role),
    }


# ─── Rule-based fallback ───────────────────────────────────────

_KNOWLEDGE_BASE = {
    "attendance": (
        "**Attendance:** Check your attendance on the Student Dashboard. "
        "Each course shows your percentage and how many more classes you need for 75%. "
        "Visit **Attendance Details** for a per-date calendar view."
    ),
    "predict": (
        "**Grade Predictions:** CampusIQ uses an XGBoost ML model trained on "
        "attendance, assignments, quizzes, and CGPA to predict your grade. "
        "Each prediction includes SHAP explainability. See the Predictions section on your dashboard."
    ),
    "risk": (
        "**Risk Score:** Your risk score (0-1) indicates probability of academic difficulty. "
        "A score above 0.6 is flagged as high risk. "
        "The SHAP factors show exactly which areas need improvement."
    ),
    "qr": (
        "**QR Attendance:** Your faculty generates a time-limited QR code in class. "
        "Open CampusIQ, scan the QR, and attendance is marked instantly. "
        "Each code is single-use and validated against the class schedule."
    ),
    "grade": (
        "**Grading:** Grades are predicted using ML models trained on historical campus data. "
        "Each prediction includes a confidence score and the top contributing factors."
    ),
    "copilot": (
        "**Command Console:** Use the Command Console to manage the ERP with natural language. "
        "Try: *Show all CSE students with CGPA above 8* or *Generate payroll summary*. "
        "High-risk actions require confirmation before execution."
    ),
    "timetable": (
        "**Timetable:** View your weekly schedule on the Timetable page. "
        "It shows a colour-coded grid of lectures, labs, and tutorials with rooms and instructor names."
    ),
}


def _rule_based_response(message: str, user_role: str) -> str:
    msg = message.lower()
    for keyword, response in _KNOWLEDGE_BASE.items():
        if keyword in msg:
            return response

    if user_role == "student":
        return (
            "Hi! I'm CampusIQ AI. Here's what I can help you with:\n\n"
            "- **My attendance** — ask about your attendance percentage\n"
            "- **My predictions** — see your predicted grades\n"
            "- **Risk score** — understand your academic risk\n"
            "- **Timetable** — view your class schedule\n\n"
            "Try: *What is my attendance?* or *Am I at risk?*"
        )
    elif user_role == "faculty":
        return (
            "Hi! I'm CampusIQ AI. I can help you with:\n\n"
            "- **My courses** — your teaching load\n"
            "- **Risk roster** — students at academic risk\n"
            "- **Attendance analytics** — class attendance trends\n\n"
            "Try: *Show students at risk in CS301* or *Average attendance for my courses*"
        )
    return (
        "Hi! I'm CampusIQ AI. As an admin:\n\n"
        "- Use **Command Console** for natural language ERP operations\n"
        "- Use **Governance Dashboard** for approvals and audit trail\n"
        "- Ask me: *How many students are there?* or *Show all departments*"
    )


# ─── Suggested actions ─────────────────────────────────────────

def _get_data_actions(crud_result: dict) -> list:
    intent = crud_result.get("intent", "")
    entity = crud_result.get("entity", "").lower()
    if intent == "READ":
        return [f"Analyze {entity} statistics", f"Count total {entity}s", f"Filter {entity}s by department"][:3]
    if intent == "ANALYZE":
        return [f"Show all {entity}s", "Group by department", "Show top performers"][:3]
    if intent in ("CREATE", "UPDATE", "DELETE"):
        return [f"Show all {entity}s", f"Count {entity}s"]
    return []


def _get_suggested_actions(message: str, user_role: str) -> list:
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
