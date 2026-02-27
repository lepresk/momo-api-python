import base64
import uuid

import httpx

from ..exceptions import create_exception
from ..models.account_balance import AccountBalance
from ..models.api_token import ApiToken
from ..models.config import Config
from ..models.payment_request import PaymentRequest
from ..models.refund_request import RefundRequest
from ..models.transaction import Transaction
from ..models.transfer_request import TransferRequest


class DisbursementApi:
    """MTN MoMo Disbursement API product."""

    PRODUCT_PATH = "disbursement"

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

    def _post_with_reference(self, path: str, payload: dict, token: str) -> str:
        """POST a request with X-Reference-Id; returns that reference ID."""
        reference_id = str(uuid.uuid4())
        headers = {
            **self._auth_headers(token),
            "X-Reference-Id": reference_id,
        }
        if self._config.callback_uri:
            headers["X-Callback-Url"] = self._config.callback_uri

        url = self._url(path)
        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=headers)
        self._raise_for_status(response)
        return reference_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_access_token(self) -> ApiToken:
        """Obtain an OAuth2 access token for the Disbursement product."""
        url = self._url("token/")
        headers = {
            **self._subscription_headers(),
            "Authorization": self._basic_auth_header(),
        }
        with httpx.Client() as client:
            response = client.post(url, headers=headers)
        self._raise_for_status(response)
        return ApiToken.from_dict(response.json())

    def get_balance(self) -> AccountBalance:
        """Get the account balance for the Disbursement product."""
        token = self.get_access_token()
        url = self._url("v1_0/account/balance")
        with httpx.Client() as client:
            response = client.get(url, headers=self._auth_headers(token.access_token))
        self._raise_for_status(response)
        return AccountBalance.parse(response.json())

    def deposit(self, request: PaymentRequest) -> str:
        """Initiate a deposit. Returns the reference ID."""
        token = self.get_access_token()
        return self._post_with_reference(
            "v1_0/deposit", request.to_dict(), token.access_token
        )

    def get_deposit_status(self, deposit_id: str) -> Transaction:
        """Get the status of a previously initiated deposit."""
        token = self.get_access_token()
        url = self._url(f"v1_0/deposit/{deposit_id}")
        with httpx.Client() as client:
            response = client.get(url, headers=self._auth_headers(token.access_token))
        self._raise_for_status(response)
        return Transaction.parse(response.json())

    def transfer(self, request: TransferRequest) -> str:
        """Initiate a transfer. Returns the reference ID."""
        token = self.get_access_token()
        return self._post_with_reference(
            "v1_0/transfer", request.to_dict(), token.access_token
        )

    def get_transfer_status(self, transfer_id: str) -> Transaction:
        """Get the status of a previously initiated transfer."""
        token = self.get_access_token()
        url = self._url(f"v1_0/transfer/{transfer_id}")
        with httpx.Client() as client:
            response = client.get(url, headers=self._auth_headers(token.access_token))
        self._raise_for_status(response)
        return Transaction.parse(response.json())

    def refund(self, request: RefundRequest) -> str:
        """Initiate a refund. Returns the reference ID."""
        token = self.get_access_token()
        return self._post_with_reference(
            "v1_0/refund", request.to_dict(), token.access_token
        )

    def get_refund_status(self, refund_id: str) -> Transaction:
        """Get the status of a previously initiated refund."""
        token = self.get_access_token()
        url = self._url(f"v1_0/refund/{refund_id}")
        with httpx.Client() as client:
            response = client.get(url, headers=self._auth_headers(token.access_token))
        self._raise_for_status(response)
        return Transaction.parse(response.json())
