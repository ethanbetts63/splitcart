from django.core.management.base import BaseCommand
from api.utils.substitution_utils.strict_substitution_generator import StrictSubstitutionGenerator
from api.utils.substitution_utils.size_substitution_generator import SizeSubstitutionGenerator
from api.utils.substitution_utils.variant_substitution_generator import VariantSubstitutionGenerator

class Command(BaseCommand):
    help = 'Generates product substitutions based on different heuristic levels.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lvl1',
            action='store_true',
            help='Generate Level 1: Same brand, same product, different size.'
        )
        parser.add_argument(
            '--lvl2',
            action='store_true',
            help='Generate Level 2: Same brand, similar product, similar size.'
        )
        parser.add_argument(
            '--lvl3',
            action='store_true',
            help='Generate Level 3: Different brand, similar product, similar size.'
        )
        parser.add_argument(
            '--lvl4',
            action='store_true',
            help='Generate Level 4: Different brand, similar product, different size.'
        )

    def handle(self, *args, **options):
        lvl1 = options['lvl1']
        lvl2 = options['lvl2']
        lvl3 = options['lvl3']
        lvl4 = options['lvl4']

        # If no specific level is requested, default to running all levels.
        run_all = not any([lvl1, lvl2, lvl3, lvl4])
        if run_all:
            self.stdout.write(self.style.SUCCESS("No specific level requested, running all available generators."))
            lvl1 = lvl2 = lvl3 = lvl4 = True
        
        self.stdout.write(self.style.SUCCESS("--- Starting Substitution Generation ---"))

        if lvl1:
            generator = StrictSubstitutionGenerator(command=self)
            generator.generate()
        
        if lvl2:
            generator = SizeSubstitutionGenerator(command=self)
            generator.generate()

        if lvl3:
            generator = VariantSubstitutionGenerator(command=self)
            generator.generate()

        if lvl4:
            self.stdout.write(self.style.WARNING("Level 4 generator is not yet implemented."))

        self.stdout.write(self.style.SUCCESS("--- Substitution Generation Complete ---"))