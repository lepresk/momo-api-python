# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2026-10-12

### Changed
- The MTN production base URL is now `https://momoapi.momo.africa`, replacing
  `https://proxy.momoapi.mtn.com`, following MTN's migration. `MomoApi.PRODUCTION_URL`
  and every non-sandbox MTN environment use the new host; the sandbox is unchanged

## [2.0.0] - 2026-10-08

Parity release: brings the Python client level with the PHP client
(`lepresk/momo-api` 1.5.0) and the Node client (`@lepresk/momo-api` 2.3.0).
Anyone moving money with 1.x should upgrade: a write whose response was lost
could not be queried and a retry could pay twice, Airtel refusals were reported
as accepted, and failed MTN transactions carried no reason.

1.2.0 below was tagged in this changelog but never published to PyPI; 2.0.0
ships its Airtel support along with everything here.

### Changed
- **BREAKING**: requires Python 3.10 or later. 3.8 and 3.9 are end-of-life and
  receive no security fixes. CI covers 3.10 to 3.13
- **BREAKING**: `request_to_pay()`, `deposit()`, `transfer()` and `refund()`
  require HTTP 202 exactly, as the PHP and Node clients do; any other status,
  2xx included, raises a `MomoException`
- **BREAKING**: `Transaction` fields MTN may leave out (`amount`, `currency`,
  `financial_transaction_id`, `external_id`, `payer_message`, `payee_note`) are
  `None` when absent instead of `""`, and `payer` / `payee` are the MSISDN
  rather than the raw `{partyIdType, partyId}` dict, which stays available
  through `Transaction.raw`. `Transaction` is no longer a dataclass: build one
  with `Transaction.parse(data)`
- **BREAKING**: `create_exception(status_code, body)` takes the raw response
  body, not a message, so it can parse the message and the failure reason
- **BREAKING**: a missing Airtel transaction raises `ResourceNotFoundException`
  on both `get_payment_status()` and `get_transfer_status()`. The disbursement
  side raised `RuntimeError`; the collection side returned a blank transaction
- **BREAKING**: every Airtel call, status and balance lookups included, raises
  a `MomoException` when Airtel's `status` envelope reports `success: false`
- **BREAKING**: an Airtel transfer amount with decimals (`"100.50"`) is sent
  truncated (`"100"`), as the Node and PHP clients do; it used to raise
  `ValueError`
- **BREAKING**: `check_account_holder()` returns `True` only for a JSON `true`
  result, not for any truthy value such as the string `"false"`
- The default HTTP client times out after 30 seconds instead of httpx's 5, which
  is short for a payment write. A timeout still raises `httpx.TimeoutException`
- A dict passed to `MomoApi.collection()` / `disbursement()` without an
  `environment` key uses the `environment` argument instead of ignoring it
- A token response with a missing or non-numeric `expires_in` no longer
  crashes, and an empty token is never cached
- Every MTN request sends `Accept: application/json`, token and sandbox
  endpoints included
- `AirtelTransaction.parse()` treats an empty or non-string field as absent

### Fixed
- Unknown environments no longer resolve silently to the production host:
  `MomoApi.create()`, `MomoApi.get_base_url()` and the factories raise
  `ValueError: Unknown environment: '...'`
- `MomoApi.sandbox()` refuses to run against a non-sandbox environment
- `MomoApi.collection()` / `disbursement()` reject missing `subscription_key`,
  `api_user` or `api_key` instead of sending empty credentials
- A FAILED transaction from Get Status had no reason. MTN reports it in an HTTP
  200 body as a bare string (`"reason": "NOT_ENOUGH_FUNDS"`) or as
  `{code, message}`; `Transaction.reason` now reads both
- Payments in the sandbox failed with the default currency. The sandbox accepts
  EUR only; against it every write now sends `EUR` whatever the request
  currency, leaving the request object untouched
- Airtel `TI` ("transaction initiated") was not recognised as pending, leaving
  the transaction in no state at all
- Airtel reports business failures (insufficient funds, invalid PIN) with HTTP
  200 and `status.success: false`. Those were read as successes:
  `request_to_pay()` and `transfer()` returned an externalId for a refused
  request. They now raise a `MomoException` carrying Airtel's message and
  result code
- The Airtel MSISDN was sent verbatim; a country-prefixed number
  (`242068511358`) was rejected. It is now stripped to the national number
- `check_account_holder()` did not URL-encode the phone number

