from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    subscription_key: str
    api_user: str = ""
    api_key: str = ""
    callback_uri: str = ""

    @classmethod
    def sandbox(cls, subscription_key: str) -> "Config":
        return cls(subscription_key=subscription_key)

    @classmethod
    def collection(
        cls,
        subscription_key: str,
        api_user: str,
        api_key: str,
        callback_uri: str = "",
    ) -> "Config":
        return cls(
            subscription_key=subscription_key,
            api_user=api_user,
            api_key=api_key,
            callback_uri=callback_uri,
        )

    @classmethod
    def disbursement(
        cls,
        subscription_key: str,
        api_user: str,
        api_key: str,
        callback_uri: str = "",
    ) -> "Config":
        return cls(
            subscription_key=subscription_key,
            api_user=api_user,
            api_key=api_key,
            callback_uri=callback_uri,
        )
