import re

class PriceNormalizer:
    """
    A utility class to handle all price-related normalization, including generating
    normalized keys for price records and standardizing per-unit pricing information.
    """
    def __init__(self, price_data: dict):
        """
        Initializes the normalizer with raw price data.

        Args:
            price_data (dict): A dictionary containing all price-related fields from a
                               cleaned product record.
        """
        # Data for the normalized key
        self.product_id = price_data.get('product_id')
        self.group_id = price_data.get('group_id')
        self.price = price_data.get('price')
        self.date = price_data.get('date')

        # Data for the per-unit normalization
        self.unit_value_raw = price_data.get('per_unit_price_value')
        self.unit_measure_raw = str(price_data.get('per_unit_price_measure', ''))
        self.unit_string_raw = str(price_data.get('per_unit_price_string', ''))
        
        # Unit definitions borrowed from ProductNormalizer
        self.UNITS = {
            'g': ['g', 'gram', 'grams'],
            'kg': ['kg', 'kilogram', 'kilograms'],
            'ml': ['ml', 'millilitre', 'millilitres'],
            'l': ['l', 'litre', 'litres'],
            'each': ['ea', 'each'],
        }

    def get_normalized_key(self) -> str | None:
        """
        Generates a normalized key for a price record.
        """
        if not all([self.product_id, self.group_id]):
            return None
        return f"{self.product_id}-{self.group_id}"

    def get_normalized_unit_price(self) -> float | None:
        """
        Returns the standardized per-unit price as a float.
        """
        if self.unit_value_raw is not None:
            return float(self.unit_value_raw)

        if not self.unit_string_raw:
            return None
        # Try to parse the value from the raw string, e.g., "$1.68 per 100 g"
        match = re.search(r'\$?(\d+\.?\d*)', self.unit_string_raw)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                return None
        return None

    def get_normalized_unit_measure(self) -> tuple[str, float] | None:
        """
        Returns a tuple of the standardized unit and quantity, 
        e.g., ("g", 100) or ("kg", 1).
        It parses the raw measure and string fields to find the first valid unit.
        """
        # 1. Create a reverse map for easy lookup of standard units
        unit_map = {variation: standard for standard, variations in self.UNITS.items() for variation in variations}
        all_unit_variations = list(unit_map.keys())

        # 2. Create a comprehensive regex pattern
        # Looks for a number (optional) followed by a separator (whitespace or /) and a unit.
        # e.g., "100 g", "kg", "1EA", "1.75/l"
        pattern = r'(\d+\.?\d*)\s*[/]?\s*(' + '|'.join(all_unit_variations) + r')'

        # 3. Prioritize sources: raw measure field first, then the full string
        for text_to_search in [self.unit_measure_raw, self.unit_string_raw]:
            if not text_to_search:
                continue

            match = re.search(pattern, text_to_search, re.IGNORECASE)
            
            if match:
                quantity_str = match.group(1)
                unit_str = match.group(2).lower()

                # Determine quantity
                try:
                    quantity = float(quantity_str) if quantity_str else 1.0
                except (ValueError, TypeError):
                    quantity = 1.0 # Default to 1 if quantity is not a valid number

                # Get standard unit
                standard_unit = unit_map.get(unit_str)

                if standard_unit:
                    return (standard_unit, quantity)
        
        return None
