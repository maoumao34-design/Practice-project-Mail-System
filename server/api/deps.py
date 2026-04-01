from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from server.core.security import decode_access_token


http_bearer = HTTPBearer(auto_error=True)


def get_auth_context(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> dict:
    """接口层：从 Bearer 解析出已通过签名校验的 email 与 domain。"""
    try:
        return decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
