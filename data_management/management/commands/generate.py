from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Generates data for the application.'

    def add_arguments(self, parser):
        parser.add_argument('--subs', action='store_true', help='Generate product substitutions.')
        parser.add_argument('--cat-links', action='store_true', help='Generate category links.')
        parser.add_argument('--pop-cats', action='store_true', help='Generate popular categories.')
        parser.add_argument('--map', action='store_true', help='Generate store location map.')
        parser.add_argument('--super-cats', action='store_true', help='Generate super categories.')
        parser.add_argument('--bargains', action='store_true', help='Generate bargains.')
        parser.add_argument('--store-clusters', action='store_true', help='Generate store clusters.')
        parser.add_argument('--archive', action='store_true', help='Archive the database.')
        parser.add_argument('--categorize', action='store_true', help='Run the interactive category analyzer.')
        parser.add_argument('--company', type=str, help='Filter map generation by company name or specify company for categorization.')
        parser.add_argument('--dev', action='store_true', help='Use development server URL.')

    def handle(self, *args, **options):
        run_all = not any(options.values()) # Check if any flag is set
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

        if options['pop_cats'] or run_all:
            from data_management.utils.generation_utils.popular_categories_generator import PopularCategoriesGenerator
            self.stdout.write(self.style.SUCCESS("Generating popular categories..."))
            generator = PopularCategoriesGenerator(self)
            generator.run()

        if options['map'] or run_all:
            from data_management.utils.generation_utils.map_generator import MapGenerator
            self.stdout.write(self.style.SUCCESS("Generating store location map..."))
            generator = MapGenerator(self, company_name=options['company'], dev=dev)
            generator.run()

        if options['super_cats'] or run_all:
            from data_management.utils.generation_utils.super_categories_generator import SuperCategoriesGenerator
            self.stdout.write(self.style.SUCCESS("Generating super categories..."))
            generator = SuperCategoriesGenerator(self)
            generator.run()

        if options['bargains'] or run_all:
            from data_management.utils.generation_utils.bargains_generator import BargainsGenerator
            self.stdout.write(self.style.SUCCESS("Generating bargains..."))
            generator = BargainsGenerator(self, dev=dev)
            generator.run()

        if options['store_clusters'] or run_all:
            from data_management.utils.generation_utils.store_clusters_generator import StoreClustersGenerator
            self.stdout.write(self.style.SUCCESS("Generating store clusters..."))
            generator = StoreClustersGenerator(self, dev=dev)
            generator.run()

        if options['archive']:
            from data_management.utils.generation_utils.archive_generator import ArchiveGenerator
            self.stdout.write(self.style.SUCCESS("Archiving database..."))
            generator = ArchiveGenerator(self)
            generator.run()

        if options['categorize']:
            from data_management.management.commands.categorization_analyzer import Command as CategorizationAnalyzerCommand
            self.stdout.write(self.style.SUCCESS("Running interactive category analyzer..."))
            # Create an instance of the CategorizationAnalyzerCommand and call its handle method
            analyzer_command = CategorizationAnalyzerCommand()
            analyzer_command.handle(company=options['company'], dev=dev)
