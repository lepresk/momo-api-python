from typing import Any, Optional

from ..support.json import optional_string


class AirtelResponseStatus:
    """The ``status`` envelope Airtel returns alongside ``data``.

    Airtel reports business failures (insufficient funds, invalid PIN, unknown
    transaction) with HTTP 200 and ``success: false`` here, so it has to be
    inspected rather than relying on the status code alone.
    """

    def __init__(
        self,
        success: bool,
        message: Optional[str] = None,
        code: Optional[str] = None,
        result_code: Optional[str] = None,
        response_code: Optional[str] = None,
    ) -> None:
        self.success = success
        self.message = message
        #: Airtel's HTTP-ish code, e.g. ``"500"``
        self.code = code
        #: Airtel's machine-readable outcome, e.g. ``"ESB000008"``
        self.result_code = result_code
        #: Airtel's long-form response code, e.g. ``"DP00800001006"``
        self.response_code = response_code

    @classmethod
    def parse(cls, body: Any) -> Optional["AirtelResponseStatus"]:
        """Return ``None`` when the payload carries no ``status`` envelope."""
        if not isinstance(body, dict) or not isinstance(body.get("status"), dict):
            return None
        status = body["status"]
        return cls(
            success=status.get("success") is not False,
            message=optional_string(status, "message"),
            code=optional_string(status, "code"),
            result_code=optional_string(status, "result_code"),
            response_code=optional_string(status, "response_code"),
        )

    def is_successful(self) -> bool:
        return self.success
