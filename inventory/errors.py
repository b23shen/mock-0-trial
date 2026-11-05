"""Custom errors raised by the inventory tracker."""


class InventoryError(Exception):
    """Base class for all inventory errors, so callers can catch them all at once."""


class ProductNotFoundError(InventoryError):
    """Raised when an operation needs a product that the location does not have.

    Attributes:
        sku: The SKU that was not found.
    """

    def __init__(self, sku: str) -> None:
        """Create the error for a missing SKU.

        Args:
            sku: The SKU that was not found.
        """
        super().__init__(f"product not found: {sku!r}")
        self.sku = sku


class LocationNotFoundError(InventoryError):
    """Raised when an operation names a location that has not been added.

    Attributes:
        name: The location name that was not found.
    """

    def __init__(self, name: str) -> None:
        """Create the error for a missing location.

        Args:
            name: The location name that was not found.
        """
        super().__init__(f"location not found: {name!r}")
        self.name = name


class InsufficientStockError(InventoryError):
    """Raised when a removal asks for more units than are in stock.

    Attributes:
        sku: The product's SKU.
        available: Units in stock at the time of the request.
        requested: Units the caller tried to remove.
    """

    def __init__(self, sku: str, available: int, requested: int) -> None:
        """Create the error with the numbers that caused it.

        Args:
            sku: The product's SKU.
            available: Units in stock at the time of the request.
            requested: Units the caller tried to remove.
        """
        super().__init__(
            f"not enough stock for {sku!r}: have {available}, tried to remove {requested}"
        )
        self.sku = sku
        self.available = available
        self.requested = requested
