################################################
# Author                : DINESHKUMAR A
# Description           : Authentication APIs
################################################

from datetime import datetime, timedelta, timezone
import hashlib
import logging
import os

import jwt

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError
)

from sqlalchemy import or_
from sqlalchemy.orm import Session

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request
)

from fastapi.responses import JSONResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

from pydantic import BaseModel, Field

from api.common.models import (
    User,
    RefreshToken
)

from api.common.session import get_db
from api.common.variables import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
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
# SECURITY CONFIG
# =========================================================

Password = PasswordHasher()

bearer_scheme = HTTPBearer()

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not configured")


# =========================================================
# REQUEST MODELS
# =========================================================

class LoginRequestModel(BaseModel):
    nameoremail: str = Field(...)
    password: str = Field(...)


class RefreshTokenRequestModel(BaseModel):
    refresh_token: str


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def hash_token(token: str) -> str:

    return hashlib.sha256(
        token.encode()
    ).hexdigest()


def create_token(
    user: User,
    token_type: str,
    expires_delta: timedelta
):

    now = datetime.now(timezone.utc)

    expires_at = now + expires_delta

    payload = {
        "sub": str(user.id),
        "account_id": str(user.account_id),
        "role": user.role_type.value if user.role_type else None,
        "type": token_type,
        "iat": now,
        "exp": expires_at
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token, expires_at


# =========================================================
# GET CURRENT USER
# =========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db)
):

    try:

        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    except jwt.InvalidTokenError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if payload.get("type") != "access":

        raise HTTPException(
            status_code=401,
            detail="Invalid token type"
        )

    user = db.query(User).filter(
        User.id == payload.get("sub"),
        User.is_active == True
    ).first()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found or inactive"
        )

    return user


# =========================================================
# LOGIN API
# =========================================================

@router.post(
    "/login",
    operation_id="login",
    tags=["Authentication API"]
)
def login(
    request_model: LoginRequestModel,
    request: Request,
    db: Session = Depends(get_db)
):

    try:

        login_name = request_model.nameoremail.strip()

        user = db.query(User).filter(
            or_(
                User.email == login_name.lower(),
                User.username == login_name
            )
        ).first()

        if not user or not user.password_hash:

            return JSONResponse(
                status_code=401,
                content={
                    "message": "Invalid username/email or password"
                }
            )

        try:

            Password.verify(
                user.password_hash,
                request_model.password
            )

        except (
            InvalidHashError,
            VerifyMismatchError,
            VerificationError
        ):

            return JSONResponse(
                status_code=401,
                content={
                    "message": "Invalid username/email or password"
                }
            )

        # PASSWORD REHASH
        if Password.check_needs_rehash(user.password_hash):

            user.password_hash = Password.hash(
                request_model.password
            )

        # USER ACTIVE CHECK
        if not user.is_active:

            return JSONResponse(
                status_code=403,
                content={
                    "message": "User account inactive"
                }
            )

        # ACCOUNT ACTIVE CHECK
        if user.account and not user.account.is_active:

            return JSONResponse(
                status_code=403,
                content={
                    "message": "Account inactive"
                }
            )

        # CREATE ACCESS TOKEN
        access_token, access_expires_at = create_token(
            user=user,
            token_type="access",
            expires_delta=timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )

        # CREATE REFRESH TOKEN
        refresh_token, refresh_expires_at = create_token(
            user=user,
            token_type="refresh",
            expires_delta=timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
        )

        # HASH TOKEN
        hashed_refresh_token = hash_token(
            refresh_token
        )

        # STORE REFRESH TOKEN
        db.add(
            RefreshToken(
                user_id=user.id,
                hashed_refresh_token=hashed_refresh_token,
                login_ip=request.client.host,
                user_agent=request.headers.get("user-agent"),
                expires_at=refresh_expires_at
            )
        )

        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_at": access_expires_at.isoformat(),
                "user": {
                    "user_id": str(user.id),
                    "account_id": str(user.account_id),
                    "email": user.email,
                    "username": user.username,
                    "role": (
                        user.role_type.value
                        if user.role_type
                        else None
                    )
                }
            }
        )

    except Exception:

        db.rollback()

        logger.exception("Error in login API")

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )


# =========================================================
# REFRESH TOKEN API
# =========================================================

