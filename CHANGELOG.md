# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
