import pytest
from pytest_httpx import HTTPXMock

from momo_api import MomoApi
from momo_api.models.payment_request import PaymentRequest
from momo_api.models.transfer_request import TransferRequest
from momo_api.models.refund_request import RefundRequest
from momo_api.exceptions import ResourceNotFoundException, InvalidSubscriptionKeyException

SANDBOX_BASE = "https://sandbox.momodeveloper.mtn.com"


def test_get_access_token(disbursement_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/disbursement/token/",
        json=token_response,
        status_code=200,
    )
    token = disbursement_api.get_access_token()
    assert token.access_token == "test-access-token-abc123"


def test_get_balance(disbursement_api, token_response, account_balance_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/disbursement/v1_0/account/balance",
        json=account_balance_response,
    )
    balance = disbursement_api.get_balance()
    assert balance.available_balance == "1000"
    assert balance.currency == "EUR"


def test_deposit(disbursement_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/token/", json=token_response)
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/v1_0/deposit", status_code=202)

    request = PaymentRequest.make("200", "46733123450", "dep-001", "EUR")
    reference_id = disbursement_api.deposit(request)
    assert isinstance(reference_id, str) and len(reference_id) == 36


def test_get_deposit_status(disbursement_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/disbursement/v1_0/deposit/dep-uuid",
        json={
            "amount": "200", "currency": "EUR",
            "financialTransactionId": "111222333",
            "externalId": "dep-001",
            "payer": {"partyIdType": "MSISDN", "partyId": "46733123450"},
            "payerMessage": "Deposit", "payeeNote": "Deposit note",
            "status": "SUCCESSFUL",
        },
    )
    transaction = disbursement_api.get_deposit_status("dep-uuid")
    assert transaction.is_successful()
    assert transaction.amount == "200"


def test_transfer(disbursement_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/token/", json=token_response)
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/v1_0/transfer", status_code=202)

    request = TransferRequest.make("150", "46733123450", "xfer-001", "EUR")
    reference_id = disbursement_api.transfer(request)
    assert isinstance(reference_id, str) and len(reference_id) == 36


def test_get_transfer_status(disbursement_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/disbursement/v1_0/transfer/xfer-uuid",
        json={
            "amount": "150", "currency": "EUR",
            "financialTransactionId": "444555666",
            "externalId": "xfer-001",
            "payee": {"partyIdType": "MSISDN", "partyId": "46733123450"},
            "payerMessage": "Salary", "payeeNote": "Salary payment",
            "status": "SUCCESSFUL",
        },
    )
    transaction = disbursement_api.get_transfer_status("xfer-uuid")
    assert transaction.is_successful()
    assert transaction.amount == "150"


def test_refund(disbursement_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/token/", json=token_response)
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/v1_0/refund", status_code=202)

    request = RefundRequest.make("50", "original-ref-uuid", "refund-001", "EUR")
    reference_id = disbursement_api.refund(request)
    assert isinstance(reference_id, str) and len(reference_id) == 36


def test_get_refund_status(disbursement_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/disbursement/v1_0/refund/refund-uuid",
        json={
            "amount": "50", "currency": "EUR",
            "financialTransactionId": "777888999",
            "externalId": "refund-001",
            "payerMessage": "Refund", "payeeNote": "Refund note",
            "status": "SUCCESSFUL",
        },
    )
    transaction = disbursement_api.get_refund_status("refund-uuid")
    assert transaction.is_successful()


def test_get_access_token_invalid_key(disbursement_api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{SANDBOX_BASE}/disbursement/token/",
        json={"message": "Invalid subscription key"},
        status_code=401,
    )
    with pytest.raises(InvalidSubscriptionKeyException):
        disbursement_api.get_access_token()


def test_get_deposit_status_not_found(disbursement_api, token_response, httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="POST", url=f"{SANDBOX_BASE}/disbursement/token/", json=token_response)
    httpx_mock.add_response(
        method="GET",
        url=f"{SANDBOX_BASE}/disbursement/v1_0/deposit/unknown",
        json={"message": "Not found"},
        status_code=404,
    )
    with pytest.raises(ResourceNotFoundException):
        disbursement_api.get_deposit_status("unknown")
