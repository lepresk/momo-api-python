# momo-api-python

A Python client for the MTN Mobile Money (MoMo) API, supporting collections, disbursements and remittances. This is a port of the PHP package [lepresk/momo-api](https://github.com/lepresk/momo-api).

More details on [lepresk.com/blog](https://lepresk.com/blog).

## Requirements

- Python 3.8+
- httpx

## Installation

```bash
pip install momo-api
```

For development:

```bash
pip install "momo-api[dev]"
```

## Configuration

Each product (Collection, Disbursement) requires the following credentials from the MTN MoMo Developer portal:

- `subscription_key`: Your product subscription key
- `api_user`: Your API user UUID
- `api_key`: Your API key
- `callback_url`: Your callback URL (optional)

## Usage

### Collection

```python
from momo_api import MomoApi, PaymentRequest

config = {
    "environment": MomoApi.ENVIRONMENT_SANDBOX,
    "subscription_key": "your-subscription-key",
    "api_user": "your-api-user-uuid",
    "api_key": "your-api-key",
    "callback_url": "https://your-callback-url.com/notify",
}

collection = MomoApi.collection(config)

# Request a payment
payment = PaymentRequest.make(
    amount="100",
    payer="46733123450",
    external_id="order-123",
    currency="EUR",
    payer_message="Payment for order 123",
    payee_note="Thank you for your purchase",
)

reference_id = collection.request_to_pay(payment)
print(f"Payment reference: {reference_id}")

# Check payment status
transaction = collection.get_payment_status(reference_id)
if transaction.is_successful():
    print("Payment successful")
elif transaction.is_pending():
    print("Payment pending")
else:
    print(f"Payment failed: {transaction.status}")

# Quick pay shortcut
reference_id = collection.quick_pay(
    amount="500",
    phone="46733123450",
    reference="order-456",
    currency="EUR",
)

# Get account balance
balance = collection.get_balance()
print(f"Balance: {balance.available_balance} {balance.currency}")
```

### Disbursement

```python
from momo_api import MomoApi, PaymentRequest, TransferRequest, RefundRequest

config = {
    "environment": MomoApi.ENVIRONMENT_SANDBOX,
    "subscription_key": "your-subscription-key",
    "api_user": "your-api-user-uuid",
    "api_key": "your-api-key",
    "callback_url": "https://your-callback-url.com/notify",
}

disbursement = MomoApi.disbursement(config)

# Deposit funds
deposit_req = PaymentRequest.make(
    amount="200",
    payer="46733123450",
    external_id="deposit-001",
    currency="EUR",
)

deposit_id = disbursement.deposit(deposit_req)
status = disbursement.get_deposit_status(deposit_id)

# Transfer funds
transfer_req = TransferRequest.make(
    amount="150",
    payee="46733123450",
    external_id="transfer-001",
    currency="EUR",
    payer_message="Monthly salary",
    payee_note="Salary payment",
)

transfer_id = disbursement.transfer(transfer_req)
status = disbursement.get_transfer_status(transfer_id)

# Refund
refund_req = RefundRequest.make(
    amount="50",
    reference_id_to_refund=transfer_id,
    external_id="refund-001",
    currency="EUR",
)

refund_id = disbursement.refund(refund_req)
status = disbursement.get_refund_status(refund_id)

# Get balance
balance = disbursement.get_balance()
print(f"Balance: {balance.available_balance} {balance.currency}")
```

### Sandbox setup

Use the Sandbox API to provision API users and keys for testing:

```python
from momo_api import MomoApi

momo = MomoApi.create(MomoApi.ENVIRONMENT_SANDBOX)
sandbox = momo.sandbox(subscription_key="your-collection-subscription-key")

api_user = "a-uuid-you-generate"
sandbox.create_api_user(api_user, callback_host="https://your-host.com")
api_key = sandbox.create_api_key(api_user)

print(f"API User: {api_user}")
print(f"API Key: {api_key}")
```

## Environments

| Constant | Value |
|---|---|
| `MomoApi.ENVIRONMENT_SANDBOX` | `sandbox` |
| `MomoApi.ENVIRONMENT_MTN_GHANA` | `mtnghana` |
| `MomoApi.ENVIRONMENT_MTN_UGANDA` | `mtnuganda` |
| `MomoApi.ENVIRONMENT_MTN_CONGO` | `mtncongo` |
| `MomoApi.ENVIRONMENT_IVORY_COAST` | `mtnivorycoast` |
| `MomoApi.ENVIRONMENT_CAMEROON` | `mtncameroon` |
| `MomoApi.ENVIRONMENT_ZAMBIA` | `mtnzambia` |
| `MomoApi.ENVIRONMENT_BENIN` | `mtnbenin` |
| `MomoApi.ENVIRONMENT_SWAZILAND` | `mtnswaziland` |
| `MomoApi.ENVIRONMENT_GUINEACONAKRY` | `mtnguineaconakry` |
| `MomoApi.ENVIRONMENT_SOUTHAFRICA` | `mtnsouthafrica` |
| `MomoApi.ENVIRONMENT_LIBERIA` | `mtnliberia` |

## Error handling

```python
from momo_api import MomoApi, PaymentRequest
from momo_api.exceptions import (
    BadRequestException,
    ResourceNotFoundException,
    ConflictException,
    InternalServerErrorException,
    InvalidSubscriptionKeyException,
)

collection = MomoApi.collection(config)

try:
    transaction = collection.get_payment_status("non-existent-id")
except ResourceNotFoundException:
    print("Payment not found")
except BadRequestException as e:
    print(f"Bad request: {e}")
except InternalServerErrorException:
    print("MTN server error, try again later")
```

## License

MIT
