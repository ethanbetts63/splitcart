from django.db import transaction
from companies.models import Store, StoreGroup, StoreGroupMembership

class StoreClustersGenerator:
    def __init__(self, command, dev=False):
        self.command = command
        self.dev = dev

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Re-initializing Store Groups ---"))
        
        try:
            with transaction.atomic():
                # 1. Delete all existing groups
                self.command.stdout.write("  - Deleting all existing Store Groups...")
                StoreGroup.objects.all().delete()
                self.command.stdout.write(self.command.style.SUCCESS("  - All old groups have been deleted."))

                # 2. Fetch all stores
                all_stores = list(Store.objects.all())
                if not all_stores:
                    self.command.stdout.write(self.command.style.WARNING("No stores found in the database."))
                    return

                self.command.stdout.write(f"  - Found {len(all_stores)} stores to process.")
                new_groups = []
                new_memberships = []

                # 3. Prepare new groups and memberships in memory
                for store in all_stores:
                    group = StoreGroup(company=store.company)
                    new_groups.append(group)
                    # The membership will be created after the group gets an ID.

                # 4. Bulk create groups
                self.command.stdout.write(f"  - Creating {len(new_groups)} new groups...")
                StoreGroup.objects.bulk_create(new_groups)

                # 5. Prepare and create memberships and set anchors
                self.command.stdout.write("  - Assigning stores to new groups and setting anchors...")
                for i, store in enumerate(all_stores):
                    group = new_groups[i]
                    group.ambassador = store
                    new_memberships.append(StoreGroupMembership(store=store, group=group))
                
                # 6. Bulk create memberships
                StoreGroupMembership.objects.bulk_create(new_memberships)

                # 7. Bulk update anchors
                StoreGroup.objects.bulk_update(new_groups, ['ambassador'])

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred: {e}"))
            return

        self.command.stdout.write(self.command.style.SUCCESS(f"Successfully created {len(new_groups)} new store groups."))
