# Default currency used by the ``make()`` factories and ``quick_pay()``.
# Matches the PHP client (``lepresk/momo-api``), whose primary market is XAF.
DEFAULT_CURRENCY = "XAF"

# The only currency the MTN sandbox accepts. Payment requests sent to the
# sandbox carry it whatever currency they were built with.
SANDBOX_CURRENCY = "EUR"
