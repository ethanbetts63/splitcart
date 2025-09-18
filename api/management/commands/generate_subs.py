from django.core.management.base import BaseCommand
from api.utils.substitution_utils.lvl1_substitution_generator import Lvl1SubstitutionGenerator
from api.utils.substitution_utils.lvl2_substitution_generator import Lvl2SubstitutionGenerator
from api.utils.substitution_utils.lvl3_substitution_generator import Lvl3SubstitutionGenerator
from api.utils.substitution_utils.lvl4_substitution_generator import Lvl4SubstitutionGenerator

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
            help='Generate Level 3: Semantic Similarity.'
        )
        parser.add_argument(
            '--lvl4',
            action='store_true',
            help='Generate Level 4: Linked Category Semantic Similarity (includes MATCH, CLOSE, and DISTANT links).'
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
            generator = Lvl1SubstitutionGenerator(command=self)
            generator.generate()
        
        if lvl2:
            generator = Lvl2SubstitutionGenerator(command=self)
            generator.generate()

        if lvl3:
            generator = Lvl3SubstitutionGenerator(command=self)
            generator.generate()

        if lvl4:
            generator = Lvl4SubstitutionGenerator(command=self)
            generator.generate()

        self.stdout.write(self.style.SUCCESS("--- Substitution Generation Complete ---"))
