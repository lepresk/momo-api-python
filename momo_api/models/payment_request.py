from dataclasses import dataclass


@dataclass
class PaymentRequest:
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
        currency: str = "XAF",
        payer_message: str = "",
        payee_note: str = "",
    ) -> "PaymentRequest":
        return cls(
            amount=amount,
            currency=currency,
            external_id=external_id,
            payer=payer,
            payer_message=payer_message,
            payee_note=payee_note,
        )

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "currency": self.currency,
            "externalId": self.external_id,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": self.payer,
            },
            "payerMessage": self.payer_message,
            "payeeNote": self.payee_note,
        }
