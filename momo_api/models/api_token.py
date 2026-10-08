from dataclasses import dataclass
from typing import Any, Dict

from ..support.json import to_int


@dataclass
class ApiToken:
    access_token: str
    token_type: str
    expires_in: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApiToken":
        return cls(
            access_token=str(data.get("access_token") or ""),
            token_type=str(data.get("token_type") or ""),
            expires_in=to_int(data.get("expires_in")),
        )
