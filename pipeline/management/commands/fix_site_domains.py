from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings

class Command(BaseCommand):
    help = 'Updates the domain for the default site.'

    def handle(self, *args, **options):
        try:
            # The default site created by Django usually has pk=1, but getting by domain is safer.
            site_to_update = Site.objects.get(domain='example.com')
            new_domain = 'www.splitcart.com.au'
            
            self.stdout.write(f"Found site: {site_to_update.name} with domain {site_to_update.domain}")
            
            site_to_update.domain = new_domain
            site_to_update.name = new_domain
            site_to_update.save()
            
            self.stdout.write(self.style.SUCCESS(f"Successfully updated site domain to '{new_domain}'"))

        except Site.DoesNotExist:
            self.stderr.write(self.style.ERROR("Could not find a site with domain 'example.com'. It may have already been updated."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))