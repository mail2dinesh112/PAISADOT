################################################
# Author                : DINESHKUMAR A
# Created Date          : 09th MAY, 2026
# Last Date Modified    : 09th MAY, 2026
# Last Modified By      : DINESHKUMAR A
# Description           : This file is used to create accounts related API endpoints.
################################################

import logging
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from requests import session
from sqlalchemy.orm import Session
from api.common.models import Account, AccountType, User, RoleType
from api.common.session import get_db
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from api.authentication.authentication import require_superadmin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# APIRouter CONFIGURATION
router = APIRouter(prefix="/pd", responses={404: {"description": "Not found"}})

# GLOBAL DECLARATION
description = "Retrieve account details using optional filters and pagination."

# =========================================================
# REQUEST MODEL
# =========================================================

class GetAccountsRequestModel(BaseModel):
    account_id   : Optional[UUID] = None
    account_name : Optional[str] = Field(default=None, min_length=1, max_length=100)
    account_type : Optional[AccountType] = None
    limit        : int = Field(default=10, ge=1, le=100)
    offset       : int = Field(default=0, ge=0)

# =========================================================
# GET ACCOUNTS
# =========================================================

@router.post("/getaccounts", operation_id="get_accounts",tags=["Authorized API"],description=description)
def get_accounts(
    request_model: GetAccountsRequestModel,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    logger.info("Get accounts request started")
    try:
        filters = [Account.is_active == True]
        if request_model.account_id:
            filters.append(Account.id == str(request_model.account_id))
        if request_model.account_name:
            filters.append(Account.account_name == request_model.account_name)
        if request_model.account_type:
            filters.append(Account.account_type == request_model.account_type)

        get_account_details = (
            session.query(Account)
            .filter(*filters)
            .order_by(Account.created_at.desc())
            .offset(request_model.offset)
            .limit(request_model.limit)
            .all()
        )
        return JSONResponse(
            status_code=200,
            content={
                "message": "Data retrieved successfully",
                "data": jsonable_encoder(get_account_details),
            },
        )
    except Exception:

        session.rollback()
        logger.exception("Exception in get_accounts")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal Server Error"},
        )

# =========================================================
# REQUEST MODEL
# =========================================================

class AccountCreateRequestModel(BaseModel):
    account_id      : Optional[UUID] = None
    account_name    : Optional[str] = None
    account_type    : AccountType
    user_first_name : Optional[str] = None
    user_last_name  : Optional[str] = None
    user_email      : Optional[str] = None
    user_phone      : Optional[str] = None
    is_active       : Optional[bool] = True

# =========================================================
# CREATE / UPDATE ACCOUNT
# =========================================================

