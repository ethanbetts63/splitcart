import type { ShoppingPlan } from './ShoppingPlan';

export type OptimizationResult = {
  max_companies: number;
  optimized_cost: number;
  savings: number;
  shopping_plan: ShoppingPlan;
};
