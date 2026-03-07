from dataclasses import dataclass, field


@dataclass
class AirtelConfig:
    client_id: str
    client_secret: str
    encrypted_pin: str = ""
    country: str = "CG"
    currency: str = "XAF"
    callback_uri: str = ""

    @classmethod
    def collection(
        cls,
        client_id: str,
        client_secret: str,
        callback_uri: str = "",
        country: str = "CG",
        currency: str = "XAF",
    ) -> "AirtelConfig":
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            country=country,
            currency=currency,
            callback_uri=callback_uri,
        )

    @classmethod
    def disbursement(
        cls,
        client_id: str,
        client_secret: str,
        encrypted_pin: str,
        callback_uri: str = "",
        country: str = "CG",
        currency: str = "XAF",
    ) -> "AirtelConfig":
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            encrypted_pin=encrypted_pin,
            country=country,
            currency=currency,
            callback_uri=callback_uri,
        )
