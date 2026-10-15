"""MTN requires X-Target-Environment on every request, authentication included."""
import pytest
from pytest_httpx import HTTPXMock

from momo_api import MomoApi

SANDBOX_BASE = "https://sandbox.momodeveloper.mtn.com"
API_USER_UUID = "a94f3bb8-6e04-4b39-8a24-abc123456789"
TOKEN = {"access_token": "token", "token_type": "access_token", "expires_in": 3600}


@pytest.mark.parametrize("product", ["collection", "disbursement"])
def test_token_request_sends_target_environment(product, collection_config, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/{product}/token/",
        match_headers={"X-Target-Environment": "sandbox"},
        json=TOKEN,
    )
    getattr(MomoApi, product)(collection_config).get_access_token()


def test_sandbox_provisioning_sends_target_environment(sandbox_api, httpx_mock: HTTPXMock):
    headers = {"X-Target-Environment": "sandbox"}
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/v1_0/apiuser", match_headers=headers, status_code=201)
    httpx_mock.add_response(
        method="GET", url=f"{SANDBOX_BASE}/v1_0/apiuser/{API_USER_UUID}", match_headers=headers, json={}
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/v1_0/apiuser/{API_USER_UUID}/apikey",
        match_headers=headers,
        status_code=201,
        json={"apiKey": "key"},
    )

    sandbox_api.create_api_user(API_USER_UUID, "https://callback.example.com")
    sandbox_api.get_api_user(API_USER_UUID)
    sandbox_api.create_api_key(API_USER_UUID)
