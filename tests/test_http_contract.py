import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from momo_api import (
    AirtelApi,
    AirtelConfig,
    MomoApi,
    MomoException,
    PaymentRequest,
    RefundRequest,
    ResourceNotFoundException,
    TransferRequest,
)

SANDBOX = MomoApi.SANDBOX_URL
PRODUCTION = MomoApi.PRODUCTION_URL
TOKEN = {"access_token": "t", "token_type": "access_token", "expires_in": 3600}
CREDENTIALS = {"subscription_key": "k", "api_user": "u", "api_key": "s"}
REFERENCE_ID = "3f1c9a2e-8b4d-4c6f-9a1e-2d7b5c8e0f13"


def collection(environment="sandbox"):
    return MomoApi.collection({**CREDENTIALS, "environment": environment})


def disbursement(environment="sandbox"):
    return MomoApi.disbursement({**CREDENTIALS, "environment": environment})


def mock_token(httpx_mock: HTTPXMock, product: str, base: str = SANDBOX) -> None:
    httpx_mock.add_response(method="POST", url=f"{base}/{product}/token/", json=TOKEN)


MTN_WRITES = [
    ("request_to_pay", "collection", "requesttopay",
     lambda id=None: collection().request_to_pay(PaymentRequest.make("100", "242068511358", "o-1"), id)),
    ("quick_pay", "collection", "requesttopay",
     lambda id=None: collection().quick_pay("100", "242068511358", "o-1", "XAF", id)),
    ("deposit", "disbursement", "deposit",
     lambda id=None: disbursement().deposit(PaymentRequest.make("100", "242068511358", "d-1"), id)),
    ("transfer", "disbursement", "transfer",
     lambda id=None: disbursement().transfer(TransferRequest.make("100", "242068511358", "t-1"), id)),
    ("refund", "disbursement", "refund",
     lambda id=None: disbursement().refund(RefundRequest.make("100", REFERENCE_ID, "r-1"), id)),
]
WRITE_IDS = [w[0] for w in MTN_WRITES]


def write_request(httpx_mock: HTTPXMock) -> httpx.Request:
    return httpx_mock.get_requests()[1]


class TestMtnHeaders:
    @pytest.mark.parametrize("name,product,path,write", MTN_WRITES, ids=WRITE_IDS)
    def test_asks_for_a_json_response_on_every_write(self, httpx_mock, name, product, path, write):
        mock_token(httpx_mock, product)
        httpx_mock.add_response(method="POST", url=f"{SANDBOX}/{product}/v1_0/{path}", status_code=202)
        write()
        headers = write_request(httpx_mock).headers
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"
        assert headers["X-Target-Environment"] == "sandbox"

    def test_asks_for_a_json_response_on_the_token_and_status_calls(self, httpx_mock):
        mock_token(httpx_mock, "collection")
        httpx_mock.add_response(url=f"{SANDBOX}/collection/v1_0/requesttopay/abc", json={"status": "PENDING"})
        collection().get_payment_status("abc")
        assert all(r.headers["Accept"] == "application/json" for r in httpx_mock.get_requests())

    def test_sends_the_callback_url_when_configured(self, httpx_mock):
        mock_token(httpx_mock, "collection")
        httpx_mock.add_response(method="POST", url=f"{SANDBOX}/collection/v1_0/requesttopay", status_code=202)
        api = MomoApi.collection({**CREDENTIALS, "callback_url": "https://cb.example/hook"})
        api.quick_pay("100", "242068511358", "o-1")
        assert write_request(httpx_mock).headers["X-Callback-Url"] == "https://cb.example/hook"

    def test_url_encodes_the_phone_on_check_account_holder(self, httpx_mock):
        mock_token(httpx_mock, "collection")
        httpx_mock.add_response(url=f"{SANDBOX}/collection/v1_0/accountholder/msisdn/%2B242%2F1/active", json={"result": True})
        assert collection().check_account_holder("+242/1") is True


class TestMtnAcceptedStatus:
    @pytest.mark.parametrize("name,product,path,write", MTN_WRITES, ids=WRITE_IDS)
    def test_accepts_202(self, httpx_mock, name, product, path, write):
        mock_token(httpx_mock, product)
        httpx_mock.add_response(method="POST", url=f"{SANDBOX}/{product}/v1_0/{path}", status_code=202)
        assert len(write()) == 36

    @pytest.mark.parametrize("name,product,path,write", MTN_WRITES, ids=WRITE_IDS)
    def test_rejects_a_non_202_success(self, httpx_mock, name, product, path, write):
        mock_token(httpx_mock, product)
        httpx_mock.add_response(method="POST", url=f"{SANDBOX}/{product}/v1_0/{path}", status_code=200)
        with pytest.raises(MomoException) as caught:
            write()
        assert caught.value.status_code == 200


