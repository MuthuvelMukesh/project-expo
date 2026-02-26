"""
HR & Payroll Management API Routes
Handles employee management, salary structures, and payroll processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime
from typing import List
from decimal import Decimal

from app.api.dependencies import get_current_user, require_role
from app.models.models import UserRole
from app.models.models import (
    User, Employee, SalaryStructure, SalaryRecord, UserRole
)
from app.core.database import get_db
from pydantic import BaseModel

router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────

class EmployeeSchema(BaseModel):
    id: int
    user_id: int
    employee_type: str
    date_of_joining: date
    date_of_birth: date = None
    phone: str = None
    bank_account: str = None
    bank_name: str = None

    class Config:
        from_attributes = True


class SalaryStructureSchema(BaseModel):
    id: int
    employee_id: int
    designation: str
    base_salary: float
    da: float = 0
    hra: float = 0
    other_allowances: float = 0
    pf_contribution: float = 0
    insurance: float = 0
    tax_rate: float = 0
    effective_from: date
    effective_to: date = None

    class Config:
        from_attributes = True


class SalaryRecordSchema(BaseModel):
    id: int
    employee_id: int
    month: int
    year: int
    gross_salary: float
    deductions: float
    net_salary: float
    payment_date: date = None
    status: str
    notes: str = None

    class Config:
        from_attributes = True


class SalaryRecordCreateSchema(BaseModel):
    employee_id: int
    month: int
    year: int
    notes: str = None


# ─── Employee Management ────────────────────────────────────────

@router.get("/employees", response_model=List[EmployeeSchema])
async def get_employees(
    employee_type: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all employees (admin/HR only)."""
    if current_user.role.value not in ["admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(Employee)
    if employee_type:
        query = query.where(Employee.employee_type == employee_type)

    result = await db.execute(query)
    employees = result.scalars().all()
    return employees


@router.get("/employees/{employee_id}", response_model=EmployeeSchema)
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get employee details."""
    query = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(query)
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Access control: employee can view own, admin can view all
    if (
        current_user.role.value == "employee"
        and employee.user_id != current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return employee


@router.post("/employees", response_model=EmployeeSchema)
async def create_employee(
    employee: EmployeeSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new employee record (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    db_employee = Employee(**employee.dict(exclude_unset=True))
    db.add(db_employee)
    await db.commit()
    await db.refresh(db_employee)
    return db_employee


# ─── Salary Structure ────────────────────────────────────────────

@router.post("/salary-structures", response_model=SalaryStructureSchema)
async def create_salary_structure(
    salary_structure: SalaryStructureSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update salary structure (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    db_structure = SalaryStructure(**salary_structure.dict())
    db.add(db_structure)
    await db.commit()
    await db.refresh(db_structure)
    return db_structure


@router.get("/salary-structures/{employee_id}", response_model=List[SalaryStructureSchema])
async def get_salary_structures(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get salary structure history for an employee."""
    query = select(SalaryStructure).where(
        SalaryStructure.employee_id == employee_id
    ).order_by(SalaryStructure.effective_from.desc())

    result = await db.execute(query)
    structures = result.scalars().all()
    return structures


# ─── Salary Processing ──────────────────────────────────────────

@router.post("/salary-records/process", response_model=SalaryRecordSchema)
async def process_salary(
    salary_create: SalaryRecordCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process salary for an employee (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # Get current salary structure
    structure_query = (
        select(SalaryStructure)
        .where(SalaryStructure.employee_id == salary_create.employee_id)
        .order_by(SalaryStructure.effective_from.desc())
    )
    result = await db.execute(structure_query)
    structure = result.scalar_one_or_none()

    if not structure:
        raise HTTPException(status_code=404, detail="Salary structure not found")

    # Calculate salary
    gross_salary = (
        structure.base_salary
        + structure.da
        + structure.hra
        + structure.other_allowances
    )
    deductions = structure.pf_contribution + structure.insurance
    tax = gross_salary * structure.tax_rate / 100
    deductions += tax
    net_salary = gross_salary - deductions

    # Check if already processed
    existing_query = select(SalaryRecord).where(
        SalaryRecord.employee_id == salary_create.employee_id,
        SalaryRecord.month == salary_create.month,
        SalaryRecord.year == salary_create.year,
    )
    result = await db.execute(existing_query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Salary already processed for this month")

    # Create salary record
    record = SalaryRecord(
        employee_id=salary_create.employee_id,
        month=salary_create.month,
        year=salary_create.year,
        gross_salary=gross_salary,
        deductions=deductions,
        net_salary=net_salary,
        status="processed",
        notes=salary_create.notes,
    )

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/salary-records/{employee_id}", response_model=List[SalaryRecordSchema])
async def get_salary_records(
    employee_id: int,
    month: int = None,
    year: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get salary records for an employee."""
    query = select(SalaryRecord).where(
        SalaryRecord.employee_id == employee_id
    ).order_by(SalaryRecord.year.desc(), SalaryRecord.month.desc())

    if month:
        query = query.where(SalaryRecord.month == month)
    if year:
        query = query.where(SalaryRecord.year == year)

    result = await db.execute(query)
    records = result.scalars().all()
    return records


@router.post("/salary-records/{record_id}/pay")
async def mark_salary_paid(
    record_id: int,
    payment_date: date = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark salary as paid."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    record_query = select(SalaryRecord).where(SalaryRecord.id == record_id)
    result = await db.execute(record_query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found")

    record.status = "paid"
    record.payment_date = payment_date or date.today()

    await db.commit()
    await db.refresh(record)

    return {
        "id": record.id,
        "status": record.status,
        "payment_date": record.payment_date,
    }


# ─── Payroll Reports ────────────────────────────────────────────

@router.get("/reports/payroll-summary")
async def get_payroll_summary(
    month: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payroll summary for a month."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(
        func.count(SalaryRecord.id).label("total_employees"),
        func.sum(SalaryRecord.gross_salary).label("total_gross"),
        func.sum(SalaryRecord.deductions).label("total_deductions"),
        func.sum(SalaryRecord.net_salary).label("total_net"),
    ).where(
        SalaryRecord.month == month,
        SalaryRecord.year == year,
    )

    result = await db.execute(query)
    row = result.first()

    return {
        "month": month,
        "year": year,
        "total_employees": row[0] or 0,
        "total_gross_salary": float(row[1] or 0),
        "total_deductions": float(row[2] or 0),
        "total_net_salary": float(row[3] or 0),
    }


@router.get("/reports/employee-salary-slip/{employee_id}/{month}/{year}")
async def get_salary_slip(
    employee_id: int,
    month: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate salary slip for an employee."""
    # Access control
    if (
        current_user.role.value == "employee"
        and current_user.id != employee_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # Get salary record
    record_query = select(SalaryRecord).where(
        SalaryRecord.employee_id == employee_id,
        SalaryRecord.month == month,
        SalaryRecord.year == year,
    )
    result = await db.execute(record_query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found")

    # Get employee and structure
    emp_query = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(emp_query)
    employee = result.scalar_one_or_none()

    struct_query = (
        select(SalaryStructure)
        .where(SalaryStructure.employee_id == employee_id)
        .order_by(SalaryStructure.effective_from.desc())
    )
    result = await db.execute(struct_query)
    structure = result.scalar_one_or_none()

    return {
        "employee_id": employee_id,
        "employee_name": employee.user.full_name,
        "month": month,
        "year": year,
        "base_salary": structure.base_salary if structure else 0,
        "allowances": {
            "da": structure.da if structure else 0,
            "hra": structure.hra if structure else 0,
            "other": structure.other_allowances if structure else 0,
        },
        "gross_salary": record.gross_salary,
        "deductions": {
            "pf": structure.pf_contribution if structure else 0,
            "insurance": structure.insurance if structure else 0,
            "tax": record.deductions - (
                (structure.pf_contribution + structure.insurance)
                if structure
                else 0
            ),
        },
        "total_deductions": record.deductions,
        "net_salary": record.net_salary,
        "payment_date": record.payment_date,
        "status": record.status,
    }
