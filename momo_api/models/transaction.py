from typing import Any, Dict, Optional

from .error_reason import ErrorReason


class Transaction:
    """The status of an MTN payment, deposit, transfer or refund.

    Every field MTN may leave out is ``None`` when absent: transfers and refunds,
    for instance, carry no ``payerMessage`` or ``payeeNote``.
    """

    STATUS_SUCCESSFUL = "SUCCESSFUL"
    STATUS_PENDING = "PENDING"
    STATUS_FAILED = "FAILED"

    def __init__(self, data: Dict[str, Any]) -> None:
        self._raw = data

    @classmethod
    def parse(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(data if isinstance(data, dict) else {})

    @property
    def raw(self) -> Dict[str, Any]:
        """The response body as MTN returned it."""
        return self._raw

    @property
    def status(self) -> str:
        return str(self._raw.get("status", ""))

    @property
    def amount(self) -> Optional[str]:
        return self._raw.get("amount")

    @property
    def currency(self) -> Optional[str]:
        return self._raw.get("currency")

    @property
    def financial_transaction_id(self) -> Optional[str]:
        return self._raw.get("financialTransactionId")

    @property
    def external_id(self) -> Optional[str]:
        return self._raw.get("externalId")

    @property
    def payer_message(self) -> Optional[str]:
        return self._raw.get("payerMessage")

    @property
    def payee_note(self) -> Optional[str]:
        return self._raw.get("payeeNote")

    @property
    def payer(self) -> Optional[str]:
        """The payer's MSISDN, when the transaction has one."""
        return self._party("payer")

    @property
    def payee(self) -> Optional[str]:
        """The payee's MSISDN, when the transaction has one."""
        return self._party("payee")

    @property
    def reason(self) -> Optional[ErrorReason]:
        """Why a FAILED transaction failed, or ``None``."""
        reason = self._raw.get("reason")
        # HTTP error bodies carry {code, message}; Get Status reports a FAILED
        # transaction with HTTP 200 and a bare string code instead
        if isinstance(reason, dict):
            return ErrorReason.from_dict(reason)
        if isinstance(reason, str) and reason != "":
            return ErrorReason(reason, "")
        return None

    def _party(self, key: str) -> Optional[str]:
        party = self._raw.get(key)
        return party.get("partyId") if isinstance(party, dict) else None

    def is_successful(self) -> bool:
        return self.status == self.STATUS_SUCCESSFUL

    def is_pending(self) -> bool:
        return self.status == self.STATUS_PENDING

    def is_failed(self) -> bool:
        return self.status == self.STATUS_FAILED

    def __repr__(self) -> str:
        return f"Transaction(status={self.status!r}, amount={self.amount!r}, external_id={self.external_id!r})"
