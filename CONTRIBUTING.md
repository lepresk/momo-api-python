# Contributing

Contributions are welcome. This document covers the basics to get started.

## Prerequisites

- Python 3.8 or later
- pip

## Setup

```bash
git clone https://github.com/lepresk/momo-api-python.git
cd momo-api-python
pip install ".[dev]"
```

## Running tests

```bash
pytest
```

Tests use [pytest-httpx](https://github.com/Colin-b/pytest_httpx) to mock HTTP calls. No real API calls are made. If you add a new method, add a corresponding test in `tests/`.

## Submitting changes

1. Fork the repository
2. Create a branch from `main`: `git checkout -b feat/your-feature`
3. Make your changes and add tests
4. Ensure all tests pass with `pytest`
5. Open a pull request with a clear description of what you changed and why

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org):

```
feat: add remittance support
fix: handle 409 conflict on duplicate reference ID
docs: update collection usage example
test: add disbursement refund status test
```

## Reporting issues

Open an issue on [GitHub](https://github.com/lepresk/momo-api-python/issues) with:
- the version you are using
- a minimal reproduction
- the expected vs actual behavior
