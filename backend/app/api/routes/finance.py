"""
Financial Management API Routes
Handles student fees, invoices, payments, and financial reporting.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime
from typing import List

from app.api.dependencies import get_current_user, require_role
from app.models.models import UserRole
from app.models.models import (
    User, Student, Invoice, Payment, StudentFees, StudentLedger, FeeWaiver, FeeStructure
)
from app.core.database import get_db
from pydantic import BaseModel

router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────

class FeeStructureSchema(BaseModel):
    semester: int
    fee_type: str
    amount: float
    valid_from: date
    valid_to: date = None

    class Config:
        from_attributes = True


class StudentFeeSchema(BaseModel):
    id: int
    student_id: int
    fee_type: str
    amount: float
    due_date: date
    semester: int
    academic_year: str
    is_paid: bool

    class Config:
        from_attributes = True


class InvoiceSchema(BaseModel):
    id: int
    invoice_number: str
    amount_due: float
    issued_date: date
    due_date: date
    status: str
    description: str = None

    class Config:
        from_attributes = True


class PaymentSchema(BaseModel):
    id: int
    invoice_id: int
    amount: float
    payment_date: date
    payment_method: str
    reference_number: str = None
    status: str
    notes: str = None

    class Config:
        from_attributes = True


class PaymentCreateSchema(BaseModel):
    invoice_id: int
    amount: float
    payment_method: str
    reference_number: str = None
    notes: str = None


class StudentBalanceSchema(BaseModel):
    student_id: int
    total_fees: float
    total_paid: float
    total_outstanding: float
    pending_invoices: int
    last_payment_date: date = None


# ─── Fee Structure Management ────────────────────────────────────

@router.post("/fee-structures", response_model=FeeStructureSchema)
async def create_fee_structure(
    fee_structure: FeeStructureSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new fee structure (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    db_fee = FeeStructure(**fee_structure.dict())
    db.add(db_fee)
    await db.commit()
    await db.refresh(db_fee)
    return db_fee


@router.get("/fee-structures/{semester}")
async def get_fee_structures(
    semester: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get fee structures for a semester."""
    query = select(FeeStructure).where(FeeStructure.semester == semester)
    result = await db.execute(query)
    structures = result.scalars().all()
    return structures


# ─── Student Fees ───────────────────────────────────────────────

