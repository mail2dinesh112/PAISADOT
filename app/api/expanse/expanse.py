from datetime import date
from decimal import Decimal
import logging
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from api.common.session import get_db
from api.common.models import (
    User,
    Category,
    Expense,
    PaymentMethod
)
from api.authentication.authentication import (
    get_current_user
)
# =========================================================
# LOGGER
# =========================================================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/pd",
    responses={404: {"description": "Not found"}}
)

# =========================================================
# REQUEST SCHEMAS
# =========================================================

class ExpenseRequest(BaseModel):

    amount          : Decimal = Field(...,gt=0,description="Expense amount")
    category_id     : UUID
    payment_method  : PaymentMethod
    expense_date    : date
    description     : Optional[str] = None
    notes           : Optional[str] = None


# =========================================================
# CREATE EXPENSE
# =========================================================

@router.post(
    "/expenses",
    tags=["Expense"]
)
def create_expense(
    request: ExpenseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:

        # =================================================
        # VALIDATE CATEGORY
        # =================================================

        category = db.query(Category).filter(
            and_(
                Category.id == request.category_id,
                Category.is_active == True
            )
        ).first()

        if not category:

            return JSONResponse(
                status_code=404,
                content={
                    "message": "Category not found"
                }
            )

        # =================================================
        # VALIDATE ACCOUNT ACCESS
        # =================================================

        if (
            category.account_id is not None and
            category.account_id != current_user.account_id
        ):

            return JSONResponse(
                status_code=403,
                content={
                    "message": "Invalid category access"
                }
            )

        # =================================================
        # CREATE EXPENSE
        # =================================================

        new_expense = Expense(
            amount=request.amount,
            category_id=request.category_id,
            account_id=current_user.account_id,
            created_by=current_user.id,
            payment_method=request.payment_method,
            expense_date=request.expense_date,
            description=request.description,
            notes=request.notes,
            is_active=True
        )

        db.add(new_expense)
        db.commit()
        db.refresh(new_expense)

        return JSONResponse(
            status_code=201,
            content={
                "message": "Expense created successfully",
                "data": jsonable_encoder(new_expense)
            }
        )

    except Exception as e:

        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "message": str(e)
            }
        )


# =========================================================
# GET ALL EXPENSES
# =========================================================

@router.get(
    "/getexpenses",
    operation_id="get_expenses",
    tags=["Authorized API"],
)
def get_expenses(
    category_id     : Optional[UUID] = None,
    payment_method  : Optional[PaymentMethod] = None,
    start_date      : Optional[date] = None,
    end_date        : Optional[date] = None,
    limit           : int = Query(default=10, ge=1, le=100),
    offset          : int = Query(default=0, ge=0),
    db              : Session = Depends(get_db),
    current_user    : User = Depends(get_current_user)
):

    try:

        query = db.query(Expense).filter(
            and_(
                Expense.account_id == current_user.account_id,
                Expense.is_active == True
            )
        )

        # =============================================
        # FILTERS
        # =============================================

        if category_id:

            query = query.filter(
                Expense.category_id == category_id
            )

        if payment_method:

            query = query.filter(
                Expense.payment_method == payment_method
            )

        if start_date:

            query = query.filter(
                Expense.expense_date >= start_date
            )

        if end_date:

            query = query.filter(
                Expense.expense_date <= end_date
            )

        # =============================================
        # PAGINATION
        # =============================================

        total = query.count()

        expenses = query.order_by(
            Expense.expense_date.desc()
        ).offset(
            offset
        ).limit(
            limit
        ).all()

        return JSONResponse(
            status_code=200,
            content={
                "total": total,
                "offset": offset,
                "limit": limit,
                "data": jsonable_encoder(expenses)
            }
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "message": str(e)
            }
        )


# =========================================================
# GET SINGLE EXPENSE
# =========================================================

@router.get(
    "/getexpenses/{expense_id}",
    operation_id="get_expense",
    tags=["Authorized API"]
)
def get_expense(
    expense_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:

        expense = db.query(Expense).filter(
            and_(
                Expense.id == expense_id,
                Expense.account_id == current_user.account_id,
                Expense.is_active == True
            )
        ).first()

        if not expense:

            return JSONResponse(
                status_code=404,
                content={
                    "message": "Expense not found"
                }
            )

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(expense)
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "message": str(e)
            }
        )


# =========================================================
# UPDATE EXPENSE
# =========================================================

@router.put(
    "/updateexpense/{expense_id}",
    operation_id="update_expense",
    tags=["Authorized API"]
)
def update_expense(
    expense_id: UUID,
    request: ExpenseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:

        # =============================================
        # GET EXPENSE
        # =============================================

        expense = db.query(Expense).filter(
            and_(
                Expense.id == expense_id,
                Expense.account_id == current_user.account_id,
                Expense.is_active == True
            )
        ).first()

        if not expense:

            return JSONResponse(
                status_code=404,
                content={
                    "message": "Expense not found"
                }
            )

        # =============================================
        # VALIDATE CATEGORY
        # =============================================

        category = db.query(Category).filter(
            and_(
                Category.id == request.category_id,
                Category.is_active == True
            )
        ).first()

        if not category:

            return JSONResponse(
                status_code=404,
                content={
                    "message": "Category not found"
                }
            )

        # =============================================
        # UPDATE FIELDS
        # =============================================

        expense.amount = request.amount
        expense.category_id = request.category_id
        expense.payment_method = request.payment_method
        expense.expense_date = request.expense_date
        expense.description = request.description
        expense.notes = request.notes

        db.commit()
        db.refresh(expense)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Expense updated successfully",
                "data": jsonable_encoder(expense)
            }
        )

    except Exception as e:

        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "message": str(e)
            }
        )


# =========================================================
# DELETE EXPENSE
# =========================================================

@router.delete(
    "/deleteexpense/{expense_id}",
    operation_id="delete_expense",
    tags=["Authorized API"]
)
def delete_expense(
    expense_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:

        expense = db.query(Expense).filter(
            and_(
                Expense.id == expense_id,
                Expense.account_id == current_user.account_id,
                Expense.is_active == True
            )
        ).first()

        if not expense:

            return JSONResponse(
                status_code=404,
                content={
                    "message": "Expense not found"
                }
            )

        # =============================================
        # SOFT DELETE
        # =============================================

        expense.is_active = False

        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "message": "Expense deleted successfully"
            }
        )

    except Exception as e:

        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "message": str(e)
            }
        )