from dataclasses import dataclass


@dataclass
class AccountBalance:
    available_balance: str
    currency: str

    @classmethod
    def parse(cls, data: dict) -> "AccountBalance":
        return cls(
            available_balance=data.get("availableBalance", ""),
            currency=data.get("currency", ""),
        )
