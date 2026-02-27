import base64
import uuid
from typing import Optional

import httpx

from ..exceptions import create_exception
from ..models.account_balance import AccountBalance
from ..models.api_token import ApiToken
from ..models.config import Config
from ..models.payment_request import PaymentRequest
from ..models.transaction import Transaction


class CollectionApi:
    """MTN MoMo Collection API product."""

    PRODUCT_PATH = "collection"

    def __init__(self, config: Config, base_url: str, environment: str):
        self._config = config
        self._base_url = base_url.rstrip("/")
        self._environment = environment

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _basic_auth_header(self) -> str:
        credentials = f"{self._config.api_user}:{self._config.api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _subscription_headers(self) -> dict:
        return {"Ocp-Apim-Subscription-Key": self._config.subscription_key}

    def _auth_headers(self, token: str) -> dict:
        return {
            "Ocp-Apim-Subscription-Key": self._config.subscription_key,
            "X-Target-Environment": self._environment,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                body = response.json()
                message = body.get("message") or body.get("error") or str(body)
            except Exception:
                message = response.text
            raise create_exception(response.status_code, message)

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{self.PRODUCT_PATH}/{path}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_access_token(self) -> ApiToken:
        """Obtain an OAuth2 access token for the Collection product."""
        url = self._url("token/")
        headers = {
            **self._subscription_headers(),
            "Authorization": self._basic_auth_header(),
        }
        with httpx.Client() as client:
            response = client.post(url, headers=headers)
        self._raise_for_status(response)
        return ApiToken.from_dict(response.json())

    def request_to_pay(self, request: PaymentRequest) -> str:
        """Initiate a payment request. Returns the reference ID."""
        token = self.get_access_token()
        reference_id = str(uuid.uuid4())
        url = self._url("v1_0/requesttopay")
        headers = {
            **self._auth_headers(token.access_token),
            "X-Reference-Id": reference_id,
        }
        if self._config.callback_uri:
            headers["X-Callback-Url"] = self._config.callback_uri

        with httpx.Client() as client:
            response = client.post(url, json=request.to_dict(), headers=headers)
        self._raise_for_status(response)
        return reference_id

    def get_payment_status(self, payment_id: str) -> Transaction:
        """Get the status of a previously initiated payment request."""
        token = self.get_access_token()
        url = self._url(f"v1_0/requesttopay/{payment_id}")
        with httpx.Client() as client:
            response = client.get(url, headers=self._auth_headers(token.access_token))
        self._raise_for_status(response)
        return Transaction.parse(response.json())

    def get_balance(self) -> AccountBalance:
        """Get the account balance for the Collection product."""
        token = self.get_access_token()
        url = self._url("v1_0/account/balance")
        with httpx.Client() as client:
            response = client.get(url, headers=self._auth_headers(token.access_token))
        self._raise_for_status(response)
        return AccountBalance.parse(response.json())

    def quick_pay(
        self,
        amount: str,
        phone: str,
        reference: str,
        currency: str = "XAF",
    ) -> str:
        """Convenience method that builds and submits a payment request."""
        payment = PaymentRequest.make(
            amount=amount,
            payer=phone,
            external_id=reference,
            currency=currency,
        )
        return self.request_to_pay(payment)
