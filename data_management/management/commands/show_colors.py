from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Displays all available Django management command color styles.'

    def handle(self, *args, **options):
        self.stdout.write("\n--- Available Django Management Command Color Styles ---")
        
        # Get all callable attributes from self.style
        style_attributes = [
            attr for attr in dir(self.style) 
            if not attr.startswith('_') and callable(getattr(self.style, attr))
        ]

        for attr_name in sorted(style_attributes):
            style_func = getattr(self.style, attr_name)
            self.stdout.write(f"  {attr_name}: {style_func(f'This is {attr_name} style.')}")
        
        self.stdout.write("------------------------------------------------------\n")
