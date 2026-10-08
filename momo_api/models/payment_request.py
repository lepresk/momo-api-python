from dataclasses import dataclass
from typing import Any, Dict

from .abstract_request import AbstractRequest, msisdn
from .currency import DEFAULT_CURRENCY


@dataclass
class PaymentRequest(AbstractRequest):
    amount: str
    currency: str
    external_id: str
    payer: str
    payer_message: str = ""
    payee_note: str = ""

    @classmethod
    def make(
        cls,
        amount: str,
        payer: str,
        external_id: str,
        currency: str = DEFAULT_CURRENCY,
        payer_message: str = "",
        payee_note: str = "",
    ) -> "PaymentRequest":
        return cls(amount, currency, external_id, payer, payer_message, payee_note)

    def _subject(self) -> Dict[str, Any]:
        return {"payer": msisdn(self.payer)}
