"""Location model: one place that holds stock, such as a warehouse or a shop."""

from inventory.errors import InsufficientStockError, ProductNotFoundError
from inventory.product import Product, _validate_sku


class Location:
    """One place where the merchant keeps stock, such as a warehouse or a shop.

    Attributes:
        name: The location's name. Must not be blank.
        products: All products the location has ever stocked, keyed by SKU.
    """

    def __init__(self, name: str) -> None:
        """Create an empty location.

        Args:
            name: The location's name.

        Raises:
            TypeError: If name is not a str.
            ValueError: If name is empty or only whitespace.
        """
        _validate_name(name)
        self.name = name
        self.products: dict[str, Product] = {}

    def add_stock(self, sku: str, amount: int) -> int:
        """Add units of a product. Creates the product if it is new.

        Args:
            sku: The product's SKU.
            amount: How many units to add. Must be an int of 1 or more.

        Returns:
            The product's quantity after the add.

        Raises:
            TypeError: If sku is not a str, or amount is not an int.
            ValueError: If sku is blank, or amount is less than 1.
        """
        _validate_sku(sku)
        _validate_amount(amount)
        product = self.products.setdefault(sku, Product(sku))
        product.quantity += amount
        return product.quantity

    def remove_stock(self, sku: str, amount: int) -> int:
        """Remove units of a product, for example after a sale.

        The quantity does not change if an error is raised.

        Args:
            sku: The product's SKU.
            amount: How many units to remove. Must be an int of 1 or more.

        Returns:
            The product's quantity after the removal.

        Raises:
            TypeError: If sku is not a str, or amount is not an int.
            ValueError: If sku is blank, or amount is less than 1.
            ProductNotFoundError: If the location has never stocked this SKU.
            InsufficientStockError: If amount is more than the units in stock.
        """
        _validate_sku(sku)
        _validate_amount(amount)
        product = self.products.get(sku)
        if product is None:
            raise ProductNotFoundError(sku)
        if amount > product.quantity:
            raise InsufficientStockError(sku, product.quantity, amount)
        product.quantity -= amount
        return product.quantity

    def get_quantity(self, sku: str) -> int:
        """Return how many units of a product are in stock.

        Args:
            sku: The product's SKU.

        Returns:
            The units in stock, or 0 if the location has never stocked this SKU.

        Raises:
            TypeError: If sku is not a str.
            ValueError: If sku is blank.
        """
        _validate_sku(sku)
        product = self.products.get(sku)
        return product.quantity if product is not None else 0


def _validate_name(name: str) -> None:
    """Check that a location name is a non-blank string.

    Args:
        name: The name to check.

    Raises:
        TypeError: If name is not a str.
        ValueError: If name is empty or only whitespace.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, got {type(name).__name__}")
    if not name.strip():
        raise ValueError("name must not be blank")


def _validate_amount(amount: int) -> None:
    """Check that an amount to add or remove is an int of 1 or more.

    Args:
        amount: The amount to check.

    Raises:
        TypeError: If amount is not an int, or is a bool.
        ValueError: If amount is less than 1.
    """
    # bool is a subclass of int, so True would silently count as 1.
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError(f"amount must be an int, got {type(amount).__name__}")
    if amount < 1:
        raise ValueError(f"amount must be 1 or more, got {amount}")
