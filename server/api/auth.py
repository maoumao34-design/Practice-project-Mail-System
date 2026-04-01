from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator

from server.api.deps import get_auth_context
from server.config import get_settings
from server.services.auth_service import AccountLockedError, login_user, register_user


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        if isinstance(v, str):
            return v.lower().strip()
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        if isinstance(v, str):
            return v.lower().strip()
        return v


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> dict:
    try:
        result = register_user(email=str(payload.email), password=payload.password)
        return {"message": "Register success", "user": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login")
def login(payload: LoginRequest) -> dict:
    try:
        result = login_user(email=str(payload.email), password=payload.password)
        return result
    except AccountLockedError as exc:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


if get_settings().app_env != "production":

    @router.get("/token-context", include_in_schema=True)
    def token_context(
        auth: Annotated[dict, Depends(get_auth_context)],
        x_intended_domain: Annotated[str | None, Header(alias="X-Intended-Domain")] = None,
    ) -> dict:
        """
        返回当前访问令牌对应的邮箱与域（M1 隔离框架探针，仅 development）。
        若携带 X-Intended-Domain 且与令牌域不一致，拒绝请求（接口层跨域校验演示）。
        """
        if x_intended_domain:
            intended = x_intended_domain.lower().strip()
            if intended != auth["domain"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-domain request denied",
                )
        return {"email": auth["email"], "domain": auth["domain"]}
