from typing import Any

from ..support.json import optional_string


class ErrorReason:
    """The ``{code, message}`` pair an API returns to explain a failure.

    Get Status sends a bare string code instead; it becomes an ``ErrorReason``
    with an empty message.

    The constants and predicates below are MTN's vocabulary. An Airtel failure is
    carried by the same type, and ``code`` and ``message`` are meaningful, but its
    codes (``ESB000008``, ...) match none of the predicates: match on ``code``
    rather than ``is_not_enough_funds()`` when handling Airtel errors.
    """

    PAYEE_NOT_FOUND = "PAYEE_NOT_FOUND"
    PAYER_NOT_FOUND = "PAYER_NOT_FOUND"
    NOT_ALLOWED = "NOT_ALLOWED"
    NOT_ALLOWED_TARGET_ENVIRONMENT = "NOT_ALLOWED_TARGET_ENVIRONMENT"
    INVALID_CALLBACK_URL_HOST = "INVALID_CALLBACK_URL_HOST"
    INVALID_CURRENCY = "INVALID_CURRENCY"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_PROCESSING_ERROR = "INTERNAL_PROCESSING_ERROR"
    NOT_ENOUGH_FUNDS = "NOT_ENOUGH_FUNDS"
    PAYER_LIMIT_REACHED = "PAYER_LIMIT_REACHED"
    PAYEE_NOT_ALLOWED_TO_RECEIVE = "PAYEE_NOT_ALLOWED_TO_RECEIVE"
    PAYMENT_NOT_APPROVED = "PAYMENT_NOT_APPROVED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    EXPIRED = "EXPIRED"
    TRANSACTION_CANCELED = "TRANSACTION_CANCELED"
    RESOURCE_ALREADY_EXIST = "RESOURCE_ALREADY_EXIST"
    COULD_NOT_PERFORM_TRANSACTION = "COULD_NOT_PERFORM_TRANSACTION"
    SENDER_ACCOUNT_NOT_ACTIVE = "SENDER_ACCOUNT_NOT_ACTIVE"
    PAYEE_LIMIT_REACHED = "PAYEE_LIMIT_REACHED"
    TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    # MTN Congo's Get Status code for a payer with no balance, at a limit, or not allowed to pay
    LOW_BALANCE_OR_PAYEE_LIMIT_REACHED_OR_NOT_ALLOWED = "LOW_BALANCE_OR_PAYEE_LIMIT_REACHED_OR_NOT_ALLOWED"

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.message = message

    @classmethod
    def from_dict(cls, data: Any) -> "ErrorReason":
        return cls(optional_string(data, "code") or "", optional_string(data, "message") or "")

    def is_code(self, code: str) -> bool:
        return self.code == code

    def is_payee_not_found(self) -> bool:
        return self.is_code(self.PAYEE_NOT_FOUND)

    def is_payer_not_found(self) -> bool:
        return self.is_code(self.PAYER_NOT_FOUND)

    def is_not_allowed(self) -> bool:
        return self.is_code(self.NOT_ALLOWED)

    def is_not_allowed_target_environment(self) -> bool:
        return self.is_code(self.NOT_ALLOWED_TARGET_ENVIRONMENT)

    def is_invalid_callback_url_host(self) -> bool:
        return self.is_code(self.INVALID_CALLBACK_URL_HOST)

    def is_invalid_currency(self) -> bool:
        return self.is_code(self.INVALID_CURRENCY)

    def is_service_unavailable(self) -> bool:
        return self.is_code(self.SERVICE_UNAVAILABLE)

    def is_internal_processing_error(self) -> bool:
        return self.is_code(self.INTERNAL_PROCESSING_ERROR)

    def is_not_enough_funds(self) -> bool:
        return self.is_code(self.NOT_ENOUGH_FUNDS)

    def is_payer_limit_reached(self) -> bool:
        return self.is_code(self.PAYER_LIMIT_REACHED)

    def is_payee_not_allowed_to_receive(self) -> bool:
        return self.is_code(self.PAYEE_NOT_ALLOWED_TO_RECEIVE)

    def is_payment_not_approved(self) -> bool:
        return self.is_code(self.PAYMENT_NOT_APPROVED)

    def is_resource_not_found(self) -> bool:
        return self.is_code(self.RESOURCE_NOT_FOUND)

    def is_approval_rejected(self) -> bool:
        return self.is_code(self.APPROVAL_REJECTED)

    def is_expired(self) -> bool:
        return self.is_code(self.EXPIRED)

    def is_transaction_canceled(self) -> bool:
        return self.is_code(self.TRANSACTION_CANCELED)

    def is_resource_already_exist(self) -> bool:
        return self.is_code(self.RESOURCE_ALREADY_EXIST)

    def is_low_balance_or_payee_limit_reached_or_not_allowed(self) -> bool:
        return self.is_code(self.LOW_BALANCE_OR_PAYEE_LIMIT_REACHED_OR_NOT_ALLOWED)

    def is_could_not_perform_transaction(self) -> bool:
        return self.is_code(self.COULD_NOT_PERFORM_TRANSACTION)

    def is_sender_account_not_active(self) -> bool:
        return self.is_code(self.SENDER_ACCOUNT_NOT_ACTIVE)

    def is_payee_limit_reached(self) -> bool:
        return self.is_code(self.PAYEE_LIMIT_REACHED)

    def is_transaction_not_found(self) -> bool:
        return self.is_code(self.TRANSACTION_NOT_FOUND)

    def is_validation_error(self) -> bool:
        return self.is_code(self.VALIDATION_ERROR)

    def is_payer_funding_failure(self) -> bool:
        """The payer could not fund the payment: not enough balance or a limit reached.

        MTN Congo reports this as ``LOW_BALANCE_OR_PAYEE_LIMIT_REACHED_OR_NOT_ALLOWED``
        rather than ``NOT_ENOUGH_FUNDS``, so check this rather than
        ``is_not_enough_funds()`` when the market does not matter.
        """
        return (
            self.is_not_enough_funds()
            or self.is_payer_limit_reached()
            or self.is_low_balance_or_payee_limit_reached_or_not_allowed()
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ErrorReason) and (self.code, self.message) == (other.code, other.message)

    def __hash__(self) -> int:
        return hash((self.code, self.message))

    def __repr__(self) -> str:
        return f"ErrorReason(code={self.code!r}, message={self.message!r})"

    def __str__(self) -> str:
        return f"[{self.code}]" if self.message == "" else f"[{self.code}] {self.message}"
