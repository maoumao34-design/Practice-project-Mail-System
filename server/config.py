from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 与 .env.example 一致；生产环境禁止使用此占位值启动
DEFAULT_INSECURE_SECRET_KEY = "please-change-this-in-env"


class Settings(BaseSettings):
    """项目配置。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "mail_system_server"
    secret_key: str = DEFAULT_INSECURE_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # 部署时请使用 APP_ENV=production（或应用内同名环境变量）
    app_env: Literal["development", "production"] = Field(
        default="development",
        description="development 时开放调试类路由；production 时关闭",
    )

    allowed_domains: list[str] = ["a.com", "b.com"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
