from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..support.json import optional_string


@dataclass
class AirtelTransaction:
    """An Airtel Money transaction.

    Status codes:

    - ``TS``: transaction successful
    - ``TF``: transaction failed
    - ``TIP``: transaction in progress
    - ``TI``: transaction initiated (also pending)
    """

    STATUS_SUCCESSFUL = "TS"
    STATUS_FAILED = "TF"
    STATUS_PENDING = "TIP"
    STATUS_IN_PROGRESS = "TI"

    id: str
    status: str
    #: Airtel's own reference for the transaction, when it returns one
    reference_id: Optional[str] = None
    airtel_money_id: Optional[str] = None
    message: Optional[str] = None

    @classmethod
    def parse(cls, data: Dict[str, Any]) -> "AirtelTransaction":
        return cls(
            id=optional_string(data, "id") or "",
            status=optional_string(data, "status") or "",
            reference_id=optional_string(data, "reference_id"),
            airtel_money_id=optional_string(data, "airtel_money_id"),
            message=optional_string(data, "message"),
        )

    def is_successful(self) -> bool:
        return self.status == self.STATUS_SUCCESSFUL

    def is_pending(self) -> bool:
        """Airtel uses two codes for "not settled yet"."""
        return self.status in (self.STATUS_PENDING, self.STATUS_IN_PROGRESS)

    def is_failed(self) -> bool:
        return self.status == self.STATUS_FAILED
