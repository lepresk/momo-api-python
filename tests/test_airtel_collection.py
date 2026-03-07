import pytest
from pytest_httpx import HTTPXMock

from momo_api.airtel.api import STAGING_URL
from momo_api.airtel.collection import AirtelCollectionApi
from momo_api.airtel.config import AirtelConfig
from momo_api.airtel.transaction import AirtelTransaction
from momo_api.exceptions import MomoException

BASE_URL = STAGING_URL


@pytest.fixture
def config() -> AirtelConfig:
    return AirtelConfig.collection("client-id", "client-secret")


@pytest.fixture
def api(config: AirtelConfig) -> AirtelCollectionApi:
    return AirtelCollectionApi(config, BASE_URL)


@pytest.fixture
def token_json() -> dict:
    return {"access_token": "test-airtel-token", "expires_in": 3600}


def test_get_access_token(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/auth/oauth2/token",
        json=token_json,
        status_code=200,
    )
    token = api.get_access_token()
    assert token == "test-airtel-token"


def test_token_is_cached(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/auth/oauth2/token",
        json=token_json,
    )
    t1 = api.get_access_token()
    t2 = api.get_access_token()
    assert t1 == t2
    # Only one request should have been made (the second used cache)
    requests = httpx_mock.get_requests()
    assert len(requests) == 1


def test_request_to_pay(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/merchant/v1/payments/", status_code=200, json={}
    )
    external_id = api.request_to_pay("5000", "068511358", "ORDER-001")
    assert len(external_id) == 36  # UUID


def test_request_to_pay_raises_on_error(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/merchant/v1/payments/", status_code=400, json={}
    )
    with pytest.raises(MomoException):
        api.request_to_pay("5000", "068511358", "ORDER-001")


def test_get_payment_status_pending(api, token_json, httpx_mock: HTTPXMock):
    external_id = "abc-123"
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/standard/v1/payments/{external_id}",
        json={"data": {"transaction": {"id": external_id, "status": "TIP"}}},
    )
    transaction = api.get_payment_status(external_id)
    assert isinstance(transaction, AirtelTransaction)
    assert transaction.is_pending()
    assert not transaction.is_successful()


def test_get_payment_status_successful(api, token_json, httpx_mock: HTTPXMock):
    external_id = "abc-123"
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/standard/v1/payments/{external_id}",
        json={
            "data": {
                "transaction": {"id": external_id, "status": "TS", "airtel_money_id": "AM999"}
            }
        },
    )
    transaction = api.get_payment_status(external_id)
    assert transaction.is_successful()
    assert transaction.airtel_money_id == "AM999"


def test_get_payment_status_raises_on_404(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/standard/v1/payments/unknown",
        status_code=404,
        json={},
    )
    with pytest.raises(MomoException):
        api.get_payment_status("unknown")


def test_get_balance(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/standard/v1/users/balance",
        json={"data": {"balance": "50000", "currency": "XAF"}},
    )
    balance = api.get_balance()
    assert balance.available_balance == "50000"
    assert balance.currency == "XAF"
