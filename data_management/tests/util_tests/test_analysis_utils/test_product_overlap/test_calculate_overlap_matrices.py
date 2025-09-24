import pandas as pd
from django.test import TestCase
from data_management.utils.analysis_utils.product_overlap.calculate_overlap_matrices import calculate_overlap_matrices

class CalculateOverlapMatricesTest(TestCase):
    def test_calculate_overlap_matrices(self):
        entity_products = {
            'store_a': {'prod1', 'prod2', 'prod3'},
            'store_b': {'prod2', 'prod3', 'prod4', 'prod5'},
            'store_c': {'prod1', 'prod6'}
        }

        overlap_matrix, percent_of_row, percent_of_col, avg_percent = calculate_overlap_matrices(entity_products)

        # Test overlap_matrix
        self.assertEqual(overlap_matrix.loc['store_a', 'store_a'], 3)
        self.assertEqual(overlap_matrix.loc['store_b', 'store_b'], 4)
        self.assertEqual(overlap_matrix.loc['store_c', 'store_c'], 2)
        self.assertEqual(overlap_matrix.loc['store_a', 'store_b'], 2)
        self.assertEqual(overlap_matrix.loc['store_a', 'store_c'], 1)
        self.assertEqual(overlap_matrix.loc['store_b', 'store_c'], 0)

        # Test percent_of_row
        self.assertAlmostEqual(percent_of_row.loc['store_a', 'store_b'], (2/3) * 100)
        self.assertAlmostEqual(percent_of_row.loc['store_b', 'store_a'], (2/4) * 100)
        self.assertAlmostEqual(percent_of_row.loc['store_a', 'store_c'], (1/3) * 100)
        self.assertAlmostEqual(percent_of_row.loc['store_c', 'store_a'], (1/2) * 100)

        # Test percent_of_col
        self.assertAlmostEqual(percent_of_col.loc['store_a', 'store_b'], (2/4) * 100)
        self.assertAlmostEqual(percent_of_col.loc['store_b', 'store_a'], (2/3) * 100)
        self.assertAlmostEqual(percent_of_col.loc['store_a', 'store_c'], (1/2) * 100)
        self.assertAlmostEqual(percent_of_col.loc['store_c', 'store_a'], (1/3) * 100)

        # Test avg_percent
        self.assertAlmostEqual(avg_percent.loc['store_a', 'store_b'], (((2/3)*100) + ((2/4)*100)) / 2)
        self.assertAlmostEqual(avg_percent.loc['store_b', 'store_a'], (((2/3)*100) + ((2/4)*100)) / 2)
