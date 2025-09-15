import re
from decimal import Decimal, InvalidOperation

class UnitPriceSorter:
    """
    A utility to sort product-price pairs by a normalized unit price
    derived from the Price model's `unit_price` and `unit_of_measure` fields.
    """

    def __init__(self):
        # Regex to extract value and unit from strings like '100g', '1kg', 'ea', etc.
        self.uom_pattern = re.compile(r'(\d*\.?\d+)?\s*([a-zA-Z]+)')
        self.conversion_map = {
            'g':    {'base': 'g', 'multiplier': 1},
            'kg':   {'base': 'g', 'multiplier': 1000},
            'ml':   {'base': 'ml', 'multiplier': 1},
            'l':    {'base': 'ml', 'multiplier': 1000},
            # 'each' or 'pack' items are treated as their own base
            'ea':   {'base': 'ea', 'multiplier': 1},
            'pk':   {'base': 'pk', 'multiplier': 1},
        }

    def _get_normalized_unit_price(self, price_obj):
        """
        Calculates a normalized unit price (per kg, per L, or per each) for a given Price object.
        Returns a tuple of (Decimal(normalized_price), str(base_unit)) or (None, None).
        """
        if price_obj.unit_price is None or not price_obj.unit_of_measure:
            return None, None

        match = self.uom_pattern.match(price_obj.unit_of_measure.lower())
        if not match:
            return None, None

        value_str, unit_str = match.groups()
        value = Decimal(value_str) if value_str else Decimal('1')
        
        unit_info = self.conversion_map.get(unit_str)
        if not unit_info:
            return None, None # Unknown unit

        try:
            # How many of the scraped units (e.g., 100g) fit into the base unit (e.g., 1000g)?
            # Example: unit_price is per 100g. Base is 1000g. factor = 1000 / 100 = 10.
            # Normalized price = price_obj.unit_price * 10.
            factor = Decimal(unit_info['multiplier']) / value
            normalized_price = price_obj.unit_price * factor
            base_unit = unit_info['base']
            
            # Standardize the reporting base unit string
            if base_unit == 'g': base_unit = 'kg'
            if base_unit == 'ml': base_unit = 'L'

            return normalized_price, base_unit

        except (InvalidOperation, ZeroDivisionError):
            return None, None

    def sort_by_unit_price(self, product_price_pairs: list) -> list:
        """
        Sorts a list of (Product, Price) tuples by their normalized unit price.
        """
        sortable_products = []
        for product, price in product_price_pairs:
            normalized_price, base_unit = self._get_normalized_unit_price(price)
            
            if normalized_price is not None:
                sortable_products.append({
                    'product': product,
                    'price': price,
                    'normalized_unit_price': normalized_price,
                    'base_unit': base_unit
                })

        # Sort by normalized price, but also group by the base unit.
        # This prevents comparing price per 'kg' with price per 'each'.
        return sorted(sortable_products, key=lambda x: (x['base_unit'], x['normalized_unit_price']))