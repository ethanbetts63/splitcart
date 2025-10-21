export interface ShoppingPlan {
  [storeName: string]: {
    items: {
      product_name: string;
      brand: string | null;
      size: string;
      quantity: number;
      price: number;
      image_url: string | null;
    }[];
    company_name: string;
    store_address: string;
    total_cost?: number;
  };
}

export interface OptimizationResult {
  max_stores: number;
  optimized_cost: number;
  savings: number;
  shopping_plan: ShoppingPlan;
}

export interface BestSingleStore {
    max_stores: 1;
    optimized_cost: number;
    savings: number;
    shopping_plan: ShoppingPlan;
    items_found_count: number;
    total_items_in_cart: number;
}

export interface OptimizationDataSet {
    baseline_cost: number;
    optimization_results: OptimizationResult[];
    best_single_store?: BestSingleStore;
}

export interface ApiResponse extends OptimizationDataSet {
  no_subs_results?: OptimizationDataSet;
}

export interface ExportData {
    shopping_plan: ShoppingPlan;
    baseline_cost: number;
    optimized_cost: number;
    savings: number;
}