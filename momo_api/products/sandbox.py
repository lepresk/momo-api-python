from typing import Any, Dict, Optional

import httpx

from ..support.http import read_json_allow_empty, send


class SandboxApi:
    """MTN MoMo sandbox provisioning API."""

    def __init__(self, subscription_key: str, base_url: str, http_client: Optional[httpx.Client] = None) -> None:
        self._subscription_key = subscription_key
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client

    def _headers(self, content_type: bool = False) -> Dict[str, str]:
        headers = {"Ocp-Apim-Subscription-Key": self._subscription_key, "Accept": "application/json"}
        if content_type:
            headers["Content-Type"] = "application/json"
        return headers

    def _send(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return send(self._http_client, method, url, **kwargs)

    def create_api_user(self, api_user: str, callback_host: str) -> str:
        """Provision an API user. Returns the reference id you passed in."""
        response = self._send(
            "POST",
            f"{self._base_url}/v1_0/apiuser",
            json={"providerCallbackHost": callback_host},
            headers={**self._headers(True), "X-Reference-Id": api_user},
        )
        read_json_allow_empty(response)
        return api_user

    def get_api_user(self, api_user: str) -> Dict[str, Any]:
        response = self._send("GET", f"{self._base_url}/v1_0/apiuser/{api_user}", headers=self._headers())
        data: Dict[str, Any] = read_json_allow_empty(response)
        return data

    def create_api_key(self, api_user: str) -> str:
        response = self._send("POST", f"{self._base_url}/v1_0/apiuser/{api_user}/apikey", headers=self._headers())
        return str(read_json_allow_empty(response).get("apiKey", ""))
