from unittest.mock import patch

import pytest

from companies.tests.factories import CompanyFactory
from pipeline.database_updating_classes.product_updating.path_manager import PathManager
from products.tests.factories import ProductFactory


def _raw(norm_string, category_path):
    return {
        'product': {
            'normalized_name_brand_size': norm_string,
            'category_path': category_path,
        }
    }


@pytest.mark.django_db
class TestPathManager:
    def test_process_batches_bulk_update_and_reuses_classification(self, mock_command):
        company = CompanyFactory(name='Woolworths')
        product_1 = ProductFactory(normalized_name_brand_size='milk-a')
        product_2 = ProductFactory(normalized_name_brand_size='milk-b')
        caches = {
            'products_by_norm_string': {
                product_1.normalized_name_brand_size: product_1.id,
                product_2.normalized_name_brand_size: product_2.id,
            }
        }
        manager = PathManager(mock_command, caches, lambda *args: None)
        raw = [
            _raw(product_1.normalized_name_brand_size, ['Dairy', 'Milk']),
            _raw(product_2.normalized_name_brand_size, ['Dairy', 'Milk']),
        ]

        with (
            patch('pipeline.database_updating_classes.product_updating.path_manager.classify_path') as mock_classify,
            patch('pipeline.database_updating_classes.product_updating.path_manager.Product.objects.bulk_update') as mock_bulk_update,
        ):
            mock_classify.return_value = {
                'path_type': 'canonical_taxonomy',
                'canonical_key': 'dairy/milk',
                'primary_category_slug': 'milk',
            }

            manager.process(raw, company)

        mock_classify.assert_called_once_with('Woolworths', ['Dairy', 'Milk'])
        _, args, kwargs = mock_bulk_update.mock_calls[0]
        assert args[1] == ['category_paths']
        assert kwargs['batch_size'] == 500
