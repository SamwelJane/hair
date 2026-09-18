import secrets
from datetime import UTC, datetime

# No ambiguous characters (0/O, 1/I) - shared by order numbers and tracking
# numbers, matching the old app's src/lib/random.ts alphabet.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def random_suffix(length: int) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def generate_order_number() -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    return f"ORD-{date_part}-{random_suffix(5)}"