class TestSandboxCurrency:
    @pytest.mark.parametrize("name,product,path,write", MTN_WRITES, ids=WRITE_IDS)
    def test_sends_eur_to_the_sandbox_whatever_the_request_currency(self, httpx_mock, name, product, path, write):
        mock_token(httpx_mock, product)
        httpx_mock.add_response(method="POST", url=f"{SANDBOX}/{product}/v1_0/{path}", status_code=202)
        write()
        assert json.loads(write_request(httpx_mock).content)["currency"] == "EUR"

    def test_keeps_the_request_currency_outside_the_sandbox(self, httpx_mock):
        mock_token(httpx_mock, "collection", PRODUCTION)
        httpx_mock.add_response(method="POST", url=f"{PRODUCTION}/collection/v1_0/requesttopay", status_code=202)
        collection(MomoApi.ENVIRONMENT_MTN_CONGO).quick_pay("100", "242068511358", "o-1", "XAF")
        assert json.loads(write_request(httpx_mock).content)["currency"] == "XAF"

    def test_does_not_change_the_request_object_itself(self, httpx_mock):
        mock_token(httpx_mock, "collection")
        httpx_mock.add_response(method="POST", url=f"{SANDBOX}/collection/v1_0/requesttopay", status_code=202)
        request = PaymentRequest.make("100", "242068511358", "o-1", "XAF")
        collection().request_to_pay(request)
        assert request.currency == "XAF"


class TestCallerReferenceId:
    """A caller-supplied id lets an orchestrator query, rather than resend, a
    write whose response it never saw."""

    @pytest.mark.parametrize("name,product,path,write", MTN_WRITES, ids=WRITE_IDS)
    def test_sends_and_returns_the_given_reference_id(self, httpx_mock, name, product, path, write):
        mock_token(httpx_mock, product)
        httpx_mock.add_response(method="POST", url=f"{SANDBOX}/{product}/v1_0/{path}", status_code=202)
        assert write(REFERENCE_ID) == REFERENCE_ID
        assert write_request(httpx_mock).headers["X-Reference-Id"] == REFERENCE_ID

    @pytest.mark.parametrize("name,product,path,write", MTN_WRITES, ids=WRITE_IDS)
    def test_generates_a_fresh_uuid_without_one(self, httpx_mock, name, product, path, write):
        mock_token(httpx_mock, product)
        httpx_mock.add_response(method="POST", url=f"{SANDBOX}/{product}/v1_0/{path}", status_code=202)
        reference_id = write()
        assert reference_id != REFERENCE_ID
        assert write_request(httpx_mock).headers["X-Reference-Id"] == reference_id

    @pytest.mark.parametrize("name,product,path,write", MTN_WRITES, ids=WRITE_IDS)
    def test_rejects_a_non_uuid_reference_id_sending_nothing(self, httpx_mock, name, product, path, write):
        with pytest.raises(ValueError, match="reference_id must be a UUID"):
            write("order-1")
        assert httpx_mock.get_requests() == []

    def test_accepts_a_deterministic_v5_uuid(self, httpx_mock):
        mock_token(httpx_mock, "collection")
        httpx_mock.add_response(method="POST", url=f"{SANDBOX}/collection/v1_0/requesttopay", status_code=202)
        v5 = "886313e1-3b8a-5372-9b90-0c9aee199e5d"
        assert collection().quick_pay("100", "242068511358", "o-1", "EUR", v5) == v5


# --- Airtel ----------------------------------------------------------------

AIRTEL = AirtelApi.STAGING_URL
AIRTEL_TOKEN = {"access_token": "airtel-token", "expires_in": 3600}
OK = {"status": {"success": True, "code": "200", "message": "SUCCESS"}}


def airtel_collection():
    return AirtelApi.collection("staging", AirtelConfig.collection("cid", "secret"))


def airtel_disbursement():
    return AirtelApi.disbursement("staging", AirtelConfig.disbursement("cid", "secret", "encrypted-pin"))


def mock_airtel_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(method="POST", url=f"{AIRTEL}/auth/oauth2/token", json=AIRTEL_TOKEN)


AIRTEL_WRITES = [
    ("request_to_pay", "/merchant/v1/payments/",
     lambda id=None, phone="068511358": airtel_collection().request_to_pay("5000", phone, "ORDER-001", id)),
    ("transfer", "/standard/v1/disbursements/",
     lambda id=None, phone="068511358": airtel_disbursement().transfer("10000", phone, "PAY-001", id)),
]
AIRTEL_IDS = [w[0] for w in AIRTEL_WRITES]
REFUSAL = {
    "status": {
        "success": False, "code": "400", "message": "Insufficient funds",
        "result_code": "ESB000008", "response_code": "DP00800001006",
    },
}


