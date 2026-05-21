################################################
# Author                : DINESHKUMAR A
# Created Date          : 13th MAY, 2026
# Last Date Modified    : 13th MAY, 2026
# Last Modified By      : DINESHKUMAR A
# Description           : This file is used to define the database models for the API.
################################################

# coding: utf-8

import enum
import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    Enum,
    Numeric,
    Text,
    text
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression


Base = declarative_base()


# =========================================================
# ENUMS
# =========================================================

class AccountType(str, enum.Enum):
    INDIVIDUAL  = "INDIVIDUAL"
    FAMILY      = "FAMILY"
    GROUP       = "GROUP"


class RoleType(str, enum.Enum):
    SUPERADMIN  = "SUPERADMIN"
    ADMIN       = "ADMIN"
    MEMBER      = "MEMBER"


class PaymentMethod(str, enum.Enum):
    CASH            = "CASH"
    UPI             = "UPI"
    CARD            = "CARD"
    BANK_TRANSFER   = "BANK_TRANSFER"

class RecurringFrequency(str, enum.Enum):
    DAILY   = "DAILY"
    WEEKLY  = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY  = "YEARLY"



# =========================================================
# ACCOUNT TABLE
# =========================================================

class Account(Base):
    __tablename__ = "accounts"

    id = Column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    account_name = Column(
        String(100),
        nullable=False
    )

    account_type = Column(
        Enum(AccountType),
        nullable=False
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=expression.true()
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    users = relationship(
        "User",
        back_populates="account"
    )

    categories = relationship(
        "Category",
        back_populates="account"
    )

    expenses = relationship(
        "Expense",
        back_populates="account"
    )

    recurring_expenses = relationship(
        "RecurringExpense",
        back_populates="account"
    )

    budgets = relationship(
        "Budget",
        back_populates="account"
    )


# =========================================================
# USER TABLE
# =========================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    first_name = Column(
        String(50),
        nullable=False
    )

    last_name = Column(
        String(50),
        nullable=True
    )

    email = Column(
        String(255),
        nullable=False,
        unique=True
    )

    phone_number = Column(
        String(20),
        nullable=True
    )

    username = Column(
        String(50),
        nullable=True,
        unique=True,
    )

    password_hash = Column(
        String,
        nullable=True
    )

    role_type = Column(
        Enum(RoleType),
        nullable=False
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=expression.true()
    )

    account_id = Column(
        ForeignKey("accounts.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    account = relationship(
        "Account",
        back_populates="users"
    )

    categories = relationship(
        "Category",
        back_populates="created_user"
    )

    expenses = relationship(
        "Expense",
        back_populates="created_user"
    )

    recurring_expenses = relationship(
        "RecurringExpense",
        back_populates="created_user"
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user"
    )

    budgets = relationship(
        "Budget",
        back_populates="created_user"
    )


# =========================================================
# CATEGORY TABLE
# =========================================================

class Category(Base):
    __tablename__ = "categories"

    id = Column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    category_name = Column(
        String(100),
        nullable=False
    )

    account_id = Column(
        ForeignKey("accounts.id"),
        nullable=False
    )

    created_by = Column(
        ForeignKey("users.id"),
        nullable=False
    )

    is_system_category = Column(
        Boolean,
        nullable=False,
        server_default=expression.false()
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=expression.true()
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    account = relationship(
        "Account",
        back_populates="categories"
    )

    created_user = relationship(
        "User",
        back_populates="categories"
    )

    expenses = relationship(
        "Expense",
        back_populates="category"
    )

    recurring_expenses = relationship(
        "RecurringExpense",
        back_populates="category"
    )

    budgets = relationship(
        "Budget",
        back_populates="category"
    )


# =========================================================
# RECURRING EXPENSE TABLE
# =========================================================

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id = Column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False
    )

    category_id = Column(
        ForeignKey("categories.id"),
        nullable=False
    )

    account_id = Column(
        ForeignKey("accounts.id"),
        nullable=False
    )

    created_by = Column(
        ForeignKey("users.id"),
        nullable=False
    )

    payment_method = Column(
        Enum(PaymentMethod),
        nullable=False
    )

    frequency = Column(
        Enum(RecurringFrequency),
        nullable=False
    )

    start_date = Column(
        Date,
        nullable=False
    )

    end_date = Column(
        Date,
        nullable=True
    )

    next_run_date = Column(
        Date,
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=expression.true()
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    account = relationship(
        "Account",
        back_populates="recurring_expenses"
    )

    created_user = relationship(
        "User",
        back_populates="recurring_expenses"
    )

    category = relationship(
        "Category",
        back_populates="recurring_expenses"
    )

    expenses = relationship(
        "Expense",
        back_populates="recurring_expense"
    )


# =========================================================
# EXPENSE TABLE
# =========================================================

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False
    )

    category_id = Column(
        ForeignKey("categories.id"),
        nullable=False
    )

    account_id = Column(
        ForeignKey("accounts.id"),
        nullable=False
    )

    created_by = Column(
        ForeignKey("users.id"),
        nullable=False
    )

    recurring_expense_id = Column(
        ForeignKey("recurring_expenses.id"),
        nullable=True
    )

    payment_method = Column(
        Enum(PaymentMethod),
        nullable=False
    )

    expense_date = Column(
        Date,
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=expression.true()
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    account = relationship(
        "Account",
        back_populates="expenses"
    )

    created_user = relationship(
        "User",
        back_populates="expenses"
    )

    category = relationship(
        "Category",
        back_populates="expenses"
    )

    recurring_expense = relationship(
        "RecurringExpense",
        back_populates="expenses"
    )


# =========================================================
# REFRESH TOKEN TABLE
# =========================================================

class RefreshToken(Base):

    __tablename__ = "refresh_tokens"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    hashed_refresh_token = Column(
        Text,
        nullable=False
    )

    login_ip = Column(
        Text,
        nullable=True
    )

    user_agent = Column(
        Text,
        nullable=True
    )

    login_time = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    last_used_ip = Column(
        Text,
        nullable=True
    )

    last_used_time = Column(
        DateTime(timezone=True),
        nullable=True
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False
    )

    is_revoked = Column(
        Boolean,
        nullable=False,
        server_default=text("false")
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    user = relationship(
        "User",
        back_populates="refresh_tokens"
    )

# =========================================================
# BUDGET TABLE
# =========================================================

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(
        UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    account_id = Column(
        ForeignKey("accounts.id"),
        nullable=False
    )

    # NULL means overall budget
    category_id = Column(
        ForeignKey("categories.id"),
        nullable=True
    )

    created_by = Column(
        ForeignKey("users.id"),
        nullable=False
    )

    budget_amount = Column(
        Numeric(12, 2),
        nullable=False
    )

    start_date = Column(
        Date,
        nullable=False
    )

    end_date = Column(
        Date,
        nullable=False
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=expression.true()
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    account = relationship(
        "Account",
        back_populates="budgets"
    )

    category = relationship(
        "Category",
        back_populates="budgets"
    )

    created_user = relationship(
        "User",
        back_populates="budgets"
    )