### Added
- Caller-supplied ids on every write: `reference_id` on MTN `request_to_pay()`,
  `quick_pay()`, `deposit()`, `transfer()` and `refund()` (sent as
  `X-Reference-Id`), `transaction_id` on Airtel `request_to_pay()` and
  `transfer()` (sent as `transaction.id`). After a timeout or 5xx you can query
  a payment whose response you never saw, and retry with the same id instead of
  risking a second payment. It must be a UUID; anything else raises
  `ValueError` before a request is sent
- `ErrorReason`: the failure reason of a transaction or exception, with the 23
  MTN failure codes as constants, a predicate for each (`is_not_enough_funds()`,
  `is_expired()`, ...), `is_code()`, and `is_payer_funding_failure()`, which
  also covers the `LOW_BALANCE_OR_PAYEE_LIMIT_REACHED_OR_NOT_ALLOWED` code MTN
  Congo returns instead of `NOT_ENOUGH_FUNDS`
- `MomoException.reason`, `.code` and `.body`, and default messages on every
  typed exception; `BadResourceException` for a malformed reference id
- Injectable HTTP client: pass an `httpx.Client` to `MomoApi.create()`,
  `MomoApi.collection()` / `disbursement()`, `AirtelApi.create()`, the Airtel
  shorthand factories or any product constructor, for timeouts, retries,
  proxies and connection reuse
- `encrypt_airtel_pin(pin, public_key)`: RSA/PKCS#1 v1.5 encryption of the
  Airtel disbursement PIN, accepting a PEM, a base64-encoded PEM or the bare
  base64 body as Airtel's portal shows it, or that body base64-encoded again.
  Needs the new `[airtel]` extra (`cryptography`)
- `AirtelResponseStatus`, the `status` envelope Airtel returns; `AirtelTransaction.reference_id`
  and `STATUS_IN_PROGRESS`; `clean_phone_number()` and `AIRTEL_COUNTRY_CODES`
- `MomoApi.ENVIRONMENTS`, `MomoApi.get_base_url()`, `get_collection()` /
  `get_disbursement()`, and a `Config` accepted by the factories with the
  environment as second argument
- `Config.with_callback_uri()`, `DEFAULT_CURRENCY`, `SANDBOX_CURRENCY`,
  `generate_uuid()`, `assert_uuid()`, `AbstractApiProduct`, `AbstractAirtelApi`,
  `AbstractRequest` and `msisdn()`
- `config`, `environment`, `base_url` and `subscription_key` properties on the
  MTN products
- Type hints throughout, checked with `mypy --strict`, and a `py.typed` marker
- The README documents retries with a caller-supplied id, and warns that
  callbacks are not signed: its examples re-query the status from MTN or Airtel
  before fulfilling an order

## [1.2.0] - 2026-03-07

### Added
- **Airtel Money support**: `AirtelApi`, `AirtelCollectionApi`, `AirtelDisbursementApi`
  - `AirtelCollectionApi.request_to_pay()`, `get_payment_status()`, `get_balance()`
  - `AirtelDisbursementApi.transfer()`, `get_transfer_status()`, `get_balance()`
  - `AirtelConfig` with `collection()` and `disbursement()` class methods
  - `AirtelTransaction` with `is_successful()`, `is_pending()`, `is_failed()` helpers
- **Token caching**: `CollectionApi` and `DisbursementApi` now cache access tokens for their TTL
- `CollectionApi.check_account_holder()` — verify an MSISDN is active
- `DisbursementApi.check_account_holder()` — verify an MSISDN is active
- `TokenCache` support class for in-memory token TTL management

## [1.0.0] - 2025-02-27

### Added
- Initial release — port of [`lepresk/momo-api`](https://github.com/lepresk/momo-api) (PHP) to Python
- `CollectionApi`: `request_to_pay()`, `quick_pay()`, `get_payment_status()`, `get_balance()`, `get_access_token()`
- `DisbursementApi`: `deposit()`, `get_deposit_status()`, `transfer()`, `get_transfer_status()`, `refund()`, `get_refund_status()`, `get_balance()`, `get_access_token()`
- `SandboxApi`: `create_api_user()`, `get_api_user()`, `create_api_key()`
- Static factory methods: `MomoApi.collection()`, `MomoApi.disbursement()`
- `PaymentRequest.make()`, `TransferRequest.make()`, `RefundRequest.make()` factories
- `Transaction` with `is_successful()`, `is_pending()`, `is_failed()` helpers
- Typed exception hierarchy: `BadRequestException`, `InvalidSubscriptionKeyException`, `ResourceNotFoundException`, `ConflictException`, `InternalServerErrorException`
- Support for 12 MTN environments (sandbox + 11 production markets)
- Uses `httpx` as the only runtime dependency
- Python 3.8+ compatible