class TestAirtelBusinessFailures:
    @pytest.mark.parametrize("name,path,write", AIRTEL_WRITES, ids=AIRTEL_IDS)
    def test_raises_when_the_envelope_reports_failure(self, httpx_mock, name, path, write):
        mock_airtel_token(httpx_mock)
        httpx_mock.add_response(method="POST", url=f"{AIRTEL}{path}", json=REFUSAL)
        with pytest.raises(MomoException) as caught:
            write()
        assert str(caught.value) == "Insufficient funds"
        assert caught.value.code == "ESB000008"
        assert caught.value.status_code == 400

    @pytest.mark.parametrize("name,path,write", AIRTEL_WRITES, ids=AIRTEL_IDS)
    def test_accepts_a_request_whose_envelope_reports_success(self, httpx_mock, name, path, write):
        mock_airtel_token(httpx_mock)
        httpx_mock.add_response(method="POST", url=f"{AIRTEL}{path}", json=OK)
        assert len(write()) == 36

    @pytest.mark.parametrize("name,path,write", AIRTEL_WRITES, ids=AIRTEL_IDS)
    def test_accepts_a_request_with_no_envelope_at_all(self, httpx_mock, name, path, write):
        mock_airtel_token(httpx_mock)
        httpx_mock.add_response(method="POST", url=f"{AIRTEL}{path}", json={"data": {}})
        assert len(write()) == 36

    def test_raises_on_a_failed_status_lookup_rather_than_returning_a_blank_transaction(self, httpx_mock):
        mock_airtel_token(httpx_mock)
        httpx_mock.add_response(
            url=f"{AIRTEL}/standard/v1/payments/abc",
            json={"status": {"success": False, "code": "404", "message": "Not found", "result_code": "ESB000014"}},
        )
        with pytest.raises(ResourceNotFoundException) as caught:
            airtel_collection().get_payment_status("abc")
        assert caught.value.code == "ESB000014"


class TestAirtelStatusPayload:
    @pytest.mark.parametrize("body", [{"data": {}}, {}, {"data": {"transaction": {}}}])
    def test_reports_a_missing_transaction_as_resource_not_found(self, httpx_mock, body):
        mock_airtel_token(httpx_mock)
        httpx_mock.add_response(url=f"{AIRTEL}/standard/v1/payments/abc", json=body)
        with pytest.raises(ResourceNotFoundException, match="externalId: abc"):
            airtel_collection().get_payment_status("abc")

    def test_reports_a_missing_transaction_on_disbursement_as_resource_not_found(self, httpx_mock):
        mock_airtel_token(httpx_mock)
        httpx_mock.add_response(url=f"{AIRTEL}/standard/v1/disbursements/abc", json={"data": {}})
        with pytest.raises(ResourceNotFoundException):
            airtel_disbursement().get_transfer_status("abc")

    def test_parses_a_well_formed_transaction(self, httpx_mock):
        mock_airtel_token(httpx_mock)
        httpx_mock.add_response(
            url=f"{AIRTEL}/standard/v1/payments/abc",
            json={"data": {"transaction": {"id": "abc", "status": "TI", "reference_id": "R1"}}, **OK},
        )
        transaction = airtel_collection().get_payment_status("abc")
        assert transaction.is_pending()
        assert transaction.reference_id == "R1"


class TestAirtelMsisdn:
    @pytest.mark.parametrize("name,path,write", AIRTEL_WRITES, ids=AIRTEL_IDS)
    def test_drops_the_country_code(self, httpx_mock, name, path, write):
        mock_airtel_token(httpx_mock)
        httpx_mock.add_response(method="POST", url=f"{AIRTEL}{path}", json=OK)
        write(phone="242068511358")
        body = json.loads(httpx_mock.get_requests()[1].content)
        msisdn = body["subscriber"]["msisdn"] if "subscriber" in body else body["payee"]["msisdn"]
        assert msisdn == "068511358"


class TestAirtelTransactionId:
    @pytest.mark.parametrize("name,path,write", AIRTEL_WRITES, ids=AIRTEL_IDS)
    def test_sends_and_returns_the_given_transaction_id(self, httpx_mock, name, path, write):
        mock_airtel_token(httpx_mock)
        httpx_mock.add_response(method="POST", url=f"{AIRTEL}{path}", json=OK)
        assert write(REFERENCE_ID) == REFERENCE_ID
        assert json.loads(httpx_mock.get_requests()[1].content)["transaction"]["id"] == REFERENCE_ID

    @pytest.mark.parametrize("name,path,write", AIRTEL_WRITES, ids=AIRTEL_IDS)
    def test_rejects_a_non_uuid_transaction_id_sending_nothing(self, httpx_mock, name, path, write):
        with pytest.raises(ValueError, match="transaction_id must be a UUID"):
            write("BATCH42-0007")
        assert httpx_mock.get_requests() == []
