import pytest
from pytest_httpx import HTTPXMock

from momo_api.exceptions import ConflictException, ResourceNotFoundException

SANDBOX_BASE = "https://sandbox.momodeveloper.mtn.com"
API_USER_UUID = "a94f3bb8-6e04-4b39-8a24-abc123456789"
CALLBACK_HOST = "https://callback.example.com"


def test_create_api_user(sandbox_api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/v1_0/apiuser",
        status_code=201,
    )
    result = sandbox_api.create_api_user(API_USER_UUID, CALLBACK_HOST)
    assert result == API_USER_UUID


def test_create_api_user_conflict(sandbox_api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/v1_0/apiuser",
        json={"message": "User already exists"},
        status_code=409,
    )
    with pytest.raises(ConflictException):
        sandbox_api.create_api_user(API_USER_UUID, CALLBACK_HOST)


def test_get_api_user(sandbox_api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/v1_0/apiuser/{API_USER_UUID}",
        json={
            "providerCallbackHost": CALLBACK_HOST,
            "apiKey": None,
            "targetEnvironment": "sandbox",
        },
    )
    result = sandbox_api.get_api_user(API_USER_UUID)
    assert result["providerCallbackHost"] == CALLBACK_HOST
    assert result["targetEnvironment"] == "sandbox"


def test_get_api_user_not_found(sandbox_api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/v1_0/apiuser/unknown-uuid",
        json={"message": "Not found"},
        status_code=404,
    )
    with pytest.raises(ResourceNotFoundException):
        sandbox_api.get_api_user("unknown-uuid")


def test_create_api_key(sandbox_api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/v1_0/apiuser/{API_USER_UUID}/apikey",
        json={"apiKey": "generated-api-key-xyz"},
        status_code=201,
    )
    api_key = sandbox_api.create_api_key(API_USER_UUID)
    assert api_key == "generated-api-key-xyz"


def test_create_api_key_user_not_found(sandbox_api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/v1_0/apiuser/unknown-uuid/apikey",
        json={"message": "Not found"},
        status_code=404,
    )
    with pytest.raises(ResourceNotFoundException):
        sandbox_api.create_api_key("unknown-uuid")
