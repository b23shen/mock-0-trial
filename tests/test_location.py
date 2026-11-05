"""Tests for the Location class."""

import pytest

from inventory.errors import (
    InsufficientStockError,
    InventoryError,
    ProductNotFoundError,
)
from inventory.location import Location


@pytest.fixture
def location() -> Location:
    return Location("Warehouse")


# --- creating a location ---


def test_new_location_has_name_and_no_products(location: Location) -> None:
    assert location.name == "Warehouse"
    assert location.products == {}


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_location_name_raises_value_error(name: str) -> None:
    with pytest.raises(ValueError, match="name"):
        Location(name)


def test_non_string_location_name_raises_type_error() -> None:
    with pytest.raises(TypeError, match="name"):
        Location(None)  # type: ignore[arg-type]


# --- add_stock ---


def test_add_stock_creates_new_product(location: Location) -> None:
    assert location.add_stock("MUG-01", 5) == 5
    assert location.get_quantity("MUG-01") == 5
    assert "MUG-01" in location.products


def test_add_stock_increases_existing_product(location: Location) -> None:
    location.add_stock("MUG-01", 5)

    assert location.add_stock("MUG-01", 3) == 8
    assert location.get_quantity("MUG-01") == 8


def test_add_stock_keeps_products_separate(location: Location) -> None:
    location.add_stock("MUG-01", 5)
    location.add_stock("CAP-02", 2)

    assert location.get_quantity("MUG-01") == 5
    assert location.get_quantity("CAP-02") == 2


def test_sku_is_case_sensitive(location: Location) -> None:
    location.add_stock("MUG-01", 5)

    assert location.get_quantity("mug-01") == 0


@pytest.mark.parametrize("amount", [0, -1])
def test_add_stock_non_positive_amount_raises_value_error(
    location: Location, amount: int
) -> None:
    with pytest.raises(ValueError, match="amount"):
        location.add_stock("MUG-01", amount)
    # A failed add must not create the product.
    assert location.products == {}


@pytest.mark.parametrize("amount", [1.5, "3", None, True])
def test_add_stock_non_int_amount_raises_type_error(
    location: Location, amount: object
) -> None:
    with pytest.raises(TypeError, match="amount"):
        location.add_stock("MUG-01", amount)  # type: ignore[arg-type]
    assert location.products == {}


@pytest.mark.parametrize("sku", ["", "  "])
def test_add_stock_blank_sku_raises_value_error(location: Location, sku: str) -> None:
    with pytest.raises(ValueError, match="sku"):
        location.add_stock(sku, 1)


def test_add_stock_non_string_sku_raises_type_error(location: Location) -> None:
    with pytest.raises(TypeError, match="sku"):
        location.add_stock(123, 1)  # type: ignore[arg-type]


# --- remove_stock ---


def test_remove_stock_decreases_quantity(location: Location) -> None:
    location.add_stock("MUG-01", 5)

    assert location.remove_stock("MUG-01", 2) == 3
    assert location.get_quantity("MUG-01") == 3


def test_remove_all_stock_leaves_zero(location: Location) -> None:
    location.add_stock("MUG-01", 5)

    assert location.remove_stock("MUG-01", 5) == 0
    assert location.get_quantity("MUG-01") == 0


def test_remove_more_than_in_stock_raises_and_keeps_quantity(location: Location) -> None:
    location.add_stock("MUG-01", 5)

    with pytest.raises(InsufficientStockError) as exc_info:
        location.remove_stock("MUG-01", 6)

    assert exc_info.value.sku == "MUG-01"
    assert exc_info.value.available == 5
    assert exc_info.value.requested == 6
    assert location.get_quantity("MUG-01") == 5


def test_remove_from_zero_stock_raises_insufficient(location: Location) -> None:
    location.add_stock("MUG-01", 1)
    location.remove_stock("MUG-01", 1)

    with pytest.raises(InsufficientStockError):
        location.remove_stock("MUG-01", 1)


def test_remove_unknown_sku_raises_not_found(location: Location) -> None:
    with pytest.raises(ProductNotFoundError) as exc_info:
        location.remove_stock("NOPE-99", 1)

    assert exc_info.value.sku == "NOPE-99"


@pytest.mark.parametrize("amount", [0, -1])
def test_remove_stock_non_positive_amount_raises_value_error(
    location: Location, amount: int
) -> None:
    location.add_stock("MUG-01", 5)

    with pytest.raises(ValueError, match="amount"):
        location.remove_stock("MUG-01", amount)
    assert location.get_quantity("MUG-01") == 5


@pytest.mark.parametrize("amount", [1.5, "1", None, True])
def test_remove_stock_non_int_amount_raises_type_error(
    location: Location, amount: object
) -> None:
    location.add_stock("MUG-01", 5)

    with pytest.raises(TypeError, match="amount"):
        location.remove_stock("MUG-01", amount)  # type: ignore[arg-type]
    assert location.get_quantity("MUG-01") == 5


def test_remove_stock_blank_sku_raises_value_error(location: Location) -> None:
    with pytest.raises(ValueError, match="sku"):
        location.remove_stock("", 1)


# --- get_quantity ---


def test_get_quantity_unknown_sku_returns_zero(location: Location) -> None:
    assert location.get_quantity("NOPE-99") == 0


def test_get_quantity_does_not_create_product(location: Location) -> None:
    location.get_quantity("NOPE-99")

    assert location.products == {}


def test_get_quantity_blank_sku_raises_value_error(location: Location) -> None:
    with pytest.raises(ValueError, match="sku"):
        location.get_quantity(" ")


def test_get_quantity_non_string_sku_raises_type_error(location: Location) -> None:
    with pytest.raises(TypeError, match="sku"):
        location.get_quantity(None)  # type: ignore[arg-type]


# --- errors ---


def test_custom_errors_share_a_base_class() -> None:
    assert issubclass(ProductNotFoundError, InventoryError)
    assert issubclass(InsufficientStockError, InventoryError)
