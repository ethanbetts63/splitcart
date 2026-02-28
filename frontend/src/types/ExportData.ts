import type { ShoppingPlan } from './ShoppingPlan';

export type ExportData = {
  shopping_plan: ShoppingPlan;
  baseline_cost: number;
  optimized_cost: number;
  savings: number;
};
