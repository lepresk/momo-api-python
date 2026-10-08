from typing import Any, Optional


def optional_string(data: Any, key: str) -> Optional[str]:
    """Read a string field, treating a missing, empty or non-string value as absent."""
    if not isinstance(data, dict):
        return None
    value = data.get(key)
    return value if isinstance(value, str) and value != "" else None
