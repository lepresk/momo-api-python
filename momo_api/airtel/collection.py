import uuid
from typing import Optional

import httpx

from ..exceptions import create_exception
from ..models.account_balance import AccountBalance
from ..support.token_cache import TokenCache
from .config import AirtelConfig
from .transaction import AirtelTransaction


class AirtelCollectionApi:
    """Airtel Money Collection API."""

    def __init__(self, config: AirtelConfig, base_url: str) -> None:
        self._config = config
        self._base_url = base_url.rstrip("/")
        self._token_cache = TokenCache()

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                body = response.json()
                message = body.get("message") or body.get("error") or str(body)
            except Exception:
                message = response.text
            raise create_exception(response.status_code, message)

    def get_access_token(self) -> str:
        """Obtain a cached OAuth2 access token."""
        cached = self._token_cache.get()
        if cached is not None:
            return cached

        url = f"{self._base_url}/auth/oauth2/token"
        with httpx.Client() as client:
            response = client.post(
                url,
                json={
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                    "grant_type": "client_credentials",
                },
                headers={"Content-Type": "application/json", "Accept": "*/*"},
            )
        self._raise_for_status(response)
        data = response.json()
        token = str(data["access_token"])
        expires_in = int(data.get("expires_in", 3600))
        self._token_cache.set(token, expires_in)
        return token

    def request_to_pay(self, amount: str, phone: str, reference: str) -> str:
        """Initiate a payment request. Returns the externalId for status checks."""
        token = self.get_access_token()
        external_id = str(uuid.uuid4())

        url = f"{self._base_url}/merchant/v1/payments/"
        with httpx.Client() as client:
            response = client.post(
                url,
                json={
                    "reference": reference,
                    "subscriber": {
                        "country": self._config.country,
                        "currency": self._config.currency,
                        "msisdn": phone,
                    },
                    "transaction": {
                        "amount": float(amount),
                        "country": self._config.country,
                        "currency": self._config.currency,
                        "id": external_id,
                    },
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Country": self._config.country,
                    "X-Currency": self._config.currency,
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                },
            )
        self._raise_for_status(response)
        return external_id

    def get_payment_status(self, external_id: str) -> AirtelTransaction:
        """Get the status of a payment. Pass the externalId returned by request_to_pay."""
        token = self.get_access_token()
        url = f"{self._base_url}/standard/v1/payments/{external_id}"
        with httpx.Client() as client:
            response = client.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Country": self._config.country,
                    "X-Currency": self._config.currency,
                    "Accept": "*/*",
                },
            )
        self._raise_for_status(response)
        data = response.json()
        return AirtelTransaction.parse(data.get("data", {}).get("transaction", {}))

    def get_balance(self) -> AccountBalance:
        """Get the account balance."""
        token = self.get_access_token()
        url = f"{self._base_url}/standard/v1/users/balance"
        with httpx.Client() as client:
            response = client.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Country": self._config.country,
                    "X-Currency": self._config.currency,
                    "Accept": "*/*",
                },
            )
        self._raise_for_status(response)
        data = response.json().get("data", {})
        return AccountBalance.parse({
            "availableBalance": str(data.get("balance", "0")),
            "currency": str(data.get("currency", "")),
        })
