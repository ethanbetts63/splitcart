from django.core.management.base import BaseCommand
from companies.models import Category

class Command(BaseCommand):
    help = 'Checks all Category objects to ensure none have more than one parent.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Starting Category Parent Check ---'))
        
        # Prefetch the 'parents' relationship to avoid thousands of extra DB queries
        all_categories = Category.objects.prefetch_related('parents').all()
        
        problematic_categories_count = 0
        
        self.stdout.write(f"Scanning {all_categories.count()} categories...")

        for category in all_categories:
            parent_count = category.parents.count()
            
            if parent_count > 1:
                problematic_categories_count += 1
                
                # Collect parent names for a clean error message
                parent_names = [parent.name for parent in category.parents.all()]
                
                self.stdout.write(self.style.ERROR(
                    f"\n[ERROR] Category '{category.name}' (ID: {category.id}, Company: {category.company.name}) has {parent_count} parents:"
                ))
                for name in parent_names:
                    self.stdout.write(self.style.ERROR(f"  - {name}"))

        self.stdout.write("\n" + "="*50)
        if problematic_categories_count > 0:
            self.stdout.write(self.style.WARNING(
                f"Check complete. Found {problematic_categories_count} categories with more than one parent."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Check complete. All categories have one or zero parents."
            ))
        self.stdout.write("="*50)
