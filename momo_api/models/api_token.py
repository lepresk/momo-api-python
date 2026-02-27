from dataclasses import dataclass


@dataclass
class ApiToken:
    access_token: str
    token_type: str
    expires_in: int

    @classmethod
    def from_dict(cls, data: dict) -> "ApiToken":
        return cls(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", ""),
            expires_in=int(data.get("expires_in", 0)),
        )
