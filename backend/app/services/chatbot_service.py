"""
CampusIQ — Chatbot Service
LLM-powered conversational interface for academic queries.
Uses Ollama for local inference. Falls back to rule-based responses.
Now integrates with NLP CRUD engine for data operations.
"""

import httpx
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.services.nlp_crud_service import process_nlp_crud

settings = get_settings()

# Keywords that indicate a data/CRUD operation vs a general chat
_DATA_KEYWORDS = [
    "show", "list", "get", "fetch", "find", "display", "how many", "count",
    "total", "average", "avg", "all students", "all faculty", "all courses",
    "department", "semester", "cgpa", "attendance", "prediction", "grade",
    "add", "create", "insert", "new course", "new department", "register",
    "update", "change", "modify", "set", "edit", "fill",
    "delete", "remove", "drop",
    "statistics", "stats", "analyze", "analysis", "group by",
    "highest", "lowest", "top", "minimum", "maximum",
    "compare", "distribution", "percentage",
    "my details", "my profile", "my data", "my attendance", "my cgpa",
    "my semester", "my section", "my roll",
]

# Pre-built knowledge base for rule-based fallback (general queries)
_KNOWLEDGE_BASE = {
    "attendance": "You can check your attendance on the Student Dashboard. Each subject shows your attendance percentage, status (safe/warning/danger), and how many classes you need to attend to reach 75%.",
    "prediction": "CampusIQ uses an XGBoost ML model to predict your likely exam grade based on attendance, assignments, quizzes, and lab participation. Check the 'Predictions' section on your dashboard.",
    "risk": "Your risk score (0-1) indicates the probability of academic difficulty. High risk (>0.6) triggers automatic alerts to your mentor. The score is explained by SHAP factors showing which areas need improvement.",
    "qr": "Faculty generates a time-limited QR code in class. Open CampusIQ on your phone, scan the QR code, and your attendance is marked instantly. The QR expires after 90 seconds.",
    "grade": "Grades are predicted using ML models trained on historical campus data. The prediction includes a confidence score and the top factors influencing your grade.",
    "help": "I can help with: attendance queries, grade predictions, risk scores, QR attendance, data analysis, and managing records. Just ask naturally!",
}


def _is_data_query(message: str) -> bool:
    """Detect if a message is a data/CRUD query vs a general chat."""
    msg_lower = message.lower()
    return any(keyword in msg_lower for keyword in _DATA_KEYWORDS)


async def process_query(
    message: str,
    user_role: str,
    user_id: int,
    db: AsyncSession = None,
) -> dict:
    """Process a natural language query using NLP CRUD engine or LLM chat."""

    # Route data queries to the NLP CRUD engine
    if db and _is_data_query(message):
        try:
            crud_result = await process_nlp_crud(
                message=message,
                user_role=user_role,
                user_id=user_id,
                db=db,
            )

            # Format CRUD result as a chat response
            response_text = crud_result["summary"]

            # If there's tabular data, append a formatted view
            if crud_result.get("result") and crud_result["result"].get("data"):
                data = crud_result["result"]["data"]
                if data and len(data) > 0:
                    # Build markdown table
                    headers = list(data[0].keys())
                    table_lines = [" | ".join(headers)]
                    table_lines.append(" | ".join(["---"] * len(headers)))
                    for row in data[:20]:  # Cap display at 20 rows
                        table_lines.append(" | ".join(str(row.get(h, "")) for h in headers))
                    response_text += "\n\n" + "\n".join(table_lines)

                    if len(data) > 20:
                        response_text += f"\n\n*...and {len(data) - 20} more records*"

            return {
                "response": response_text,
                "sources": ["CampusIQ AI Data Engine"],
                "suggested_actions": _get_data_actions(crud_result),
            }
        except Exception:
            pass  # Fall through to general chat

    # Try Ollama for general conversation
    llm_response = await _query_ollama(message, user_role)
    if llm_response:
        return {
            "response": llm_response,
            "sources": ["CampusIQ AI (Local LLM)"],
            "suggested_actions": _get_suggested_actions(message),
        }

    # Fallback to rule-based
    response = _rule_based_response(message)
    return {
        "response": response,
        "sources": ["CampusIQ Knowledge Base"],
        "suggested_actions": _get_suggested_actions(message),
    }


async def _query_ollama(message: str, user_role: str) -> Optional[str]:
    """Query the Ollama local LLM."""
    try:
        system_prompt = (
            "You are CampusIQ, an AI assistant for a college ERP system. "
            f"The user is a {user_role}. Answer questions about academics, "
            "attendance, grades, and campus life. Be concise, helpful, and "
            "use data when available. If you don't know something specific, "
            "suggest checking the relevant dashboard section."
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                    "stream": False,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")

    except Exception:
        pass  # Fall back to rule-based

    return None


def _rule_based_response(message: str) -> str:
    """Simple keyword-based response when LLM is unavailable."""
    msg_lower = message.lower()

    for keyword, response in _KNOWLEDGE_BASE.items():
        if keyword in msg_lower:
            return response

    return (
        "I'm CampusIQ AI assistant! I can help you with:\n"
        "• **Attendance** — Check your attendance status\n"
        "• **Predictions** — See your predicted grades\n"
        "• **Risk Score** — Understand your academic risk\n"
        "• **QR Attendance** — How to mark attendance\n"
        "• **Data Queries** — Ask about students, courses, departments\n"
        "• **CRUD Ops** — Add, update, or view records with natural language\n\n"
        "Try asking: 'Show all students in CS department' or 'What is the average CGPA?'"
    )


def _get_data_actions(crud_result: dict) -> list:
    """Generate follow-up actions based on CRUD result."""
    intent = crud_result.get("intent", "")
    entity = crud_result.get("entity", "").lower()

    actions = []
    if intent == "READ":
        actions.extend([
            f"Analyze {entity} statistics",
            f"Count total {entity}s",
            f"Filter {entity}s by department"
        ])
    elif intent == "ANALYZE":
        actions.extend([
            f"Show all {entity}s",
            "Group by department",
            "Show top performers"
        ])
    elif intent in ("CREATE", "UPDATE", "DELETE"):
        actions.extend([
            f"Show all {entity}s",
            f"Count {entity}s",
        ])

    return actions[:3]


def _get_suggested_actions(message: str) -> list:
    """Generate contextual suggested follow-up actions."""
    msg_lower = message.lower()
    actions = []

    if "attendance" in msg_lower:
        actions.extend(["View attendance calendar", "Set attendance reminder"])
    if "grade" in msg_lower or "predict" in msg_lower:
        actions.extend(["View detailed prediction", "See improvement suggestions"])
    if "risk" in msg_lower:
        actions.extend(["Schedule mentor meeting", "View study resources"])

    return actions[:3] if actions else [
        "Show all students",
        "Average CGPA by department",
        "Ask about predictions"
    ]
