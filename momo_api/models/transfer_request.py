from dataclasses import dataclass
from typing import Any, Dict

from .abstract_request import AbstractRequest, msisdn
from .currency import DEFAULT_CURRENCY


@dataclass
class TransferRequest(AbstractRequest):
    amount: str
    currency: str
    external_id: str
    payee: str
    payer_message: str = ""
    payee_note: str = ""

    @classmethod
    def make(
        cls,
        amount: str,
        payee: str,
        external_id: str,
        currency: str = DEFAULT_CURRENCY,
        payer_message: str = "",
        payee_note: str = "",
    ) -> "TransferRequest":
        return cls(amount, currency, external_id, payee, payer_message, payee_note)

    def _subject(self) -> Dict[str, Any]:
        return {"payee": msisdn(self.payee)}
