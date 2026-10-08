# mtn-momo-client

[![PyPI](https://img.shields.io/pypi/v/mtn-momo-client)](https://pypi.org/project/mtn-momo-client/)
[![Python](https://img.shields.io/pypi/pyversions/mtn-momo-client)](https://pypi.org/project/mtn-momo-client/)
[![CI](https://github.com/lepresk/momo-api-python/actions/workflows/ci.yml/badge.svg)](https://github.com/lepresk/momo-api-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MTN Mobile Money and Airtel Money API client for Python: collections, disbursements and remittances.

This is a port of the PHP package [`lepresk/momo-api`](https://github.com/lepresk/momo-api), kept in step with it and with the [Node.js client](https://github.com/lepresk/momo-api-node). Fully typed (`py.typed`).

## Requirements

- Python 3.10 or later
- An MTN MoMo developer account with API credentials (for MTN)
- An Airtel Money developer account with OAuth2 credentials (for Airtel)

## Installation

```bash
pip install mtn-momo-client

# to encrypt the Airtel disbursement PIN with encrypt_airtel_pin()
pip install "mtn-momo-client[airtel]"
```

## Getting started

### Sandbox setup

Before making live API calls you need to provision a sandbox user and API key:

```python
from momo_api import MomoApi, generate_uuid

sandbox = MomoApi.create(MomoApi.ENVIRONMENT_SANDBOX).sandbox("your-subscription-key")

api_user = generate_uuid()
sandbox.create_api_user(api_user, "https://your-callback-host.com")
api_key = sandbox.create_api_key(api_user)
```

## Collection

The Collection product requests payments from customers.

```python
from momo_api import Config, MomoApi, PaymentRequest

config = Config.collection(
    "your-subscription-key",
    "your-api-user",
    "your-api-key",
    "https://your-callback-host.com/webhook",
)
collection = MomoApi.create(MomoApi.ENVIRONMENT_SANDBOX).get_collection(config)

# Request a payment
request = PaymentRequest.make(
    "100",                     # amount
    "242068511358",            # payer phone number (MSISDN)
    "order-123",               # your external reference
    "XAF",                     # currency (optional, defaults to XAF)
    "Payment for order #123",  # payer message (optional)
    "Thank you",               # payee note (optional)
)
reference_id = collection.request_to_pay(request)

# Check payment status
transaction = collection.get_payment_status(reference_id)
if transaction.is_successful():
    print("Paid:", transaction.financial_transaction_id)
elif transaction.is_pending():
    print("Still pending")
else:
    print("Failed:", transaction.reason)

# Account balance
balance = collection.get_balance()
print(balance.available_balance, balance.currency)

# Quick pay shorthand; currency is optional and defaults to XAF
reference_id = collection.quick_pay("50", "242068511358", "quick-order-456")
```

The sandbox accepts EUR only. Against the sandbox, `request_to_pay()`,
`quick_pay()`, `deposit()`, `transfer()` and `refund()` send `EUR` whatever
currency the request was built with (`SANDBOX_CURRENCY`), so the same XAF code
runs in both environments. Outside the sandbox the request currency is sent as is.

## Disbursement

The Disbursement product sends money to customers.

```python
from momo_api import Config, MomoApi, PaymentRequest, RefundRequest, TransferRequest

config = Config.disbursement("your-subscription-key", "your-api-user", "your-api-key")
disbursement = MomoApi.create(MomoApi.ENVIRONMENT_SANDBOX).get_disbursement(config)

# Deposit funds to a customer
deposit_id = disbursement.deposit(PaymentRequest.make("200", "242068511358", "dep-001"))
deposit = disbursement.get_deposit_status(deposit_id)

# Transfer funds
transfer_id = disbursement.transfer(TransferRequest.make("300", "242068511358", "xfer-001"))
transfer = disbursement.get_transfer_status(transfer_id)

# Refund a previous payment
refund_id = disbursement.refund(RefundRequest.make("50", "original-payment-reference-id", "refund-001"))
refund = disbursement.get_refund_status(refund_id)
```

Both products also offer `get_balance()` and `check_account_holder(phone)`.

## Airtel Money

### Airtel Collection (receive payments)

```python
from momo_api import AirtelApi, AirtelConfig

collection = AirtelApi.collection(
    "staging",
    AirtelConfig.collection(
        "YOUR_CLIENT_ID",
        "YOUR_CLIENT_SECRET",
        callback_uri="https://your-callback-host.com/webhook",
        country="CG",    # optional, defaults to CG
        currency="XAF",  # optional, defaults to XAF
    ),
)

external_id = collection.request_to_pay("5000", "068511358", "ORDER-001")

transaction = collection.get_payment_status(external_id)
if transaction.is_successful():
    print("Received, Airtel Money id:", transaction.airtel_money_id)
elif transaction.is_pending():
    print("Pending")
elif transaction.is_failed():
    print("Failed:", transaction.message)
```

### Airtel Disbursement (send money)

```python
from momo_api import AirtelApi, AirtelConfig

disbursement = AirtelApi.disbursement(
    "production",
    AirtelConfig.disbursement("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET", "YOUR_ENCRYPTED_PIN"),
)

external_id = disbursement.transfer("10000", "068511358", "PAY-001")
transaction = disbursement.get_transfer_status(external_id)
```

### Airtel disbursement PIN

The transfer endpoint takes an RSA-encrypted PIN, never the PIN itself. Encrypt
it with the public key Airtel gives you (needs the `[airtel]` extra):

```python
import os

from momo_api import AirtelApi, AirtelConfig, encrypt_airtel_pin

disbursement = AirtelApi.disbursement(
    "production",
    AirtelConfig.disbursement(
        os.environ["AIRTEL_CLIENT_ID"],
        os.environ["AIRTEL_CLIENT_SECRET"],
        encrypt_airtel_pin("1234", os.environ["AIRTEL_PUBLIC_KEY"]),
    ),
)
```

The key is accepted as a PEM, a base64-encoded PEM, the bare base64 body as
Airtel's portal shows it, or that body base64-encoded again.

### Airtel phone numbers

Airtel expects a national MSISDN. Numbers are normalised for you: passing
`242068511358` or `068511358` sends `068511358` either way. `clean_phone_number()`
is exported if you need the same normalisation elsewhere.

### Airtel failures

Airtel reports business failures with HTTP 200 and `status.success: false`, so
`request_to_pay()` and `transfer()` raise a `MomoException` in that case rather
than returning an externalId for a refused request. Status and balance lookups
raise the same way:

```python
from momo_api import MomoException

try:
    disbursement.transfer("10000", "068511358", "PAY-001")
except MomoException as error:
    print(error, error.code)  # "Invalid PIN", "ESB000008"
```

Status codes: `TS` successful, `TF` failed, `TIP` and `TI` both pending.

### Airtel environments

| Mode | URL | Use case |
|------|-----|----------|
| `staging` | `https://openapiuat.airtel.cg` | Testing |
| `production` | `https://openapi.airtel.cg` | Production (Congo) |

## Static factory methods

`MomoApi.collection()` and `MomoApi.disbursement()` build a product from flat
credentials, in any environment:

```python
from momo_api import MomoApi

collection = MomoApi.collection({
    "environment": MomoApi.ENVIRONMENT_MTN_GHANA,  # optional, defaults to sandbox
    "subscription_key": "your-subscription-key",
    "api_user": "your-api-user",
    "api_key": "your-api-key",
    "callback_url": "https://your-callback-host.com/webhook",  # optional
})
```

Missing credentials raise `ValueError` immediately (`subscription_key is
required`), and an environment outside the table below raises
`ValueError: Unknown environment: '...'` rather than silently pointing at
production.

The environment is the dict's `environment` key when present, the second
argument otherwise. They also accept a `Config`, with the environment as the
second argument:

```python
collection = MomoApi.collection(config, MomoApi.ENVIRONMENT_MTN_GHANA)
```

## Custom HTTP client

By default each request goes through a short-lived `httpx.Client` with a
30-second timeout. A timeout raises `httpx.TimeoutException`, not a
`MomoException`, and leaves the outcome unknown: MTN or Airtel may have
accepted the payment, so query its status with your reference id before
retrying (see [Retrying without paying twice](#retrying-without-paying-twice)).

Pass your own client to change timeouts, add retries, proxies or logging, and
reuse connections:

```python
import httpx

from momo_api import AirtelApi, MomoApi

client = httpx.Client(timeout=10, transport=httpx.HTTPTransport(retries=2))

collection = MomoApi.collection(credentials, http_client=client)  # static factories
momo = MomoApi.create(MomoApi.ENVIRONMENT_MTN_GHANA, client)        # inherited by its products
airtel = AirtelApi.create("production", client)
```

The client is scoped to what you pass it to; nothing is installed process-wide.
You own its lifetime: close it when you are done.

## Supported environments

| Constant | Value |
|---|---|
| `MomoApi.ENVIRONMENT_MTN_CONGO` | `mtncongo` |
| `MomoApi.ENVIRONMENT_MTN_UGANDA` | `mtnuganda` |
| `MomoApi.ENVIRONMENT_MTN_GHANA` | `mtnghana` |
| `MomoApi.ENVIRONMENT_IVORY_COAST` | `mtnivorycoast` |
| `MomoApi.ENVIRONMENT_ZAMBIA` | `mtnzambia` |
| `MomoApi.ENVIRONMENT_CAMEROON` | `mtncameroon` |
| `MomoApi.ENVIRONMENT_BENIN` | `mtnbenin` |
| `MomoApi.ENVIRONMENT_SWAZILAND` | `mtnswaziland` |
| `MomoApi.ENVIRONMENT_GUINEACONAKRY` | `mtnguineaconakry` |
| `MomoApi.ENVIRONMENT_SOUTHAFRICA` | `mtnsouthafrica` |
| `MomoApi.ENVIRONMENT_LIBERIA` | `mtnliberia` |
| `MomoApi.ENVIRONMENT_SANDBOX` | `sandbox` |

## Retrying without paying twice

Each write returns the id you poll its status with. By default it is a random
UUID, so if the request times out or fails with a 5xx you never learn it: you
cannot ask whether the payment went through, and retrying sends a new id that
MTN or Airtel treats as a new payment.

Pass your own UUID as the last argument instead, and store it before sending.
After an ambiguous failure, query the status with it; retry with the same id
only once the status says the first attempt does not exist.

```python
import uuid

# Derive it from your own key, so the same line always gets the same id
reference_id = str(uuid.uuid5(MY_NAMESPACE_UUID, f"{batch_ref}-{line_no}"))
disbursement.transfer(transfer_request, reference_id)
transfer = disbursement.get_transfer_status(reference_id)

# Airtel takes it as transaction_id, the externalId it returns
airtel_disbursement.transfer("10000", "068511358", "PAY-001", reference_id)
```

The id must be a UUID (any version): anything else raises `ValueError` before a
request is sent. Without it, every method keeps generating a random UUID.

## Handling callbacks

> **Callbacks are not signed.** Neither MTN nor Airtel signs the request sent to
> your callback URL, and that URL is no secret: it travels in the `X-Callback-Url`
> header of every request. Anyone can call it with `"status": "SUCCESSFUL"`.
> Never fulfil an order from the callback body. Treat the callback as a signal
> that something changed, then ask MTN or Airtel for the real status.

### MTN MoMo

MTN sends the callback as a JSON body (`PUT`). Use it only to find the order,
then re-query the payment with the reference id `request_to_pay()` returned,
which you stored with the order:

```python
def handle_momo_callback(body: dict) -> int:
    # Look the order up in your own records; never trust the amount in the callback
    order = orders.find_by_external_id(body.get("externalId", ""))
    if order is None:
        return 404

    # Ask MTN, with the reference id stored when the payment was requested
    transaction = collection.get_payment_status(order.momo_reference_id)

    if (
        transaction.is_successful()
        and transaction.external_id == order.id
        and float(transaction.amount) == float(order.amount)
    ):
        order.mark_paid()  # make this idempotent: MTN may call more than once
    elif transaction.is_failed():
        order.mark_failed(str(transaction.reason))
    return 200
```

### Airtel Money

Airtel's callback carries `transaction.id`, the externalId you passed to
`request_to_pay()`. Re-query it the same way:

```python
def handle_airtel_callback(body: dict) -> int:
    order = orders.find_by_external_id((body.get("transaction") or {}).get("id", ""))
    if order is None:
        return 404

    # Ask Airtel; the callback's status_code is not proof of payment
    transaction = airtel_collection.get_payment_status(order.id)

    if transaction.is_successful():
        order.mark_paid()
    elif transaction.is_failed():
        order.mark_failed(transaction.message or "")
    return 200
```

`Transaction.parse()` turns a dict into a `Transaction`; it does not verify
anything. Use it on data you fetched yourself, not on a callback you intend to act on.

## Error handling

Every API error is raised as a typed exception extending `MomoException`:

```python
from momo_api import (
    BadRequestException,
    InvalidSubscriptionKeyException,
    MomoException,
)

try:
    reference_id = collection.request_to_pay(request)
except InvalidSubscriptionKeyException:
    print("Check your subscription key and API credentials")
except BadRequestException:
    print("Invalid request parameters")
except MomoException as error:
    print(f"MoMo API error ({error.status_code}): {error}")
```

`MomoException` carries the parsed API payload: `str(error)` is the API's own
message, `reason` an `ErrorReason` with the helpers described below, `code` its
machine-readable code (`NOT_ENOUGH_FUNDS`, ...) and `body` the raw response.

| Exception | Status |
|---|---|
| `BadRequestException` | 400 |
| `BadResourceException` | 400, malformed reference id |
| `InvalidSubscriptionKeyException` | 401 |
| `ResourceNotFoundException` | 404 |
| `ConflictException` | 409, duplicated reference id |
| `InternalServerErrorException` | 500 |
| `MomoException` | anything else, including a non-202 answer to a write |

### Why a payment failed

A failed transaction carries an `ErrorReason`:

```python
transaction = collection.get_payment_status(reference_id)

if transaction.is_failed():
    reason = transaction.reason
    # every MTN failure code has a predicate, or use reason.is_code(ErrorReason.X)

    # is_payer_funding_failure() also covers LOW_BALANCE_OR_PAYEE_LIMIT_REACHED_OR_NOT_ALLOWED,
    # which MTN Congo returns instead of NOT_ENOUGH_FUNDS
    if reason and reason.is_payer_funding_failure():
        print("Payer has insufficient funds or reached a limit")
    elif reason and reason.is_expired():
        print("The payment request expired")
    else:
        print(reason)  # "[COULD_NOT_PERFORM_TRANSACTION]"
```

## API reference

### CollectionApi

| Method | Description |
|---|---|
| `request_to_pay(request, reference_id=None)` | Initiate a payment request; returns the reference id |
| `get_payment_status(payment_id)` | Status of a payment |
| `quick_pay(amount, phone, reference, currency="XAF", reference_id=None)` | Shorthand to initiate a payment |
| `get_balance()` | Collection account balance |
| `check_account_holder(phone)` | Whether an MSISDN is an active account holder |
| `get_access_token()` | OAuth access token (cached) |

### DisbursementApi

| Method | Description |
|---|---|
| `deposit(request, reference_id=None)` | Deposit funds to a customer; returns the reference id |
| `get_deposit_status(deposit_id)` | Status of a deposit |
| `transfer(request, reference_id=None)` | Transfer funds; returns the reference id |
| `get_transfer_status(transfer_id)` | Status of a transfer |
| `refund(request, reference_id=None)` | Refund a previous payment; returns the reference id |
| `get_refund_status(refund_id)` | Status of a refund |
| `get_balance()` | Disbursement account balance |
| `check_account_holder(phone)` | Whether an MSISDN is an active account holder |
| `get_access_token()` | OAuth access token (cached) |

### AirtelCollectionApi

| Method | Description |
|---|---|
| `request_to_pay(amount, phone, reference, transaction_id=None)` | Request a payment; returns the external id |
| `get_payment_status(external_id)` | Status of a payment (`AirtelTransaction`) |
| `get_balance()` | Account balance |
| `get_access_token()` | OAuth token (cached) |

### AirtelDisbursementApi

| Method | Description |
|---|---|
| `transfer(amount, phone, reference, transaction_id=None)` | Transfer money (requires `encrypted_pin`); returns the external id |
| `get_transfer_status(external_id)` | Status of a transfer (`AirtelTransaction`) |
| `get_balance()` | Account balance |
| `get_access_token()` | OAuth token (cached) |

### SandboxApi

| Method | Description |
|---|---|
| `create_api_user(api_user, callback_host)` | Provision a sandbox API user |
| `get_api_user(api_user)` | Sandbox API user details |
| `create_api_key(api_user)` | Generate an API key for a sandbox user |

## Ecosystem

The same client is available for multiple languages:

| Language | Package | Install |
|----------|---------|---------|
| **PHP** | [`lepresk/momo-api`](https://github.com/lepresk/momo-api) | `composer require lepresk/momo-api` |
| **Node.js / TypeScript** | [`@lepresk/momo-api`](https://github.com/lepresk/momo-api-node) | `npm install @lepresk/momo-api` |
| **Python** | [`mtn-momo-client`](https://github.com/lepresk/momo-api-python) | `pip install mtn-momo-client` |

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full history of changes.

## License

MIT
