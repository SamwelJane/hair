from app.core.config import get_settings

settings = get_settings()


def bank_transfer_details() -> dict[str, str]:
    return {
        "bankName": settings.bank_transfer_bank_name or "Set BANK_TRANSFER_BANK_NAME in env",
        "accountName": settings.bank_transfer_account_name or "Hiar Business Ltd",
        "accountNumber": settings.bank_transfer_account_number or "Set BANK_TRANSFER_ACCOUNT_NUMBER in env",
        "swiftCode": settings.bank_transfer_swift_code or "",
    }


def initiate_bank_transfer(order_id: str) -> str:
    """Bank transfer is manual: we just record that the customer intends to
    pay this way and show them account details + a reference. An admin later
    confirms receipt, which is what actually marks the order Paid."""
    return f"BANK-{order_id}"
