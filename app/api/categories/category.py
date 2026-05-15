################################################
# Author                : DINESHKUMAR A
# Created Date          : 14th MAY, 2026
# Last Date Modified    : 14th MAY, 2026
# Description           : Category APIs
################################################

from uuid import UUID
import logging

from fastapi import (
    APIRouter,
    Depends
)

from fastapi.responses import JSONResponse

from pydantic import (
    BaseModel,
    Field
)

from sqlalchemy.orm import Session
from sqlalchemy import func

from api.common.models import (
    Category,
    User,
    RoleType
)

from api.common.session import get_db

from app.api.authentication.authentication import (
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
# REQUEST MODELS
# =========================================================

class CategoryRequestModel(BaseModel):

    category_id: UUID | None = None

    category_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category name"
    )


# =========================================================
# GET CATEGORIES
# =========================================================

@router.get(
    "/getcategories",
    operation_id="get_categories",
    tags=["Authorized API"],
    description="Retrieve system and account categories"
)
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:

        # =====================================================
        # SUPER ADMIN
        # =====================================================

        if current_user.role_type == RoleType.SUPERADMIN:

            categories = db.query(Category).filter(
                Category.is_active == True
            ).order_by(
                Category.category_name.asc()
            ).all()

        # =====================================================
        # ACCOUNT USER
        # =====================================================

        else:

            categories = db.query(Category).filter(
                Category.is_active == True,

                (
                    (Category.is_system_category == True)
                    |
                    (Category.account_id == current_user.account_id)
                )
            ).order_by(
                Category.category_name.asc()
            ).all()

        return JSONResponse(
            status_code=200,
            content={
                "message": (
                    "Categories retrieved successfully"
                ),
                "data": [
                    {
                        "id": str(category.id),

                        "category_name": (
                            category.category_name
                        ),

                        "account_id": (
                            str(category.account_id)
                            if category.account_id
                            else None
                        ),

                        "is_system_category": (
                            category.is_system_category
                        ),

                        "is_active": (
                            category.is_active
                        )
                    }
                    for category in categories
                ]
            }
        )

    except Exception:

        logger.exception(
            "Error retrieving categories"
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error"
            }
        )


# =========================================================
# CREATE / UPDATE CATEGORY
# =========================================================

@router.post(
    "/savecategory",
    operation_id="save_category",
    tags=["Authorized API"],
    description="Create or update category"
)
def save_category(
    request: CategoryRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:

        # =====================================================
        # CLEAN CATEGORY NAME
        # =====================================================

        category_name = request.category_name.strip()

        if not category_name:

            return JSONResponse(
                status_code=400,
                content={
                    "message": (
                        "Category name is required"
                    )
                }
            )

        # =====================================================
        # SUPER ADMIN CATEGORY
        # =====================================================

        if current_user.role_type == RoleType.SUPERADMIN:

            account_id = None

            is_system_category = True

        # =====================================================
        # ACCOUNT CATEGORY
        # =====================================================

        else:

            account_id = current_user.account_id

            is_system_category = False

        # =====================================================
        # CREATE CATEGORY
        # =====================================================

        if request.category_id is None:

            # DUPLICATE CHECK
            existing_category = db.query(Category).filter(
                func.lower(
                    Category.category_name
                ) == category_name.lower(),

                Category.account_id == account_id,

                Category.is_active == True
            ).first()

            if existing_category:

                return JSONResponse(
                    status_code=400,
                    content={
                        "message": (
                            "Category already exists"
                        )
                    }
                )

            # CREATE CATEGORY
            new_category = Category(
                category_name=category_name,
                account_id=account_id,
                created_by=current_user.id,
                is_system_category=is_system_category,
                is_active=True
            )

            db.add(new_category)

            db.commit()

            db.refresh(new_category)

            return JSONResponse(
                status_code=201,
                content={
                    "message": (
                        "Category created successfully"
                    ),
                    "data": {
                        "id": str(new_category.id),

                        "category_name": (
                            new_category.category_name
                        ),

                        "account_id": (
                            str(new_category.account_id)
                            if new_category.account_id
                            else None
                        ),

                        "is_system_category": (
                            new_category.is_system_category
                        ),

                        "is_active": (
                            new_category.is_active
                        )
                    }
                }
            )

        # =====================================================
        # UPDATE CATEGORY
        # =====================================================

        category = db.query(Category).filter(
            Category.id == str(request.category_id),
            Category.is_active == True
        ).first()

        if not category:

            return JSONResponse(
                status_code=404,
                content={
                    "message": "Category not found"
                }
            )

        # =====================================================
        # ACCESS VALIDATION
        # =====================================================

        if current_user.role_type != RoleType.SUPERADMIN:

            if (
                category.account_id
                != current_user.account_id
            ):

                return JSONResponse(
                    status_code=403,
                    content={
                        "message": (
                            "Permission denied"
                        )
                    }
                )

        # =====================================================
        # DUPLICATE CHECK
        # =====================================================

        duplicate_category = db.query(Category).filter(
            func.lower(
                Category.category_name
            ) == category_name.lower(),

            Category.account_id == category.account_id,

            Category.id != str(request.category_id),

            Category.is_active == True
        ).first()

        if duplicate_category:

            return JSONResponse(
                status_code=400,
                content={
                    "message": (
                        "Category already exists"
                    )
                }
            )

        # =====================================================
        # UPDATE CATEGORY
        # =====================================================

        category.category_name = category_name

        db.commit()

        db.refresh(category)

        return JSONResponse(
            status_code=200,
            content={
                "message": (
                    "Category updated successfully"
                ),
                "data": {
                    "id": str(category.id),

                    "category_name": (
                        category.category_name
                    ),

                    "account_id": (
                        str(category.account_id)
                        if category.account_id
                        else None
                    ),

                    "is_system_category": (
                        category.is_system_category
                    ),

                    "is_active": (
                        category.is_active
                    )
                }
            }
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Error saving category"
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error"
            }
        )

# ========================================================
# DELETE CATEGORY
# ======================================================== 
@router.delete(
    "/deletecategory",
    operation_id="delete_category",
    tags=["Authorized API"],
    description="Soft delete category"
)

def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:

        category = db.query(Category).filter(
            Category.id == str(category_id),
            Category.is_active == True
        ).first()

        if not category:

            return JSONResponse(
                status_code=404,
                content={
                    "message": "Category not found"
                }
            )

        # =====================================================
        # ACCESS VALIDATION
        # =====================================================

        if current_user.role_type != RoleType.SUPERADMIN:

            if (
                category.account_id
                != current_user.account_id
            ):

                return JSONResponse(
                    status_code=403,
                    content={
                        "message": (
                            "Permission denied"
                        )
                    }
                )

        # =====================================================
        # SOFT DELETE CATEGORY
        # =====================================================

        category.is_active = False

        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "message": (
                    "Category deleted successfully"
                )
            }
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Error deleting category"
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error"
            }
        )