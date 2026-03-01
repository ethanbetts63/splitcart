import re
import unicodedata

class ProductNormalizer:
    """
    A class to encapsulate all product normalization logic.

    This class takes raw product data, processes it through a pipeline of cleaning
    and standardization methods, and provides clean, normalized outputs.
    """
    def __init__(self, product_data, brand_translations=None, product_translations=None):
        """
        Initializes the normalizer with raw product data.

        Args:
            product_data (dict): A dictionary containing product info like 'name', 'brand', etc.
            brand_translations (dict): A dictionary mapping brand variations to canonical names.
            product_translations (dict): A dictionary mapping product name variations to canonical names.
        """
        self.name = str(product_data.get('name', ''))
        raw_brand = product_data.get('brand')
        self.brand = str(raw_brand) if raw_brand else ''
        self.size = str(product_data.get('size', ''))
        self.barcode = product_data.get('barcode')
        self.sku = product_data.get('sku')
        self.brand_translations = brand_translations if brand_translations is not None else {}
        self.product_translations = product_translations if product_translations is not None else {}

        # Immediately process the data to populate internal state
        self.normalized_brand_name = self._get_normalized_brand_name(self.brand)

        self.raw_sizes = self._extract_all_sizes()

        self.standardized_sizes = self._get_standardized_sizes()

    @staticmethod
    def _clean_value(value: str) -> str:
        """ Corresponds to clean_value.py logic. """
        if not isinstance(value, str):
            return ""
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
        value = value.lower()
        value = re.sub(r'[^a-z0-9\s]', '', value)
        words = sorted(list(set(value.split())))
        return " ".join(words)

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

        # Updated regex part to handle optional slash
        separator_pattern = r'\s*[/]?\s*'

        range_pattern = r'(\d+\.?\d*)' + separator_pattern + r'-\s*(\d+\.?\d*)' + separator_pattern + r'(' + '|'.join(all_unit_variations) + r')\b'
        for match in re.finditer(range_pattern, processed_text):
            unit = unit_map[match.group(3)]
            sizes.add(f"{match.group(1)}{unit}")
            sizes.add(f"{match.group(2)}{unit}")
        processed_text = re.sub(range_pattern, '', processed_text)

        multipack_pattern_1 = r'(\d+)\s*[xX]' + separator_pattern + r'(\d+\.?\d*)' + separator_pattern + r'(' + '|'.join(all_unit_variations) + r')\b'
        for match in re.finditer(multipack_pattern_1, processed_text):
            unit = unit_map[match.group(3)]
            sizes.add(f"{match.group(1)}pk")
            sizes.add(f"{match.group(2)}{unit}")
        processed_text = re.sub(multipack_pattern_1, '', processed_text)

        multipack_pattern_2 = r'(\d+\.?\d*)' + separator_pattern + r'(' + '|'.join(all_unit_variations) + r')\s*[xX]\s*(\d+)'
        for match in re.finditer(multipack_pattern_2, processed_text):
            unit = unit_map[match.group(2)]
            sizes.add(f"{match.group(1)}{unit}")
            sizes.add(f"{match.group(3)}pk")
        processed_text = re.sub(multipack_pattern_2, '', processed_text)

        number_unit_pattern = r'(\d+\.?\d*)' + separator_pattern + r'(' + '|'.join(all_unit_variations) + r')\b'
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

    def _get_normalized_brand_name(self, brand_str: str) -> str:
        """
        Resolves the raw brand string to a normalized key.
        """
        if not brand_str:
            return ''

        # Normalize the raw brand string to create a lookup key
        normalized_brand_str = self._clean_value(brand_str)
        
        # Look for a translation
        translated_normalized_brand_str = self.brand_translations.get(normalized_brand_str)
    
        if translated_normalized_brand_str:
            return translated_normalized_brand_str
        else:
            return normalized_brand_str


    def _get_standardized_sizes(self) -> list:
        from data_management.utils.size_comparer import SizeComparer
        """
        Performs a multi-pass standardization of raw size strings.
        1. Standardizes text variations (e.g., 'pack' -> 'pk', '1ea' -> 'ea').
        2. Parses numerical values and converts to a canonical unit (e.g., '0.095kg' -> '95g').
        3. De-duplicates based on the final canonical value.
        """
        # --- Pass 1: Standardize text variations ---
        initial_standardized_strings = set()
        for size in self.raw_sizes:
            s = size.lower().replace(" ", "")
            s = s.replace("pack", "pk")
            s = s.replace("each", "ea")
            if s == '1ea':
                s = 'ea'
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

    def get_cleaned_barcode(self) -> str or None:
        """ Corresponds to clean_barcode.py logic. """
        if not self.barcode:
            return None

        barcode_str = str(self.barcode).strip().lower()

        if barcode_str == 'notfound' or barcode_str == 'null' or barcode_str == '':
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

    def get_normalized_brand_name(self) -> str:
        """
        Returns the non-human-readable, normalized name for the brand.
        """
        return self.normalized_brand_name

    def get_normalized_name_brand_size_string(self) -> str:
        """
        Public method to get the final normalized string for de-duplication.
        This uses a "bag of words" approach to be robust against data entry errors.
        """
        # 1. Get the full string together with spaces intact.
        combined_string = f"{self.name} {self.normalized_brand_name} {' '.join(self.standardized_sizes)}"

        # 2. Clean, sort, and deduplicate words into the generated key.
        generated_key = self._clean_value(combined_string)

        # 3. Look for a translation for the generated key.
        canonical_key = self.product_translations.get(generated_key)
    
        if canonical_key:
            return canonical_key
        else:
            return generated_key