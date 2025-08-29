import re
import unicodedata

class ProductNormalizer:
    """
    A class to encapsulate all product normalization logic.

    This class takes raw product data, processes it through a pipeline of cleaning
    and standardization methods, and provides clean, normalized outputs.
    """
    def __init__(self, product_data):
        """
        Initializes the normalizer with raw product data.

        Args:
            product_data (dict): A dictionary containing product info like 'name', 'brand', etc.
        """
        self.name = str(product_data.get('name', ''))
        self.brand = str(product_data.get('brand', ''))
        self.package_size = str(product_data.get('package_size', ''))
        
        # Immediately process the data to populate internal state
        self.raw_sizes = self._extract_all_sizes()
        self.cleaned_brand = self._get_cleaned_brand()
        self.cleaned_name = self._get_cleaned_name()
        self.standardized_sizes = self._get_standardized_sizes()

    def _clean_value(self, value: str) -> str:
        """ Corresponds to clean_value.py logic. """
        if not isinstance(value, str):
            return ""
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
        value = value.lower()
        value = re.sub(r'[^a-z0-9\s]', '', value)
        words = sorted(list(set(value.split())))
        return "".join(words)

    def _extract_sizes_from_string(self, text: str) -> list:
        """ Corresponds to extract_sizes.py logic. """
        if not isinstance(text, str):
            return []
        patterns = [
            r'(\d+\s*x\s*\d+\s*g)',      # 4x100g
            r'(\d+\s*x\s*\d+\s*ml)',     # 4x250ml
            r'(\d+\.?\d*\s*k?g)',       # 1kg, 1.5kg, 500g
            r'(\d+\.?\d*\s*l)',         # 1l, 1.5l
            r'(\d+\s*ml)',              # 750ml
            r'(\d+\s*pack)',            # 6 pack
            r'(\d+\s*pk)',              # 6 pk
            r'(\d+\s*each)',            # 1 each
            r'(\d+\s*ea)',              # 1 ea
        ]
        found_sizes = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                found_sizes.append(str(match))
        return found_sizes

    def _extract_all_sizes(self) -> list:
        """ Corresponds to get_extracted_sizes.py logic. """
        all_sizes = set()
        for text in [self.name, self.brand, self.package_size]:
            sizes = self._extract_sizes_from_string(text)
            for size in sizes:
                all_sizes.add(size.lower())
        return sorted(list(all_sizes))

    def _get_cleaned_brand(self) -> str:
        """ Corresponds to get_cleaned_brand.py logic. """
        if self.brand:
            return self.brand
        known_brands = ["Coles", "Woolworths", "Aldi", "IGA", "Black & Gold"]
        for b in known_brands:
            if b.lower() in self.name.lower():
                return b
        return ""

    def _get_cleaned_name(self) -> str:
        """ Corresponds to get_cleaned_name.py logic. """
        cleaned_name = self.name
        if self.cleaned_brand:
            cleaned_name = cleaned_name.replace(self.cleaned_brand, '')
        for size in self.raw_sizes:
            cleaned_name = cleaned_name.replace(size, '')
        return cleaned_name.strip()

    def _get_standardized_sizes(self) -> list:
        """ Corresponds to standardize_sizes_for_norm_string.py logic. """
        standardized = set()
        for size in self.raw_sizes:
            s = size.lower().replace(" ", "")
            s = s.replace("pack", "pk")
            s = s.replace("each", "ea")
            standardized.add(s)
        return sorted(list(standardized))

    # --- Public API ---

    def get_raw_sizes(self) -> list:
        """ Public method to get the originally extracted, unique size strings. """
        return self.raw_sizes

    def get_normalized_string(self) -> str:
        """ 
        Public method to get the final normalized string for de-duplication.
        This now uses a "bag of words" approach, combining all parts before cleaning.
        """
        # Combine all the cleaned parts into a single string
        combined_string = f"{self.cleaned_name} {self.cleaned_brand} {' '.join(self.standardized_sizes)}"
        
        # Clean the entire combined string at once to alphabetize all words together
        return self._clean_value(combined_string)
