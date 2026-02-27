"""
HR & Payroll Management API Routes
Handles employee management, salary structures, and payroll processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime
from typing import List, Optional

from app.api.dependencies import get_current_user, require_role
from app.models.models import (
    User, Employee, SalaryStructure, SalaryRecord, UserRole,
    EmployeeAttendance, LeaveType, LeaveBalance, LeaveRequest,
)
from app.core.database import get_db
from pydantic import BaseModel

router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────

class EmployeeCreateSchema(BaseModel):
    user_id: int
    employee_type: str
    date_of_joining: date
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None


class EmployeeSchema(BaseModel):
    id: int
    user_id: int
    employee_type: str
    date_of_joining: date
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None

    class Config:
        from_attributes = True


class SalaryStructureCreateSchema(BaseModel):
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
    effective_to: Optional[date] = None


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
    effective_to: Optional[date] = None

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
    payment_date: Optional[date] = None
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class SalaryRecordCreateSchema(BaseModel):
    employee_id: int
    month: int
    year: int
    notes: Optional[str] = None


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

    # Access control: admin can view all, others can only view own record
    if current_user.role != UserRole.ADMIN and employee.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return employee


@router.post("/employees", response_model=EmployeeSchema)
async def create_employee(
    employee: EmployeeCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new employee record (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    db_employee = Employee(**employee.model_dump(exclude_unset=True))
    db.add(db_employee)
    await db.flush()
    await db.refresh(db_employee)
    return db_employee


# ─── Salary Structure ────────────────────────────────────────────

@router.post("/salary-structures", response_model=SalaryStructureSchema)
async def create_salary_structure(
    salary_structure: SalaryStructureCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update salary structure (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    db_structure = SalaryStructure(**salary_structure.model_dump())
    db.add(db_structure)
    await db.flush()
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
    await db.flush()
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

    await db.flush()
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
    # Access control: admin can view all, others can only view own record
    if current_user.role != UserRole.ADMIN:
        emp_check = await db.execute(
            select(Employee).where(Employee.user_id == current_user.id)
        )
        own_emp = emp_check.scalar_one_or_none()
        if not own_emp or own_emp.id != employee_id:
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

    # Get employee and user name (explicit join to avoid lazy-load crash in async)
    emp_query = select(Employee, User).join(User, Employee.user_id == User.id).where(Employee.id == employee_id)
    result = await db.execute(emp_query)
    row = result.first()
    employee = row[0] if row else None
    emp_user = row[1] if row else None

    struct_query = (
        select(SalaryStructure)
        .where(SalaryStructure.employee_id == employee_id)
        .order_by(SalaryStructure.effective_from.desc())
    )
    result = await db.execute(struct_query)
    structure = result.scalar_one_or_none()

    return {
        "employee_id": employee_id,
        "employee_name": emp_user.full_name if emp_user else "Unknown",
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


# ─── Employee Update & Delete ───────────────────────────────────


class EmployeeUpdateSchema(BaseModel):
    employee_type: Optional[str] = None
    date_of_joining: Optional[date] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None


@router.put("/employees/{employee_id}", response_model=EmployeeSchema)
async def update_employee(
    employee_id: int,
    updates: EmployeeUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update employee record (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(query)
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = updates.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    await db.flush()
    await db.refresh(employee)
    return employee


@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete employee record (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(query)
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    await db.delete(employee)
    await db.flush()
    return {"detail": "Employee deleted", "id": employee_id}


# ─── Salary Structure Update ────────────────────────────────────


@router.put("/salary-structures/{structure_id}", response_model=SalaryStructureSchema)
async def update_salary_structure(
    structure_id: int,
    updates: SalaryStructureCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update salary structure (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(SalaryStructure).where(SalaryStructure.id == structure_id)
    result = await db.execute(query)
    structure = result.scalar_one_or_none()
    if not structure:
        raise HTTPException(status_code=404, detail="Salary structure not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(structure, field, value)

    await db.flush()
    await db.refresh(structure)
    return structure


# ─── Employee Attendance ────────────────────────────────────────


class AttendanceCreateSchema(BaseModel):
    employee_id: int
    date: date
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    hours_worked: Optional[float] = None
    status: str = "present"


class AttendanceSchema(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    hours_worked: Optional[float] = None
    status: str

    class Config:
        from_attributes = True


class AttendanceSummarySchema(BaseModel):
    employee_id: int
    employee_name: str
    month: int
    year: int
    total_days: int
    present: int
    absent: int
    halfday: int
    leave: int
    total_hours: float


@router.post("/attendance", response_model=AttendanceSchema)
async def record_employee_attendance(
    attendance: AttendanceCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record employee attendance (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # Check for duplicate entry
    existing = await db.execute(
        select(EmployeeAttendance).where(
            EmployeeAttendance.employee_id == attendance.employee_id,
            EmployeeAttendance.date == attendance.date,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Attendance already recorded for this date")

    db_att = EmployeeAttendance(**attendance.model_dump())
    db.add(db_att)
    await db.flush()
    await db.refresh(db_att)
    return db_att


@router.get("/attendance/{employee_id}", response_model=List[AttendanceSchema])
async def get_employee_attendance(
    employee_id: int,
    month: int = None,
    year: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance records for an employee."""
    # Access control
    if current_user.role != UserRole.ADMIN:
        emp_check = await db.execute(
            select(Employee).where(Employee.user_id == current_user.id)
        )
        own_emp = emp_check.scalar_one_or_none()
        if not own_emp or own_emp.id != employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(EmployeeAttendance).where(
        EmployeeAttendance.employee_id == employee_id
    ).order_by(EmployeeAttendance.date.desc())

    if month and year:
        from sqlalchemy import extract
        query = query.where(
            extract('month', EmployeeAttendance.date) == month,
            extract('year', EmployeeAttendance.date) == year,
        )

    result = await db.execute(query)
    records = result.scalars().all()
    return records


