import json
from typing import Dict, Optional, Tuple, Type

from .models.error_reason import ErrorReason
from .support.json import optional_string


class MomoException(Exception):
    """Base exception for MTN MoMo and Airtel Money API errors."""

    default_message = ""
    default_status: Optional[int] = None

    def __init__(
        self,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        reason: Optional[ErrorReason] = None,
        body: Optional[str] = None,
    ) -> None:
        message = message or self.default_message
        super().__init__(message)
        self.message = message
        #: HTTP status code returned by the API
        self.status_code = status_code if status_code is not None else self.default_status
        #: The failure reason from the API payload, when present
        self.reason = reason
        #: Raw response body, kept for debugging
        self.body = body

    @property
    def code(self) -> Optional[str]:
        """Machine-readable error code from the API payload, when present."""
        return self.reason.code if self.reason and self.reason.code else None


class BadRequestException(MomoException):
    """HTTP 400: invalid data was sent in the request."""

    default_message = "Bad request, e.g. invalid data was sent in the request."
    default_status = 400


class BadResourceException(MomoException):
    """HTTP 400: an incorrectly formatted reference id was provided."""

    default_message = "Bad request, e.g. an incorrectly formatted reference id was provided."
    default_status = 400


class InvalidSubscriptionKeyException(MomoException):
    """HTTP 401: invalid subscription key."""

    default_message = "Invalid subscription key"
    default_status = 401


class ResourceNotFoundException(MomoException):
    """HTTP 404: reference id not found, or closed in the sandbox."""

    default_message = "Not found, reference id not found or closed in sandbox"
    default_status = 404


class ConflictException(MomoException):
    """HTTP 409: duplicated reference id."""

    default_message = "Conflict, duplicated reference id"
    default_status = 409


class InternalServerErrorException(MomoException):
    """HTTP 500."""

    default_message = "Internal server error"
    default_status = 500


_BY_STATUS: Dict[int, Type[MomoException]] = {
    400: BadRequestException,
    401: InvalidSubscriptionKeyException,
    404: ResourceNotFoundException,
    409: ConflictException,
    500: InternalServerErrorException,
}


def _parse_error_body(body: Optional[str]) -> Tuple[Optional[str], Optional[ErrorReason]]:
    """MTN and Airtel report failures as a JSON body such as
    ``{"code":"NOT_ENOUGH_FUNDS","message":"..."}``. Parsing it lets the raised
    exception carry a readable message and the same typed ``ErrorReason`` a
    failed ``Transaction`` exposes."""
    try:
        parsed = json.loads(body or "")
    except ValueError:
        return None, None
    if not isinstance(parsed, dict):
        return None, None
    return optional_string(parsed, "message"), ErrorReason.from_dict(parsed)


def create_exception(status_code: int, body: Optional[str] = None) -> MomoException:
    """Map an HTTP status and response body to the matching exception."""
    message, reason = _parse_error_body(body)
    exception_class = _BY_STATUS.get(status_code)
    if exception_class is not None:
        return exception_class(message, reason=reason, body=body)
    return MomoException(
        message or f"Operation failed with status {status_code}", status_code, reason, body
    )
