"""Product model: one SKU and how many units of it are in stock."""

from dataclasses import dataclass


@dataclass
class Product:
    """A product in the store, identified by its SKU.

    Attributes:
        sku: Unique product ID, for example "TSHIRT-RED-M". Must not be blank.
        quantity: Number of units in stock. Must be an int of 0 or more.

    Raises:
        TypeError: If sku is not a str, or quantity is not an int.
        ValueError: If sku is empty or only whitespace, or quantity is negative.
    """

    sku: str
    quantity: int = 0

    def __post_init__(self) -> None:
        """Check the fields right after the dataclass sets them.

        Raises:
            TypeError: If sku is not a str, or quantity is not an int.
            ValueError: If sku is blank, or quantity is negative.
        """
        _validate_sku(self.sku)
        _validate_quantity(self.quantity)


def _validate_sku(sku: str) -> None:
    """Check that a SKU is a non-blank string.

    Args:
        sku: The SKU to check.

    Raises:
        TypeError: If sku is not a str.
        ValueError: If sku is empty or only whitespace.
    """
    if not isinstance(sku, str):
        raise TypeError(f"sku must be a str, got {type(sku).__name__}")
    if not sku.strip():
        raise ValueError("sku must not be blank")


def _validate_quantity(quantity: int) -> None:
    """Check that a quantity is an int of 0 or more.

    Args:
        quantity: The quantity to check.

    Raises:
        TypeError: If quantity is not an int, or is a bool.
        ValueError: If quantity is negative.
    """
    # bool is a subclass of int, so True would silently count as 1.
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError(f"quantity must be an int, got {type(quantity).__name__}")
    if quantity < 0:
        raise ValueError(f"quantity must be 0 or more, got {quantity}")
