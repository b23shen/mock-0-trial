"""Tests for the Store class."""

import pytest

from inventory.errors import (
    InsufficientStockError,
    InventoryError,
    ProductNotFoundError,
)
from inventory.store import Store


@pytest.fixture
def store() -> Store:
    return Store("Corner Shop")


# --- creating a store ---


def test_new_store_has_name_and_no_products(store: Store) -> None:
    assert store.name == "Corner Shop"
    assert store.products == {}


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_store_name_raises_value_error(name: str) -> None:
    with pytest.raises(ValueError, match="name"):
        Store(name)


def test_non_string_store_name_raises_type_error() -> None:
    with pytest.raises(TypeError, match="name"):
        Store(None)  # type: ignore[arg-type]


# --- add_stock ---


def test_add_stock_creates_new_product(store: Store) -> None:
    assert store.add_stock("MUG-01", 5) == 5
    assert store.get_quantity("MUG-01") == 5
    assert "MUG-01" in store.products


def test_add_stock_increases_existing_product(store: Store) -> None:
    store.add_stock("MUG-01", 5)

    assert store.add_stock("MUG-01", 3) == 8
    assert store.get_quantity("MUG-01") == 8


def test_add_stock_keeps_products_separate(store: Store) -> None:
    store.add_stock("MUG-01", 5)
    store.add_stock("CAP-02", 2)

    assert store.get_quantity("MUG-01") == 5
    assert store.get_quantity("CAP-02") == 2


def test_sku_is_case_sensitive(store: Store) -> None:
    store.add_stock("MUG-01", 5)

    assert store.get_quantity("mug-01") == 0


@pytest.mark.parametrize("amount", [0, -1])
def test_add_stock_non_positive_amount_raises_value_error(
    store: Store, amount: int
) -> None:
    with pytest.raises(ValueError, match="amount"):
        store.add_stock("MUG-01", amount)
    # A failed add must not create the product.
    assert store.products == {}


@pytest.mark.parametrize("amount", [1.5, "3", None, True])
def test_add_stock_non_int_amount_raises_type_error(
    store: Store, amount: object
) -> None:
    with pytest.raises(TypeError, match="amount"):
        store.add_stock("MUG-01", amount)  # type: ignore[arg-type]
    assert store.products == {}


@pytest.mark.parametrize("sku", ["", "  "])
def test_add_stock_blank_sku_raises_value_error(store: Store, sku: str) -> None:
    with pytest.raises(ValueError, match="sku"):
        store.add_stock(sku, 1)


def test_add_stock_non_string_sku_raises_type_error(store: Store) -> None:
    with pytest.raises(TypeError, match="sku"):
        store.add_stock(123, 1)  # type: ignore[arg-type]


# --- remove_stock ---


def test_remove_stock_decreases_quantity(store: Store) -> None:
    store.add_stock("MUG-01", 5)

    assert store.remove_stock("MUG-01", 2) == 3
    assert store.get_quantity("MUG-01") == 3


def test_remove_all_stock_leaves_zero(store: Store) -> None:
    store.add_stock("MUG-01", 5)

    assert store.remove_stock("MUG-01", 5) == 0
    assert store.get_quantity("MUG-01") == 0


def test_remove_more_than_in_stock_raises_and_keeps_quantity(store: Store) -> None:
    store.add_stock("MUG-01", 5)

    with pytest.raises(InsufficientStockError) as exc_info:
        store.remove_stock("MUG-01", 6)

    assert exc_info.value.sku == "MUG-01"
    assert exc_info.value.available == 5
    assert exc_info.value.requested == 6
    assert store.get_quantity("MUG-01") == 5


def test_remove_from_zero_stock_raises_insufficient(store: Store) -> None:
    store.add_stock("MUG-01", 1)
    store.remove_stock("MUG-01", 1)

    with pytest.raises(InsufficientStockError):
        store.remove_stock("MUG-01", 1)


def test_remove_unknown_sku_raises_not_found(store: Store) -> None:
    with pytest.raises(ProductNotFoundError) as exc_info:
        store.remove_stock("NOPE-99", 1)

    assert exc_info.value.sku == "NOPE-99"


@pytest.mark.parametrize("amount", [0, -1])
def test_remove_stock_non_positive_amount_raises_value_error(
    store: Store, amount: int
) -> None:
    store.add_stock("MUG-01", 5)

    with pytest.raises(ValueError, match="amount"):
        store.remove_stock("MUG-01", amount)
    assert store.get_quantity("MUG-01") == 5


@pytest.mark.parametrize("amount", [1.5, "1", None, True])
def test_remove_stock_non_int_amount_raises_type_error(
    store: Store, amount: object
) -> None:
    store.add_stock("MUG-01", 5)

    with pytest.raises(TypeError, match="amount"):
        store.remove_stock("MUG-01", amount)  # type: ignore[arg-type]
    assert store.get_quantity("MUG-01") == 5


def test_remove_stock_blank_sku_raises_value_error(store: Store) -> None:
    with pytest.raises(ValueError, match="sku"):
        store.remove_stock("", 1)


# --- get_quantity ---


def test_get_quantity_unknown_sku_returns_zero(store: Store) -> None:
    assert store.get_quantity("NOPE-99") == 0


def test_get_quantity_does_not_create_product(store: Store) -> None:
    store.get_quantity("NOPE-99")

    assert store.products == {}


def test_get_quantity_blank_sku_raises_value_error(store: Store) -> None:
    with pytest.raises(ValueError, match="sku"):
        store.get_quantity(" ")


def test_get_quantity_non_string_sku_raises_type_error(store: Store) -> None:
    with pytest.raises(TypeError, match="sku"):
        store.get_quantity(None)  # type: ignore[arg-type]


# --- errors ---


def test_custom_errors_share_a_base_class() -> None:
    assert issubclass(ProductNotFoundError, InventoryError)
    assert issubclass(InsufficientStockError, InventoryError)
