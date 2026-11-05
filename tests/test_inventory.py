"""Tests for the Inventory class."""

import pytest

from inventory.errors import (
    InsufficientStockError,
    InventoryError,
    LocationNotFoundError,
    ProductNotFoundError,
)
from inventory.inventory import Inventory
from inventory.location import Location


@pytest.fixture
def inventory() -> Inventory:
    """An inventory with two empty locations: Warehouse and Downtown."""
    inv = Inventory()
    inv.add_location("Warehouse")
    inv.add_location("Downtown")
    return inv


# --- add_location ---


def test_new_inventory_has_no_locations() -> None:
    assert Inventory().locations == {}


def test_add_location_returns_and_stores_location() -> None:
    inv = Inventory()

    location = inv.add_location("Warehouse")

    assert isinstance(location, Location)
    assert location.name == "Warehouse"
    assert inv.locations == {"Warehouse": location}


def test_add_duplicate_location_raises_and_keeps_old_one(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 5)

    with pytest.raises(ValueError, match="already exists"):
        inventory.add_location("Warehouse")
    # The existing location and its stock must not be replaced.
    assert inventory.get_quantity("Warehouse", "MUG-01") == 5


@pytest.mark.parametrize("name", ["", "  "])
def test_add_blank_location_raises_value_error(name: str) -> None:
    inv = Inventory()

    with pytest.raises(ValueError, match="name"):
        inv.add_location(name)
    assert inv.locations == {}


def test_add_non_string_location_raises_type_error() -> None:
    with pytest.raises(TypeError, match="name"):
        Inventory().add_location(None)  # type: ignore[arg-type]


def test_add_location_names_are_case_sensitive(inventory: Inventory) -> None:
    inventory.add_location("warehouse")

    assert set(inventory.locations) == {"Warehouse", "Downtown", "warehouse"}


def test_returned_location_is_the_one_inventory_uses() -> None:
    inv = Inventory()
    location = inv.add_location("Warehouse")

    inv.add_stock("Warehouse", "MUG-01", 3)

    assert location.get_quantity("MUG-01") == 3


# --- add_stock / remove_stock / get_quantity at one location ---


def test_add_stock_only_changes_that_location(inventory: Inventory) -> None:
    assert inventory.add_stock("Warehouse", "MUG-01", 10) == 10

    assert inventory.get_quantity("Warehouse", "MUG-01") == 10
    assert inventory.get_quantity("Downtown", "MUG-01") == 0


def test_remove_stock_only_changes_that_location(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 10)
    inventory.add_stock("Downtown", "MUG-01", 4)

    assert inventory.remove_stock("Downtown", "MUG-01", 3) == 1

    assert inventory.get_quantity("Downtown", "MUG-01") == 1
    assert inventory.get_quantity("Warehouse", "MUG-01") == 10


def test_remove_more_than_at_location_raises(inventory: Inventory) -> None:
    # Enough in total, but not at Downtown.
    inventory.add_stock("Warehouse", "MUG-01", 10)
    inventory.add_stock("Downtown", "MUG-01", 2)

    with pytest.raises(InsufficientStockError):
        inventory.remove_stock("Downtown", "MUG-01", 3)
    assert inventory.get_quantity("Downtown", "MUG-01") == 2


def test_add_stock_unknown_sku_creates_product(inventory: Inventory) -> None:
    assert "MUG-01" not in inventory.locations["Warehouse"].products

    assert inventory.add_stock("Warehouse", "MUG-01", 2) == 2

    assert inventory.locations["Warehouse"].products["MUG-01"].quantity == 2
    # The new product exists only at the location we added it to.
    assert "MUG-01" not in inventory.locations["Downtown"].products


def test_remove_sku_missing_at_location_raises(inventory: Inventory) -> None:
    # The SKU exists, but only at the other location.
    inventory.add_stock("Warehouse", "MUG-01", 10)

    with pytest.raises(ProductNotFoundError):
        inventory.remove_stock("Downtown", "MUG-01", 1)


def test_remove_sku_unknown_everywhere_raises(inventory: Inventory) -> None:
    with pytest.raises(ProductNotFoundError) as exc_info:
        inventory.remove_stock("Warehouse", "NOPE-99", 1)

    assert exc_info.value.sku == "NOPE-99"


