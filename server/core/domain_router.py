from server.config import get_settings


DOMAIN_STORAGE_MAP = {
    "a.com": "domain_a",
    "b.com": "domain_b",
}


def extract_domain_from_email(email: str) -> str:
    if "@" not in email:
        raise ValueError("Invalid email format")
    return email.rsplit("@", 1)[1].lower().strip()


def get_storage_name_by_domain(domain: str) -> str:
    settings = get_settings()
    if domain not in settings.allowed_domains:
        raise ValueError("Domain is not allowed")
    storage_name = DOMAIN_STORAGE_MAP.get(domain)
    if not storage_name:
        raise ValueError("Domain storage is not configured")
    return storage_name


def assert_allowed_domains_match_storage_map(allowed_domains: list[str]) -> None:
    """启动时自检：`allowed_domains` 与 `DOMAIN_STORAGE_MAP` 必须完全一致，避免运维只改一侧。"""
    allowed = {d.lower().strip() for d in allowed_domains}
    mapped = set(DOMAIN_STORAGE_MAP.keys())
    if allowed != mapped:
        raise RuntimeError(
            "allowed_domains 必须与 DOMAIN_STORAGE_MAP 的键集合完全一致："
            f"allowed={sorted(allowed)!r}, mapped={sorted(mapped)!r}"
        )
