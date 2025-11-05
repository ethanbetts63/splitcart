from abc import ABC, abstractmethod
import ast
from django.db import transaction

class BaseReconciler(ABC):
    """
    An abstract base class for reconciling entities based on a translation table.
    """
    def __init__(self, command, translation_table_path):
        self.command = command
        self.translation_table_path = translation_table_path

    def _load_translation_table(self):
        """
        Safely loads the translation dictionary from the .py file.
        """
        try:
            with open(self.translation_table_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            if '=' in file_content:
                dict_str = file_content.split('=', 1)[1].strip()
                return ast.literal_eval(dict_str)
            return {}
        except (FileNotFoundError, SyntaxError, ValueError) as e:
            self.command.stderr.write(self.command.style.ERROR(f"Error loading translation table from {self.translation_table_path}: {e}"))
            return {}

    @abstractmethod
    def get_model(self):
        """Return the Django model class to be reconciled."""
        pass

    @abstractmethod
    def get_variation_field_name(self):
        """Return the name of the field holding the variation key."""
        pass

    @abstractmethod
    def get_canonical_field_name(self):
        """Return the name of the field holding the canonical key."""
        pass

    @abstractmethod
    def merge_items(self, canonical_item, duplicate_item):
        """Merge the duplicate item into the canonical item."""
        pass

    def run(self):
        """
        The main reconciliation logic.
        """
        model = self.get_model()
        model_name = model._meta.verbose_name
        self.command.stdout.write(self.command.style.SUCCESS(f"{model_name.capitalize()} Reconciler run started."))
        
        translations = self._load_translation_table()

        if not translations:
            self.command.stdout.write(f"{model_name.capitalize()} translation table is empty or could not be loaded. Nothing to reconcile.")
            return

        variation_keys = list(translations.keys())
        
        filter_kwargs = {f"{self.get_variation_field_name()}__in": variation_keys}
        potential_duplicates = model.objects.filter(**filter_kwargs)

        if not potential_duplicates.exists():
            self.command.stdout.write(f"No {model_name}s found matching any variation keys.")
            return

        self.command.stdout.write(f"Found {potential_duplicates.count()} potential duplicate {model_name}s to process.")

        items_to_delete = []
        for duplicate_item in potential_duplicates:
            variation_key = getattr(duplicate_item, self.get_variation_field_name())
            canonical_key = translations.get(variation_key)
            if not canonical_key:
                continue

            try:
                filter_kwargs = {f"{self.get_canonical_field_name()}": canonical_key}
                canonical_item = model.objects.get(**filter_kwargs)
                
                if canonical_item.id == duplicate_item.id:
                    continue

                self.merge_items(canonical_item, duplicate_item)
                if duplicate_item not in items_to_delete:
                    items_to_delete.append(duplicate_item)

            except model.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Could not find canonical {model_name} for key {canonical_key}. Skipping."))
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred for {variation_key}: {e}"))
                continue
        
        if items_to_delete:
            self.command.stdout.write(f"--- Deleting {len(items_to_delete)} merged {model_name}s ---")
            for item in items_to_delete:
                item.delete()

        self.command.stdout.write(self.command.style.SUCCESS(f"{model_name.capitalize()} Reconciler run finished."))
