"""Cache key construction."""


def profile_cache_key(user_id: int, locale: str) -> str:
    if not locale:
        raise ValueError("locale is required")
    return f"profile:{user_id}"
