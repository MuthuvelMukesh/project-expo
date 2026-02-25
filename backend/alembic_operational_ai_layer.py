"""
CampusIQ — Database Migration: Conversational Operational AI Layer
Creates tables for operational plans, approvals, executions, and immutable audit logs.

Usage:
    alembic revision --autogenerate -m "add_operational_ai_layer"
    alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "operational_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.String(length=80), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("module", sa.String(length=30), nullable=False, server_default="nlp"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("intent_type", sa.String(length=20), nullable=False),
        sa.Column("entity", sa.String(length=50), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("scope", sa.JSON(), nullable=True),
        sa.Column("affected_fields", sa.JSON(), nullable=True),
        sa.Column("values", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ambiguity", sa.JSON(), nullable=True),
        sa.Column("risk_level", sa.String(length=10), nullable=False, server_default="LOW"),
        sa.Column("estimated_impact_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("requires_confirmation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_senior_approval", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_2fa", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("escalation_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("preview", sa.JSON(), nullable=True),
        sa.Column("rollback_plan", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_operational_plans_id", "operational_plans", ["id"], unique=False)
    op.create_index("ix_operational_plans_plan_id", "operational_plans", ["plan_id"], unique=True)
    op.create_index("ix_operational_plans_user_id", "operational_plans", ["user_id"], unique=False)

    op.create_table(
        "operational_approval_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.String(length=80), sa.ForeignKey("operational_plans.plan_id"), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reviewer_role", sa.String(length=20), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("approved_scope", sa.JSON(), nullable=True),
        sa.Column("rejected_scope", sa.JSON(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("two_factor_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_operational_approval_decisions_id", "operational_approval_decisions", ["id"], unique=False)
    op.create_index("ix_operational_approval_decisions_plan_id", "operational_approval_decisions", ["plan_id"], unique=False)
    op.create_index("ix_operational_approval_decisions_reviewer_id", "operational_approval_decisions", ["reviewer_id"], unique=False)

    op.create_table(
        "operational_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("execution_id", sa.String(length=80), nullable=False),
        sa.Column("plan_id", sa.String(length=80), sa.ForeignKey("operational_plans.plan_id"), nullable=False),
        sa.Column("executed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("failure_state", sa.JSON(), nullable=True),
        sa.Column("rollback_state", sa.JSON(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_operational_executions_id", "operational_executions", ["id"], unique=False)
    op.create_index("ix_operational_executions_execution_id", "operational_executions", ["execution_id"], unique=True)
    op.create_index("ix_operational_executions_plan_id", "operational_executions", ["plan_id"], unique=False)
    op.create_index("ix_operational_executions_executed_by", "operational_executions", ["executed_by"], unique=False)

    op.create_table(
        "immutable_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=80), nullable=False),
        sa.Column("plan_id", sa.String(length=80), nullable=True),
        sa.Column("execution_id", sa.String(length=80), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("module", sa.String(length=30), nullable=False),
        sa.Column("operation_type", sa.String(length=30), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("risk_level", sa.String(length=10), nullable=False),
        sa.Column("intent_payload", sa.JSON(), nullable=True),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_immutable_audit_logs_id", "immutable_audit_logs", ["id"], unique=False)
    op.create_index("ix_immutable_audit_logs_event_id", "immutable_audit_logs", ["event_id"], unique=True)
    op.create_index("ix_immutable_audit_logs_plan_id", "immutable_audit_logs", ["plan_id"], unique=False)
    op.create_index("ix_immutable_audit_logs_execution_id", "immutable_audit_logs", ["execution_id"], unique=False)
    op.create_index("ix_immutable_audit_logs_user_id", "immutable_audit_logs", ["user_id"], unique=False)
    op.create_index("ix_immutable_audit_logs_created_at", "immutable_audit_logs", ["created_at"], unique=False)


def downgrade():
    op.drop_index("ix_immutable_audit_logs_created_at", table_name="immutable_audit_logs")
    op.drop_index("ix_immutable_audit_logs_user_id", table_name="immutable_audit_logs")
    op.drop_index("ix_immutable_audit_logs_execution_id", table_name="immutable_audit_logs")
    op.drop_index("ix_immutable_audit_logs_plan_id", table_name="immutable_audit_logs")
    op.drop_index("ix_immutable_audit_logs_event_id", table_name="immutable_audit_logs")
    op.drop_index("ix_immutable_audit_logs_id", table_name="immutable_audit_logs")
    op.drop_table("immutable_audit_logs")

    op.drop_index("ix_operational_executions_executed_by", table_name="operational_executions")
    op.drop_index("ix_operational_executions_plan_id", table_name="operational_executions")
    op.drop_index("ix_operational_executions_execution_id", table_name="operational_executions")
    op.drop_index("ix_operational_executions_id", table_name="operational_executions")
    op.drop_table("operational_executions")

    op.drop_index("ix_operational_approval_decisions_reviewer_id", table_name="operational_approval_decisions")
    op.drop_index("ix_operational_approval_decisions_plan_id", table_name="operational_approval_decisions")
    op.drop_index("ix_operational_approval_decisions_id", table_name="operational_approval_decisions")
    op.drop_table("operational_approval_decisions")

    op.drop_index("ix_operational_plans_user_id", table_name="operational_plans")
    op.drop_index("ix_operational_plans_plan_id", table_name="operational_plans")
    op.drop_index("ix_operational_plans_id", table_name="operational_plans")
    op.drop_table("operational_plans")
