from dataclasses import dataclass


@dataclass
class TransferRequest:
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
        currency: str = "XAF",
        payer_message: str = "",
        payee_note: str = "",
    ) -> "TransferRequest":
        return cls(
            amount=amount,
            currency=currency,
            external_id=external_id,
            payee=payee,
            payer_message=payer_message,
            payee_note=payee_note,
        )

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "currency": self.currency,
            "externalId": self.external_id,
            "payee": {
                "partyIdType": "MSISDN",
                "partyId": self.payee,
            },
            "payerMessage": self.payer_message,
            "payeeNote": self.payee_note,
        }
