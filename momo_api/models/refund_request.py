from dataclasses import dataclass
from typing import Any, Dict

from .abstract_request import AbstractRequest
from .currency import DEFAULT_CURRENCY


@dataclass
class RefundRequest(AbstractRequest):
    amount: str
    currency: str
    external_id: str
    reference_id_to_refund: str
    payer_message: str = ""
    payee_note: str = ""

    @classmethod
    def make(
        cls,
        amount: str,
        reference_id_to_refund: str,
        external_id: str,
        currency: str = DEFAULT_CURRENCY,
        payer_message: str = "",
        payee_note: str = "",
    ) -> "RefundRequest":
        return cls(amount, currency, external_id, reference_id_to_refund, payer_message, payee_note)

    def _subject(self) -> Dict[str, Any]:
        return {"referenceIdToRefund": self.reference_id_to_refund}
