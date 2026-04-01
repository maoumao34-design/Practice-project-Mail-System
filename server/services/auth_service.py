import re
from datetime import datetime, timedelta, timezone

from server.core.database import get_session_by_domain
from server.core.domain_router import extract_domain_from_email, get_storage_name_by_domain
from server.core.security import (
    create_access_token,
    dummy_password_verify_for_timing,
    hash_password,
    verify_password,
)
from server.repositories.user_repo import create_user, get_user_by_email


MAX_LOGIN_RETRY = 5
LOCK_MINUTES = 15


class AccountLockedError(ValueError):
    """账号被临时锁定。"""


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def validate_password_policy(password: str) -> None:
    """M1 密码策略：8-64，至少包含 1 个字母和 1 个数字。"""
    if len(password) < 8 or len(password) > 64:
        raise ValueError("Password length must be between 8 and 64")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one number")


def register_user(email: str, password: str) -> dict:
    domain = extract_domain_from_email(email)
    get_storage_name_by_domain(domain)
    validate_password_policy(password)

    with get_session_by_domain(domain) as session:
        existing_user = get_user_by_email(session, email)
        if existing_user:
            # 与登录侧一致：不泄露「邮箱是否已注册」
            raise ValueError("Unable to complete registration")

        hashed = hash_password(password)
        user = create_user(session, email, hashed)
        return {"id": user.id, "email": user.email}


def login_user(email: str, password: str) -> dict:
    domain = extract_domain_from_email(email)
    get_storage_name_by_domain(domain)

    with get_session_by_domain(domain) as session:
        user = get_user_by_email(session, email)
        if not user:
            dummy_password_verify_for_timing(password)
            raise ValueError("Invalid email or password")

        now_utc = datetime.now(timezone.utc)
        locked_until_utc = _as_utc(user.locked_until)
        if locked_until_utc and locked_until_utc > now_utc:
            raise AccountLockedError("Account is locked. Try again later.")

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_RETRY:
                user.locked_until = now_utc + timedelta(minutes=LOCK_MINUTES)
            session.add(user)
            session.commit()
            locked_until_utc = _as_utc(user.locked_until)
            if locked_until_utc and locked_until_utc > now_utc:
                raise AccountLockedError("Account is locked. Try again later.")
            raise ValueError("Invalid email or password")

        user.failed_login_attempts = 0
        user.locked_until = None
        session.add(user)
        session.commit()

    token = create_access_token(subject=email, domain=domain)
    return {"access_token": token, "token_type": "bearer"}
