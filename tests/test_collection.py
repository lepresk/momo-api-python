import pytest
import httpx
from pytest_httpx import HTTPXMock

from momo_api import MomoApi
from momo_api.models.payment_request import PaymentRequest
from momo_api.exceptions import (
    BadRequestException,
    InvalidSubscriptionKeyException,
    ResourceNotFoundException,
)

SANDBOX_BASE = "https://sandbox.momodeveloper.mtn.com"


def test_get_access_token(collection_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/collection/token/",
        json=token_response,
        status_code=200,
    )
    token = collection_api.get_access_token()
    assert token.access_token == "test-access-token-abc123"
    assert token.expires_in == 3600


def test_request_to_pay_returns_reference_id(collection_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/token/", json=token_response)
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/v1_0/requesttopay", status_code=202)

    request = PaymentRequest.make("100", "46733123450", "order-123", "EUR")
    reference_id = collection_api.request_to_pay(request)

    assert isinstance(reference_id, str)
    assert len(reference_id) == 36  # UUID format


def test_get_payment_status_successful(collection_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/collection/v1_0/requesttopay/some-uuid",
        json={
            "amount": "100", "currency": "EUR",
            "financialTransactionId": "363440463",
            "externalId": "order-123",
            "payer": {"partyIdType": "MSISDN", "partyId": "46733123450"},
            "payerMessage": "Payment", "payeeNote": "Thank you",
            "status": "SUCCESSFUL",
        },
    )
    transaction = collection_api.get_payment_status("some-uuid")
    assert transaction.is_successful()
    assert transaction.amount == "100"
    assert transaction.payer["partyId"] == "46733123450"


def test_get_payment_status_pending(collection_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/collection/v1_0/requesttopay/some-uuid",
        json={
            "amount": "100", "currency": "EUR", "externalId": "order-123",
            "payer": {"partyIdType": "MSISDN", "partyId": "46733123450"},
            "payerMessage": "", "payeeNote": "", "status": "PENDING",
        },
    )
    transaction = collection_api.get_payment_status("some-uuid")
    assert transaction.is_pending()
    assert not transaction.is_successful()


def test_get_payment_status_failed(collection_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/collection/v1_0/requesttopay/some-uuid",
        json={
            "amount": "100", "currency": "EUR", "externalId": "order-123",
            "payer": {"partyIdType": "MSISDN", "partyId": "46733123450"},
            "payerMessage": "", "payeeNote": "", "status": "FAILED",
            "reason": {"code": "PAYER_NOT_FOUND", "message": "Payer not found"},
        },
    )
    transaction = collection_api.get_payment_status("some-uuid")
    assert transaction.is_failed()


def test_get_balance(collection_api, token_response, account_balance_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/collection/v1_0/account/balance",
        json=account_balance_response,
    )
    balance = collection_api.get_balance()
    assert balance.available_balance == "1000"
    assert balance.currency == "EUR"


def test_quick_pay(collection_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/token/", json=token_response)
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/v1_0/requesttopay", status_code=202)

    reference_id = collection_api.quick_pay("50", "46733123450", "quick-ref", "EUR")
    assert isinstance(reference_id, str)


def test_get_access_token_invalid_key(collection_api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/collection/token/",
        json={"message": "Invalid subscription key"},
        status_code=401,
    )
    with pytest.raises(InvalidSubscriptionKeyException):
        collection_api.get_access_token()


def test_request_to_pay_bad_request(collection_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/token/", json=token_response)
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/collection/v1_0/requesttopay",
        json={"message": "Bad request"},
        status_code=400,
    )
    with pytest.raises(BadRequestException):
        collection_api.request_to_pay(PaymentRequest.make("100", "46733123450", "order-bad"))


def test_get_payment_status_not_found(collection_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/collection/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/collection/v1_0/requesttopay/unknown-id",
        json={"message": "Not found"},
        status_code=404,
    )
    with pytest.raises(ResourceNotFoundException):
        collection_api.get_payment_status("unknown-id")
