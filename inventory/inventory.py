"""Inventory model: all of a merchant's locations, and stock moves between them."""

from inventory.errors import LocationNotFoundError
from inventory.location import Location
from inventory.product import _validate_sku


class Inventory:
    """All the locations of one merchant, such as a warehouse and a shop.

    Each stock operation names a location and is passed on to that Location.

    Attributes:
        locations: All added locations, keyed by location name.
    """

    def __init__(self) -> None:
        """Create an inventory with no locations."""
        self.locations: dict[str, Location] = {}

    def add_location(self, name: str) -> Location:
        """Add a new, empty location.

        Args:
            name: The location's name, for example "Warehouse".

        Returns:
            The new Location.

        Raises:
            TypeError: If name is not a str.
            ValueError: If name is blank, or a location with this name already exists.
        """
        location = Location(name)
        if name in self.locations:
            raise ValueError(f"location already exists: {name!r}")
        self.locations[name] = location
        return location

    def add_stock(self, location: str, sku: str, amount: int) -> int:
        """Add units of a product at one location.

        Args:
            location: The location's name.
            sku: The product's SKU.
            amount: How many units to add. Must be an int of 1 or more.

        Returns:
            The product's quantity at that location after the add.

        Raises:
            LocationNotFoundError: If the location has not been added.
            TypeError: If sku is not a str, or amount is not an int.
            ValueError: If sku is blank, or amount is less than 1.
        """
        return self._get_location(location).add_stock(sku, amount)

    def remove_stock(self, location: str, sku: str, amount: int) -> int:
        """Remove units of a product at one location.

        The quantity does not change if an error is raised.

        Args:
            location: The location's name.
            sku: The product's SKU.
            amount: How many units to remove. Must be an int of 1 or more.

        Returns:
            The product's quantity at that location after the removal.

        Raises:
            LocationNotFoundError: If the location has not been added.
            TypeError: If sku is not a str, or amount is not an int.
            ValueError: If sku is blank, or amount is less than 1.
            ProductNotFoundError: If the location has never stocked this SKU.
            InsufficientStockError: If amount is more than the units in stock there.
        """
        return self._get_location(location).remove_stock(sku, amount)

    def get_quantity(self, location: str, sku: str) -> int:
        """Return how many units of a product are in stock at one location.

        Args:
            location: The location's name.
            sku: The product's SKU.

        Returns:
            The units in stock there, or 0 if that location has never stocked this SKU.

        Raises:
            LocationNotFoundError: If the location has not been added.
            TypeError: If sku is not a str.
            ValueError: If sku is blank.
        """
        return self._get_location(location).get_quantity(sku)

    def get_total_quantity(self, sku: str) -> int:
        """Return how many units of a product are in stock across all locations.

        Args:
            sku: The product's SKU.

        Returns:
            The sum over all locations, or 0 if no location has this SKU.

        Raises:
            TypeError: If sku is not a str.
            ValueError: If sku is blank.
        """
        # Check here too: with no locations the loop below never checks the SKU.
        _validate_sku(sku)
        return sum(loc.get_quantity(sku) for loc in self.locations.values())

    def transfer_stock(
        self, from_location: str, to_location: str, sku: str, amount: int
    ) -> None:
        """Move units of a product from one location to another.

        This is all or nothing: if an error is raised, neither location changes.

        Args:
            from_location: The name of the location to take stock from.
            to_location: The name of the location to put stock in.
            sku: The product's SKU.
            amount: How many units to move. Must be an int of 1 or more.

        Raises:
            LocationNotFoundError: If either location has not been added.
            ValueError: If both locations are the same, sku is blank,
                or amount is less than 1.
            TypeError: If sku is not a str, or amount is not an int.
            ProductNotFoundError: If the source has never stocked this SKU.
            InsufficientStockError: If amount is more than the units in the source.
        """
        source = self._get_location(from_location)
        destination = self._get_location(to_location)
        if source is destination:
            raise ValueError(f"cannot transfer to the same location: {from_location!r}")
        # remove_stock does every check before it changes anything, so after it
        # succeeds, add_stock with the same sku and amount cannot fail.
        source.remove_stock(sku, amount)
        destination.add_stock(sku, amount)

    def _get_location(self, name: str) -> Location:
        """Return the location with this name.

        Args:
            name: The location's name.

        Returns:
            The matching Location.

        Raises:
            LocationNotFoundError: If no location has this name.
        """
        location = self.locations.get(name)
        if location is None:
            raise LocationNotFoundError(name)
        return location
