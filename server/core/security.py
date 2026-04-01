from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from server.config import get_settings
from server.core.domain_router import extract_domain_from_email


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 任一有效 bcrypt 串；未知用户登录时也走 verify，削弱「是否存在用户」的时序侧信道
_LOGIN_TIMING_DUMMY_HASH = (
    "$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def dummy_password_verify_for_timing(plain_password: str) -> None:
    """对虚构哈希执行一次校验，用于对齐「用户不存在」与「密码错误」的耗时量级。"""
    verify_password(plain_password, _LOGIN_TIMING_DUMMY_HASH)


def create_access_token(subject: str, domain: str) -> str:
    """签发 JWT；sub 为邮箱，domain 必须与邮箱域名一致（调用方保证传入已规范化的邮箱）。"""
    if extract_domain_from_email(subject) != domain:
        raise ValueError("Token domain does not match email")
    settings = get_settings()
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "domain": domain,
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """解析 JWT，返回 email、domain；缺失或不一致则抛 ValueError。"""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    email = payload.get("sub")
    domain = payload.get("domain")
    if not isinstance(email, str) or not isinstance(domain, str):
        raise ValueError("Invalid token payload")
    try:
        derived = extract_domain_from_email(email)
    except ValueError as exc:
        raise ValueError("Invalid token email") from exc
    if derived != domain:
        raise ValueError("Token domain mismatch")
    return {"email": email, "domain": domain}
