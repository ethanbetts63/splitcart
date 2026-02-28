import type { CompanyPriceInfo } from './CompanyPriceInfo';

export type Product = {
  id: number;
  name: string;
  brand_name?: string;
  size?: string;
  image_url?: string;
  prices: CompanyPriceInfo[];
  quantity?: number;
  level?: string;
  level_description?: string;
  primary_category?: {
    name: string;
    slug: string;
  };
  min_unit_price?: number | null;
  slug?: string;
  bargain_info?: {
    discount_percentage: number;
    cheapest_company_name: string;
  } | null;
  best_discount?: number;
  cheaper_store_name?: string;
  cheaper_company_name?: string;
};
