from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.api.auth import router as auth_router
from server.api.health import router as health_router
from server.config import DEFAULT_INSECURE_SECRET_KEY, get_settings
from server.core.database import create_db_and_tables
from server.core.domain_router import assert_allowed_domains_match_storage_map
from server.models.user import User  # noqa: F401  # 确保模型被加载进 metadata


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    s = get_settings()
    if s.app_env == "production":
        if (not s.secret_key) or (s.secret_key == DEFAULT_INSECURE_SECRET_KEY):
            raise RuntimeError(
                "生产环境必须在环境变量中设置强随机 SECRET_KEY，"
                "且不得使用占位默认值；参见 README / .env.example。"
            )
    assert_allowed_domains_match_storage_map(s.allowed_domains)
    create_db_and_tables()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(health_router)
app.include_router(auth_router)
