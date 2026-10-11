from typing import Any, Optional


def optional_string(data: Any, key: str) -> Optional[str]:
    """Read a string field, treating a missing, empty or non-string value as absent."""
    if not isinstance(data, dict):
        return None
    value = data.get(key)
    return value if isinstance(value, str) and value != "" else None


def to_int(value: Any, default: int = 0) -> int:
    """Read an integer field that may arrive as a number, a numeric string such as
    ``"3599.0"``, or null."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default
