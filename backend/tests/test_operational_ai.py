import pytest

from app.models.models import Course, Department, Student, User, UserRole
from app.services import conversational_ops_service as ops


async def _make_user(db_session, email: str, role: UserRole, full_name: str = "Test User"):
    user = User(
        email=email,
        hashed_password="hashed",
        full_name=full_name,
        role=role,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_plan_requires_clarification(db_session, monkeypatch):
    admin = await _make_user(db_session, "admin1@campusiq.edu", UserRole.ADMIN, "Admin 1")

    async def fake_extract(_message: str, _module: str):
        return {
            "intent": "UPDATE",
            "entity": "student",
            "filters": {},
            "scope": {},
            "affected_fields": [],
            "values": {},
            "confidence": 0.41,
            "ambiguity": {
                "is_ambiguous": True,
                "fields": ["scope", "affected_fields"],
                "question": "Which student and which fields should be updated?",
            },
        }, None

    monkeypatch.setattr(ops, "_extract_intent", fake_extract)

    result = await ops.create_operational_plan(
        db=db_session,
        user=admin,
        message="Update student",
        module="nlp",
    )

    assert result["status"] == "clarification_required"
    assert result["clarification"] is not None
    assert result["clarification"]["code"] == "CLARIFICATION_REQUIRED"


@pytest.mark.asyncio
async def test_student_delete_becomes_escalation(db_session, monkeypatch):
    student_user = await _make_user(db_session, "student1@campusiq.edu", UserRole.STUDENT, "Student 1")
    dept = Department(name="Computer Science", code="CSE")
    db_session.add(dept)
    await db_session.flush()
    db_session.add(
        Student(
            user_id=student_user.id,
            roll_number="CSE100",
            department_id=dept.id,
            semester=3,
            section="A",
            cgpa=8.0,
        )
    )
    await db_session.flush()

    async def fake_extract(_message: str, _module: str):
        return {
            "intent": "DELETE",
            "entity": "course",
            "filters": {"id": 1},
            "scope": {},
            "affected_fields": [],
            "values": {},
            "confidence": 0.92,
            "ambiguity": {"is_ambiguous": False, "fields": []},
        }, None

    monkeypatch.setattr(ops, "_extract_intent", fake_extract)

    result = await ops.create_operational_plan(
        db=db_session,
        user=student_user,
        message="Delete course 1",
        module="nlp",
    )

    assert result["intent"] == "ESCALATE"
    assert result["requires_senior_approval"] is True
    assert result["permission"]["escalation_required"] is True


@pytest.mark.asyncio
async def test_execute_and_rollback_update(db_session, monkeypatch):
    admin = await _make_user(db_session, "admin2@campusiq.edu", UserRole.ADMIN, "Admin 2")

    dept = Department(name="Electronics", code="ECE")
    db_session.add(dept)
    await db_session.flush()

    course = Course(code="ECE101", name="Signals", department_id=dept.id, semester=2, credits=3)
    db_session.add(course)
    await db_session.flush()

    async def fake_extract(_message: str, _module: str):
        return {
            "intent": "UPDATE",
            "entity": "course",
            "filters": {"id": course.id},
            "scope": {},
            "affected_fields": ["credits"],
            "values": {"credits": 5},
            "confidence": 0.95,
            "ambiguity": {"is_ambiguous": False, "fields": []},
        }, None

    monkeypatch.setattr(ops, "_extract_intent", fake_extract)

    plan = await ops.create_operational_plan(
        db=db_session,
        user=admin,
        message="Update ECE101 credits to 5",
        module="nlp",
    )
    assert plan["status"] in {"awaiting_confirmation", "ready_for_execution"}

    decision = await ops.add_approval_decision(
        db=db_session,
        user=admin,
        plan_id=plan["plan_id"],
        decision="APPROVE",
        approved_ids=[course.id],
    )
    assert decision["status"] == "approved"

    executed = await ops.execute_operational_plan(
        db=db_session,
        user=admin,
        plan_id=plan["plan_id"],
    )
    assert executed["status"] == "executed"
    assert executed["affected_count"] == 1

    refreshed = (await db_session.get(Course, course.id))
    assert refreshed.credits == 5

    rolled = await ops.rollback_execution(
        db=db_session,
        user=admin,
        execution_id=executed["execution_id"],
    )
    assert rolled["status"] == "rolled_back"

    restored = (await db_session.get(Course, course.id))
    assert restored.credits == 3


@pytest.mark.asyncio
async def test_high_risk_requires_2fa(db_session, monkeypatch):
    admin = await _make_user(db_session, "admin3@campusiq.edu", UserRole.ADMIN, "Admin 3")

    async def fake_extract(_message: str, _module: str):
        return {
            "intent": "UPDATE",
            "entity": "salary_record",
            "filters": {"id": 999},
            "scope": {},
            "affected_fields": ["net_salary"],
            "values": {"net_salary": 200000},
            "confidence": 0.99,
            "ambiguity": {"is_ambiguous": False, "fields": []},
        }, None

    monkeypatch.setattr(ops, "_extract_intent", fake_extract)

    plan = await ops.create_operational_plan(
        db=db_session,
        user=admin,
        message="Set salary",
        module="hr",
    )

    assert plan["risk_level"] == "HIGH"
    assert plan["requires_2fa"] is True

    rejected = await ops.add_approval_decision(
        db=db_session,
        user=admin,
        plan_id=plan["plan_id"],
        decision="APPROVE",
    )
    assert rejected["error"] == "TWO_FACTOR_REQUIRED"

    approved = await ops.add_approval_decision(
        db=db_session,
        user=admin,
        plan_id=plan["plan_id"],
        decision="APPROVE",
        two_factor_code="123456",
    )
    assert approved["status"] == "approved"
