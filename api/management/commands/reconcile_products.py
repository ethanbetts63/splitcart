from django.core.management.base import BaseCommand
from api.database_updating_classes.product_reconciler import ProductReconciler

class Command(BaseCommand):
    help = 'Reconciles duplicate products based on the translation table.'

    def handle(self, *args, **options):
        reconciler = ProductReconciler(self)
        reconciler.run()
