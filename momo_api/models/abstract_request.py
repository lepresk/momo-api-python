from abc import ABC, abstractmethod
from typing import Any, Dict


def msisdn(phone: str) -> Dict[str, str]:
    """The ``{partyIdType, partyId}`` shape MTN uses for a payer or payee."""
    return {"partyIdType": "MSISDN", "partyId": phone}


class AbstractRequest(ABC):
    """Fields shared by every MTN write request. Subclasses add the one field
    that distinguishes them: the payer, the payee, or the payment being refunded."""

    amount: str
    currency: str
    external_id: str
    payer_message: str
    payee_note: str

    @abstractmethod
    def _subject(self) -> Dict[str, Any]:
        """The field this request type adds to the common body."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": self.amount,
            "currency": self.currency,
            "externalId": self.external_id,
            **self._subject(),
            "payerMessage": self.payer_message,
            "payeeNote": self.payee_note,
        }
