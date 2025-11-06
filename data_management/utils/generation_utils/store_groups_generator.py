from django.db import transaction
from companies.models import Store, StoreGroup, StoreGroupMembership

class StoreGroupsGenerator:
    def __init__(self, command, dev=False):
        self.command = command

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Generating Store Groups Directly in Database ---"))
        
        try:
            with transaction.atomic():
                # 1. Clear all existing group data for a clean slate
                self.command.stdout.write("  - Deleting all existing StoreGroup and StoreGroupMembership records...")
                StoreGroupMembership.objects.all().delete()
                StoreGroup.objects.all().delete()
                self.command.stdout.write("  - Existing records deleted.")

                # 2. Get all stores from the database
                all_stores = list(Store.objects.all())
                self.command.stdout.write(f"  - Found {len(all_stores)} stores to process.")

                # 3. Create a new group for each store
                for store in all_stores:
                    # Create a new group with the store as its own anchor
                    new_group = StoreGroup.objects.create(
                        company=store.company, 
                        anchor=store
                    )
                    # Link the store to its new group
                    StoreGroupMembership.objects.create(store=store, group=new_group)
                
                self.command.stdout.write(self.command.style.SUCCESS(f"  Successfully created {len(all_stores)} new store groups."))

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during store cluster generation: {e}"))
            # The transaction will be rolled back automatically by the 'with' block.
