import pandas as pd
from django.test import TestCase
from unittest.mock import patch, MagicMock
import matplotlib.pyplot as plt
from api.utils.analysis_utils.product_overlap.generate_heatmap_image import generate_heatmap_image

class GenerateHeatmapImageTest(TestCase):
    @patch('api.utils.analysis_utils.product_overlap.generate_heatmap_image.plt.title')
    @patch('api.utils.analysis_utils.product_overlap.generate_heatmap_image.plt.savefig')
    @patch('api.utils.analysis_utils.product_overlap.generate_heatmap_image.os.makedirs')
    def test_generate_heatmap_image_for_company(self, mock_makedirs, mock_savefig, mock_title):
        # Sample data
        entity_products = {
            'company_a': {'prod1', 'prod2', 'prod3'},
            'company_b': {'prod2', 'prod3', 'prod4', 'prod5'},
        }
        # Create dummy matrices
        entities = list(entity_products.keys())
        overlap_matrix = pd.DataFrame([[3, 2], [2, 4]], index=entities, columns=entities)
        percent_of_row = pd.DataFrame([[100.0, 66.6], [50.0, 100.0]], index=entities, columns=entities)
        percent_of_col = pd.DataFrame([[100.0, 50.0], [66.6, 100.0]], index=entities, columns=entities)
        avg_percent = pd.DataFrame([[100.0, 58.3], [58.3, 100.0]], index=entities, columns=entities)

        generate_heatmap_image(overlap_matrix, percent_of_row, percent_of_col, avg_percent, 'company')

        mock_makedirs.assert_called()
        mock_savefig.assert_called_once()
        mock_title.assert_called_once()
        # Check that the title is correct for company
        self.assertIn('Product Overlap Between Companies', mock_title.call_args[0][0])

    @patch('api.utils.analysis_utils.product_overlap.generate_heatmap_image.plt.title')
    @patch('api.utils.analysis_utils.product_overlap.generate_heatmap_image.plt.savefig')
    @patch('api.utils.analysis_utils.product_overlap.generate_heatmap_image.os.makedirs')
    def test_generate_heatmap_image_for_store(self, mock_makedirs, mock_savefig, mock_title):
        # Sample data
        entity_products = {
            'store_a': {'prod1', 'prod2', 'prod3'},
            'store_b': {'prod2', 'prod3', 'prod4', 'prod5'},
        }
        # Create dummy matrices
        entities = list(entity_products.keys())
        overlap_matrix = pd.DataFrame([[3, 2], [2, 4]], index=entities, columns=entities)
        percent_of_row = pd.DataFrame([[100.0, 66.6], [50.0, 100.0]], index=entities, columns=entities)
        percent_of_col = pd.DataFrame([[100.0, 50.0], [66.6, 100.0]], index=entities, columns=entities)
        avg_percent = pd.DataFrame([[100.0, 58.3], [58.3, 100.0]], index=entities, columns=entities)

        generate_heatmap_image(overlap_matrix, percent_of_row, percent_of_col, avg_percent, 'store', 'MyCompany')

        mock_makedirs.assert_called()
        mock_savefig.assert_called_once()
        mock_title.assert_called_once()
        # Check that the title is correct for store
        self.assertIn('Product Overlap Between Stores for MyCompany', mock_title.call_args[0][0])