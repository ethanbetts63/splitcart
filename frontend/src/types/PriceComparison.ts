export interface PriceComparison {
  company_a_id: number;
  company_a_name: string;
  company_b_id: number;
  company_b_name: string;
  overlap_count: number;
  cheaper_at_a_percentage: number;
  cheaper_at_b_percentage: number;
  same_price_percentage: number;
}
