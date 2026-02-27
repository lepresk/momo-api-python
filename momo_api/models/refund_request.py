from dataclasses import dataclass


@dataclass
class RefundRequest:
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
        currency: str = "XAF",
        payer_message: str = "",
        payee_note: str = "",
    ) -> "RefundRequest":
        return cls(
            amount=amount,
            currency=currency,
            external_id=external_id,
            reference_id_to_refund=reference_id_to_refund,
            payer_message=payer_message,
            payee_note=payee_note,
        )

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "currency": self.currency,
            "externalId": self.external_id,
            "referenceIdToRefund": self.reference_id_to_refund,
            "payerMessage": self.payer_message,
            "payeeNote": self.payee_note,
        }
