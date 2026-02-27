from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Transaction:
    STATUS_SUCCESSFUL = "SUCCESSFUL"
    STATUS_PENDING = "PENDING"
    STATUS_FAILED = "FAILED"

    amount: str
    status: str
    currency: str
    financial_transaction_id: str = ""
    external_id: str = ""
    payer_message: str = ""
    payee_note: str = ""
    payer: Optional[dict] = None
    payee: Optional[dict] = None
    _raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def parse(cls, data: dict) -> "Transaction":
        return cls(
            amount=data.get("amount", ""),
            status=data.get("status", ""),
            currency=data.get("currency", ""),
            financial_transaction_id=data.get("financialTransactionId", ""),
            external_id=data.get("externalId", ""),
            payer_message=data.get("payerMessage", ""),
            payee_note=data.get("payeeNote", ""),
            payer=data.get("payer"),
            payee=data.get("payee"),
            _raw=data,
        )

    def is_successful(self) -> bool:
        return self.status == self.STATUS_SUCCESSFUL

    def is_pending(self) -> bool:
        return self.status == self.STATUS_PENDING

    def is_failed(self) -> bool:
        return self.status == self.STATUS_FAILED
