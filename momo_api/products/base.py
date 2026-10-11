import base64
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from ..models.account_balance import AccountBalance
from ..models.api_token import ApiToken
from ..models.config import Config
from ..models.currency import SANDBOX_CURRENCY
from ..models.transaction import Transaction
from ..support.http import assert_status, read_json, send
from ..support.token_cache import TokenCache
from ..support.uuid import assert_uuid, generate_uuid

# MomoApi.ENVIRONMENT_SANDBOX; importing it here would be circular
_SANDBOX = "sandbox"


class AbstractApiProduct:
    """Shared behaviour of the MTN products. Collection and Disbursement expose
    the same endpoints under a different path segment, so everything but the
    endpoint list lives here."""

    #: ``collection`` or ``disbursement``: the first segment of every endpoint
    PRODUCT_PATH = ""

    def __init__(
        self,
        config: Config,
        base_url: str,
        environment: str,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._config = config
        self._base_url = base_url.rstrip("/")
        self._environment = environment
        self._http_client = http_client
        self._token_cache = TokenCache()

    @property
    def config(self) -> Config:
        return self._config

    @property
    def subscription_key(self) -> str:
        return self._config.subscription_key

    @property
    def environment(self) -> str:
        return self._environment

    @property
    def base_url(self) -> str:
        return self._base_url

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{self.PRODUCT_PATH}/{path}"

    def _send(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return send(self._http_client, method, url, **kwargs)

    def _basic_auth(self) -> str:
        credentials = f"{self._config.api_user}:{self._config.api_key}".encode()
        return "Basic " + base64.b64encode(credentials).decode()

    def _auth_headers(self, token: str) -> Dict[str, str]:
        """Headers every authenticated call carries."""
        return {
            "Authorization": f"Bearer {token}",
            "Ocp-Apim-Subscription-Key": self._config.subscription_key,
            "X-Target-Environment": self._environment,
            "Accept": "application/json",
        }

    def _write_headers(self, token: str, reference_id: str) -> Dict[str, str]:
        """``_auth_headers`` plus what a write request needs."""
        headers = {
            **self._auth_headers(token),
            "X-Reference-Id": reference_id,
            "Content-Type": "application/json",
        }
        if self._config.callback_uri:
            headers["X-Callback-Url"] = self._config.callback_uri
        return headers

    def _submit(self, path: str, body: Dict[str, Any], reference_id: Optional[str] = None) -> str:
        """POST a request and return its reference id. The API answers
        ``202 Accepted`` and reports the outcome asynchronously.

        The reference id is ``reference_id`` when given, a random UUID otherwise.
        Passing your own lets you query the status after a timeout or 5xx without
        having seen the response, and retry with the same id instead of risking a
        second payment. MTN requires a UUID; anything else raises ``ValueError``
        before sending.

        The sandbox rejects any currency but EUR, so there the body's currency is
        replaced: code written for XAF runs unchanged against the sandbox.
        """
        reference_id = generate_uuid() if reference_id is None else reference_id
        assert_uuid(reference_id, "reference_id")
        token = self.get_access_token()
        if self._environment == _SANDBOX:
            body = {**body, "currency": SANDBOX_CURRENCY}

        response = self._send(
            "POST",
            self._url(path),
            json=body,
            headers=self._write_headers(token.access_token, reference_id),
        )
        assert_status(response, 202)
        return reference_id

    def _get_transaction(self, path: str) -> Transaction:
        token = self.get_access_token()
        response = self._send("GET", self._url(path), headers=self._auth_headers(token.access_token))
        return Transaction.parse(read_json(response))  # parse() tolerates a non-dict body

    def get_access_token(self) -> ApiToken:
        """Create an access token for the other endpoints. Cached for its lifetime
        minus a minute, so repeated calls do not re-authenticate."""
        cached = self._token_cache.get()
        if cached is not None:
            return ApiToken(access_token=cached, token_type="access_token", expires_in=0)

        response = self._send(
            "POST",
            self._url("token/"),
            headers={
                "Authorization": self._basic_auth(),
                "Ocp-Apim-Subscription-Key": self._config.subscription_key,
                "Accept": "application/json",
            },
        )
        token = ApiToken.from_dict(read_json(response))
        self._token_cache.set(token.access_token, token.expires_in)
        return token

    def get_balance(self) -> AccountBalance:
        """Balance of your own account."""
        token = self.get_access_token()
        response = self._send(
            "GET", self._url("v1_0/account/balance"), headers=self._auth_headers(token.access_token)
        )
        data = read_json(response)
        return AccountBalance.parse(data if isinstance(data, dict) else {})

    def check_account_holder(self, phone: str) -> bool:
        """Whether an MSISDN is a registered, active account holder."""
        token = self.get_access_token()
        response = self._send(
            "GET",
            self._url(f"v1_0/accountholder/msisdn/{quote(phone, safe='')}/active"),
            headers=self._auth_headers(token.access_token),
        )
        data = read_json(response)
        return isinstance(data, dict) and data.get("result") is True
