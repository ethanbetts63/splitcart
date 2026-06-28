import type { OptimizationResult } from './OptimizationResult';
import type { BestSingleCompany } from './BestSingleCompany';

export type OptimizationDataSet = {
  baseline_cost: number;
  optimization_results: OptimizationResult[];
  best_single_company?: BestSingleCompany;
};
