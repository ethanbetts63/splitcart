import type { OptimizationDataSet } from './OptimizationDataSet';

export type ApiResponse = OptimizationDataSet & {
  no_subs_results?: OptimizationDataSet;
};
