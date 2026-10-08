from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AccountBalance:
    available_balance: str
    currency: str

    @classmethod
    def parse(cls, data: Dict[str, Any]) -> "AccountBalance":
        return cls(
            available_balance=data.get("availableBalance", ""),
            currency=data.get("currency", ""),
        )
