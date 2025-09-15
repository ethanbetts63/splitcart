import re
import unicodedata
import json
import os
from api.utils.substitution_utils.size_comparer import SizeComparer
from api.data.analysis.brand_synonyms import BRAND_SYNONYMS
try:
    from api.data.product_name_translation_table import PRODUCT_NAME_TRANSLATIONS
except (ImportError, SyntaxError):
    PRODUCT_NAME_TRANSLATIONS = {}

# Load brand rules once when the module is loaded
BRAND_RULES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'brand_rules.json')
BRAND_RULES = []
if os.path.exists(BRAND_RULES_PATH):
    try:
        with open(BRAND_RULES_PATH, 'r') as f:
            BRAND_RULES = json.load(f)
    except (IOError, json.JSONDecodeError):
        BRAND_RULES = [] # Ensure it's an empty list on error

class ProductNormalizer:
    """
    A class to encapsulate all product normalization logic.

    This class takes raw product data, processes it through a pipeline of cleaning
    and standardization methods, and provides clean, normalized outputs.
    """
    def __init__(self, product_data, brand_cache=None):
        """
        Initializes the normalizer with raw product data.

        Args:
            product_data (dict): A dictionary containing product info like 'name', 'brand', etc.
            brand_cache (dict): A cache of brand information, including name variations.
        """
        self.name = str(product_data.get('name', ''))
        raw_brand = product_data.get('brand')
        self.brand = str(raw_brand) if raw_brand else ''
        self.size = str(product_data.get('size', ''))
        self.barcode = product_data.get('barcode')
        self.sku = product_data.get('sku')
        self.brand_cache = brand_cache if brand_cache is not None else {}
        
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
        """ Corresponds to the original, more precise extract_sizes.py logic. """
        if not text:
            return []

        sizes = set()
        processed_text = text.lower().replace(',', '')

        prefixes_to_remove = ['approx. ', 'approx ', 'around ', 'about ']
        for prefix in prefixes_to_remove:
            if processed_text.startswith(prefix):
                processed_text = processed_text[len(prefix):]

        units = {
            'g': ['g', 'gram', 'grams'],
            'kg': ['kg', 'kilogram', 'kilograms'],
            'ml': ['ml', 'millilitre', 'millilitres'],
            'l': ['l', 'litre', 'litres'],
            'pk': ['pk', 'pack', 'packs'],
            'ea': ['each', 'ea'],
        }
        
        unit_map = {variation: standard for standard, variations in units.items() for variation in variations}
        all_unit_variations = list(unit_map.keys())

        range_pattern = r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
        for match in re.finditer(range_pattern, processed_text):
            unit = unit_map[match.group(3)]
            sizes.add(f"{match.group(1)}{unit}")
            sizes.add(f"{match.group(2)}{unit}")
        processed_text = re.sub(range_pattern, '', processed_text)

        multipack_pattern_1 = r'(\d+)\s*[xX]\s*(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
        for match in re.finditer(multipack_pattern_1, processed_text):
            unit = unit_map[match.group(3)]
            sizes.add(f"{match.group(1)}pk")
            sizes.add(f"{match.group(2)}{unit}")
        processed_text = re.sub(multipack_pattern_1, '', processed_text)

        multipack_pattern_2 = r'(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\s*[xX]\s*(\d+)'
        for match in re.finditer(multipack_pattern_2, processed_text):
            unit = unit_map[match.group(2)]
            sizes.add(f"{match.group(1)}{unit}")
            sizes.add(f"{match.group(3)}pk")
        processed_text = re.sub(multipack_pattern_2, '', processed_text)

        number_unit_pattern = r'(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
        for match in re.finditer(number_unit_pattern, processed_text):
            unit = unit_map[match.group(2)]
            sizes.add(f"{match.group(1)}{unit}")
        processed_text = re.sub(number_unit_pattern, '', processed_text)
        
        standalone_units = [u for u in all_unit_variations if len(u) > 1] + ['ea']
        standalone_unit_pattern = r'\b(' + '|'.join(standalone_units) + r')\b'
        for match in re.finditer(standalone_unit_pattern, processed_text):
            unit = unit_map[match.group(1)]
            sizes.add(unit)

        return list(sizes)

    def _extract_all_sizes(self) -> list:
        """ Corresponds to get_extracted_sizes.py logic. """
        all_sizes = set()
        for text in [self.name, self.brand, self.size]:
            sizes = self._extract_sizes_from_string(text)
            for size in sizes:
                all_sizes.add(size.lower())
        return sorted(list(all_sizes))

    def _get_cleaned_brand(self) -> str:
        """ Corresponds to the original, more precise get_cleaned_brand.py logic. """
        if not self.brand:
            return ''

        brand_str = str(self.brand)
        name_str = str(self.name).lower()

        cleaned_brand_for_lookup = self._clean_value(brand_str)
        cleaned_brand = BRAND_SYNONYMS.get(cleaned_brand_for_lookup, brand_str)

        for rule in BRAND_RULES:
            rule_brands = [b.lower() for b in rule.get('brands', [])]
            condition_values = [v.lower() for v in rule.get('condition_values', [])]

            if cleaned_brand.lower() in rule_brands:
                if any(keyword in name_str for keyword in condition_values):
                    cleaned_brand = rule['canonical_brand']
                    break

        return cleaned_brand

    def _get_cleaned_name(self) -> str:
        name_to_clean = self.name
        canonical_brand = self.cleaned_brand

        if not canonical_brand:
            return name_to_clean

        # Compile a list of all possible brand variations to remove.
        brand_details = self.brand_cache.get(canonical_brand, {})
        variations = brand_details.get('name_variations', [])
        
        # Also include the canonical name itself and the original raw brand string.
        strings_to_remove = [canonical_brand, self.brand] + variations
        
        # Remove duplicates and None/empty strings, sort by length descending.
        unique_strings_to_remove = sorted(list(set(s for s in strings_to_remove if s)), key=len, reverse=True)

        # Find the first variation that exists in the name and remove it.
        for s in unique_strings_to_remove:
            pattern = r'(\b' + re.escape(s) + r'\b)'
            if re.search(pattern, name_to_clean, re.IGNORECASE):
                name_to_clean = re.sub(pattern, '', name_to_clean, flags=re.IGNORECASE).strip()
                break
        
        # Final cleanup of extra spaces and size strings.
        if self.raw_sizes:
            for s in self.raw_sizes:
                name_to_clean = re.sub(re.escape(s), '', name_to_clean, flags=re.IGNORECASE).strip()

        units = ['g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms', 'ml', 'millilitre', 'millilitres', 'l', 'litre', 'litres', 'pk', 'pack', 'each', 'ea']
        size_pattern = r'\b\d+\.?\d*\s*(' + '|'.join(units) + r')s?\b'
        name_to_clean = re.sub(size_pattern, '', name_to_clean, flags=re.IGNORECASE)
        
        name_to_clean = re.sub(r'\s+', ' ', name_to_clean).strip()
        return name_to_clean

    def _get_standardized_sizes(self) -> list:
        """
        Performs a multi-pass standardization of raw size strings.
        1. Standardizes text variations (e.g., 'pack' -> 'pk').
        2. Parses numerical values and converts to a canonical unit (e.g., '0.095kg' -> '95g').
        3. De-duplicates based on the final canonical value.
        """
        # --- Pass 1: Standardize text variations (the existing logic) ---
        initial_standardized_strings = set()
        for size in self.raw_sizes:
            s = size.lower().replace(" ", "")
            s = s.replace("pack", "pk")
            s = s.replace("each", "ea")
            initial_standardized_strings.add(s)
    
        # --- Pass 2: Canonical numerical conversion and de-duplication ---
        size_comparer = SizeComparer()
        canonical_sizes = {} # Use a dict to de-duplicate while preserving a preferred string
    
        for size_str in initial_standardized_strings:
            # Use the parser from SizeComparer
            parsed_tuple = size_comparer._parse_size(size_str)
            if parsed_tuple:
                value, unit = parsed_tuple
                # Use the canonical tuple as a key to handle de-duplication
                if parsed_tuple not in canonical_sizes:
                    # Store the preferred string representation
                    canonical_sizes[parsed_tuple] = f"{int(value) if value.is_integer() else value}{unit}"
            else:
                # If the size string can't be parsed, keep it as is.
                # Use the string itself as a key to avoid duplicates.
                if size_str not in canonical_sizes.values():
                    canonical_sizes[('str', size_str)] = size_str
    
        return sorted(list(canonical_sizes.values()))
    # --- Public API ---

    def get_cleaned_barcode(self) -> str or None:
        """ Corresponds to clean_barcode.py logic. """
        if not self.barcode:
            return None

        barcode_str = str(self.barcode).strip().lower()

        if barcode_str == 'notfound' or barcode_str == 'null':
            return None

        barcodes = [b.strip() for b in barcode_str.split(',')]
        
        valid_ean13 = None
        found_12_digit = None

        for b in barcodes:
            if len(b) == 13 and b.isdigit():
                valid_ean13 = b
                break
            elif len(b) == 12 and b.isdigit():
                if not found_12_digit:
                    found_12_digit = f"0{b}"

        if valid_ean13:
            return valid_ean13
        if found_12_digit:
            return found_12_digit

        for b in barcodes:
            if len(b) < 12:
                if self.sku and b == str(self.sku):
                    return None
        
        return None

    def get_raw_sizes(self) -> list:
        """ Public method to get the originally extracted, unique size strings. """
        return self.raw_sizes

    def get_normalized_brand_key(self) -> str:
        """
        Returns a fully normalized version of the cleaned (canonical) brand name.
        This is suitable for use as a unique key.
        """
        return self._clean_value(self.cleaned_brand)

    def get_fully_normalized_name(self) -> str:
        """
        Returns a fully normalized version of the cleaned name, suitable for similarity matching.
        This version is lowercased and has punctuation removed, but retains spaces.
        """
        value = self.cleaned_name
        # Normalize unicode characters, remove accents, etc.
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
        value = value.lower()
        # Remove all non-alphanumeric characters except for whitespace
        value = re.sub(r'[^a-z0-9\s]', '', value)
        # Condense multiple whitespace characters into a single space
        value = re.sub(r'\s+', ' ', value).strip()
        return value

    def get_normalized_name_brand_size_string(self) -> str:
        """ 
        Public method to get the final normalized string for de-duplication.
        This uses a "bag of words" approach to be robust against data entry errors.
        """
        # 1. Get the full string together with spaces intact.
        combined_string = f"{self.cleaned_name} {self.cleaned_brand} {' '.join(self.standardized_sizes)}"

        # 2. Clean the string to remove punctuation and standardize case.
        cleaned_string = unicodedata.normalize('NFKD', combined_string).encode('ascii', 'ignore').decode('utf-8')
        cleaned_string = cleaned_string.lower()
        cleaned_string = re.sub(r'[^a-z0-9\s]', '', cleaned_string)

        # 3. Split into words, sort alphabetically, and join to create the final key.
        words = sorted(list(set(cleaned_string.split())))
        return "".join(words)