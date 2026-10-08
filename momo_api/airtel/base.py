import json
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from ..exceptions import ResourceNotFoundException, create_exception
from ..models.account_balance import AccountBalance
from ..support.http import read_json, send
from ..support.phone import clean_phone_number
from ..support.token_cache import TokenCache
from .config import AirtelConfig
from .response_status import AirtelResponseStatus
from .transaction import AirtelTransaction


class AbstractAirtelApi:
    """Shared behaviour of the Airtel Money products. Collection and Disbursement
    authenticate identically and read status from the same envelope shape."""

    def __init__(self, config: AirtelConfig, base_url: str, http_client: Optional[httpx.Client] = None) -> None:
        self._config = config
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client
        self._token_cache = TokenCache()

    @property
    def config(self) -> AirtelConfig:
        return self._config

    @property
    def base_url(self) -> str:
        return self._base_url

    def _send(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return send(self._http_client, method, url, **kwargs)

    def _msisdn(self, phone: str) -> str:
        """Airtel expects a national MSISDN and rejects a country-prefixed one. MTN,
        by contrast, wants the full international number, which is why this lives
        here and not on a shared base."""
        return clean_phone_number(phone)

    def _airtel_headers(self, token: str) -> Dict[str, str]:
        """Headers every authenticated Airtel call carries."""
        return {
            "Authorization": f"Bearer {token}",
            "X-Country": self._config.country,
            "X-Currency": self._config.currency,
            "Accept": "*/*",
        }

    def _read_airtel(self, response: httpx.Response) -> Any:
        """Read an Airtel payload, raising when its ``status`` envelope reports a
        business failure. Airtel answers those with HTTP 200, so the status code
        alone is not enough to tell success from refusal."""
        body = read_json(response)
        status = AirtelResponseStatus.parse(body)
        if status is not None and not status.is_successful():
            # Route through the same factory as an HTTP failure, so an Airtel
            # refusal maps to the same typed exception a 4xx/5xx would have
            # produced. Airtel's own code is HTTP-shaped ("500"), so it drives the
            # class; the result code becomes the reason's code.
            try:
                http_status = int(status.code or "")
            except ValueError:
                http_status = 0
            raise create_exception(
                http_status or response.status_code,
                json.dumps({
                    "code": status.result_code or status.response_code,
                    "message": status.message,
                }),
            )
        return body

    def get_access_token(self) -> str:
        """OAuth2 client-credentials token, cached for its lifetime minus a minute."""
        cached = self._token_cache.get()
        if cached is not None:
            return cached

        response = self._send(
            "POST",
            f"{self._base_url}/auth/oauth2/token",
            json={
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "grant_type": "client_credentials",
            },
            headers={"Content-Type": "application/json", "Accept": "*/*"},
        )
        data = read_json(response)
        token = str(data["access_token"])
        self._token_cache.set(token, int(data.get("expires_in", 3600)))
        return token

    def _get_transaction(self, path: str, external_id: str) -> AirtelTransaction:
        """Read a transaction from the ``{data: {transaction}}`` envelope.

        :raises ResourceNotFoundException: when Airtel answers without a transaction
        """
        token = self.get_access_token()
        response = self._send("GET", f"{self._base_url}{path}", headers=self._airtel_headers(token))
        data = self._read_airtel(response)
        transaction = (data.get("data") or {}).get("transaction") if isinstance(data, dict) else None
        if not transaction:
            raise ResourceNotFoundException(
                f"Transaction not found in Airtel system for externalId: {external_id}"
            )
        return AirtelTransaction.parse(transaction)

    def _path_id(self, external_id: str) -> str:
        return quote(external_id, safe="")

    def get_balance(self) -> AccountBalance:
        token = self.get_access_token()
        response = self._send(
            "GET", f"{self._base_url}/standard/v1/users/balance", headers=self._airtel_headers(token)
        )
        data = self._read_airtel(response).get("data") or {}
        return AccountBalance.parse({
            "availableBalance": str(data.get("balance", "0")),
            "currency": str(data.get("currency", "")),
        })
