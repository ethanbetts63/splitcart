import json

class FileReader:
    """
    Reads and consolidates data from a .jsonl product file.
    """
    def __init__(self, file_path):
        self.file_path = file_path

    def read_and_consolidate(self):
        """
        Reads a .jsonl file, extracts shared metadata from the first line,
        and returns the metadata and a consolidated list of unique product data.
        """
        first_line_meta = None
        consolidated_data = {}

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if not data.get('product'):
                            continue

                        # Capture metadata from the first valid line
                        if first_line_meta is None and data.get('metadata'):
                            first_line_meta = data['metadata']
                        
                        # Use normalized_name_brand_size to ensure uniqueness within the file
                        key = data['product'].get('normalized_name_brand_size')
                        if key and key not in consolidated_data:
                            consolidated_data[key] = data

                    except (json.JSONDecodeError, KeyError):
                        # Ignore malformed lines or lines missing essential keys
                        continue
        except FileNotFoundError:
            return None, []

        return first_line_meta, list(consolidated_data.values())
