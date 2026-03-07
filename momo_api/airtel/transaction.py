from dataclasses import dataclass
from typing import Optional


@dataclass
class AirtelTransaction:
    """Represents an Airtel Money transaction.

    Status codes:
    - TS  = Transaction Successful
    - TF  = Transaction Failed
    - TIP = Transaction In Progress (pending)
    """

    STATUS_SUCCESSFUL = "TS"
    STATUS_FAILED = "TF"
    STATUS_PENDING = "TIP"

    id: str
    status: str
    airtel_money_id: Optional[str] = None
    message: Optional[str] = None

    @classmethod
    def parse(cls, data: dict) -> "AirtelTransaction":
        return cls(
            id=str(data.get("id", "")),
            status=str(data.get("status", "")),
            airtel_money_id=data.get("airtel_money_id"),
            message=data.get("message"),
        )

    def is_successful(self) -> bool:
        return self.status == self.STATUS_SUCCESSFUL

    def is_pending(self) -> bool:
        return self.status == self.STATUS_PENDING

    def is_failed(self) -> bool:
        return self.status == self.STATUS_FAILED
