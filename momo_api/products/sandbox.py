import httpx

from ..exceptions import create_exception
from ..models.config import Config


class SandboxApi:
    """MTN MoMo Sandbox provisioning API."""

    BASE_PATH = "v1_0/apiuser"

    def __init__(self, subscription_key: str, base_url: str):
        self._subscription_key = subscription_key
        self._base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "Ocp-Apim-Subscription-Key": self._subscription_key,
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
        return f"{self._base_url}/{self.BASE_PATH}/{path}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_api_user(self, api_user: str, callback_host: str) -> str:
        """Create an API user in the sandbox environment. Returns the api_user UUID."""
        url = f"{self._base_url}/{self.BASE_PATH}"
        payload = {"providerCallbackHost": callback_host}
        headers = {
            **self._headers(),
            "X-Reference-Id": api_user,
        }
        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=headers)
        self._raise_for_status(response)
        return api_user

    def get_api_user(self, api_user: str) -> dict:
        """Retrieve details about a sandbox API user."""
        url = self._url(api_user)
        with httpx.Client() as client:
            response = client.get(url, headers=self._headers())
        self._raise_for_status(response)
        return response.json()

    def create_api_key(self, api_user: str) -> str:
        """Create an API key for a sandbox API user. Returns the generated API key string."""
        url = self._url(f"{api_user}/apikey")
        with httpx.Client() as client:
            response = client.post(url, headers=self._headers())
        self._raise_for_status(response)
        data = response.json()
        return data.get("apiKey", "")
