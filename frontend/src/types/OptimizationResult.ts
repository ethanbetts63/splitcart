import type { ShoppingPlan } from './ShoppingPlan';

export type OptimizationResult = {
  max_stores: number;
  optimized_cost: number;
  savings: number;
  shopping_plan: ShoppingPlan;
};
