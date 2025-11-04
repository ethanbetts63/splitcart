import re

class PriceNormalizer:
    """
    A utility class to handle all price-related normalization, including generating
    normalized keys for price records and standardizing per-unit pricing information.
    """
    def __init__(self, price_data: dict, company: str):
        """
        Initializes the normalizer with raw price data.

        Args:
            price_data (dict): A dictionary containing all price-related fields from a
                               cleaned product record.
            company (str): The name of the company (e.g., 'Coles', 'Aldi') to handle
                           company-specific logic like Aldi's prices being in cents.
        """
        self.company = company

        # Data for the normalized key
        self.product_id = price_data.get('product_id')
        self.store_id = price_data.get('store_id')
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
        if not all([self.product_id, self.store_id]):
            return None
        return f"{self.product_id}-{self.store_id}"

    def get_normalized_unit_price(self) -> float | None:
        """
        Returns the standardized per-unit price as a float.
        Handles company-specific transformations (e.g., Aldi prices in cents).
        """
        value_to_process = self.unit_value_raw
        source_is_raw_value = True

        if value_to_process is None:
            source_is_raw_value = False
            if not self.unit_string_raw:
                return None
            # Try to parse the value from the raw string, e.g., "$1.68 per 100 g"
            match = re.search(r'\$?(\d+\.?\d*)', self.unit_string_raw)
            if match:
                try:
                    value_to_process = float(match.group(1))
                except (ValueError, TypeError):
                    return None
            else:
                return None
        
        if value_to_process is None:
            return None

        # Handle company-specific value transformations
        if self.company.lower() == 'aldi' and source_is_raw_value:
            # Only divide if the value came from the raw field, which is in cents.
            # If parsed from string, it's already in dollars.
            value_to_process /= 100.0
        
        return float(value_to_process)

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
        # Looks for a number (optional) followed by a unit.
        # e.g., "100 g", "kg", "1EA"
        pattern = r'(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')'

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
