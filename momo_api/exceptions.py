from typing import Optional


class MomoException(Exception):
    """Base exception for MTN MoMo API errors."""

    def __init__(self, message: str = "", status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class BadRequestException(MomoException):
    """Raised when the API returns HTTP 400."""


class InvalidSubscriptionKeyException(MomoException):
    """Raised when the API returns HTTP 401 (invalid subscription key)."""


class ResourceNotFoundException(MomoException):
    """Raised when the API returns HTTP 404."""


class ConflictException(MomoException):
    """Raised when the API returns HTTP 409 (duplicate reference ID, etc.)."""


class InternalServerErrorException(MomoException):
    """Raised when the API returns HTTP 500."""


def create_exception(status_code: int, message: Optional[str] = None) -> MomoException:
    """Factory that maps HTTP status codes to the appropriate exception class."""
    msg = message or ""
    mapping = {
        400: BadRequestException,
        401: InvalidSubscriptionKeyException,
        404: ResourceNotFoundException,
        409: ConflictException,
        500: InternalServerErrorException,
    }
    exc_class = mapping.get(status_code, MomoException)
    return exc_class(msg, status_code=status_code)
