import type { ShoppingPlan } from './ShoppingPlan';

export type BestSingleCompany = {
  max_companies: 1;
  optimized_cost: number;
  savings: number;
  shopping_plan: ShoppingPlan;
  items_found_count: number;
  total_items_in_cart: number;
};
