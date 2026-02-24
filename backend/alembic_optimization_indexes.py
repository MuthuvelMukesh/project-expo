"""
CampusIQ — Database Migration: Optimized Indexes
Run this migration to add all performance-critical indexes.

Usage:
    alembic revision --autogenerate -m "add_optimized_indexes"
    alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add optimized indexes."""
    
    # Student performance queries
    op.create_index('idx_student_cgpa', 'students', ['cgpa'], unique=False)
    op.create_index('idx_student_semester', 'students', ['semester'], unique=False)
    op.create_index('idx_student_dept_sem', 'students', ['department_id', 'semester'], unique=False)
    op.create_index('idx_student_admission', 'students', ['admission_year'], unique=False)
    
    # Attendance queries
    op.create_index('idx_attendance_student_date', 'attendance', ['student_id', sa.desc('date')], unique=False)
    op.create_index('idx_attendance_course_date', 'attendance', ['course_id', sa.desc('date')], unique=False)
    op.create_index('idx_attendance_present', 'attendance', ['is_present'], unique=False, 
                   postgresql_where=sa.text("is_present = true"))
    
    # Prediction queries
    op.create_index('idx_prediction_student_recent', 'predictions', ['student_id', sa.desc('created_at')], unique=False)
    op.create_index('idx_prediction_risk_score', 'predictions', [sa.desc('risk_score')], unique=False)
    
    # Course queries
    op.create_index('idx_course_semester', 'courses', ['semester'], unique=False)
    op.create_index('idx_course_dept_sem', 'courses', ['department_id', 'semester'], unique=False)
    
    # Faculty queries
    op.create_index('idx_faculty_dept', 'faculty', ['department_id'], unique=False)
    
    # User queries
    op.create_index('idx_user_email', 'users', ['email'], unique=False)
    op.create_index('idx_user_role', 'users', ['role'], unique=False)
    
    print("✅ All performance indexes created successfully!")


def downgrade():
    """Remove indexes."""
    op.drop_index('idx_student_cgpa', 'students')
    op.drop_index('idx_student_semester', 'students')
    op.drop_index('idx_student_dept_sem', 'students')
    op.drop_index('idx_student_admission', 'students')
    op.drop_index('idx_attendance_student_date', 'attendance')
    op.drop_index('idx_attendance_course_date', 'attendance')
    op.drop_index('idx_attendance_present', 'attendance')
    op.drop_index('idx_prediction_student_recent', 'predictions')
    op.drop_index('idx_prediction_risk_score', 'predictions')
    op.drop_index('idx_course_semester', 'courses')
    op.drop_index('idx_course_dept_sem', 'courses')
    op.drop_index('idx_faculty_dept', 'faculty')
    op.drop_index('idx_user_email', 'users')
    op.drop_index('idx_user_role', 'users')
