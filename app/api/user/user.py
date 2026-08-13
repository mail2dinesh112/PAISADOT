################################################
# Author                : DINESHKUMAR A
# Created Date          : 09th MAY, 2026
# Last Date Modified    : 09th MAY, 2026
# Last Modified By      : DINESHKUMAR A
# Description           : This file is used to create user related API endpoints.
################################################

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.common.models import Account, User, RoleType
from api.common.session import get_db
from api.authentication.authentication import get_current_user
from argon2 import PasswordHasher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pd",
    responses={404: {"description": "Not found"}}
)

ph = PasswordHasher()

# =========================================================
# REQUEST MODEL
# =========================================================

class GetUsersRequestModel(BaseModel):
    account_id  : UUID
    user_id     : Optional[UUID] = None
    first_name  : Optional[str] = None
    last_name   : Optional[str] = None
    email       : Optional[str] = None
    phone       : Optional[str] = None
    role_type   : Optional[RoleType] = None
    limit       : int = Field(default=10, ge=1, le=100)
    offset      : int = Field(default=0, ge=0)


# =========================================================
# GET USERS
# =========================================================

@router.post(
    "/getusers",
    operation_id="get_users",
    tags=["Authorized API"],
    description="Retrieve users"
)
def get_users(
    request_model: GetUsersRequestModel,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Get users request started")

    try:

        # =====================================================
        # TENANT ISOLATION
        # =====================================================
        if (
            current_user.role_type != RoleType.SUPERADMIN
            and str(current_user.account_id) != str(request_model.account_id)
        ):
            return JSONResponse(
                status_code=403,
                content={"message": "Permission denied"}
            )

        filters = [User.account_id == str(request_model.account_id)]

        if request_model.user_id:
            filters.append(
                User.id == str(request_model.user_id)
            )

        if request_model.first_name:
            filters.append(
                User.first_name.ilike(f"%{request_model.first_name}%")
            )

        if request_model.last_name:
            filters.append(
                User.last_name.ilike(f"%{request_model.last_name}%")
            )

        if request_model.email:
            filters.append(
                User.email == str(request_model.email).lower()
            )

        if request_model.phone:
            filters.append(
                User.phone_number == request_model.phone
            )

        if request_model.role_type:
            filters.append(
                User.role_type == request_model.role_type
            )

        users = (
            session.query(User)
            .filter(*filters, User.is_active == True)
            .order_by(User.created_at.desc())
            .offset(request_model.offset)
            .limit(request_model.limit)
            .all()
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": "Users retrieved successfully",
                "data": jsonable_encoder(users)
            }
        )

    except Exception as e:

        logger.exception(f"Error retrieving users: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )


# =========================================================
# REQUEST MODEL
# =========================================================
class CreateUserRequestModel(BaseModel):
    user_id     : Optional[UUID] = None
    account_id  : UUID
    first_name  : Optional[str] = None
    last_name   : Optional[str] = None
    email       : Optional[str] = None
    phone       : Optional[str] = None
    role_type   : Optional[RoleType] = None
    is_active   : Optional[bool] = True

# =========================================================
# CREATE / UPDATE USER
# =========================================================

@router.post(
    "/createuser",
    operation_id="create_user",
    tags=["Authorized API"],
    description="Create or update user"
)
def create_user(
    request_model: CreateUserRequestModel,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Create/Update user request started")

    try:

        # =====================================================
        # CREATE USER
        # =====================================================
        if request_model.user_id is None:

            # TENANT ISOLATION
            if (
                current_user.role_type != RoleType.SUPERADMIN
                and str(current_user.account_id) != str(request_model.account_id)
            ):
                return JSONResponse(
                    status_code=403,
                    content={"message": "Permission denied"}
                )

            # VALIDATE ACCOUNT
            account = session.query(Account).filter(
                Account.id == str(request_model.account_id),
                Account.is_active == True
            ).first()

            if not account:
                return JSONResponse(
                    status_code=404,
                    content={
                        "message": "Account not found or inactive"
                    }
                )

            # CHECK EMAIL DUPLICATE
            if request_model.email:

                duplicate_email = session.query(User).filter(
                    User.email == str(request_model.email).lower()
                ).first()

                if duplicate_email:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "message": "Email already exists"
                        }
                    )

            # CHECK PHONE DUPLICATE
            if request_model.phone:

                duplicate_phone = session.query(User).filter(
                    User.phone_number == request_model.phone
                ).first()

                if duplicate_phone:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "message": "Phone number already exists"
                        }
                    )
                
            # CREATE USER
            new_user = User(
                first_name   = request_model.first_name,
                last_name    = request_model.last_name,
                email        = str(request_model.email).lower(),
                phone_number = request_model.phone,
                role_type    = request_model.role_type,
                account_id   = str(request_model.account_id),
                is_active    = request_model.is_active
            )

            session.add(new_user)

            session.commit()

            session.refresh(new_user)

            return JSONResponse(
                status_code=201,
                content={
                    "message": "User created successfully",
                    "data": jsonable_encoder(new_user)
                }
            )

        # =====================================================
        # UPDATE USER
        # =====================================================

        exist_user = session.query(User).filter(
            User.id == str(request_model.user_id)
        ).first()

        if not exist_user:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "User not found"
                }
            )

        # TENANT ISOLATION
        if (
            current_user.role_type != RoleType.SUPERADMIN
            and str(current_user.account_id) != str(exist_user.account_id)
        ):
            return JSONResponse(
                status_code=403,
                content={"message": "Permission denied"}
            )

        # DUPLICATE EMAIL CHECK
        if request_model.email is not None:

            duplicate_email = session.query(User).filter(
                User.email == str(request_model.email).lower(),
                User.id != str(request_model.user_id)
            ).first()

            if duplicate_email:
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": "Email already exists"
                    }
                )

        # DUPLICATE PHONE CHECK
        if request_model.phone is not None:

            duplicate_phone = session.query(User).filter(
                User.phone_number == request_model.phone,
                User.id != str(request_model.user_id)
            ).first()

            if duplicate_phone:
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": "Phone number already exists"
                    }
                )

        # UPDATE VALUES
        if request_model.first_name is not None:
            exist_user.first_name = request_model.first_name

        if request_model.last_name is not None:
            exist_user.last_name = request_model.last_name

        if request_model.email is not None:
            exist_user.email = str(request_model.email).lower()

        if request_model.phone is not None:
            exist_user.phone_number = request_model.phone

        if request_model.role_type is not None:
            exist_user.role_type = request_model.role_type

        if request_model.is_active is not None:
            exist_user.is_active = request_model.is_active

        session.commit()

        session.refresh(exist_user)

        return JSONResponse(
            status_code=200,
            content={
                "message": "User updated successfully",
                "data": jsonable_encoder(exist_user)
            }
        )

    except Exception as e:

        session.rollback()

        logger.exception(f"Error in create_user API: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )
    
    
# =========================================================
# REQUEST MODEL
# =========================================================

class CreateUserCredentialRequestModel(BaseModel):
    user_id   : UUID
    username  : str
    password  : str

# =========================================================
# CREATE USER CREDENTIALS
# =========================================================

@router.post(
    "/createcredentials",
    operation_id="create_user_credentials",
    tags=["Authorized API"],
    description="Create user credentials (username & password)"
)
def create_user_credentials(
    request_model: CreateUserCredentialRequestModel,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Create user credentials request started")

    try:

        exist_user = session.query(User).filter(
            User.id == str(request_model.user_id)
        ).first()

        if not exist_user:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "User not found"
                }
            )

        # TENANT ISOLATION
        if (
            current_user.role_type != RoleType.SUPERADMIN
            and str(current_user.account_id) != str(exist_user.account_id)
        ):
            return JSONResponse(
                status_code=403,
                content={"message": "Permission denied"}
            )

        duplicate_username = session.query(User).filter(
            User.username == request_model.username,
            User.id != str(request_model.user_id),
            # User.account_id == exist_user.account_id
        ).first()

        if duplicate_username:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Username already exists"
                }
            )
        
        exist_user.username = request_model.username
        exist_user.password_hash = ph.hash(request_model.password)

        session.commit()

        session.refresh(exist_user)

        return JSONResponse(
            status_code=200,
            content={
                "message": "User credentials created successfully",
                "data": jsonable_encoder(exist_user)
            }
        )

    except Exception as e:

        session.rollback()

        logger.exception(f"Error in create_user_credentials API: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )

# =========================================================
# REQUEST MODEL
# =========================================================

class ResetUserPasswordRequestModel(BaseModel):
    user_id             : UUID
    new_password        : str
    current_password    : str

# =========================================================
# RESET USER PASSWORD
# =========================================================

@router.post(
    "/resetpassword",
    operation_id="reset_user_password",
    tags=["Authorized API"],
    description="Reset user password"
)
def reset_user_password(
    request_model: ResetUserPasswordRequestModel,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Reset user password request started")

    try:

        # SELF-SERVICE ONLY
        if str(current_user.id) != str(request_model.user_id):
            return JSONResponse(
                status_code=403,
                content={"message": "Permission denied"}
            )

        exist_user = session.query(User).filter(
            User.id == str(request_model.user_id)
        ).first()

        if not exist_user:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "User not found"
                }
            )

        # VERIFY CURRENT PASSWORD
        try:
            ph.verify(exist_user.password_hash, request_model.current_password)
        except Exception:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Current password is incorrect"
                }
            )
        # CHECK NEW PASSWORD IS NOT SAME AS CURRENT PASSWORD
        try:
            ph.verify(exist_user.password_hash, request_model.new_password)
            return JSONResponse(
                status_code=400,
                content={
                    "message": "New password cannot be the same as the current password"
                }
            )
        except Exception:
            pass

        exist_user.password_hash = ph.hash(request_model.new_password)

        session.commit()

        session.refresh(exist_user)

        return JSONResponse(
            status_code=200,
            content={
                "message": "User password reset successfully",
                "data": jsonable_encoder(exist_user)
            }
        )

    except Exception as e:

        session.rollback()

        logger.exception(f"Error in reset_user_password API: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )
    
# =========================================================
# GET DEACTIVATED USERS
# =========================================================

@router.get(
    "/deactivatedusers",
    operation_id="get_deactivated_users",
    tags=["Authorized API"],
    description="Get deactivated users"
)
def get_deactivated_users(
    account_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Get deactivated users request started")

    try:

        # TENANT ISOLATION
        if (
            current_user.role_type != RoleType.SUPERADMIN
            and str(current_user.account_id) != str(account_id)
        ):
            return JSONResponse(
                status_code=403,
                content={"message": "Permission denied"}
            )

        users = (
            session.query(User)
            .filter(User.is_active == False, User.account_id == str(account_id))
            .order_by(User.created_at.desc())
            .all()
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": "Deactivated users retrieved successfully",
                "data": jsonable_encoder(users)
            }
        )

    except Exception as e:

        logger.exception(f"Error retrieving deactivated users: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )

# =========================================================
# DELETE USER (PERMANENT)
# =========================================================

@router.delete(
    "/deleteuser",
    operation_id="delete_user",
    tags=["Authorized API"],
    description="Permanently delete a user. Intended for use on already-deactivated users."
)
def delete_user(
    user_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Delete user request started")

    try:

        exist_user = session.query(User).filter(
            User.id == str(user_id)
        ).first()

        if not exist_user:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "User not found"
                }
            )

        # TENANT ISOLATION
        if (
            current_user.role_type != RoleType.SUPERADMIN
            and str(current_user.account_id) != str(exist_user.account_id)
        ):
            return JSONResponse(
                status_code=403,
                content={"message": "Permission denied"}
            )

        session.delete(exist_user)

        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "message": "User permanently deleted"
            }
        )

    except IntegrityError:

        session.rollback()

        return JSONResponse(
            status_code=400,
            content={
                "message": "Cannot permanently delete this user — they have existing expenses, categories, or other records. Keep them deactivated instead."
            }
        )

    except Exception as e:

        session.rollback()

        logger.exception(f"Error deleting user: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )