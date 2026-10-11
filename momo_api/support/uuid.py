import re
import uuid

# Any version: callers may derive a deterministic v5 UUID from a business key
_UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def assert_uuid(value: str, name: str) -> None:
    """Raise ``ValueError`` unless ``value`` is a UUID, before anything is sent."""
    if not isinstance(value, str) or not _UUID_PATTERN.fullmatch(value):
        raise ValueError(f'{name} must be a UUID, got "{value}"')
