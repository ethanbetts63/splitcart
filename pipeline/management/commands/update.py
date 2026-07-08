import json
import os
import time
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from companies.models import Company
from pipeline.database_updating_classes.product_updating.update_orchestrator import UpdateOrchestrator
from pipeline.database_updating_classes.category_link_update_orchestrator import CategoryLinkUpdateOrchestrator                  
from pipeline.database_updating_classes.substitution_update_orchestrator import SubstitutionUpdateOrchestrator

class Command(BaseCommand):
    help = 'Updates the database with data from various sources.'

    def add_arguments(self, parser):
        parser.add_argument('--products', action='store_true', help='Update products from the product_inbox directory.')
        parser.add_argument('--companies', action='store_true', help='Update companies from archived company seed data.')
        parser.add_argument('--post-process-only', action='store_true', help='Skip file processing and run only the post-processing steps for products.')
        parser.add_argument('--cat-links', action='store_true', help='Update category links from the category_links_inbox directory.')
        parser.add_argument('--subs', action='store_true', help='Update substitutions from the substitutions_inbox directory.')
        parser.add_argument('--archive', action='store_true', help='Read from archive data for supported update types.')

    def handle(self, *args, **options):
        run_products_processed = options['products']
        run_companies = options['companies']
        run_category_links = options['cat_links']
        run_substitutions = options['subs']
        post_process_only = options['post_process_only']
        archive = options['archive']

        if run_companies:
            if not archive:
                raise CommandError('update --companies currently requires --archive.')
            self._update_companies_from_archive()

        if run_substitutions:
            orchestrator = SubstitutionUpdateOrchestrator(self)
            orchestrator.run()

        if run_category_links:
            orchestrator = CategoryLinkUpdateOrchestrator(self)
            orchestrator.run()

        if run_products_processed:
            if post_process_only:
                self.stdout.write(self.style.SUCCESS('--- Running only product post-processing tasks ---'))
                orchestrator = UpdateOrchestrator(self, post_process_only=True)
                orchestrator.run()
            else:
                source_path = (
                    settings.PIPELINE_DATA_DIR / 'archive' / 'product_archive'
                    if archive
                    else settings.PIPELINE_DATA_DIR / 'inboxes' / 'product_inbox'
                )

                def files_exist_in_inbox():
                    if not os.path.exists(source_path):
                        return False
                    for _, _, files in os.walk(source_path):
                        if any(f.endswith('.jsonl') for f in files):
                            return True
                    return False

                error_counter = 0
                MAX_RESTARTS = 10

                if archive:
                    if files_exist_in_inbox():
                        self.stdout.write(self.style.SUCCESS('Starting archived product update...'))
                        orchestrator = UpdateOrchestrator(
                            self,
                            source_path=source_path,
                            preserve_source_files=True,
                        )
                        orchestrator.run()
                    else:
                        self.stdout.write(self.style.WARNING('No product archive files found.'))
                    self.stdout.write(self.style.SUCCESS('--- Product update from archive complete ---'))
                    return

                while files_exist_in_inbox():
                    if error_counter >= MAX_RESTARTS:
                        self.stderr.write(self.style.ERROR(
                            f"Update command halted after {MAX_RESTARTS} consecutive restarts due to duplicate barcode errors."
                        ))
                        break
                    
                    try:
                        self.stdout.write(self.style.SUCCESS('Starting update orchestrator...'))
                        orchestrator = UpdateOrchestrator(
                            self,
                            source_path=source_path,
                            preserve_source_files=archive,
                        )
                        orchestrator.run()
                        # A successful run resets the counter
                        error_counter = 0
                        self.stdout.write(self.style.SUCCESS('Update cycle finished. Waiting 30 seconds before checking for more files...'))
                        time.sleep(30)
                    except IntegrityError as e:
                        if 'Duplicate entry' in str(e) and 'for key \'products_product.barcode\'' in str(e):
                            self.stdout.write(self.style.WARNING(
                                f"Duplicate barcode error detected. Waiting 30 seconds before restarting... (Attempt {error_counter + 1}/{MAX_RESTARTS})"
                            ))
                            error_counter += 1
                            continue # Loop to the next attempt
                        else:
                            # It's a different integrity error, we should not loop.
                            self.stderr.write(self.style.ERROR(f"An unhandled IntegrityError occurred: {e}"))
                            raise # Re-raise and halt
                    except Exception as e:
                        # Any other exception should also break the loop.
                        self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
                        raise # Re-raise and halt

            self.stdout.write(self.style.SUCCESS('--- Product update from inbox complete ---'))

    def _update_companies_from_archive(self):
        archive_file = settings.PIPELINE_DATA_DIR / 'archive' / 'company_archive' / 'companies.json'
        if not archive_file.exists():
            raise CommandError(f'Company archive not found: {archive_file}')

        with archive_file.open(encoding='utf-8') as f:
            companies = json.load(f)

        created_count = 0
        updated_count = 0
        for company_data in companies:
            name = company_data['name']
            defaults = {
                'name': name,
                'image_url_template': company_data.get('image_url_template'),
            }
            company = Company.objects.filter(name__iexact=name).first()
            if company:
                for field, value in defaults.items():
                    setattr(company, field, value)
                company.save(update_fields=list(defaults))
                updated_count += 1
            else:
                Company.objects.create(**defaults)
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'--- Company update from archive complete: {created_count} created, {updated_count} updated ---'
        ))