def test_remove_all_then_more_raises_insufficient(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 2)
    inventory.remove_stock("Warehouse", "MUG-01", 2)

    with pytest.raises(InsufficientStockError):
        inventory.remove_stock("Warehouse", "MUG-01", 1)
    assert inventory.get_quantity("Warehouse", "MUG-01") == 0


def test_get_quantity_unknown_sku_returns_zero(inventory: Inventory) -> None:
    assert inventory.get_quantity("Warehouse", "NOPE-99") == 0


def test_get_quantity_sku_only_at_other_location_returns_zero(
    inventory: Inventory,
) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 10)

    assert inventory.get_quantity("Downtown", "MUG-01") == 0


def test_get_quantity_does_not_create_product(inventory: Inventory) -> None:
    inventory.get_quantity("Warehouse", "NOPE-99")

    assert inventory.locations["Warehouse"].products == {}


def test_location_name_is_case_sensitive(inventory: Inventory) -> None:
    with pytest.raises(LocationNotFoundError):
        inventory.get_quantity("warehouse", "MUG-01")


@pytest.mark.parametrize(
    "call",
    [
        lambda inv: inv.add_stock("Uptown", "MUG-01", 1),
        lambda inv: inv.remove_stock("Uptown", "MUG-01", 1),
        lambda inv: inv.get_quantity("Uptown", "MUG-01"),
    ],
    ids=["add_stock", "remove_stock", "get_quantity"],
)
def test_unknown_location_raises_not_found(inventory: Inventory, call) -> None:
    with pytest.raises(LocationNotFoundError) as exc_info:
        call(inventory)

    assert exc_info.value.name == "Uptown"
    # A typo must not create a new location.
    assert "Uptown" not in inventory.locations


def test_unknown_location_is_checked_before_sku(inventory: Inventory) -> None:
    # Both the location and the SKU are unknown; the location error wins.
    with pytest.raises(LocationNotFoundError):
        inventory.remove_stock("Uptown", "NOPE-99", 1)


@pytest.mark.parametrize("amount", [0, -1, -100])
def test_add_stock_non_positive_amount_raises(
    inventory: Inventory, amount: int
) -> None:
    with pytest.raises(ValueError, match="amount"):
        inventory.add_stock("Warehouse", "MUG-01", amount)
    # A failed add must not create the product.
    assert inventory.locations["Warehouse"].products == {}


@pytest.mark.parametrize("amount", [0, -1])
def test_remove_stock_non_positive_amount_raises(
    inventory: Inventory, amount: int
) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 5)

    with pytest.raises(ValueError, match="amount"):
        inventory.remove_stock("Warehouse", "MUG-01", amount)
    assert inventory.get_quantity("Warehouse", "MUG-01") == 5


# --- get_total_quantity ---


def test_total_sums_all_locations(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 10)
    inventory.add_stock("Downtown", "MUG-01", 4)
    inventory.add_stock("Downtown", "CAP-02", 7)

    assert inventory.get_total_quantity("MUG-01") == 14
    assert inventory.get_total_quantity("CAP-02") == 7


def test_total_unknown_sku_returns_zero(inventory: Inventory) -> None:
    assert inventory.get_total_quantity("NOPE-99") == 0


def test_total_after_all_stock_removed_returns_zero(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 3)
    inventory.add_stock("Downtown", "MUG-01", 2)
    inventory.remove_stock("Warehouse", "MUG-01", 3)
    inventory.remove_stock("Downtown", "MUG-01", 2)

    assert inventory.get_total_quantity("MUG-01") == 0


def test_total_with_no_locations_returns_zero() -> None:
    assert Inventory().get_total_quantity("MUG-01") == 0


def test_total_blank_sku_raises_even_with_no_locations() -> None:
    with pytest.raises(ValueError, match="sku"):
        Inventory().get_total_quantity(" ")


def test_total_non_string_sku_raises_type_error(inventory: Inventory) -> None:
    with pytest.raises(TypeError, match="sku"):
        inventory.get_total_quantity(None)  # type: ignore[arg-type]


# --- transfer_stock ---


def test_transfer_moves_stock(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 10)
    inventory.add_stock("Downtown", "MUG-01", 1)

    inventory.transfer_stock("Warehouse", "Downtown", "MUG-01", 4)

    assert inventory.get_quantity("Warehouse", "MUG-01") == 6
    assert inventory.get_quantity("Downtown", "MUG-01") == 5


