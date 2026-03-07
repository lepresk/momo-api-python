import pytest
from pytest_httpx import HTTPXMock

from momo_api.airtel.api import STAGING_URL
from momo_api.airtel.config import AirtelConfig
from momo_api.airtel.disbursement import AirtelDisbursementApi
from momo_api.airtel.transaction import AirtelTransaction
from momo_api.exceptions import MomoException

BASE_URL = STAGING_URL


@pytest.fixture
def config() -> AirtelConfig:
    return AirtelConfig.disbursement("client-id", "client-secret", "encrypted-pin")


@pytest.fixture
def api(config: AirtelConfig) -> AirtelDisbursementApi:
    return AirtelDisbursementApi(config, BASE_URL)


@pytest.fixture
def token_json() -> dict:
    return {"access_token": "test-airtel-token", "expires_in": 3600}


def test_transfer(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/standard/v1/disbursements/", status_code=200, json={}
    )
    external_id = api.transfer("10000", "068511358", "PAY-001")
    assert len(external_id) == 36


def test_transfer_raises_when_no_pin():
    config = AirtelConfig.collection("client-id", "client-secret")
    api = AirtelDisbursementApi(config, BASE_URL)
    with pytest.raises(ValueError):
        api.transfer("10000", "068511358", "PAY-001")


def test_transfer_raises_on_400(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/standard/v1/disbursements/", status_code=400, json={}
    )
    with pytest.raises(MomoException):
        api.transfer("10000", "068511358", "PAY-001")


def test_get_transfer_status_pending(api, token_json, httpx_mock: HTTPXMock):
    external_id = "abc-123"
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/standard/v1/disbursements/{external_id}",
        json={"data": {"transaction": {"id": external_id, "status": "TIP"}}},
    )
    transaction = api.get_transfer_status(external_id)
    assert isinstance(transaction, AirtelTransaction)
    assert transaction.is_pending()


def test_get_transfer_status_successful(api, token_json, httpx_mock: HTTPXMock):
    external_id = "abc-123"
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/standard/v1/disbursements/{external_id}",
        json={
            "data": {
                "transaction": {"id": external_id, "status": "TS", "airtel_money_id": "AM456"}
            }
        },
    )
    transaction = api.get_transfer_status(external_id)
    assert transaction.is_successful()
    assert transaction.airtel_money_id == "AM456"


def test_get_transfer_status_raises_when_missing(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/standard/v1/disbursements/abc-123",
        json={"data": {}},
    )
    with pytest.raises(RuntimeError):
        api.get_transfer_status("abc-123")


def test_get_balance(api, token_json, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/auth/oauth2/token", json=token_json
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/standard/v1/users/balance",
        json={"data": {"balance": "100000", "currency": "XAF"}},
    )
    balance = api.get_balance()
    assert balance.available_balance == "100000"
    assert balance.currency == "XAF"
