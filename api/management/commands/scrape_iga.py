import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_iga import scrape_and_save_iga_data

class Command(BaseCommand):
    """
    This Django management command initiates the scraping process for IGA stores.
    It dynamically builds a list of all specific subcategories to ensure each
    product is scraped only once.
    """
    help = 'Launches the scraper to fetch all product data from specified IGA stores.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting IGA scraping process ---"))

        company_name = "iga"
        stores_to_scrape = [
            {'store_name': 'east-victoria-park', 'store_id': '48264'},
        ]
        
        # Load the category hierarchy from the file
        category_hierarchy = self.get_category_hierarchy()
        
        # Recursively find all the "leaf" categories to scrape
        categories_to_scrape = self.find_leaf_categories(category_hierarchy)

        self.stdout.write(f"Found {len(stores_to_scrape)} IGA store(s) to scrape.")
        self.stdout.write(f"Extracted {len(categories_to_scrape)} specific subcategories to process.")

        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
        os.makedirs(raw_data_path, exist_ok=True)
        self.stdout.write(f"Data will be saved to: {raw_data_path}")
        
        self.stdout.write("Handing off to the scraper function...")
        scrape_and_save_iga_data(company_name, stores_to_scrape, categories_to_scrape, raw_data_path)

        self.stdout.write(self.style.SUCCESS("\n--- IGA scraping process complete ---"))

    def get_category_hierarchy(self) -> list:
        """Loads the category hierarchy from the JSON file."""
        # In a real-world scenario, you might fetch this from the API directly.
        # For now, we use the provided text file.
        # This assumes 'iga_category_hierachy.txt' is in a known location, e.g., 'api/data/'
        file_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'iga_category_hierachy.txt')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # The actual categories are nested under 'children' of the root object
                return data.get('children', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.stdout.write(self.style.ERROR(f"Could not load IGA category hierarchy file. Error: {e}"))
            return []

    def find_leaf_categories(self, nodes: list) -> list:
        """
        Recursively traverses the category tree to find all nodes that have
        no children (the "leaf" nodes).
        
        Args:
            nodes: A list of category nodes from the hierarchy.

        Returns:
            A flat list of the 'displayName' of each leaf category.
        """
        leaf_categories = []
        for node in nodes:
            children = node.get('children', [])
            if not children:
                # This is a leaf node, add its name to our list
                leaf_categories.append(node['displayName'])
            else:
                # This is not a leaf node, so we go deeper
                leaf_categories.extend(self.find_leaf_categories(children))
        return leaf_categories