def test_transfer_keeps_total_the_same(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 10)

    inventory.transfer_stock("Warehouse", "Downtown", "MUG-01", 3)

    assert inventory.get_total_quantity("MUG-01") == 10


def test_transfer_creates_product_at_destination(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 10)

    inventory.transfer_stock("Warehouse", "Downtown", "MUG-01", 10)

    assert inventory.get_quantity("Warehouse", "MUG-01") == 0
    assert inventory.get_quantity("Downtown", "MUG-01") == 10


def test_transfer_back_and_forth_keeps_total(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 10)

    inventory.transfer_stock("Warehouse", "Downtown", "MUG-01", 6)
    inventory.transfer_stock("Downtown", "Warehouse", "MUG-01", 2)

    assert inventory.get_quantity("Warehouse", "MUG-01") == 6
    assert inventory.get_quantity("Downtown", "MUG-01") == 4
    assert inventory.get_total_quantity("MUG-01") == 10


def test_transfer_too_much_raises_and_changes_nothing(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 3)

    # The error comes from the remove_stock sub-action, with its details.
    with pytest.raises(InsufficientStockError) as exc_info:
        inventory.transfer_stock("Warehouse", "Downtown", "MUG-01", 4)

    assert exc_info.value.sku == "MUG-01"
    assert exc_info.value.available == 3
    assert exc_info.value.requested == 4
    assert inventory.get_quantity("Warehouse", "MUG-01") == 3
    assert inventory.get_quantity("Downtown", "MUG-01") == 0
    assert "MUG-01" not in inventory.locations["Downtown"].products


def test_transfer_sku_missing_at_source_raises(inventory: Inventory) -> None:
    inventory.add_stock("Downtown", "MUG-01", 5)

    with pytest.raises(ProductNotFoundError):
        inventory.transfer_stock("Warehouse", "Downtown", "MUG-01", 1)
    assert inventory.get_quantity("Downtown", "MUG-01") == 5


def test_transfer_to_unknown_location_changes_nothing(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 5)

    with pytest.raises(LocationNotFoundError) as exc_info:
        inventory.transfer_stock("Warehouse", "Uptown", "MUG-01", 2)

    assert exc_info.value.name == "Uptown"
    # The source must not lose stock when the destination is wrong.
    assert inventory.get_quantity("Warehouse", "MUG-01") == 5


def test_transfer_from_unknown_location_raises(inventory: Inventory) -> None:
    with pytest.raises(LocationNotFoundError) as exc_info:
        inventory.transfer_stock("Uptown", "Warehouse", "MUG-01", 1)

    assert exc_info.value.name == "Uptown"


def test_transfer_from_zero_stock_raises(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 1)
    inventory.remove_stock("Warehouse", "MUG-01", 1)

    with pytest.raises(InsufficientStockError):
        inventory.transfer_stock("Warehouse", "Downtown", "MUG-01", 1)


def test_transfer_same_unknown_location_raises_not_found(
    inventory: Inventory,
) -> None:
    # The location check runs before the same-location check.
    with pytest.raises(LocationNotFoundError):
        inventory.transfer_stock("Uptown", "Uptown", "MUG-01", 1)


def test_transfer_to_same_location_raises(inventory: Inventory) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 5)

    with pytest.raises(ValueError, match="same location"):
        inventory.transfer_stock("Warehouse", "Warehouse", "MUG-01", 1)
    assert inventory.get_quantity("Warehouse", "MUG-01") == 5


@pytest.mark.parametrize(
    ("amount", "error"),
    [(0, ValueError), (-1, ValueError), (1.5, TypeError), (True, TypeError)],
)
def test_transfer_bad_amount_raises_and_changes_nothing(
    inventory: Inventory, amount: object, error: type[Exception]
) -> None:
    inventory.add_stock("Warehouse", "MUG-01", 5)

    with pytest.raises(error, match="amount"):
        inventory.transfer_stock("Warehouse", "Downtown", "MUG-01", amount)  # type: ignore[arg-type]

    assert inventory.get_quantity("Warehouse", "MUG-01") == 5
    assert inventory.get_quantity("Downtown", "MUG-01") == 0


def test_transfer_blank_sku_raises(inventory: Inventory) -> None:
    with pytest.raises(ValueError, match="sku"):
        inventory.transfer_stock("Warehouse", "Downtown", "", 1)


# --- errors ---


def test_location_not_found_shares_base_class() -> None:
    assert issubclass(LocationNotFoundError, InventoryError)
