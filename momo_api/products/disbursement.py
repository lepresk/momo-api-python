from typing import Optional

from ..models.payment_request import PaymentRequest
from ..models.refund_request import RefundRequest
from ..models.transaction import Transaction
from ..models.transfer_request import TransferRequest
from .base import AbstractApiProduct


class DisbursementApi(AbstractApiProduct):
    """MTN MoMo Disbursement API: send money.

    Every write method takes an optional ``reference_id``: a UUID to use as the
    reference id instead of a random one, so the operation can be queried, and
    not resent, even if the response never arrives.
    """

    PRODUCT_PATH = "disbursement"

    def deposit(self, request: PaymentRequest, reference_id: Optional[str] = None) -> str:
        """Deposit funds into a customer account."""
        return self._submit("v1_0/deposit", request.to_dict(), reference_id)

    def get_deposit_status(self, deposit_id: str) -> Transaction:
        return self._get_transaction(f"v1_0/deposit/{deposit_id}")

    def transfer(self, request: TransferRequest, reference_id: Optional[str] = None) -> str:
        """Transfer funds to a payee."""
        return self._submit("v1_0/transfer", request.to_dict(), reference_id)

    def get_transfer_status(self, transfer_id: str) -> Transaction:
        return self._get_transaction(f"v1_0/transfer/{transfer_id}")

    def refund(self, request: RefundRequest, reference_id: Optional[str] = None) -> str:
        """Refund a previously collected payment."""
        return self._submit("v1_0/refund", request.to_dict(), reference_id)

    def get_refund_status(self, refund_id: str) -> Transaction:
        return self._get_transaction(f"v1_0/refund/{refund_id}")