@router.post(
    "/refresh-token",
    operation_id="refresh_token",
    tags=["Authentication API"]
)
def refresh_token(
    request_model: RefreshTokenRequestModel,
    request: Request,
    db: Session = Depends(get_db)
):

    try:

        incoming_refresh_token = (
            request_model.refresh_token
        )

        hashed_token = hash_token(
            incoming_refresh_token
        )

        stored_token = db.query(
            RefreshToken
        ).filter(
            RefreshToken.hashed_refresh_token == hashed_token,
            RefreshToken.is_revoked == False
        ).first()

        if not stored_token:

            return JSONResponse(
                status_code=401,
                content={
                    "message": "Invalid refresh token"
                }
            )

        # CHECK EXPIRY
        if stored_token.expires_at < datetime.now(
            timezone.utc
        ):

            stored_token.is_revoked = True
            stored_token.revoked_at = datetime.now(
                timezone.utc
            )

            db.commit()

            return JSONResponse(
                status_code=401,
                content={
                    "message": "Refresh token expired"
                }
            )

        # VERIFY JWT
        try:

            payload = jwt.decode(
                incoming_refresh_token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )

        except jwt.ExpiredSignatureError:

            return JSONResponse(
                status_code=401,
                content={
                    "message": "Refresh token expired"
                }
            )

        except jwt.InvalidTokenError:

            return JSONResponse(
                status_code=401,
                content={
                    "message": "Invalid refresh token"
                }
            )

        # VALIDATE TYPE
        if payload.get("type") != "refresh":

            return JSONResponse(
                status_code=401,
                content={
                    "message": "Invalid token type"
                }
            )

        # GET USER
        user = db.query(User).filter(
            User.id == payload.get("sub"),
            User.is_active == True
        ).first()

        if not user:

            return JSONResponse(
                status_code=401,
                content={
                    "message": "User not found or inactive"
                }
            )

        # CREATE NEW ACCESS TOKEN
        access_token, access_expires_at = create_token(
            user=user,
            token_type="access",
            expires_delta=timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )

        # REFRESH TOKEN ROTATION
        new_refresh_token, refresh_expires_at = create_token(
            user=user,
            token_type="refresh",
            expires_delta=timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
        )

        # REVOKE OLD TOKEN
        stored_token.is_revoked = True

        stored_token.revoked_at = datetime.now(
            timezone.utc
        )

        stored_token.last_used_ip = request.client.host

        stored_token.last_used_time = datetime.now(
            timezone.utc
        )

        # STORE NEW TOKEN
        db.add(
            RefreshToken(
                user_id=user.id,
                hashed_refresh_token=hash_token(
                    new_refresh_token
                ),
                login_ip=request.client.host,
                user_agent=request.headers.get(
                    "user-agent"
                ),
                expires_at=refresh_expires_at
            )
        )

        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "message": "Token refreshed successfully",
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_at": access_expires_at.isoformat()
            }
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Error in refresh token API"
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )


# =========================================================
# LOGOUT API
# =========================================================

@router.post(
    "/logout",
    operation_id="logout",
    tags=["Authentication API"]
)
def logout(
    request_model: RefreshTokenRequestModel,
    db: Session = Depends(get_db)
):

    try:

        hashed_token = hash_token(
            request_model.refresh_token
        )

        stored_token = db.query(
            RefreshToken
        ).filter(
            RefreshToken.hashed_refresh_token == hashed_token,
            RefreshToken.is_revoked == False
        ).first()

        if not stored_token:

            return JSONResponse(
                status_code=401,
                content={
                    "message": "Invalid refresh token"
                }
            )

        stored_token.is_revoked = True

        stored_token.revoked_at = datetime.now(
            timezone.utc
        )

        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "message": "Logout successful"
            }
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Error in logout API"
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )


# =========================================================
# LOGOUT ALL DEVICES API
# =========================================================

@router.post(
    "/logout-all",
    operation_id="logout_all",
    tags=["Authentication API"]
)
def logout_all(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    try:

        db.query(
            RefreshToken
        ).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False
        ).update(
            {
                "is_revoked": True,
                "revoked_at": datetime.now(
                    timezone.utc
                )
            },
            synchronize_session=False
        )

        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "message": (
                    "Logged out from all devices"
                )
            }
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Error in logout all API"
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error"
            }
        )