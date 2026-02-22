"""
CampusIQ — Chatbot Service
LLM-powered conversational interface for academic queries.
Uses Ollama for local inference. Falls back to rule-based responses.
"""

import httpx
import json
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

# Pre-built knowledge base for rule-based fallback
_KNOWLEDGE_BASE = {
    "attendance": "You can check your attendance on the Student Dashboard. Each subject shows your attendance percentage, status (safe/warning/danger), and how many classes you need to attend to reach 75%.",
    "prediction": "CampusIQ uses an XGBoost ML model to predict your likely exam grade based on attendance, assignments, quizzes, and lab participation. Check the 'Predictions' section on your dashboard.",
    "risk": "Your risk score (0-1) indicates the probability of academic difficulty. High risk (>0.6) triggers automatic alerts to your mentor. The score is explained by SHAP factors showing which areas need improvement.",
    "qr": "Faculty generates a time-limited QR code in class. Open CampusIQ on your phone, scan the QR code, and your attendance is marked instantly. The QR expires after 90 seconds.",
    "grade": "Grades are predicted using ML models trained on historical campus data. The prediction includes a confidence score and the top factors influencing your grade.",
    "help": "I can help with: attendance queries, grade predictions, risk scores, QR attendance, and general academic information. Just ask naturally!",
}


async def process_query(message: str, user_role: str, user_id: int) -> dict:
    """Process a natural language query using LLM or rule-based fallback."""

    # Try Ollama first
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
        "• **QR Attendance** — How to mark attendance\n\n"
        "Try asking something like: 'What is my attendance?' or 'Am I at risk?'"
    )


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

    return actions[:3] if actions else ["View dashboard", "Check attendance", "Ask about predictions"]
