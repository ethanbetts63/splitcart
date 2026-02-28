import type { PriceComparisonData } from './PriceComparisonData';

export interface PrimaryCategory {
  name: string;
  slug: string;
  price_comparison_data?: PriceComparisonData;
}
