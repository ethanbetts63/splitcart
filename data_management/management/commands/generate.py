from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Generates data for the application.'

    def add_arguments(self, parser):
        parser.add_argument('--subs', action='store_true', help='Generate product substitutions.')
        parser.add_argument('--cat-links', action='store_true', help='Generate category links.')
        parser.add_argument('--map', action='store_true', help='Generate store location map.')
        parser.add_argument('--primary-cats', action='store_true', help='Generate primary categories.')
        parser.add_argument('--bargains', action='store_true', help='Generate all viable bargain combinations and save to a file.')
        parser.add_argument('--use-stale', action='store_true', help='Include all prices, not just fresh ones, in bargain generation.')
        parser.add_argument('--store-groups', action='store_true', help='Generate store groups.')
        parser.add_argument('--price-comps', action='store_true', help='Generate price comparison data.')
        parser.add_argument('--archive', action='store_true', help='Archive the database.')
        parser.add_argument('--categorize', action='store_true', help='Run the interactive category analyzer.')
        parser.add_argument('--company', type=str, help='Filter map generation by company name or specify company for categorization.')
        parser.add_argument('--dev', action='store_true', help='Use development server URL.')

    def handle(self, *args, **options):
        run_all = not any(options[key] for key in ['subs', 'cat_links', 'map', 'primary_cats', 'bargains', 'store_groups', 'price_comps', 'archive', 'categorize'])
        dev = options['dev']

        if options['subs'] or run_all:
            from data_management.utils.generation_utils.substitutions_generator import SubstitutionsGenerator
            self.stdout.write(self.style.SUCCESS("Generating substitutions..."))
            generator = SubstitutionsGenerator(self, dev=dev)
            generator.run()

        if options['cat_links'] or run_all:
            from data_management.utils.generation_utils.category_links_generator import CategoryLinksGenerator
            self.stdout.write(self.style.SUCCESS("Generating category links..."))
            generator = CategoryLinksGenerator(self, dev=dev)
            generator.run()

        if options['map'] or run_all:
            from data_management.utils.generation_utils.map_generator import MapGenerator
            self.stdout.write(self.style.SUCCESS("Generating store location map..."))
            generator = MapGenerator(self, company_name=options['company'], dev=dev)
            generator.run()

        if options['primary_cats']:
            from data_management.utils.generation_utils.primary_categories_generator import PrimaryCategoriesGenerator
            self.stdout.write(self.style.SUCCESS("Generating primary categories..."))
            generator = PrimaryCategoriesGenerator(self)
            generator.run()

        if options['bargains'] or run_all:
            from data_management.utils.generation_utils.bargain_generator import BargainGenerator
            self.stdout.write(self.style.SUCCESS("Generating all bargain combinations..."))
            generator = BargainGenerator(self, dev=dev, use_stale=options['use_stale'])
            generator.run()

        if options['store_groups'] or run_all:
            from data_management.utils.generation_utils.store_groups_generator import StoreGroupsGenerator
            self.stdout.write(self.style.SUCCESS("Generating store groups..."))
            generator = StoreGroupsGenerator(self, dev=dev)
            generator.run()

        if options['price_comps'] or run_all:
            from data_management.utils.generation_utils.price_comparisons_generator import PriceComparisonsGenerator
            self.stdout.write(self.style.SUCCESS("Generating price comparisons..."))
            generator = PriceComparisonsGenerator(self)
            generator.run()

        if options['archive']:
            from data_management.utils.generation_utils.archive_generator import ArchiveGenerator
            self.stdout.write(self.style.SUCCESS("Archiving database..."))
            generator = ArchiveGenerator(self)
            generator.run()