@router.post(
    "/createaccount",
    operation_id="create_account",
    tags=["Authorized API"],
    description="Create or update account details."
)
def create_account(
    request_model: AccountCreateRequestModel,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    logger.info("Create/Update account request started")

    try:

        # =========================================================
        # CREATE ACCOUNT
        # =========================================================
        if request_model.account_id is None:

            # -----------------------------------------------------
            # Check duplicate account
            # -----------------------------------------------------
            exist_account = session.query(Account).filter(
                Account.account_name == request_model.account_name,
                Account.account_type == request_model.account_type,
            ).first()

            if exist_account:
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": "Account with the same name and type already exists"
                    }
                )

            # -----------------------------------------------------
            # Check duplicate email
            # -----------------------------------------------------
            if request_model.user_email:

                exist_user = session.query(User).filter(
                    User.email == request_model.user_email,
                ).first()

                if exist_user:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "message": "User with the same email already exists"
                        }
                    )

            # -----------------------------------------------------
            # Check duplicate phone
            # -----------------------------------------------------
            if request_model.user_phone:

                exist_user_phone = session.query(User).filter(
                    User.phone_number == request_model.user_phone
                ).first()

                if exist_user_phone:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "message": "User with the same phone number already exists"
                        }
                    )

            # -----------------------------------------------------
            # Create account
            # -----------------------------------------------------
            new_account = Account(
                account_name=request_model.account_name,
                account_type=request_model.account_type,
                is_active=request_model.is_active
            )

            session.add(new_account)

            # IMPORTANT
            session.flush()
            session.refresh(new_account)

            # -----------------------------------------------------
            # Create admin user
            # -----------------------------------------------------
            account_admin = User(
                first_name=request_model.user_first_name,
                last_name=request_model.user_last_name,
                email=request_model.user_email,
                phone_number=request_model.user_phone,
                password_hash="hashed_password",
                username=request_model.user_email.split("@")[0],
                role_type=RoleType.ADMIN,
                account_id=new_account.id,
                is_active=request_model.is_active
            )

            session.add(account_admin)

            session.commit()

            session.refresh(new_account)

            return JSONResponse(
                status_code=201,
                content={
                    "data": jsonable_encoder(new_account),
                    "message": "Account created successfully"
                }
            )

        # =========================================================
        # UPDATE ACCOUNT
        # =========================================================
        exist_account = session.query(Account).filter(
            Account.id == str(request_model.account_id)
        ).first()

        if not exist_account:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "Account not found"
                }
            )

        # ---------------------------------------------------------
        # Check duplicate account name
        # ---------------------------------------------------------
        duplicate_account = session.query(Account).filter(
            Account.account_name == request_model.account_name,
            Account.account_type == request_model.account_type,
            Account.id != str(request_model.account_id)
        ).first()

        if duplicate_account:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Account with the same name and type already exists"
                }
            )

        # ---------------------------------------------------------
        # Update account details
        # ---------------------------------------------------------
        exist_account.account_name = request_model.account_name
        exist_account.account_type = request_model.account_type

        if request_model.is_active is not None:
            exist_account.is_active = request_model.is_active

        session.commit()
        session.refresh(exist_account)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Account updated successfully",
                "data": jsonable_encoder(exist_account)
            }
        )

    except Exception as error:

        session.rollback()

        logger.exception(
            f"Exception in create_account API: {str(error)}"
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error"
            }
        )
    
# =========================================================
# DELETE ACCOUNT
# =========================================================
    
@router.delete(
    "/deleteaccount",
    operation_id="delete_account",
    tags=["Authorized API"],
)
def delete_account(
    account_id: UUID,
    is_active: Optional[bool] = True,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    logger.info("Delete account request started")

    try:

        # =====================================================
        # CHECK ACCOUNT
        # =====================================================

        exist_account = session.query(Account).filter(
            Account.id == str(account_id)
        ).first()

        if not exist_account:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "Account not found"
                }
            )

        # =====================================================
        # SOFT DELETE
        # =====================================================

        if is_active:

            # DEACTIVATE ACCOUNT
            exist_account.is_active = False

            # DEACTIVATE USERS
            session.query(User).filter(
                User.account_id == str(account_id)
            ).update(
                {"is_active": False},
                synchronize_session=False
            )

            session.commit()

            return JSONResponse(
                status_code=200,
                content={
                    "message": "Account deactivated successfully"
                }
            )

        # =====================================================
        # PERMANENT DELETE
        # =====================================================

        session.query(User).filter(
            User.account_id == str(account_id)
        ).delete(
            synchronize_session=False
        )

        session.delete(exist_account)

        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "message": "Account deleted permanently"
            }
        )

    except Exception as error:

        session.rollback()

        logger.exception(
            f"Exception in delete_account API: {str(error)}"
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error"
            }
        )
    
# =========================================================
# DEACTIVATE ACCOUNTS
# =========================================================
    
@router.get(
    "/deactivatedaccounts",
    operation_id="deactivate_accounts",
    tags=["Authorized API"],
)
def deactivated_accounts(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    logger.info("Deactivated accounts request started")

    try:

        # DEACTIVATE ACCOUNTS
        get_deactivated_accounts = session.query(Account).filter(
            Account.is_active == False
        ).order_by(Account.created_at.desc()).all()

        return JSONResponse(
            status_code=200,
            content={
                "message": "Deactivated accounts retrieved successfully",
                "data": jsonable_encoder(get_deactivated_accounts)
            }
        )

    except Exception as error:

        session.rollback()

        logger.exception(
            f"Exception in deactivated_accounts API: {str(error)}"
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error"
            }
        )