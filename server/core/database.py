from pathlib import Path

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from server.core.domain_router import DOMAIN_STORAGE_MAP, get_storage_name_by_domain


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"

ENGINES = {
    "domain_a": create_engine(
        f"sqlite:///{(DATA_ROOT / 'domain_a' / 'db' / 'mail.db').as_posix()}",
        connect_args={"check_same_thread": False},
    ),
    "domain_b": create_engine(
        f"sqlite:///{(DATA_ROOT / 'domain_b' / 'db' / 'mail.db').as_posix()}",
        connect_args={"check_same_thread": False},
    ),
}


def create_db_and_tables() -> None:
    for engine in ENGINES.values():
        SQLModel.metadata.create_all(engine)
        _ensure_user_table_columns(engine)


def _ensure_user_table_columns(engine) -> None:
    """最小迁移：为既有 user 表补齐新增字段。"""
    with engine.begin() as conn:
        columns = conn.execute(text("PRAGMA table_info(user)")).fetchall()
        column_names = {row[1] for row in columns}
        if "failed_login_attempts" not in column_names:
            conn.execute(
                text(
                    "ALTER TABLE user ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0"
                )
            )
        if "locked_until" not in column_names:
            conn.execute(text("ALTER TABLE user ADD COLUMN locked_until DATETIME"))


def get_session_by_storage(storage_name: str) -> Session:
    engine = ENGINES.get(storage_name)
    if not engine:
        raise ValueError("Storage engine not found")
    return Session(engine)


def get_session_by_domain(domain: str) -> Session:
    storage_name = DOMAIN_STORAGE_MAP.get(domain)
    if not storage_name:
        raise ValueError("Domain storage is not configured")
    return get_session_by_storage(storage_name)


def get_session_for_token_domain(domain: str) -> Session:
    """存储层入口：仅使用已从 JWT 校验过的 domain；再次校验允许列表与存储映射。"""
    get_storage_name_by_domain(domain)
    return get_session_by_domain(domain)
