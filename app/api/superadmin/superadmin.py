################################################
# Description           : Super Admin management APIs
################################################

from typing import Optional
from uuid import UUID
import logging

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.common.models import User, RoleType
from api.common.session import get_db
from api.authentication.authentication import require_superadmin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pd",
    responses={404: {"description": "Not found"}}
)

ph = PasswordHasher()


def serialize_superadmin(user: User) -> dict:
    # Built explicitly (never jsonable_encoder(user)) so password_hash
    # can never leak into a response.
    return {
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "username": user.username,
        "role_type": user.role_type.value,
        "is_active": user.is_active,
    }


# =========================================================
# REQUEST MODEL
# =========================================================

class CreateSuperAdminRequestModel(BaseModel):
    first_name : str = Field(..., min_length=1, max_length=50)
    last_name  : Optional[str] = Field(default=None, max_length=50)
    email      : str = Field(...)
    phone      : Optional[str] = None
    username   : str = Field(..., min_length=1, max_length=50)
    password   : str = Field(..., min_length=8)


# =========================================================
# CREATE SUPER ADMIN
# =========================================================

@router.post(
    "/createsuperadmin",
    operation_id="create_superadmin",
    tags=["Authorized API"],
    description="Create a new Super Admin. Requires an existing Super Admin."
)
def create_superadmin(
    request: CreateSuperAdminRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):

    try:

        email = request.email.strip().lower()

        # =================================================
        # DUPLICATE CHECKS
        # =================================================

        if db.query(User).filter(User.email == email).first():

            return JSONResponse(
                status_code=400,
                content={"message": "Email already exists"}
            )

        if db.query(User).filter(User.username == request.username).first():

            return JSONResponse(
                status_code=400,
                content={"message": "Username already exists"}
            )

        if request.phone and db.query(User).filter(
            User.phone_number == request.phone
        ).first():

            return JSONResponse(
                status_code=400,
                content={"message": "Phone number already exists"}
            )

        # =================================================
        # CREATE SUPER ADMIN
        # =================================================

        new_superadmin = User(
            first_name=request.first_name,
            last_name=request.last_name,
            email=email,
            phone_number=request.phone,
            username=request.username,
            password_hash=ph.hash(request.password),
            role_type=RoleType.SUPERADMIN,
            account_id=None,
            is_active=True
        )

        db.add(new_superadmin)
        db.commit()
        db.refresh(new_superadmin)

        return JSONResponse(
            status_code=201,
            content={
                "message": "Super Admin created successfully",
                "data": serialize_superadmin(new_superadmin)
            }
        )

    except Exception:

        db.rollback()
        logger.exception("Error creating super admin")

        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )


# =========================================================
# REQUEST MODEL
# =========================================================

class UpdateSuperAdminRequestModel(BaseModel):
    first_name : Optional[str] = Field(default=None, min_length=1, max_length=50)
    last_name  : Optional[str] = Field(default=None, max_length=50)
    email      : Optional[str] = None
    phone      : Optional[str] = None
    is_active  : Optional[bool] = None


# =========================================================
# UPDATE SUPER ADMIN
# =========================================================

@router.put(
    "/updatesuperadmin/{user_id}",
    operation_id="update_superadmin",
    tags=["Authorized API"],
    description="Update an existing Super Admin's profile. Requires an existing Super Admin."
)
def update_superadmin(
    user_id: UUID,
    request: UpdateSuperAdminRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):

    try:

        target = db.query(User).filter(
            User.id == str(user_id),
            User.role_type == RoleType.SUPERADMIN
        ).first()

        if not target:

            return JSONResponse(
                status_code=404,
                content={"message": "Super Admin not found"}
            )

        # =================================================
        # DUPLICATE CHECKS
        # =================================================

        if request.email is not None:

            email = request.email.strip().lower()

            duplicate = db.query(User).filter(
                User.email == email,
                User.id != str(user_id)
            ).first()

            if duplicate:

                return JSONResponse(
                    status_code=400,
                    content={"message": "Email already exists"}
                )

            target.email = email

        if request.phone is not None:

            duplicate = db.query(User).filter(
                User.phone_number == request.phone,
                User.id != str(user_id)
            ).first()

            if duplicate:

                return JSONResponse(
                    status_code=400,
                    content={"message": "Phone number already exists"}
                )

            target.phone_number = request.phone

        # =================================================
        # UPDATE FIELDS
        # =================================================

        if request.first_name is not None:
            target.first_name = request.first_name

        if request.last_name is not None:
            target.last_name = request.last_name

        if request.is_active is not None:
            target.is_active = request.is_active

        db.commit()
        db.refresh(target)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Super Admin updated successfully",
                "data": serialize_superadmin(target)
            }
        )

    except Exception:

        db.rollback()
        logger.exception("Error updating super admin")

        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )
