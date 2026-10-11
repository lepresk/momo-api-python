import json

import pytest

from momo_api import (
    BadRequestException,
    BadResourceException,
    ConflictException,
    ErrorReason,
    InternalServerErrorException,
    InvalidSubscriptionKeyException,
    MomoException,
    ResourceNotFoundException,
    Transaction,
    create_exception,
)

BODY = json.dumps({"code": "PAYER_NOT_FOUND", "message": "Payer not found"})


def test_extracts_the_message_field_from_a_json_error_body():
    assert str(create_exception(400, BODY)) == "Payer not found"


def test_exposes_the_failure_as_a_typed_error_reason():
    exception = create_exception(400, BODY)
    assert exception.reason == ErrorReason("PAYER_NOT_FOUND", "Payer not found")
    assert exception.reason.is_payer_not_found()


def test_reports_the_same_vocabulary_as_transaction_reason():
    payload = {"code": "NOT_ENOUGH_FUNDS", "message": "Insufficient funds"}
    transaction = Transaction.parse({"status": "FAILED", "reason": payload})
    assert create_exception(400, json.dumps(payload)).reason == transaction.reason


@pytest.mark.parametrize("body", ["not json", "[1, 2]", '"text"'])
def test_has_no_reason_when_the_body_is_not_a_json_object(body):
    assert create_exception(400, body).reason is None


def test_exposes_the_error_code_from_a_json_error_body():
    assert create_exception(400, BODY).code == "PAYER_NOT_FOUND"
    assert create_exception(400, "").code is None


def test_keeps_the_raw_body_available_for_debugging():
    assert create_exception(400, BODY).body == BODY


@pytest.mark.parametrize("body", [json.dumps({"code": "X"}), None, "", "<html>"])
def test_falls_back_to_the_default_message(body):
    assert str(create_exception(404, body)) == ResourceNotFoundException.default_message


@pytest.mark.parametrize("status,exception_class", [
    (400, BadRequestException),
    (401, InvalidSubscriptionKeyException),
    (404, ResourceNotFoundException),
    (409, ConflictException),
    (500, InternalServerErrorException),
])
def test_maps_each_status_to_its_exception(status, exception_class):
    exception = create_exception(status, BODY)
    assert type(exception) is exception_class
    assert exception.status_code == status


def test_maps_an_unmapped_status_to_a_plain_momo_exception():
    exception = create_exception(503, BODY)
    assert type(exception) is MomoException
    assert exception.status_code == 503
    assert str(exception) == "Payer not found"


def test_describes_the_failure_when_an_unmapped_status_has_no_message():
    assert str(create_exception(418)) == "Operation failed with status 418"


def test_exposes_bad_resource_exception_for_malformed_reference_ids():
    exception = BadResourceException()
    assert exception.status_code == 400
    assert "reference id" in str(exception)


@pytest.mark.parametrize("exception_class", [
    BadRequestException, BadResourceException, InvalidSubscriptionKeyException,
    ResourceNotFoundException, ConflictException, InternalServerErrorException,
])
def test_keeps_every_typed_exception_catchable_as_momo_exception(exception_class):
    with pytest.raises(MomoException):
        raise exception_class()
