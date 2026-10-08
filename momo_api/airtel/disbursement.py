from typing import Optional

from ..support.uuid import assert_uuid, generate_uuid
from .base import AbstractAirtelApi
from .transaction import AirtelTransaction


class AirtelDisbursementApi(AbstractAirtelApi):
    """Airtel Money Disbursement API: send money."""

    def transfer(
        self,
        amount: str,
        phone: str,
        reference: str,
        transaction_id: Optional[str] = None,
    ) -> str:
        """Send money to a payee. Returns the externalId to poll with
        ``get_transfer_status()``.

        :param transaction_id: UUID to use as the externalId instead of a random
            one, so the transfer can be queried, and not resent, even if the
            response never arrives
        :raises ValueError: when ``encrypted_pin`` is not configured, or
            ``transaction_id`` is not a UUID
        :raises MomoException: when Airtel refuses the transfer, even with HTTP 200
        """
        if not self._config.encrypted_pin:
            raise ValueError("encrypted_pin is required for disbursement transfers")

        external_id = generate_uuid() if transaction_id is None else transaction_id
        assert_uuid(external_id, "transaction_id")
        token = self.get_access_token()

        response = self._send(
            "POST",
            f"{self._base_url}/standard/v1/disbursements/",
            json={
                "payee": {"msisdn": self._msisdn(phone)},
                "reference": reference,
                "pin": self._config.encrypted_pin,
                "transaction": {
                    "amount": str(int(float(amount))),
                    "id": external_id,
                },
            },
            headers={**self._airtel_headers(token), "Content-Type": "application/json"},
        )
        self._read_airtel(response)
        return external_id

    def get_transfer_status(self, external_id: str) -> AirtelTransaction:
        """Pass the externalId returned by ``transfer()``."""
        return self._get_transaction(f"/standard/v1/disbursements/{self._path_id(external_id)}", external_id)
