import re

import pytest

from momo_api import ErrorReason, Transaction

CODES = [
    name for name, value in vars(ErrorReason).items()
    if name.isupper() and isinstance(value, str)
]


def predicate_for(code: str) -> str:
    return "is_" + code.lower()


def test_exposes_code_and_message_parsed_from_the_api_payload():
    reason = ErrorReason.from_dict({"code": "NOT_ENOUGH_FUNDS", "message": "Payer has insufficient funds"})
    assert reason.code == "NOT_ENOUGH_FUNDS"
    assert reason.message == "Payer has insufficient funds"


def test_defaults_code_and_message_to_empty_strings_when_absent():
    reason = ErrorReason.from_dict({})
    assert (reason.code, reason.message) == ("", "")


def test_matches_a_code_with_is_code():
    reason = ErrorReason("EXPIRED", "")
    assert reason.is_code(ErrorReason.EXPIRED)
    assert not reason.is_code(ErrorReason.NOT_ENOUGH_FUNDS)


@pytest.mark.parametrize("code", CODES)
def test_provides_a_predicate_for_every_code(code):
    predicate = getattr(ErrorReason(code, ""), predicate_for(code))
    assert predicate() is True


@pytest.mark.parametrize("code", CODES)
def test_a_predicate_that_does_not_match_returns_false(code):
    assert getattr(ErrorReason("SOMETHING_ELSE", ""), predicate_for(code))() is False


def test_exposes_every_mtn_failure_code_as_a_constant():
    assert len(CODES) == 23
    for code in CODES:
        assert getattr(ErrorReason, code) == code


def test_renders_as_code_and_message():
    assert str(ErrorReason("NOT_ENOUGH_FUNDS", "Insufficient funds")) == "[NOT_ENOUGH_FUNDS] Insufficient funds"


def test_renders_as_code_alone_when_there_is_no_message():
    assert str(ErrorReason("NOT_ENOUGH_FUNDS", "")) == "[NOT_ENOUGH_FUNDS]"


@pytest.mark.parametrize("code,expected", [
    ("NOT_ENOUGH_FUNDS", True),
    ("PAYER_LIMIT_REACHED", True),
    ("LOW_BALANCE_OR_PAYEE_LIMIT_REACHED_OR_NOT_ALLOWED", True),
    ("PAYEE_NOT_FOUND", False),
    ("EXPIRED", False),
])
def test_groups_the_payer_funding_failures_including_the_congo_code(code, expected):
    assert ErrorReason(code, "").is_payer_funding_failure() is expected


class TestTransactionReason:
    def test_returns_the_parsed_reason_of_a_failed_transaction(self):
        transaction = Transaction.parse({
            "status": "FAILED",
            "reason": {"code": "PAYER_NOT_FOUND", "message": "Payer not found"},
        })
        assert transaction.reason == ErrorReason("PAYER_NOT_FOUND", "Payer not found")
        assert transaction.reason.is_payer_not_found()

    def test_returns_none_when_the_transaction_carries_no_reason(self):
        assert Transaction.parse({"status": "SUCCESSFUL"}).reason is None

    def test_parses_the_bare_string_reason_get_status_returns(self):
        reason = Transaction.parse({"status": "FAILED", "reason": "NOT_ENOUGH_FUNDS"}).reason
        assert reason == ErrorReason("NOT_ENOUGH_FUNDS", "")
        assert reason.is_not_enough_funds()
        assert str(reason) == "[NOT_ENOUGH_FUNDS]"

    def test_parses_the_code_mtn_congo_returns_for_a_payer_who_cannot_pay(self):
        reason = Transaction.parse({
            "status": "FAILED", "reason": "LOW_BALANCE_OR_PAYEE_LIMIT_REACHED_OR_NOT_ALLOWED",
        }).reason
        assert reason.is_payer_funding_failure()
        assert not reason.is_not_enough_funds()

    @pytest.mark.parametrize("value", ["", 42, None, ["NOT_ENOUGH_FUNDS"]])
    def test_returns_none_when_reason_is_empty_or_another_type(self, value):
        assert Transaction.parse({"status": "FAILED", "reason": value}).reason is None


class TestTransactionFields:
    def test_absent_optional_fields_are_none(self):
        # Transfer and refund status bodies omit payerMessage and payeeNote
        transaction = Transaction.parse({"status": "SUCCESSFUL", "amount": "100", "currency": "UGX"})
        assert transaction.payer_message is None
        assert transaction.payee_note is None
        assert transaction.external_id is None
        assert transaction.payer is None
        assert transaction.payee is None

    def test_reads_the_party_msisdn(self):
        transaction = Transaction.parse({
            "status": "SUCCESSFUL",
            "payee": {"partyIdType": "MSISDN", "partyId": "242068511358"},
        })
        assert transaction.payee == "242068511358"
        assert transaction.raw["payee"]["partyIdType"] == "MSISDN"
