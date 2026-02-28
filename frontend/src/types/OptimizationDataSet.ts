import type { OptimizationResult } from './OptimizationResult';
import type { BestSingleStore } from './BestSingleStore';

export type OptimizationDataSet = {
  baseline_cost: number;
  optimization_results: OptimizationResult[];
  best_single_store?: BestSingleStore;
};
