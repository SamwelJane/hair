from decimal import Decimal

from app.services.packages import compute_volume_cbm, mask_customer_name


def test_mask_customer_name_first_and_last():
    assert mask_customer_name("Jane Doe") == "Jane D."


def test_mask_customer_name_multiple_middle_names_uses_first_and_last():
    assert mask_customer_name("Jane Amanda Doe") == "Jane D."


def test_mask_customer_name_single_word_name_unmasked():
    assert mask_customer_name("Cher") == "Cher"


def test_mask_customer_name_blank_falls_back_to_placeholder():
    assert mask_customer_name("   ") == "Customer"


def test_compute_volume_cbm_converts_cm_cubed_to_cubic_metres():
    result = compute_volume_cbm(Decimal(20), Decimal(15), Decimal(10))
    assert result == Decimal("0.003")


def test_compute_volume_cbm_returns_none_if_any_dimension_missing():
    assert compute_volume_cbm(Decimal(20), Decimal(15), None) is None
    assert compute_volume_cbm(None, None, None) is None
