from django.core.management.base import BaseCommand
from companies.models import Store

def _clean_postcode(postcode: str) -> str | None:
    """
    Cleans a postcode string: adds leading zero for 3-digit postcodes,
    discards non-4-digit postcodes.
    """
    if not isinstance(postcode, str):
        return None

    cleaned_postcode = postcode.strip()

    if len(cleaned_postcode) == 3 and cleaned_postcode.isdigit():
        return '0' + cleaned_postcode
    elif len(cleaned_postcode) == 4 and cleaned_postcode.isdigit():
        return cleaned_postcode
    else:
        return None

class Command(BaseCommand):
    help = 'Fixes postcode entries in existing Store models by adding leading zeros or discarding invalid formats.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Fixing Store Postcodes ---"))

        fixed_count = 0
        skipped_count = 0

        for store in Store.objects.all():
            original_postcode = store.postcode
            cleaned_postcode = _clean_postcode(original_postcode)

            if cleaned_postcode != original_postcode:
                if cleaned_postcode is None:
                    self.stdout.write(self.style.WARNING(f"Discarding invalid postcode '{original_postcode}' for store {store.store_name} (ID: {store.id})."))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Fixed postcode for store {store.store_name} (ID: {store.id}): '{original_postcode}' -> '{cleaned_postcode}'."))
                store.postcode = cleaned_postcode
                store.save()
                fixed_count += 1
            else:
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nFixed {fixed_count} store postcodes."))
        self.stdout.write(self.style.SUCCESS(f"Skipped {skipped_count} store postcodes (already valid or no change needed)."))
        self.stdout.write(self.style.SUCCESS("--- Store Postcode Fix Complete ---"))
