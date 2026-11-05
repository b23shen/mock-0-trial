"""Tests for the Product class."""

import pytest

from inventory.product import Product


def test_create_with_sku_and_quantity() -> None:
    product = Product("TSHIRT-RED-M", 5)

    assert product.sku == "TSHIRT-RED-M"
    assert product.quantity == 5


def test_quantity_defaults_to_zero() -> None:
    assert Product("MUG-01").quantity == 0


def test_zero_quantity_is_allowed() -> None:
    assert Product("MUG-01", 0).quantity == 0


def test_equal_when_fields_match() -> None:
    assert Product("MUG-01", 3) == Product("MUG-01", 3)


@pytest.mark.parametrize("sku", ["", " ", "\t\n"])
def test_blank_sku_raises_value_error(sku: str) -> None:
    with pytest.raises(ValueError, match="sku"):
        Product(sku, 1)


@pytest.mark.parametrize("sku", [None, 123, ["MUG-01"]])
def test_non_string_sku_raises_type_error(sku: object) -> None:
    with pytest.raises(TypeError, match="sku"):
        Product(sku, 1)  # type: ignore[arg-type]


def test_negative_quantity_raises_value_error() -> None:
    with pytest.raises(ValueError, match="quantity"):
        Product("MUG-01", -1)


@pytest.mark.parametrize("quantity", [1.5, "3", None, True, False])
def test_non_int_quantity_raises_type_error(quantity: object) -> None:
    with pytest.raises(TypeError, match="quantity"):
        Product("MUG-01", quantity)  # type: ignore[arg-type]