@router.put("/attendance/{record_id}", response_model=AttendanceSchema)
async def update_attendance(
    record_id: int,
    updates: AttendanceCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an attendance record (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(EmployeeAttendance).where(EmployeeAttendance.id == record_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    await db.flush()
    await db.refresh(record)
    return record


@router.get("/attendance-summary/{employee_id}")
async def get_attendance_summary(
    employee_id: int,
    month: int = None,
    year: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance summary for an employee for a given month/year."""
    from sqlalchemy import extract, case

    if not month or not year:
        now = datetime.now()
        month = month or now.month
        year = year or now.year

    # Access control
    if current_user.role != UserRole.ADMIN:
        emp_check = await db.execute(
            select(Employee).where(Employee.user_id == current_user.id)
        )
        own_emp = emp_check.scalar_one_or_none()
        if not own_emp or own_emp.id != employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(
        func.count(EmployeeAttendance.id).label("total_days"),
        func.sum(case((EmployeeAttendance.status == "present", 1), else_=0)).label("present"),
        func.sum(case((EmployeeAttendance.status == "absent", 1), else_=0)).label("absent"),
        func.sum(case((EmployeeAttendance.status == "halfday", 1), else_=0)).label("halfday"),
        func.sum(case((EmployeeAttendance.status == "leave", 1), else_=0)).label("on_leave"),
        func.coalesce(func.sum(EmployeeAttendance.hours_worked), 0).label("total_hours"),
    ).where(
        EmployeeAttendance.employee_id == employee_id,
        extract('month', EmployeeAttendance.date) == month,
        extract('year', EmployeeAttendance.date) == year,
    )

    result = await db.execute(query)
    row = result.first()

    # Get employee name
    emp_query = select(Employee, User).join(User, Employee.user_id == User.id).where(Employee.id == employee_id)
    emp_result = await db.execute(emp_query)
    emp_row = emp_result.first()

    return {
        "employee_id": employee_id,
        "employee_name": emp_row[1].full_name if emp_row else "Unknown",
        "month": month,
        "year": year,
        "total_days": row[0] or 0,
        "present": int(row[1] or 0),
        "absent": int(row[2] or 0),
        "halfday": int(row[3] or 0),
        "leave": int(row[4] or 0),
        "total_hours": float(row[5] or 0),
    }


# ─── Leave Management ───────────────────────────────────────────


class LeaveTypeCreateSchema(BaseModel):
    name: str
    code: str
    max_days_per_year: int = 12
    is_carry_forward: bool = False
    description: Optional[str] = None


class LeaveTypeSchema(BaseModel):
    id: int
    name: str
    code: str
    max_days_per_year: int
    is_carry_forward: bool
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class LeaveBalanceSchema(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    leave_type_name: Optional[str] = None
    year: int
    total_days: int
    used_days: int
    remaining_days: int

    class Config:
        from_attributes = True


class LeaveRequestCreateSchema(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveRequestSchema(BaseModel):
    id: int
    employee_id: int
    leave_type_id: int
    leave_type_name: Optional[str] = None
    employee_name: Optional[str] = None
    start_date: date
    end_date: date
    num_days: float
    reason: Optional[str] = None
    status: str
    reviewed_by: Optional[int] = None
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeaveReviewSchema(BaseModel):
    status: str  # approved or rejected
    review_comment: Optional[str] = None


# --- Leave Type CRUD ---

@router.post("/leave-types", response_model=LeaveTypeSchema)
async def create_leave_type(
    leave_type: LeaveTypeCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new leave type (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    db_lt = LeaveType(**leave_type.model_dump())
    db.add(db_lt)
    await db.flush()
    await db.refresh(db_lt)
    return db_lt


@router.get("/leave-types", response_model=List[LeaveTypeSchema])
async def get_leave_types(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all leave types."""
    result = await db.execute(
        select(LeaveType).where(LeaveType.is_active == True).order_by(LeaveType.name)
    )
    return result.scalars().all()


@router.put("/leave-types/{leave_type_id}", response_model=LeaveTypeSchema)
async def update_leave_type(
    leave_type_id: int,
    updates: LeaveTypeCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a leave type (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(select(LeaveType).where(LeaveType.id == leave_type_id))
    lt = result.scalar_one_or_none()
    if not lt:
        raise HTTPException(status_code=404, detail="Leave type not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(lt, field, value)

    await db.flush()
    await db.refresh(lt)
    return lt


# --- Leave Balance ---

@router.post("/leave-balances/initialize")
async def initialize_leave_balances(
    employee_id: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initialize leave balances for an employee for a year (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # Get all active leave types
    lt_result = await db.execute(select(LeaveType).where(LeaveType.is_active == True))
    leave_types = lt_result.scalars().all()

    created = []
    for lt in leave_types:
        # Check if already exists
        existing = await db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == lt.id,
                LeaveBalance.year == year,
            )
        )
        if existing.scalar_one_or_none():
            continue

        balance = LeaveBalance(
            employee_id=employee_id,
            leave_type_id=lt.id,
            year=year,
            total_days=lt.max_days_per_year,
            used_days=0,
            remaining_days=lt.max_days_per_year,
        )
        db.add(balance)
        created.append(lt.name)

    await db.flush()
    return {"detail": f"Initialized balances for: {', '.join(created) if created else 'all already exist'}", "employee_id": employee_id, "year": year}


@router.get("/leave-balances/{employee_id}")
async def get_leave_balances(
    employee_id: int,
    year: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get leave balances for an employee."""
    if not year:
        year = datetime.now().year

    # Access control
    if current_user.role != UserRole.ADMIN:
        emp_check = await db.execute(
            select(Employee).where(Employee.user_id == current_user.id)
        )
        own_emp = emp_check.scalar_one_or_none()
        if not own_emp or own_emp.id != employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(LeaveBalance, LeaveType).join(
        LeaveType, LeaveBalance.leave_type_id == LeaveType.id
    ).where(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.year == year,
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "id": bal.id,
            "employee_id": bal.employee_id,
            "leave_type_id": bal.leave_type_id,
            "leave_type_name": lt.name,
            "leave_type_code": lt.code,
            "year": bal.year,
            "total_days": bal.total_days,
            "used_days": bal.used_days,
            "remaining_days": bal.remaining_days,
        }
        for bal, lt in rows
    ]


# --- Leave Requests ---

@router.post("/leave-requests", response_model=LeaveRequestSchema)
async def create_leave_request(
    request_data: LeaveRequestCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a leave request (any authenticated employee)."""
    # Find employee record for current user
    emp_result = await db.execute(
        select(Employee).where(Employee.user_id == current_user.id)
    )
    employee = emp_result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=400, detail="No employee record found for current user")

    # Calculate num days
    delta = (request_data.end_date - request_data.start_date).days + 1
    if delta <= 0:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    num_days = float(delta)

    # Check leave balance
    year = request_data.start_date.year
    bal_result = await db.execute(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.leave_type_id == request_data.leave_type_id,
            LeaveBalance.year == year,
        )
    )
    balance = bal_result.scalar_one_or_none()
    if balance and balance.remaining_days < num_days:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient leave balance. Available: {balance.remaining_days}, Requested: {num_days}"
        )

    leave_req = LeaveRequest(
        employee_id=employee.id,
        leave_type_id=request_data.leave_type_id,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        num_days=num_days,
        reason=request_data.reason,
        status="pending",
    )

    db.add(leave_req)
    await db.flush()
    await db.refresh(leave_req)

    # Get leave type name for response
    lt_result = await db.execute(select(LeaveType).where(LeaveType.id == request_data.leave_type_id))
    lt = lt_result.scalar_one_or_none()

    return LeaveRequestSchema(
        id=leave_req.id,
        employee_id=leave_req.employee_id,
        leave_type_id=leave_req.leave_type_id,
        leave_type_name=lt.name if lt else None,
        employee_name=current_user.full_name,
        start_date=leave_req.start_date,
        end_date=leave_req.end_date,
        num_days=leave_req.num_days,
        reason=leave_req.reason,
        status=leave_req.status,
        created_at=leave_req.created_at,
    )


@router.get("/leave-requests", response_model=List[LeaveRequestSchema])
async def get_leave_requests(
    employee_id: int = None,
    status_filter: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get leave requests. Admins see all; employees see only their own."""
    query = select(LeaveRequest, LeaveType, Employee, User).join(
        LeaveType, LeaveRequest.leave_type_id == LeaveType.id
    ).join(
        Employee, LeaveRequest.employee_id == Employee.id
    ).join(
        User, Employee.user_id == User.id
    ).order_by(LeaveRequest.created_at.desc())

    if current_user.role != UserRole.ADMIN:
        emp_result = await db.execute(
            select(Employee).where(Employee.user_id == current_user.id)
        )
        own_emp = emp_result.scalar_one_or_none()
        if not own_emp:
            return []
        query = query.where(LeaveRequest.employee_id == own_emp.id)
    elif employee_id:
        query = query.where(LeaveRequest.employee_id == employee_id)

    if status_filter:
        query = query.where(LeaveRequest.status == status_filter)

    result = await db.execute(query)
    rows = result.all()

    return [
        LeaveRequestSchema(
            id=lr.id,
            employee_id=lr.employee_id,
            leave_type_id=lr.leave_type_id,
            leave_type_name=lt.name,
            employee_name=u.full_name,
            start_date=lr.start_date,
            end_date=lr.end_date,
            num_days=lr.num_days,
            reason=lr.reason,
            status=lr.status,
            reviewed_by=lr.reviewed_by,
            review_comment=lr.review_comment,
            reviewed_at=lr.reviewed_at,
            created_at=lr.created_at,
        )
        for lr, lt, emp, u in rows
    ]


@router.put("/leave-requests/{request_id}/review")
async def review_leave_request(
    request_id: int,
    review: LeaveReviewSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a leave request (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if review.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    result = await db.execute(select(LeaveRequest).where(LeaveRequest.id == request_id))
    leave_req = result.scalar_one_or_none()
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave_req.status != "pending":
        raise HTTPException(status_code=400, detail="Can only review pending requests")

    leave_req.status = review.status
    leave_req.reviewed_by = current_user.id
    leave_req.review_comment = review.review_comment
    leave_req.reviewed_at = datetime.utcnow()

    # If approved, update leave balance
    if review.status == "approved":
        year = leave_req.start_date.year
        bal_result = await db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == leave_req.employee_id,
                LeaveBalance.leave_type_id == leave_req.leave_type_id,
                LeaveBalance.year == year,
            )
        )
        balance = bal_result.scalar_one_or_none()
        if balance:
            balance.used_days += int(leave_req.num_days)
            balance.remaining_days = balance.total_days - balance.used_days

    await db.flush()
    return {
        "id": leave_req.id,
        "status": leave_req.status,
        "reviewed_by": current_user.id,
        "review_comment": review.review_comment,
    }


@router.put("/leave-requests/{request_id}/cancel")
async def cancel_leave_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending leave request (employee who owns it or admin)."""
    result = await db.execute(select(LeaveRequest).where(LeaveRequest.id == request_id))
    leave_req = result.scalar_one_or_none()
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # Access control
    if current_user.role != UserRole.ADMIN:
        emp_result = await db.execute(
            select(Employee).where(Employee.user_id == current_user.id)
        )
        own_emp = emp_result.scalar_one_or_none()
        if not own_emp or own_emp.id != leave_req.employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if leave_req.status not in ("pending", "approved"):
        raise HTTPException(status_code=400, detail="Can only cancel pending or approved requests")

    # If was approved, restore balance
    if leave_req.status == "approved":
        year = leave_req.start_date.year
        bal_result = await db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == leave_req.employee_id,
                LeaveBalance.leave_type_id == leave_req.leave_type_id,
                LeaveBalance.year == year,
            )
        )
        balance = bal_result.scalar_one_or_none()
        if balance:
            balance.used_days = max(0, balance.used_days - int(leave_req.num_days))
            balance.remaining_days = balance.total_days - balance.used_days

    leave_req.status = "cancelled"
    await db.flush()
    return {"id": leave_req.id, "status": "cancelled"}


# ─── Staff Self-Service ─────────────────────────────────────────


@router.get("/my-profile")
async def get_my_employee_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's employee profile with summary info."""
    emp_result = await db.execute(
        select(Employee).where(Employee.user_id == current_user.id)
    )
    employee = emp_result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="No employee record found")

    # Get latest salary info
    sal_result = await db.execute(
        select(SalaryRecord)
        .where(SalaryRecord.employee_id == employee.id)
        .order_by(SalaryRecord.year.desc(), SalaryRecord.month.desc())
    )
    latest_salary = sal_result.scalars().first()

    # Get current year leave balances
    year = datetime.now().year
    lb_result = await db.execute(
        select(LeaveBalance, LeaveType).join(
            LeaveType, LeaveBalance.leave_type_id == LeaveType.id
        ).where(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.year == year,
        )
    )
    leave_balances = [
        {
            "leave_type": lt.name,
            "code": lt.code,
            "total": bal.total_days,
            "used": bal.used_days,
            "remaining": bal.remaining_days,
        }
        for bal, lt in lb_result.all()
    ]

    # Attendance summary for current month
    from sqlalchemy import extract, case
    now = datetime.now()
    att_result = await db.execute(
        select(
            func.count(EmployeeAttendance.id).label("total"),
            func.sum(case((EmployeeAttendance.status == "present", 1), else_=0)).label("present"),
            func.sum(case((EmployeeAttendance.status == "absent", 1), else_=0)).label("absent"),
        ).where(
            EmployeeAttendance.employee_id == employee.id,
            extract('month', EmployeeAttendance.date) == now.month,
            extract('year', EmployeeAttendance.date) == now.year,
        )
    )
    att_row = att_result.first()

    return {
        "employee": {
            "id": employee.id,
            "user_id": employee.user_id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "employee_type": employee.employee_type,
            "date_of_joining": employee.date_of_joining,
            "phone": employee.phone,
        },
        "latest_salary": {
            "month": latest_salary.month if latest_salary else None,
            "year": latest_salary.year if latest_salary else None,
            "net_salary": latest_salary.net_salary if latest_salary else 0,
            "status": latest_salary.status if latest_salary else None,
        },
        "leave_balances": leave_balances,
        "attendance_this_month": {
            "total_days": att_row[0] or 0,
            "present": int(att_row[1] or 0),
            "absent": int(att_row[2] or 0),
        },
    }


# ─── Employee Directory ─────────────────────────────────────────


@router.get("/directory")
async def get_employee_directory(
    search: str = None,
    employee_type: str = None,
    department: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get employee directory with name, type, department, phone.
    Searchable by name, filterable by type.
    """
    query = select(Employee, User).join(User, Employee.user_id == User.id)

    if employee_type:
        query = query.where(Employee.employee_type == employee_type)

    if search:
        query = query.where(User.full_name.ilike(f"%{search}%"))

    query = query.order_by(User.full_name)
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "id": emp.id,
            "user_id": emp.user_id,
            "full_name": u.full_name,
            "email": u.email,
            "employee_type": emp.employee_type,
            "phone": emp.phone,
            "date_of_joining": emp.date_of_joining,
            "city": emp.city,
            "state": emp.state,
        }
        for emp, u in rows
    ]