@router.get("/student-fees/{student_id}", response_model=List[StudentFeeSchema])
async def get_student_fees(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all fees for a student."""
    # Verify access
    if current_user.role == UserRole.STUDENT:
        student = await db.execute(
            select(Student).where(Student.user_id == current_user.id)
        )
        student = student.scalar_one_or_none()
        if not student or student.id != student_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(StudentFees).where(StudentFees.student_id == student_id)
    result = await db.execute(query)
    fees = result.scalars().all()
    return fees


# ─── Invoices ───────────────────────────────────────────────────

@router.post("/invoices/generate/{student_id}", response_model=InvoiceSchema)
async def generate_invoice(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an invoice for a student (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # Get student unpaid fees
    fee_query = select(func.sum(StudentFees.amount)).where(
        StudentFees.student_id == student_id,
        StudentFees.is_paid == False,
    )
    result = await db.execute(fee_query)
    total_amount = result.scalar() or 0

    if total_amount == 0:
        raise HTTPException(status_code=400, detail="No outstanding fees")

    # Generate invoice number
    invoice_count = await db.execute(select(func.count(Invoice.id)))
    invoice_num = f"INV-{datetime.now().year}-{invoice_count.scalar() + 1:05d}"

    invoice = Invoice(
        student_id=student_id,
        invoice_number=invoice_num,
        amount_due=total_amount,
        issued_date=date.today(),
        due_date=date.today(),
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.get("/invoices/student/{student_id}", response_model=List[InvoiceSchema])
async def get_student_invoices(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get invoices for a student."""
    query = select(Invoice).where(Invoice.student_id == student_id)
    result = await db.execute(query)
    invoices = result.scalars().all()
    return invoices


# ─── Payments ───────────────────────────────────────────────────

@router.post("/payments", response_model=PaymentSchema)
async def record_payment(
    payment: PaymentCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a payment for an invoice."""
    # Get invoice
    invoice_query = select(Invoice).where(Invoice.id == payment.invoice_id)
    invoice = await db.execute(invoice_query)
    invoice = invoice.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Create payment
    db_payment = Payment(
        invoice_id=payment.invoice_id,
        student_id=invoice.student_id,
        amount=payment.amount,
        payment_date=date.today(),
        payment_method=payment.payment_method,
        reference_number=payment.reference_number,
        status="pending",
        notes=payment.notes,
    )

    db.add(db_payment)

    # Update invoice status if fully paid
    if payment.amount >= invoice.amount_due:
        invoice.status = "paid"

    # Add to ledger
    ledger = StudentLedger(
        student_id=invoice.student_id,
        transaction_type="credit",
        amount=payment.amount,
        balance=0,  # Will be calculated
        description=f"Payment for {invoice.invoice_number}",
        reference_id=invoice.id,
    )
    db.add(ledger)

    await db.commit()
    await db.refresh(db_payment)
    return db_payment


@router.get("/payments/verify/{reference_number}")
async def verify_payment(
    reference_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify a payment by reference number."""
    query = select(Payment).where(
        Payment.reference_number == reference_number
    )
    result = await db.execute(query)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "payment_id": payment.id,
        "amount": payment.amount,
        "status": payment.status,
        "verified": payment.status == "reconciled",
    }


# ─── Student Balance ─────────────────────────────────────────────

@router.get("/student-balance/{student_id}", response_model=StudentBalanceSchema)
async def get_student_balance(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get outstanding balance for a student."""
    # Calculate total fees
    fees_query = select(func.sum(StudentFees.amount)).where(
        StudentFees.student_id == student_id
    )
    result = await db.execute(fees_query)
    total_fees = result.scalar() or 0.0

    # Calculate total paid
    payments_query = select(func.sum(Payment.amount)).where(
        Payment.student_id == student_id,
        Payment.status.in_(["verified", "reconciled"]),
    )
    result = await db.execute(payments_query)
    total_paid = result.scalar() or 0.0

    # Outstanding invoices
    invoices_query = select(func.count(Invoice.id)).where(
        Invoice.student_id == student_id,
        Invoice.status.in_(["issued", "overdue"]),
    )
    result = await db.execute(invoices_query)
    pending_count = result.scalar() or 0

    # Last payment date
    last_payment_query = select(func.max(Payment.payment_date)).where(
        Payment.student_id == student_id
    )
    result = await db.execute(last_payment_query)
    last_payment = result.scalar()

    return StudentBalanceSchema(
        student_id=student_id,
        total_fees=total_fees,
        total_paid=total_paid,
        total_outstanding=total_fees - total_paid,
        pending_invoices=pending_count,
        last_payment_date=last_payment,
    )


# ─── Financial Reports ──────────────────────────────────────────

@router.get("/reports/outstanding")
async def get_outstanding_dues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get report of all outstanding dues (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(
        Student.id,
        Student.roll_number,
        func.sum(Invoice.amount_due).label("total_due"),
    ).join(Invoice).where(
        Invoice.status.in_(["issued", "overdue"])
    ).group_by(Student.id)

    result = await db.execute(query)
    dues = result.all()

    return {
        "count": len(dues),
        "total_outstanding": sum(d[2] for d in dues),
        "dues": [
            {"student_id": d[0], "roll_number": d[1], "amount": d[2]}
            for d in dues
        ],
    }


@router.get("/reports/collections")
async def get_collection_report(
    from_date: date = None,
    to_date: date = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payment collection report."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    query = select(
        func.count(Payment.id).label("transaction_count"),
        func.sum(Payment.amount).label("total_collected"),
        Payment.payment_method,
    ).group_by(Payment.payment_method)

    if from_date:
        query = query.where(Payment.payment_date >= from_date)
    if to_date:
        query = query.where(Payment.payment_date <= to_date)

    result = await db.execute(query)
    collections = result.all()

    return {
        "period": {"from": from_date, "to": to_date},
        "collections": [
            {
                "method": c[2],
                "count": c[0],
                "amount": c[1],
            }
            for c in collections
        ],
    }


@router.get("/reports/revenue")
async def get_revenue_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get revenue summary report."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # Total fees
    fees_total = await db.execute(select(func.sum(StudentFees.amount)))
    fees_amount = fees_total.scalar() or 0.0

    # Total collected
    paid_total = await db.execute(
        select(func.sum(Payment.amount)).where(
            Payment.status.in_(["verified", "reconciled"])
        )
    )
    collected = paid_total.scalar() or 0.0

    # Outstanding
    outstanding = fees_amount - collected

    return {
        "total_fees": fees_amount,
        "total_collected": collected,
        "total_outstanding": outstanding,
        "collection_percentage": (
            (collected / fees_amount * 100) if fees_amount > 0 else 0
        ),
    }
