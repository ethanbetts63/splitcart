//==============================================================================
//|                                 Shared Types                                 |
//------------------------------------------------------------------------------
//| This file contains all shared TypeScript types for the application.        |
//| It is organized by data model and feature area.                            |
//==============================================================================

// --- Core Data Models ---

export type CompanyPriceInfo = {
  company: string;
  price_display: string;
  is_lowest: boolean;
  image_url?: string;
  per_unit_price_string?: string;
};

export type Product = {
  id: number;
  name: string;
  brand_name?: string;
  size?: string;
  image_url?: string;
  prices: CompanyPriceInfo[];
  quantity?: number; // Often added for cart item context
  level?: string;
  level_description?: string;
  primary_category?: {
    name: string;
    slug: string;
  };
};

export type CartSubstitution = {
  id: string;
  substituted_product: Product;
  quantity: number;
  is_approved: boolean;
  created_at?: string;
  updated_at?: string;
};

export type CartItem = {
  id: string;
  product: Product;
  quantity: number;
  baseline_price?: number; // Added for store-specific baseline calculation
  substitutions?: CartSubstitution[];
  created_at?: string;
  updated_at?: string;
};

export type Cart = {
  id: string;
  name: string;
  items: CartItem[];
  is_active: boolean;
  selected_store_list?: SelectedStoreListType;
  created_at?: string;
  updated_at?: string;
};

// --- Store & Location Types ---

export type SelectedStoreListType = {
  id: string;
  name: string;
  stores: number[];
  created_at: string;
  updated_at: string;
  last_used_at: string;
};

export type Store = {
  id: number;
  company_name: string;
  store_name: string;
  latitude: number;
  longitude: number;
};

// --- API & Optimization Types ---

export type ShoppingPlan = {
  [storeName: string]: {
    items: {
      product_name: string;
      brand: string | null;
      size: string;
      quantity: number;
      price: number;
      image_url: string | null;
      image_base64?: string; // For PDF generation
    }[];
    company_name: string;
    store_address: string;
    total_cost?: number;
    subtotal?: number; // For PDF generation
  };
};

export type OptimizationResult = {
  max_stores: number;
  optimized_cost: number;
  savings: number;
  shopping_plan: ShoppingPlan;
};

export type BestSingleStore = {
    max_stores: 1;
    optimized_cost: number;
    savings: number;
    shopping_plan: ShoppingPlan;
    items_found_count: number;
    total_items_in_cart: number;
};

export type OptimizationDataSet = {
  baseline_cost: number;
  optimization_results: OptimizationResult[];
  best_single_store?: BestSingleStore;
};

export type ApiResponse = OptimizationDataSet & {
  no_subs_results?: OptimizationDataSet;
};

export type ExportData = {
    shopping_plan: ShoppingPlan;
    baseline_cost: number;
    optimized_cost: number;
    savings: number;
};

// --- Auth & Setup Types ---

export type InitialSetupData = {
  cart: Cart;
  anonymous_id?: string;
};

// --- Pillar Page Types ---

export interface PrimaryCategory {
  name: string;
  slug: string;
}

export interface FAQ {
  question: string;
  answer: string;
}

export interface PillarPage {
  name: string;
  slug: string;
  hero_title: string;
  introduction_paragraph: string;
  image_path: string;
  primary_categories: PrimaryCategory[];
  faqs: FAQ[];
}
