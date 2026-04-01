from uuid import uuid4

from fastapi.testclient import TestClient

from server.core.database import get_session_by_domain
from server.main import app
from server.repositories.user_repo import get_user_by_email


def test_user_data_not_visible_across_domain_dbs() -> None:
    email_a = f"iso_a_{uuid4().hex[:10]}@a.com"
    email_b = f"iso_b_{uuid4().hex[:10]}@b.com"
    password = "strongpass123"
    with TestClient(app) as client:
        assert client.post(
            "/api/v1/auth/register",
            json={"email": email_a, "password": password},
        ).status_code == 201
        assert client.post(
            "/api/v1/auth/register",
            json={"email": email_b, "password": password},
        ).status_code == 201

    with get_session_by_domain("a.com") as session:
        assert get_user_by_email(session, email_a) is not None
        assert get_user_by_email(session, email_b) is None
    with get_session_by_domain("b.com") as session:
        assert get_user_by_email(session, email_b) is not None
        assert get_user_by_email(session, email_a) is None


def test_token_context_reflects_domain() -> None:
    email = f"iso_ctx_{uuid4().hex[:10]}@a.com"
    password = "strongpass123"
    with TestClient(app) as client:
        assert client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        ).status_code == 201
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        ctx_res = client.get(
            "/api/v1/auth/token-context",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ctx_res.status_code == 200
        body = ctx_res.json()
        assert body["email"] == email
        assert body["domain"] == "a.com"


def test_intended_domain_header_cross_domain_denied() -> None:
    email = f"iso_hdr_{uuid4().hex[:10]}@a.com"
    password = "strongpass123"
    with TestClient(app) as client:
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        token = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        ).json()["access_token"]
        res = client.get(
            "/api/v1/auth/token-context",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Intended-Domain": "b.com",
            },
        )
        assert res.status_code == 403
        assert res.json()["detail"] == "Cross-domain request denied"


def test_token_context_route_not_registered_when_app_env_production(
    monkeypatch,
) -> None:
    """生产进程应在首次加载前设置 APP_ENV=production，此时不注册探针路由。

    路由不存在时对任意请求均返回统一 404，且不执行 Bearer 校验，避免 401/404 区分有效令牌。
    """
    monkeypatch.setenv("APP_ENV", "production")
    import importlib

    import server.api.auth as auth_module
    import server.config as config_module

    config_module.get_settings.cache_clear()
    importlib.reload(auth_module)
    assert not any(
        "token-context" in (getattr(r, "path", "") or "")
        for r in auth_module.router.routes
    )
